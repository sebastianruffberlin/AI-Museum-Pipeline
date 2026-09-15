from __future__ import annotations

import datetime
import json

from ..configuration import RuntimeConfig
from ..infrastructure.llm import LLMClient
from ..persistence.postgres import PostgresStore
from .jsonutil import clean_and_parse


class EmotionModule:
    def __init__(self,cfg:RuntimeConfig,store:PostgresStore,llm:LLMClient):
        self.cfg=cfg; self.store=store; self.llm=llm; self.profile=cfg.museum.emotion

    def annotation_set(self)->str:
        return str(self.profile.get("annotation_prefix","emotion_"))+datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    def _schema(self,name:str)->dict:
        from ..skills.loader import SkillLoader
        skill = "emotion-generation" if "gen" in name else "emotion-judge"
        return SkillLoader(self.cfg).schema(skill)

    def vocabulary(self,conn)->str:
        resources=self.profile.get("resources") or {}
        if resources.get("source")=="database":
            row=self.store.query_profile_resource(conn,self.cfg.museum.root/"emotion"/resources["vocabulary_query"])
            if row.get("value") is not None:
                value=row["value"]
                return value if isinstance(value,str) else json.dumps(value,ensure_ascii=False)
        data=json.loads((self.cfg.museum.root/"emotion"/resources["file_fallback"]).read_text(encoding="utf-8"))
        return json.dumps(data,ensure_ascii=False)

    def _prompt_name(self,key:str)->str:
        p=self.profile.get("prompts") or {}
        if self.cfg.settings.prompt_variant=="cache" and p.get(key+"_cache"):
            return p[key+"_cache"]
        return p[key]

    def generator_body(self,master:str,context:str,vocab:str,image_b64:str)->dict:
        p=self.profile.get("prompts") or {}
        system=self.cfg.museum.prompt(p["generator_system"])
        tmpl=self.cfg.museum.prompt(self._prompt_name("generator_user"))
        user=(tmpl.replace("${item.master_caption}",master or "")
                  .replace("${item.context_data_string}",context or "")
                  .replace("${typeof VOCAB==='string'?VOCAB:JSON.stringify(VOCAB)}",vocab or ""))
        body=self.cfg.models.request_defaults("emotion.generator")
        body.update({"messages":[{"role":"system","content":system},{"role":"user","content":[{"type":"text","text":user},{"type":"image_url","image_url":{"url":image_b64}}]}],"response_format":{"type":"json_schema","json_schema":{"name":"mh","strict":True,"schema":self._schema("emo_gen_schema")}}})
        return body

    def judge_body(self,master:str,context:str,vocab:str,lesarten:list,image_b64:str)->dict:
        p=self.profile.get("prompts") or {}
        system=self.cfg.museum.prompt(p["judge_system"])
        tmpl=self.cfg.museum.prompt(self._prompt_name("judge_user"))
        user=(tmpl.replace("${item.master_caption}",master or "")
                  .replace("${item.context_data_string}",context or "")
                  .replace("${typeof VOCAB==='string'?VOCAB:JSON.stringify(VOCAB)}",vocab or "")
                  .replace("${JSON.stringify(item.generator_lesarten||[])}",json.dumps(lesarten,ensure_ascii=False)))
        body=self.cfg.models.request_defaults("emotion.judge")
        body.update({"messages":[{"role":"system","content":system},{"role":"user","content":[{"type":"text","text":user},{"type":"image_url","image_url":{"url":image_b64}}]}],"response_format":{"type":"json_schema","json_schema":{"name":"mh","strict":True,"schema":self._schema("emo_judge_schema")}}})
        return body

    def run_generator(self,conn,master:str,context:str,image_b64:str)->dict:
        vocab=self.vocabulary(conn)
        raw=self.llm.chat_content("emotion.generator",self.generator_body(master,context,vocab,image_b64))
        gen=clean_and_parse(raw) or {}
        return {"lesarten":gen.get("lesarten",[]) or [],"freie_wirkung":gen.get("freie_wirkung",[]) or [],"nicht_mappbar":gen.get("nicht_mappbar",[]) or [],"keine_lesart":gen.get("keine_lesart_begruendung")}

    def run_judge(self,conn,master:str,context:str,image_b64:str,gen_result:dict)->dict:
        lesarten=gen_result.get("lesarten",[]) or []
        if not lesarten: return {"urteile":[]}
        vocab=self.vocabulary(conn)
        raw=self.llm.chat_content("emotion.judge",self.judge_body(master,context,vocab,lesarten,image_b64))
        return clean_and_parse(raw) or {"urteile":[]}

    def write(self,conn,obj_id:str,master:str,gen_result:dict,judge_result:dict)->int:
        annot=self.annotation_set(); lesarten=gen_result.get("lesarten",[]) or []; verdicts=judge_result.get("urteile",[]) or []
        vmap={v.get("concept_id_in"):v for v in verdicts if isinstance(v,dict)}
        gen_model=self.cfg.models.logical_model("emotion.generator"); judge_model=self.cfg.models.logical_model("emotion.judge")
        for reading in lesarten:
            verdict=vmap.get(reading.get("concept_id"),{"action":"confirmed","concept_id_out":reading.get("concept_id"),"status":"ungeprueft","judge_comment":"","validation_issues":[]})
            out=verdict.get("concept_id_out") or reading.get("concept_id")
            self.store.write_emotion(conn,{"obj_id":obj_id,"annotation_set_id":annot,"concept_id":out,"concept_id_original":reading.get("concept_id") if verdict.get("action")=="remapped" else "","reading_statement":reading.get("reading_statement",""),"reading_scope":reading.get("reading_scope","object_overall"),"why":reading.get("why",""),"evidence_json":json.dumps(reading.get("evidence",[]),ensure_ascii=False),"judge_status":verdict.get("status","ungeprueft"),"judge_action":verdict.get("action","confirmed"),"judge_comment":verdict.get("judge_comment",""),"validation_issues":list(verdict.get("validation_issues") or []),"caption_used":master or "","perspective_type":self.profile.get("perspective_type","machine_proposal"),"vocabulary_version":str(self.profile.get("vocabulary_version","")),"generator_model":gen_model,"judge_model":judge_model,"generator_prompt":str(self.profile.get("generator_prompt_version","")),"judge_prompt":str(self.profile.get("judge_prompt_version",""))})
        self.store.write_emotion_run(conn,{"obj_id":obj_id,"annotation_set_id":annot,"reading_count":len(lesarten),"visible_findings":[],"depicted_situations":[],"free_effects_json":json.dumps(gen_result.get("freie_wirkung",[]),ensure_ascii=False),"unmappable_effects_json":json.dumps(gen_result.get("nicht_mappbar",[]),ensure_ascii=False),"considered_rejected_json":json.dumps([],ensure_ascii=False),"no_reading_reason":gen_result.get("keine_lesart"),"caption_used":master or "","vocabulary_version":str(self.profile.get("vocabulary_version","")),"generator_model":gen_model,"judge_model":judge_model,"generator_prompt":str(self.profile.get("generator_prompt_version",""))})
        return len(lesarten)

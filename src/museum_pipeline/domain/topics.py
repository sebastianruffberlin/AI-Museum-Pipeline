from __future__ import annotations

import datetime
import json
from typing import Any

from ..configuration import RuntimeConfig
from ..infrastructure.llm import LLMClient
from ..persistence.postgres import PostgresStore
from .jsonutil import clean_and_parse


class TopicsModule:
    def __init__(self,cfg:RuntimeConfig,store:PostgresStore,llm:LLMClient):
        self.cfg=cfg; self.store=store; self.llm=llm; self.profile=cfg.museum.topics

    def annotation_set(self)->str:
        return str(self.profile.get("annotation_prefix","topics_"))+datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    def _schema(self,name:str)->dict:
        skill = "topic-generation" if "gen" in name else "topic-judge"
        from ..skills.loader import SkillLoader
        return SkillLoader(self.cfg).schema(skill)

    def resources(self,conn)->tuple[str,str,dict[str,str]]:
        resources=self.profile.get("resources") or {}
        source=str(resources.get("source") or "file")
        framework=""; parsed:Any=[]; taxonomy_text=""

        def load_files()->tuple[str,Any,str]:
            framework_name=resources.get("framework_file") or resources.get("framework_fallback")
            taxonomy_name=resources.get("taxonomy_file") or resources.get("taxonomy_fallback")
            if not framework_name or not taxonomy_name:
                raise RuntimeError(
                    "Topics resources are empty and no file fallback is configured. "
                    "Provide framework_file + taxonomy_file (or *_fallback) in the museum Topics profile."
                )
            framework_path=self.cfg.museum.root/"topics"/str(framework_name)
            taxonomy_path=self.cfg.museum.root/"topics"/str(taxonomy_name)
            if not framework_path.is_file() or not taxonomy_path.is_file():
                raise RuntimeError(
                    f"Topics fallback files not found: {framework_path} / {taxonomy_path}"
                )
            framework_value=framework_path.read_text(encoding="utf-8")
            taxonomy_value=json.loads(taxonomy_path.read_text(encoding="utf-8"))
            return framework_value,taxonomy_value,json.dumps(taxonomy_value,ensure_ascii=False)

        if source=="database":
            query_name=resources.get("database_query")
            if not query_name:
                raise RuntimeError("Topics database source requires resources.database_query")
            row=self.store.query_profile_resource(conn,self.cfg.museum.root/"topics"/str(query_name))
            framework=str(row.get("framework") or "")
            taxonomy_obj=row.get("taxonomy") or row.get("taxonomie") or []
            if isinstance(taxonomy_obj,str):
                taxonomy_text=taxonomy_obj
                try: parsed=json.loads(taxonomy_obj)
                except Exception: parsed=[]
            else:
                parsed=taxonomy_obj
                taxonomy_text=json.dumps(taxonomy_obj,ensure_ascii=False)
            if not framework or not taxonomy_text or taxonomy_text in ("[]", "null", ""):
                framework,parsed,taxonomy_text=load_files()
        elif source=="file":
            framework,parsed,taxonomy_text=load_files()
        else:
            raise RuntimeError(f"Unsupported Topics resource source: {source!r}")

        slugs={}
        seq=parsed if isinstance(parsed,list) else (parsed.get("topics",[]) if isinstance(parsed,dict) else [])
        for item in seq:
            if isinstance(item,dict) and item.get("schwerpunkt") and item.get("slug"):
                slugs[str(item["schwerpunkt"])]=str(item["slug"])
            elif isinstance(item,dict) and item.get("label") and item.get("slug"):
                slugs[str(item["label"])]=str(item["slug"])

        taxonomy_name=resources.get("taxonomy_file") or resources.get("taxonomy_fallback")
        if taxonomy_name:
            fpath=self.cfg.museum.root/"topics"/str(taxonomy_name)
            if fpath.exists():
                fobj=json.loads(fpath.read_text(encoding="utf-8"))
                fseq=fobj if isinstance(fobj,list) else fobj.get("topics",[])
                for item in fseq:
                    if isinstance(item,dict):
                        label=item.get("schwerpunkt") or item.get("label")
                        if label and item.get("slug"):
                            slugs.setdefault(str(label),str(item["slug"]))
        return framework,taxonomy_text,slugs

    def _prompt_name(self,key:str)->str:
        p=self.profile.get("prompts") or {}
        if self.cfg.settings.prompt_variant=="cache" and p.get(key+"_cache"):
            return p[key+"_cache"]
        return p[key]

    def generator_body(self,context:str,master:str,framework:str,taxonomy:str,image_b64:str)->dict:
        p=self.profile.get("prompts") or {}; system=self.cfg.museum.prompt(p["generator_system"]); tmpl=self.cfg.museum.prompt(self._prompt_name("generator_user"))
        user=(tmpl.replace("${item.context_data_string||''}",context or "").replace("${item.master_caption||''}",master or "").replace("${FRAMEWORK}",framework or "").replace("${TAX}",taxonomy or ""))
        content=[{"type":"text","text":user}]
        if image_b64: content.append({"type":"image_url","image_url":{"url":image_b64}})
        body=self.cfg.models.request_defaults("topics.generator")
        body.update({"messages":[{"role":"system","content":system},{"role":"user","content":content}],"response_format":{"type":"json_schema","json_schema":{"name":"sp_gen","strict":True,"schema":self._schema("sp_gen_schema")}}})
        return body

    def judge_body(self,context:str,master:str,framework:str,taxonomy:str,gen_result:dict,image_b64:str)->dict:
        p=self.profile.get("prompts") or {}; system=self.cfg.museum.prompt(p["judge_system"]); tmpl=self.cfg.museum.prompt(self._prompt_name("judge_user"))
        result=json.dumps({"objektbefund":gen_result.get("objektbefund",{}),"schwerpunkte":gen_result.get("schwerpunkte",[]),"nicht_vergeben":gen_result.get("nicht_vergeben",[])},ensure_ascii=False)
        user=(tmpl.replace("${item.context_data_string||''}",context or "").replace("${item.master_caption||''}",master or "").replace("${FRAMEWORK}",framework or "").replace("${TAX}",taxonomy or "").replace("${JSON.stringify({objektbefund:item.gen_objektbefund,schwerpunkte:item.gen_schwerpunkte,nicht_vergeben:item.gen_nicht_vergeben})}",result))
        content=[{"type":"text","text":user}]
        if image_b64: content.append({"type":"image_url","image_url":{"url":image_b64}})
        body=self.cfg.models.request_defaults("topics.judge")
        body.update({"messages":[{"role":"system","content":system},{"role":"user","content":content}],"response_format":{"type":"json_schema","json_schema":{"name":"sp_judge","strict":True,"schema":self._schema("sp_judge_schema")}}})
        return body

    def run_generator(self,conn,context:str,master:str,image_b64:str)->dict:
        framework,tax,_=self.resources(conn)
        raw=self.llm.chat_content("topics.generator",self.generator_body(context,master,framework,tax,image_b64))
        gen=clean_and_parse(raw) or {}
        return {"objektbefund":gen.get("objektbefund",{}),"schwerpunkte":gen.get("schwerpunkte",[]) or [],"nicht_vergeben":gen.get("nicht_vergeben",[]) or []}

    def run_judge(self,conn,context:str,master:str,image_b64:str,gen_result:dict)->dict:
        framework,tax,_=self.resources(conn)
        raw=self.llm.chat_content("topics.judge",self.judge_body(context,master,framework,tax,gen_result,image_b64))
        return clean_and_parse(raw) or {"schwerpunkte":[],"pflichtpruefung":{"erforderlich":False,"gruende":[]}}

    def write(self,conn,obj_id:str,gen_result:dict,judge_result:dict)->int:
        _,_,slugs=self.resources(conn); annot=self.annotation_set(); mandatory=bool((judge_result.get("pflichtpruefung") or {}).get("erforderlich")); n=0
        for item in (judge_result.get("schwerpunkte") or []):
            label=str(item.get("schwerpunkt") or "")
            slug=slugs.get(label) or str(item.get("slug") or "")
            if not label or not slug: continue
            status=str(item.get("status") or "")
            if status.startswith("begründeter"): judge_status="gruen"
            elif status.startswith("möglicher"): judge_status="gelb"
            else: judge_status="rot"
            detail={"unterthemen":item.get("unterthemen",[]),"schlagworte":item.get("schlagworte",[]),"abgrenzung":item.get("abgrenzung",""),"belege":item.get("belege",[]),"urspruenglicher_status":item.get("urspruenglicher_status",""),"judge_begruendung":item.get("judge_begruendung","")}
            self.store.write_topic(conn,{"obj_id":obj_id,"topic":label,"slug":slug,"source":str(self.profile.get("source_label","llm")),"status":status,"relation_types":list(item.get("bezugstypen") or []),"rationale":item.get("begruendung",""),"judge_status":judge_status,"judge_decision":item.get("judge_entscheidung",""),"review_class":"C" if mandatory else "A","mandatory_review":mandatory,"detail_json":json.dumps(detail,ensure_ascii=False),"taxonomy_version":str(self.profile.get("taxonomy_version","")),"annotation_set":annot})
            n+=1
        self.store.write_topic_run(conn,{"obj_id":obj_id,"annotation_set":annot,"object_findings_json":json.dumps(gen_result.get("objektbefund",{}),ensure_ascii=False),"taxonomy_version":str(self.profile.get("taxonomy_version","")),"generator_model":self.cfg.models.logical_model("topics.generator"),"judge_model":self.cfg.models.logical_model("topics.judge")})
        return n

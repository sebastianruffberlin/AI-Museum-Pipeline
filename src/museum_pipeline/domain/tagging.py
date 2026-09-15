from __future__ import annotations

import json

from ..configuration import RuntimeConfig
from ..infrastructure.llm import LLMClient
from ..persistence.postgres import PostgresStore
from .captions import reference_caption_body, synthesis_body, synthesis_user
from .jsonutil import clean_and_parse
from .policy import TaggingPolicy
from .authority.gnd import GNDAuthority


class TaggingModule:
    """Core keyword pipeline. Museum semantics are supplied by the profile."""
    def __init__(self,cfg:RuntimeConfig,store:PostgresStore,llm:LLMClient):
        self.cfg=cfg; self.store=store; self.llm=llm
        self.profile=cfg.museum.tagging; self.policy=TaggingPolicy(cfg)
        self.clusters=self.policy.clusters; self.meta_keys=self.policy.meta_keys
        self.authority=GNDAuthority(cfg,llm)

    def _p(self,key:str)->str:
        return self.cfg.museum.prompt((self.profile.get("prompts") or {})[key])

    # ---- independent #001 caption chain ---------------------------------
    def caption_primary_body(self,image_b64:str)->dict:
        return reference_caption_body(self.cfg,"tagging.caption.primary",self._p("caption_system"),self._p("caption_user"),image_b64,system_role=True)

    def caption_secondary_body(self,image_b64:str)->dict:
        # The reference request deliberately has no thinking flag.
        return reference_caption_body(self.cfg,"tagging.caption.secondary",self._p("caption_system"),self._p("caption_user"),image_b64,system_role=False)

    def caption_synthesis_body(self,cap_a:str,cap_b:str,image_b64:str)->dict:
        user=synthesis_user(cap_a,cap_b,bias_filter=False)
        return synthesis_body(self.cfg,"tagging.caption.synthesis",self._p("caption_synthesis_system"),user,image_b64)

    # ---- generation ------------------------------------------------------
    def tagging_user(self,master:str,cap1:str,cap2:str,context:str)->str:
        return (self._p("generator_user")
                .replace("${item.master_caption}",master or "")
                .replace("${item.caption_1 || 'nicht verfügbar'}",cap1 or "nicht verfügbar")
                .replace("${item.caption_2 || 'nicht verfügbar'}",cap2 or "nicht verfügbar")
                .replace("${item.context_data_string}",context or ""))

    def generator_body(self,master:str,cap1:str,cap2:str,context:str,image_b64:str)->dict:
        body=self.cfg.models.request_defaults("tagging.generator")
        body.update({"messages":[{"role":"system","content":self._p("generator_system")},{"role":"user","content":[{"type":"text","text":self.tagging_user(master,cap1,cap2,context)},{"type":"image_url","image_url":{"url":image_b64}}]}],"response_format":{"type":"json_object"}})
        return body

    # ---- audit -----------------------------------------------------------
    def audit_user(self,master:str,cap1:str,cap2:str,context:str,llm2_content:str,llm2_reasoning:str)->str:
        return (self._p("audit_user")
                .replace("${item.master_caption}",master or "")
                .replace("${item.caption_1}",cap1 or "")
                .replace("${item.caption_2}",cap2 or "")
                .replace("${item.context_data_string}",context or "")
                .replace("${LLM2_CONTENT}",llm2_content or "")
                .replace("${LLM2_REASONING}",llm2_reasoning or ""))

    def audit_schema(self)->dict:
        error_classes=list((self.cfg.museum.tagging_policy.get("error_classes") or {}).get("all") or [])
        item={"type":"object","additionalProperties":False,"required":["term","why","fehlerklassen","correct_cluster","judge_comment"],"properties":{"term":{"type":"string"},"why":{"type":"string"},"fehlerklassen":{"type":"array","items":{"type":"string","enum":error_classes}},"correct_cluster":{"type":["string","null"]},"judge_comment":{"type":"string"}}}
        audit_fields=list(self.profile.get("audit_fields") or [])
        required=["_decolonial_audit_log","Protokoll_Status","_provenance_critique"]+self.clusters+["Kritischer_Hinweis"]
        return {"type":"object","additionalProperties":False,"required":required,"properties":{"_decolonial_audit_log":{"type":"object","additionalProperties":False,"required":audit_fields,"properties":{k:{"type":"string"} for k in audit_fields}},"Protokoll_Status":{"type":"string","enum":list(self.profile.get("protokoll_status_values") or [])},"_provenance_critique":{"type":["string","null"]},"Kritischer_Hinweis":{"type":["string","null"]},**{c:{"type":"array","items":item} for c in self.clusters}}}

    def audit_body(self,master:str,cap1:str,cap2:str,context:str,llm2_content:str,llm2_reasoning:str,image_b64:str)->dict:
        body=self.cfg.models.request_defaults("tagging.audit")
        body.update({"messages":[{"role":"system","content":self._p("audit_system")},{"role":"user","content":[{"type":"text","text":self.audit_user(master,cap1,cap2,context,llm2_content,llm2_reasoning)},{"type":"image_url","image_url":{"url":image_b64}}]}],"response_format":{"type":"json_schema","json_schema":{"name":"audit","strict":True,"schema":self.audit_schema()}}})
        return body

    # ---- repair ----------------------------------------------------------
    def collect_yellows(self,pv:dict,pr:dict)->list[dict]:
        out=[]
        for c in self.clusters:
            for src in (pv.get(c),pr.get(c)):
                if isinstance(src,list):
                    for t in src:
                        if t and t.get("status")=="yellow":
                            out.append({"original":t.get("term"),"cluster":c,"why":t.get("why",""),"judge_comment":t.get("judge_comment",""),"fehlerklassen":t.get("fehlerklassen",[])})
        return out

    def repair_schema(self)->dict:
        from ..skills.loader import SkillLoader
        return SkillLoader(self.cfg).schema("keyword-repair")

    def repair_body(self,master:str,metadata:str,yellows:list[dict])->dict:
        user='Objektkontext und zu reparierende gelbe Terme:\n"""\n'+json.dumps({"master_caption":master,"metadaten":metadata,"zu_reparieren":yellows},ensure_ascii=False,indent=2)+'\n"""\nGib für JEDEN Term einen Eintrag in "repairs" zurück (gleiche Reihenfolge, gleicher cluster, gleiches original).'
        body=self.cfg.models.request_defaults("tagging.repair")
        body.update({"messages":[{"role":"system","content":self._p("repair_system")},{"role":"user","content":user}],"response_format":{"type":"json_schema","json_schema":{"name":"repair_result","strict":True,"schema":self.repair_schema()}}})
        return body

    def repair_post(self,parsed_base:dict,repair_content:str)->tuple[dict,dict]:
        pv_in=json.loads(json.dumps(parsed_base.get("payload_valid") or {})); pr_in=json.loads(json.dumps(parsed_base.get("payload_rejected") or {}))
        parsed=clean_and_parse(repair_content) if repair_content else {}; repairs=parsed.get("repairs",[]) if isinstance(parsed,dict) else []
        rep_map={str(r.get("cluster"))+"||"+str(r.get("original","")).strip().lower():r for r in repairs if r.get("cluster") and r.get("original") is not None}
        valid={c:[] for c in self.clusters}; rejected={c:[] for c in self.clusters}; seen:set[str]=set()
        norm=lambda s:str(s or "").strip().lower()
        for c in self.clusters:
            for g in pv_in.get(c) if isinstance(pv_in.get(c),list) else []:
                if g and g.get("status")!="yellow": valid[c].append(g); seen.add(norm(g.get("term")))
            for rd in pr_in.get(c) if isinstance(pr_in.get(c),list) else []:
                if rd and rd.get("status")!="yellow": rejected[c].append(rd)
        yellows=[]
        for c in self.clusters:
            for src in (pv_in.get(c),pr_in.get(c)):
                if isinstance(src,list):
                    for t in src:
                        if t and t.get("status")=="yellow": yellows.append((c,t))
        for source,y in yellows:
            r=rep_map.get(source+"||"+norm(y.get("term"))); folded=False
            if r and r.get("repairable") and isinstance(r.get("repaired_terms"),list) and r["repaired_terms"]:
                target=y.get("correct_cluster") if y.get("correct_cluster") in self.clusters else source
                for rt in r["repaired_terms"]:
                    screened=self.policy.bias_screen(rt)
                    if not screened or screened.get("drop") or not screened.get("term") or self.policy.date_re.search(screened["term"]) or norm(screened["term"]) in seen: continue
                    seen.add(norm(screened["term"])); valid[target].append({"term":screened["term"],"why":y.get("why",""),"status":"green","judge_comment":"","_repaired_from":y.get("term")}); folded=True
            if not folded: rejected[source].append(y)
        new_valid={k:pv_in[k] for k in self.meta_keys if k in pv_in}; new_rejected={k:pr_in[k] for k in self.meta_keys if k in pr_in}
        for c in self.clusters: new_valid[c]=valid[c]; new_rejected[c]=rejected[c]
        return new_valid,new_rejected

    # ---- authority + final ----------------------------------------------
    def merge(self,gnd_by_cluster:dict,payload_rejected:dict,meta:dict)->dict:
        final={"_decolonial_audit_log":meta.get("_decolonial_audit_log"),"Protokoll_Status":meta.get("Protokoll_Status","Unknown"),"Kritischer_Hinweis":meta.get("Kritischer_Hinweis")}
        for cluster in self.clusters:
            merged=[]
            for vi in gnd_by_cluster.get(cluster) or []:
                merged.append({"term":vi.get("term"),"status":"green","gnd_name":vi.get("gnd_name"),"gnd_id":vi.get("gnd_id"),"confidence":vi.get("confidence"),"llm2_rationale":vi.get("llm2_rationale"),"llm3_judge_comment":vi.get("llm3_judge_comment"),"llm4_reasoning":vi.get("llm4_reasoning")})
            for ri in payload_rejected.get(cluster) or []:
                if not ri: continue
                merged.append({"term":ri.get("term"),"status":ri.get("status") or "red","gnd_name":None,"gnd_id":None,"confidence":None,"llm2_rationale":ri.get("why"),"llm3_judge_comment":ri.get("judge_comment"),"llm4_reasoning":"Status nicht grün – zurückgehalten, kein Normdaten-Abgleich durchgeführt."})
            final[cluster]=merged
        return final

    def write(self,conn,obj_id:str,final:dict)->int:
        audit=final.get("_decolonial_audit_log") or {}; fields=list(self.profile.get("audit_fields") or [])
        vals=[audit.get(f,"") for f in fields]; vals=(vals+[""]*5)[:5]; n=0
        for cluster in self.clusters:
            for kw in final.get(cluster) or []:
                self.store.write_keyword(conn,{"obj_id":obj_id,"cluster":cluster,"keyword":kw.get("term"),"gnd_name":kw.get("gnd_name"),"gnd_id":kw.get("gnd_id"),"confidence":kw.get("confidence"),"status":kw.get("status"),"llm2":kw.get("llm2_rationale"),"llm3":kw.get("llm3_judge_comment"),"llm4":kw.get("llm4_reasoning"),"hinweis":final.get("Kritischer_Hinweis") or "","audit1":vals[0],"audit2":vals[1],"audit3":vals[2],"audit4":vals[3],"audit5":vals[4],"status2":final.get("Protokoll_Status","Unknown"),"modell":self.cfg.models.provenance.get("tagging_model","")}); n+=1
        return n

    @staticmethod
    def content_and_reasoning(resp:dict)->tuple[str,str]:
        try:
            msg=resp["choices"][0]["message"]
            content = msg.get("content") or ""
            reasoning = msg.get("reasoning") or msg.get("reasoning_content") or ""
            return content, reasoning
        except Exception:
            return "",""

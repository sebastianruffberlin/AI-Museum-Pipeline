from __future__ import annotations

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Optional

import requests

from ...configuration import RuntimeConfig
from ...infrastructure.llm import LLMClient


def _parse_json(raw: Any) -> Optional[dict]:
    if not raw:
        return None
    if isinstance(raw, dict):
        return raw
    s = re.sub(r"```json", "", str(raw), flags=re.I).replace("```", "").strip()
    a, b = s.find("{"), s.rfind("}")
    if a != -1 and b != -1:
        s = s[a:b+1]
    try:
        return json.loads(s)
    except Exception:
        return None


class GNDAuthority:
    """GND adapter. Optional integration; the harness is not GND-specific."""
    def __init__(self, cfg: RuntimeConfig, llm: LLMClient):
        self.cfg=cfg; self.llm=llm
        self.profile=cfg.museum.authority
        self.clusters=list(cfg.museum.tagging.get("clusters") or [])
        self.flags=list(self.profile.get("flags") or [])
        self.retrieval=self.profile.get("retrieval") or {}

    @property
    def enabled(self) -> bool:
        return bool(self.profile.get("enabled", False)) and self.profile.get("provider") == "gnd"

    def _flatten(self, payload_valid: dict, caption: str, metadata: str) -> list[dict]:
        out=[]; n=0
        for cluster in self.clusters:
            arr=payload_valid.get(cluster) if isinstance(payload_valid.get(cluster),list) else []
            for it in arr:
                if not it or not it.get("term"): continue
                n+=1
                out.append({"id":str(n),"cluster":cluster,"term":it["term"],"why":it.get("why", ""),"judge_comment":it.get("judge_comment", ""),"caption":caption,"metadata":metadata})
        return out

    def _msearch(self, terms: list[dict]) -> list[list[dict]]:
        lines=[]
        fields=self.retrieval.get("fields") or []
        source_fields=self.retrieval.get("source_fields") or []
        size=int(self.retrieval.get("size",5))
        for item in terms:
            lines.append(json.dumps({"index":self.cfg.settings.os_index}))
            lines.append(json.dumps({"size":size,"query":{"multi_match":{"query":item["term"],"fields":fields,"fuzziness":"AUTO"}},"_source":source_fields}))
        r=requests.post(self.cfg.settings.os_msearch,data=("\n".join(lines)+"\n").encode("utf-8"),headers={"Content-Type":"application/x-ndjson"},timeout=self.cfg.settings.os_timeout)
        r.raise_for_status(); responses=r.json().get("responses",[])
        result=[]
        for i in range(len(terms)):
            try: hits=responses[i]["hits"]["hits"]
            except (IndexError,KeyError,TypeError): hits=[]
            result.append([{"gnd_id":h.get("_source",{}).get("gnd_id"),"preferred_name":h.get("_source",{}).get("preferred_name"),"alternate_names":h.get("_source",{}).get("alternate_names"),"definition":h.get("_source",{}).get("def")} for h in hits])
        return result

    def _body(self, term: dict, candidates: list[dict]) -> dict:
        p=self.profile.get("prompts") or {}
        system=self.cfg.museum.prompt(p["system"])
        tmpl=self.cfg.museum.prompt(p["user"])
        user=(tmpl.replace("${item.term}",str(term["term"]))
                  .replace("${item.cluster}",str(term["cluster"]))
                  .replace("${item.why}",str(term.get("why","")))
                  .replace("${item.judge_comment}",str(term.get("judge_comment","")))
                  .replace("${item.caption}",str(term.get("caption","")))
                  .replace("${item.metadata}",str(term.get("metadata","")))
                  .replace("${GND_CANDIDATES}",json.dumps(candidates,ensure_ascii=False)))
        body=self.cfg.models.request_defaults(str(self.profile.get("role","authority.gnd")))
        body.update({"response_format":{"type":"json_object"},"messages":[{"role":"system","content":system},{"role":"user","content":user}]})
        return body

    def _call_one(self, term: dict, candidates: list[dict]) -> dict:
        try:
            role=str(self.profile.get("role","authority.gnd"))
            content=self.llm.chat_content(role,self._body(term,candidates))
            return {**term,"final_response":content or None}
        except Exception as e:
            return {**term,"final_response":None,"_llm1_error":str(e)[:300]}

    def _score_from_tags(self,tags:Any)->float:
        t=" ".join(tags) if isinstance(tags,list) else str(tags or "")
        return min(1.0,round(sum(1 for f in self.flags if f in t)*0.2*100)/100)

    def _consolidate(self, results:list[dict])->dict:
        by_cluster:dict[str,list]={}
        for item in results:
            v=_parse_json(item.get("final_response"))
            gnd_raw=None
            if v:
                conf=v.get("gnd_confidence") or "no_match"; gnd_id=v.get("gnd_id")
                if gnd_id in ("null","",None) or conf=="no_match": gnd_id=None
                gnd_raw={"cluster":item["cluster"],"term":item["term"],"gnd_id":gnd_id,"gnd_preferred_name":v.get("gnd_preferred_name"),"gnd_confidence":conf,"unsicherheit_score":self._score_from_tags(v.get("debug_tags")),"reasoning":v.get("reasoning","")}
            cluster=(gnd_raw or {}).get("cluster") or item.get("cluster") or "Unsorted"
            if not gnd_raw:
                by_cluster.setdefault(cluster,[]).append({"term":item.get("term"),"gnd_name":None,"gnd_id":None,"confidence":"no_match","llm2_rationale":item.get("why",""),"llm3_judge_comment":item.get("judge_comment",""),"llm4_reasoning":"LLM-/Parsing-Fehler: keine valide GND-Zuordnung."})
            else:
                by_cluster.setdefault(cluster,[]).append({"term":gnd_raw["term"],"gnd_name":gnd_raw.get("gnd_preferred_name"),"gnd_id":gnd_raw.get("gnd_id"),"confidence":gnd_raw.get("gnd_confidence") or "no_match","llm2_rationale":item.get("why",""),"llm3_judge_comment":item.get("judge_comment",""),"llm4_reasoning":gnd_raw.get("reasoning","")})
        return by_cluster

    def resolve(self,payload_valid:dict,caption:str,metadata:str)->dict:
        if not self.enabled:
            # Keep green terms, simply without an authority ID.
            out={}
            for cluster in self.clusters:
                out[cluster]=[{"term":x.get("term"),"gnd_name":None,"gnd_id":None,"confidence":"not_checked","llm2_rationale":x.get("why",""),"llm3_judge_comment":x.get("judge_comment",""),"llm4_reasoning":"Authority enrichment disabled by museum profile."} for x in (payload_valid.get(cluster) or []) if x]
            return out
        terms=self._flatten(payload_valid,caption,metadata)
        if not terms: return {}
        candidates=self._msearch(terms)
        role=str(self.profile.get("role","authority.gnd"))
        concurrency=self.cfg.hardware.workers_for_role(self.cfg.models,role)
        results:[dict|None]=[None]*len(terms)
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futures={ex.submit(self._call_one,terms[i],candidates[i]):i for i in range(len(terms))}
            for fut in as_completed(futures): results[futures[fut]]=fut.result()
        return self._consolidate([r for r in results if r is not None])

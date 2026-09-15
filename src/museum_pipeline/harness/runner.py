from __future__ import annotations

import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Callable

from ..domain import image_features
from ..domain.captions import reference_caption_body, synthesis_body, synthesis_user, decompose
from ..domain.embeddings import image_embeddings, text_embeddings
from ..infrastructure import logsetup
from .runtime import Runtime

_log=logsetup.get()


class EmptyOutput(RuntimeError): pass


@dataclass(frozen=True)
class Phase:
    name:str
    module:str
    handler:Callable
    state_key:str|None=None
    role:str|None=None


class WorkflowRunner:
    """Phase-oriented execution harness.

    The workflow is declared in workflows/*.yaml. Within each enabled module,
    all objects run through the same atomic model phase before the next model
    phase begins, preserving the model-residency strategy.
    """
    def __init__(self,runtime:Runtime,workers:int|None=None):
        self.rt=runtime; self.cfg=runtime.cfg
        self.worker_cap=workers or self.cfg.hardware.default_workers

    def _workers(self,phase:Phase)->int:
        return self.cfg.hardware.phase_workers(phase.name,self.cfg.models,phase.role,self.worker_cap)

    def _run_phase(self,phase:Phase,objects:list[dict],*,force:bool=False)->int:
        conn0=self.rt.pool.get()
        todo=[]
        for obj in objects:
            oid=obj["obj_id"]
            if self.rt.state.failed(conn0,oid): continue
            if not force and self.rt.store.module_done(conn0,phase.module,oid): continue
            if not force and phase.state_key and self.rt.state.has(conn0,oid,phase.state_key): continue
            todo.append(obj)
        if not todo:
            _log.info("### %s: nichts zu tun ###",phase.name); self.rt.pool.close_all(); return 0
        workers=self._workers(phase)
        _log.info("\n### %s: %d Objekte, %d parallel ###",phase.name,len(todo),workers)
        start=time.time(); ok=0; lock=threading.Lock()
        def work(obj):
            nonlocal ok
            conn=self.rt.pool.get(); oid=obj["obj_id"]
            try:
                t=time.time(); phase.handler(conn,obj)
                with lock: ok+=1
                _log.info("  [%s ✓] %s (%.1fs)",phase.name,oid,time.time()-t)
            except Exception as exc:
                try: conn.rollback()
                except Exception: pass
                self.rt.state.fail(conn,oid,phase.name,f"{type(exc).__name__}: {exc}")
                _log.error("  [%s ✗] %s: %s",phase.name,oid,exc)
                _log.debug(traceback.format_exc())
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures=[ex.submit(work,obj) for obj in todo]
            for future in as_completed(futures): future.result()
        self.rt.pool.close_all()
        _log.info("### %s fertig: %d/%d ok in %.1fs ###",phase.name,ok,len(todo),time.time()-start)
        return ok

    def _required(self,conn,obj_id:str,key:str)->str:
        value=self.rt.state.get(conn,obj_id,key,required=True)
        if value is None: raise EmptyOutput(f"Pflicht-Zwischenergebnis fehlt: {key}")
        return value

    # ------------------------------------------------------------------
    # Module phase definitions
    def image_embedding_phases(self)->list[Phase]:
        def run(conn,o):
            image_embeddings(self.rt.store,self.rt.assets,conn,o["obj_id"],o["asset_ref"]); conn.commit()
        return [Phase("image_embeddings","image_embeddings",run)]

    def image_feature_phases(self)->list[Phase]:
        def run(conn,o):
            _,raw=self.rt.images.get(o["obj_id"],o["asset_ref"]); self.rt.store.write_derived(conn,image_features.analyze(o["obj_id"],raw)); conn.commit()
        return [Phase("image_features","image_features",run)]

    def caption_phases(self)->list[Phase]:
        c=self.cfg.museum.data.get("captions",{}).get("prompts",{})
        system=self.cfg.museum.prompt(c["system"])
        user=self.cfg.museum.prompt(c["user"])
        synth_system=self.cfg.museum.prompt(c["synthesis_system"])

        def call_with_usage(role, body):
            resp=self.rt.llm.chat_raw(role,body)
            value=self.rt.llm.content_of(resp)
            if not str(value or "").strip():
                raise EmptyOutput(f"{role} lieferte keinen Inhalt")
            tokens=self.rt.llm.usage_total(resp)
            return value,tokens

        def primary(conn,o):
            image,_=self.rt.images.get(o["obj_id"],o["asset_ref"])
            value,tokens=call_with_usage(
                "caption.primary",
                reference_caption_body(
                    self.cfg,"caption.primary",system,user,image,system_role=True
                ),
            )
            self.rt.state.set(conn,o["obj_id"],"captions.primary",value)
            self.rt.state.set(conn,o["obj_id"],"captions.primary.tokens",tokens)

        def secondary(conn,o):
            image,_=self.rt.images.get(o["obj_id"],o["asset_ref"])
            value,tokens=call_with_usage(
                "caption.secondary",
                reference_caption_body(
                    self.cfg,"caption.secondary",system,user,image,system_role=False
                ),
            )
            self.rt.state.set(conn,o["obj_id"],"captions.secondary",value)
            self.rt.state.set(conn,o["obj_id"],"captions.secondary.tokens",tokens)

        def synth(conn,o):
            image,_=self.rt.images.get(o["obj_id"],o["asset_ref"])
            a=self.rt.state.get(conn,o["obj_id"],"captions.primary") or ""
            b=self.rt.state.get(conn,o["obj_id"],"captions.secondary") or ""
            body=synthesis_body(
                self.cfg,
                "caption.synthesis",
                synth_system,
                synthesis_user(a,b,bias_filter=True),
                image,
            )
            value,tokens=call_with_usage("caption.synthesis",body)
            self.rt.state.set(conn,o["obj_id"],"captions.master",value)
            self.rt.state.set(conn,o["obj_id"],"captions.synthesis.tokens",tokens)

        def write(conn,o):
            master=self._required(conn,o["obj_id"],"captions.master")
            a=self.rt.state.get(conn,o["obj_id"],"captions.primary") or ""
            b=self.rt.state.get(conn,o["obj_id"],"captions.secondary") or ""

            token_keys=(
                "captions.primary.tokens",
                "captions.secondary.tokens",
                "captions.synthesis.tokens",
            )

            tokens_total=0
            for key in token_keys:
                try:
                    tokens_total += int(
                        self.rt.state.get(conn,o["obj_id"],key) or 0
                    )
                except (TypeError,ValueError):
                    pass

            self.rt.store.write_captions(
                conn,
                decompose(
                    self.cfg,
                    o["obj_id"],
                    o["asset_ref"],
                    master,
                    a,
                    b,
                    tokens_total=tokens_total,
                ),
            )
            conn.commit()
            self.rt.state.set(conn,o["obj_id"],"captions.completed","1")

        return [
            Phase(
                "captions.primary","captions",primary,
                "captions.primary","caption.primary"
            ),
            Phase(
                "captions.secondary","captions",secondary,
                "captions.secondary","caption.secondary"
            ),
            Phase(
                "captions.synthesis","captions",synth,
                "captions.master","caption.synthesis"
            ),
            Phase(
                "captions.write","captions",write,
                "captions.completed"
            ),
        ]

    def tagging_phases(self)->list[Phase]:
        tag=self.rt.tagging
        def cap_a(conn,o):
            image,_=self.rt.images.get(o["obj_id"],o["asset_ref"])
            value=self.rt.llm.chat_content(
                "tagging.caption.primary",
                tag.caption_primary_body(image),
            )
            if not str(value or "").strip():
                raise EmptyOutput("tagging.caption.primary lieferte keinen Inhalt")
            self.rt.state.set(conn,o["obj_id"],"tagging.caption.primary",value)
        def cap_b(conn,o):
            image,_=self.rt.images.get(o["obj_id"],o["asset_ref"])
            value=self.rt.llm.chat_content(
                "tagging.caption.secondary",
                tag.caption_secondary_body(image),
            )
            if not str(value or "").strip():
                raise EmptyOutput("tagging.caption.secondary lieferte keinen Inhalt")
            self.rt.state.set(conn,o["obj_id"],"tagging.caption.secondary",value)
        def cap_s(conn,o):
            image,_=self.rt.images.get(o["obj_id"],o["asset_ref"])
            a=self._required(conn,o["obj_id"],"tagging.caption.primary")
            b=self._required(conn,o["obj_id"],"tagging.caption.secondary")
            value=self.rt.llm.chat_content(
                "tagging.caption.synthesis",
                tag.caption_synthesis_body(a,b,image),
            )
            if not str(value or "").strip():
                raise EmptyOutput("tagging.caption.synthesis lieferte keinen Inhalt")
            self.rt.state.set(conn,o["obj_id"],"tagging.caption.master",value)
        def gen(conn,o):
            image,_=self.rt.images.get(o["obj_id"],o["asset_ref"]); master=self._required(conn,o["obj_id"],"tagging.caption.master"); a=self.rt.state.get(conn,o["obj_id"],"tagging.caption.primary") or ""; b=self.rt.state.get(conn,o["obj_id"],"tagging.caption.secondary") or ""; ctx=self.rt.context.tagging(conn,o["obj_id"])
            resp=self.rt.llm.chat_raw("tagging.generator",tag.generator_body(master,a,b,ctx,image)); content,reasoning=tag.content_and_reasoning(resp)
            if not content: raise EmptyOutput("Tagging generator lieferte keinen Inhalt")
            self.rt.state.set(conn,o["obj_id"],"tagging.generator",{"content":content,"reasoning":reasoning})
        def audit(conn,o):
            image,_=self.rt.images.get(o["obj_id"],o["asset_ref"]); master=self._required(conn,o["obj_id"],"tagging.caption.master"); a=self.rt.state.get(conn,o["obj_id"],"tagging.caption.primary") or ""; b=self.rt.state.get(conn,o["obj_id"],"tagging.caption.secondary") or ""; ctx=self.rt.context.tagging(conn,o["obj_id"]); gen=self.rt.state.get_json(conn,o["obj_id"],"tagging.generator",required=True) or {}
            content=self.rt.llm.chat_content("tagging.audit",tag.audit_body(master,a,b,ctx,gen.get("content",""),gen.get("reasoning",""),image))
            if not content: raise EmptyOutput("Tagging audit lieferte keinen Inhalt")
            self.rt.state.set(conn,o["obj_id"],"tagging.audit",content)
        def debias(conn,o):
            content=self._required(conn,o["obj_id"],"tagging.audit"); self.rt.state.set(conn,o["obj_id"],"tagging.policy",tag.policy.process(content))
        def repair(conn,o):
            parsed=self.rt.state.get_json(conn,o["obj_id"],"tagging.policy",required=True) or {}; master=self._required(conn,o["obj_id"],"tagging.caption.master"); ctx=self.rt.context.tagging(conn,o["obj_id"]); yellows=tag.collect_yellows(parsed.get("payload_valid",{}),parsed.get("payload_rejected",{})); content=""
            if yellows:
                content=self.rt.llm.chat_content(
                    "tagging.repair",
                    tag.repair_body(master,ctx,yellows),
                )
                if not str(content or "").strip():
                    raise EmptyOutput("tagging.repair lieferte keinen Inhalt")
            pv,pr=tag.repair_post(parsed,content); self.rt.state.set(conn,o["obj_id"],"tagging.repaired",{"pv":pv,"pr":pr})
        def authority(conn,o):
            pvpr=self.rt.state.get_json(conn,o["obj_id"],"tagging.repaired",required=True) or {}; master=self._required(conn,o["obj_id"],"tagging.caption.master"); ctx=self.rt.context.tagging(conn,o["obj_id"]); result=tag.authority.resolve(pvpr.get("pv",{}),master,ctx); self.rt.state.set(conn,o["obj_id"],"tagging.authority",result)
        def write(conn,o):
            parsed=self.rt.state.get_json(conn,o["obj_id"],"tagging.policy",required=True) or {}; pvpr=self.rt.state.get_json(conn,o["obj_id"],"tagging.repaired",required=True) or {}; authority_result=self.rt.state.get_json(conn,o["obj_id"],"tagging.authority",required=True) or {}
            final=tag.merge(authority_result,pvpr.get("pr",{}),{"_decolonial_audit_log":parsed.get("_decolonial_audit_log"),"Protokoll_Status":parsed.get("Protokoll_Status","Unknown"),"Kritischer_Hinweis":parsed.get("Kritischer_Hinweis")}); tag.write(conn,o["obj_id"],final); conn.commit(); self.rt.state.set(conn,o["obj_id"],"tagging.completed","1")
        return [
            Phase("tagging.caption.primary","tagging",cap_a,"tagging.caption.primary","tagging.caption.primary"),
            Phase("tagging.caption.secondary","tagging",cap_b,"tagging.caption.secondary","tagging.caption.secondary"),
            Phase("tagging.caption.synthesis","tagging",cap_s,"tagging.caption.master","tagging.caption.synthesis"),
            Phase("tagging.generator","tagging",gen,"tagging.generator","tagging.generator"),
            Phase("tagging.audit","tagging",audit,"tagging.audit","tagging.audit"),
            Phase("tagging.debias","tagging",debias,"tagging.policy"),
            Phase("tagging.repair","tagging",repair,"tagging.repaired","tagging.repair"),
            Phase("tagging.authority","tagging",authority,"tagging.authority","authority.gnd"),
            Phase("tagging.write","tagging",write,"tagging.completed"),
        ]

    def emotion_phases(self)->list[Phase]:
        module=self.rt.emotion
        def gen(conn,o):
            ctx,master=self.rt.context.emotion(conn,o["obj_id"]); image,_=self.rt.images.get(o["obj_id"],o["asset_ref"]); self.rt.state.set(conn,o["obj_id"],"emotion.generator",module.run_generator(conn,master,ctx,image))
        def judge(conn,o):
            ctx,master=self.rt.context.emotion(conn,o["obj_id"]); image,_=self.rt.images.get(o["obj_id"],o["asset_ref"]); g=self.rt.state.get_json(conn,o["obj_id"],"emotion.generator",required=True) or {}; self.rt.state.set(conn,o["obj_id"],"emotion.judge",module.run_judge(conn,master,ctx,image,g))
        def write(conn,o):
            _,master=self.rt.context.emotion(conn,o["obj_id"]); g=self.rt.state.get_json(conn,o["obj_id"],"emotion.generator",required=True) or {}; j=self.rt.state.get_json(conn,o["obj_id"],"emotion.judge",required=True) or {}; module.write(conn,o["obj_id"],master,g,j); conn.commit(); self.rt.state.set(conn,o["obj_id"],"emotion.completed","1")
        return [Phase("emotion.generator","emotion",gen,"emotion.generator","emotion.generator"),Phase("emotion.judge","emotion",judge,"emotion.judge","emotion.judge"),Phase("emotion.write","emotion",write,"emotion.completed")]

    def topic_phases(self)->list[Phase]:
        module=self.rt.topics
        def gen(conn,o):
            ctx,master=self.rt.context.topics(conn,o["obj_id"]); image,_=self.rt.images.get(o["obj_id"],o["asset_ref"]); self.rt.state.set(conn,o["obj_id"],"topics.generator",module.run_generator(conn,ctx,master,image))
        def judge(conn,o):
            ctx,master=self.rt.context.topics(conn,o["obj_id"]); image,_=self.rt.images.get(o["obj_id"],o["asset_ref"]); g=self.rt.state.get_json(conn,o["obj_id"],"topics.generator",required=True) or {}; self.rt.state.set(conn,o["obj_id"],"topics.judge",module.run_judge(conn,ctx,master,image,g))
        def write(conn,o):
            g=self.rt.state.get_json(conn,o["obj_id"],"topics.generator",required=True) or {}; j=self.rt.state.get_json(conn,o["obj_id"],"topics.judge",required=True) or {}; module.write(conn,o["obj_id"],g,j); conn.commit(); self.rt.state.set(conn,o["obj_id"],"topics.completed","1")
        return [Phase("topics.generator","topics",gen,"topics.generator","topics.generator"),Phase("topics.judge","topics",judge,"topics.judge","topics.judge"),Phase("topics.write","topics",write,"topics.completed")]

    def text_embedding_phases(self)->list[Phase]:
        def run(conn,o): text_embeddings(self.rt.store,self.rt.assets,conn,o["obj_id"]); conn.commit()
        return [Phase("text_embeddings","text_embeddings",run)]

    def phases(self)->list[Phase]:
        enabled=self.cfg.workflow.modules; out=[]
        factories=[("image_embeddings",self.image_embedding_phases),("image_features",self.image_feature_phases),("captions",self.caption_phases),("tagging",self.tagging_phases),("emotion",self.emotion_phases),("topics",self.topic_phases),("text_embeddings",self.text_embedding_phases)]
        for module,factory in factories:
            if enabled.get(module): out.extend(factory())
        return out

    def run(self,objects:list[dict],*,force:bool=False,retry_failed:bool=False)->dict:
        self.rt.initialize()
        if force or retry_failed:
            conn=self.rt.pool.get()
            for o in objects:
                self.rt.state.clear_object(conn,o["obj_id"])
                if force: self.rt.store.delete_module_results(conn,o["obj_id"],[m for m,v in self.cfg.workflow.modules.items() if v])
            conn.commit(); self.rt.pool.close_all()
        result={}
        for phase in self.phases(): result[phase.name]=self._run_phase(phase,objects,force=force)
        return result

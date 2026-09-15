from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from .configuration import RuntimeConfig
from .settings import Settings
from .infrastructure import logsetup


def _load(workflow:str|None=None)->tuple[Settings,RuntimeConfig]:
    settings=Settings.from_env()
    return settings,RuntimeConfig.load(settings,workflow)


def _ids(args)->list[str]|None:
    values=[]
    if args.ids:
        values.extend(x.strip() for x in args.ids.replace(",","|").split("|") if x.strip())
    if args.ids_file:
        values.extend(x.strip() for x in Path(args.ids_file).read_text(encoding="utf-8").splitlines() if x.strip())
    return list(dict.fromkeys(values)) or None


def cmd_validate(args)->int:
    _,cfg=_load(args.workflow)
    print("OK")
    print(f"museum_profile:   {cfg.settings.museum_profile}")
    print(f"model_profile:    {cfg.settings.model_profile}")
    print(f"hardware_profile: {cfg.settings.hardware_profile} ({cfg.hardware.data.get('status')})")
    print(f"workflow:         {cfg.workflow.data.get('name')}")
    print("modules:          "+", ".join(k for k,v in cfg.workflow.modules.items() if v))
    return 0


def cmd_show(args)->int:
    _,cfg=_load(args.workflow)
    data={"museum_profile":cfg.settings.museum_profile,"model_profile":cfg.settings.model_profile,"hardware_profile":cfg.settings.hardware_profile,"hardware_status":cfg.hardware.data.get("status"),"workflow":cfg.workflow.data,"model_roles":cfg.models.data.get("roles"),"hardware_models":cfg.hardware.data.get("models")}
    print(json.dumps(data,ensure_ascii=False,indent=2)); return 0


def cmd_run(args)->int:
    from .harness.runtime import Runtime
    from .harness.runner import WorkflowRunner
    _,cfg=_load(args.workflow); rt=Runtime(cfg); conn=rt.store.connect()
    try:
        ids=_ids(args); collections=args.collection or None
        if ids: objects=rt.store.pick_objects(conn,limit=len(ids),ids=ids,collections=collections)
        elif args.force: objects=rt.store.pick_objects(conn,limit=args.count,collections=collections)
        else: objects=rt.store.pick_open_objects(conn,cfg.workflow.modules,limit=args.count,collections=collections)
    finally: conn.close()
    if not objects:
        print("Keine passenden offenen Objekte gefunden."); return 0
    print(f"workflow={cfg.workflow.data.get('name')} | objects={len(objects)} | workers≤{args.workers or cfg.hardware.default_workers}")
    runner=WorkflowRunner(rt,args.workers)
    runner.run(
        objects,
        force=args.force,
        retry_failed=args.retry_failed,
    )

    # Phase exceptions are deliberately captured per object so one bad object
    # does not abort all parallel work. They are persisted in RunState.
    # The CLI must nevertheless return non-zero when any selected object
    # finished with such a failure; otherwise automation would treat a
    # partially/fully failed batch as successful.
    conn=rt.store.connect()
    try:
        failed=[
            str(obj["obj_id"])
            for obj in objects
            if rt.state.failed(conn,str(obj["obj_id"]))
        ]
    finally:
        conn.close()

    if failed:
        print(
            f"Workflow mit Fehlern beendet: "
            f"{len(failed)}/{len(objects)} Objekt(e) fehlgeschlagen."
        )
        return 1

    return 0


def build_parser()->argparse.ArgumentParser:
    p=argparse.ArgumentParser(prog="museum-pipeline",description="AI Museum Pipeline – profile-driven multimodal enrichment harness")
    sub=p.add_subparsers(dest="command",required=True)
    v=sub.add_parser("validate-config",help="validate museum/model/hardware/workflow profiles"); v.add_argument("--workflow"); v.set_defaults(func=cmd_validate)
    s=sub.add_parser("show-config",help="print resolved non-secret runtime configuration"); s.add_argument("--workflow"); s.set_defaults(func=cmd_show)
    r=sub.add_parser("run",help="run the phase-oriented workflow")
    r.add_argument("--count", type=int, default=20, help="maximum number of objects to process (default: 20)")
    r.add_argument("--workers", type=int)
    r.add_argument("--workflow")
    r.add_argument("-v", "--verbose", action="count", default=0, help="increase console verbosity; use -vv for debug")
    r.add_argument("--ids",help="object IDs separated by | or comma"); r.add_argument("--ids-file"); r.add_argument("--collection",action="append")
    r.add_argument("--force",action="store_true",help="delete results of enabled modules for selected objects and run from scratch")
    r.add_argument("--retry-failed",action="store_true",help="clear scratch/error state for selected objects before running")
    r.set_defaults(func=cmd_run)
    return p


def main()->int:
    args = build_parser().parse_args()
    logsetup.setup(getattr(args, "verbose", 0))
    try:
        return int(args.func(args))
    except RuntimeError as exc:
        print(f"ERROR: {exc}")
        return 2

if __name__=="__main__": raise SystemExit(main())

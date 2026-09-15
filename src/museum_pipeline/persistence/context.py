from __future__ import annotations

import re

from ..configuration import RuntimeConfig
from .postgres import PostgresStore


def _clean(value) -> str:
    if value is None:
        return "Keine Angabe"
    return str(value).replace("\u200b", " ").replace("\u00a0", " ").strip()


class ContextBuilder:
    """Builds stage contexts from profile-defined metadata mappings.

    No source column name or institution-specific cluster is hard-coded here.
    """
    def __init__(self, cfg: RuntimeConfig, store: PostgresStore):
        self.cfg=cfg; self.store=store
        self.meta=cfg.museum.metadata
        self.field_by_id={f["id"]: f for f in self.meta.get("fields", [])}

    def _context(self, conn, obj_id: str, name: str) -> str:
        row=self.store.fetch_source_row(conn,obj_id) or {}
        c=(self.meta.get("contexts") or {})[name]
        labels=c.get("labels") or {}
        lines=[]
        for fid in c.get("include", []):
            f=self.field_by_id[fid]
            val=_clean(row.get(f["source"]))
            if val in ("", "Keine Angabe"):
                continue
            label=labels.get(fid, f["label"])
            lines.append(f"{label}: {val}")
        clusters=c.get("keyword_clusters") or []
        if clusters:
            kws=self.store.keywords(conn,obj_id,clusters)
            if kws:
                lines.append(f"{c.get('keyword_label','Inhaltsschlagworte')}: {kws}")
        return "\n".join(lines)

    def tagging(self, conn, obj_id: str) -> str:
        return self._context(conn,obj_id,"tagging")

    def emotion(self, conn, obj_id: str) -> tuple[str,str]:
        ctx=self._context(conn,obj_id,"emotion")
        master=self.store.master_caption(conn,obj_id)
        drops=set((self.meta.get("contexts") or {}).get("emotion",{}).get("caption_drop_sections",[]))
        if drops:
            parts=re.split(r"(?=^###\s*\d+\.)", master, flags=re.M)
            kept=[]
            for p in parts:
                m=re.match(r"^###\s*(\d+)\.",p.strip())
                if m and int(m.group(1)) in drops:
                    continue
                if p.strip(): kept.append(p.strip())
            master="\n\n".join(kept)
        return ctx, master

    def topics(self, conn, obj_id: str) -> tuple[str,str]:
        return self._context(conn,obj_id,"topics"), self.store.master_caption(conn,obj_id)

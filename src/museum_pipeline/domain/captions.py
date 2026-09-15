from __future__ import annotations

import re
from typing import Optional

from ..configuration import RuntimeConfig

_LEER_MARKER = [
    "nicht verfügbar", "keine sichtbar", "keine sichtbaren schäden oder auffälligkeiten",
    "keine auffälligkeiten", "keine.", "objektart nicht eindeutig erkennbar",
]
_HEADER_RE = re.compile(r"^[#*\s]*([1-8])[.\)]?\s*\*{0,2}\s*([A-ZÄÖÜ][A-ZÄÖÜ\s\/,]{3,})")


def _vision_messages(system: str, user: str, image_b64: str, system_role: bool = True) -> list[dict]:
    if system_role:
        return [
            {"role": "system", "content": system},
            {"role": "user", "content": [{"type": "text", "text": user}, {"type": "image_url", "image_url": {"url": image_b64}}]},
        ]
    return [{"role": "user", "content": [{"type": "text", "text": system + "\n\n" + user}, {"type": "image_url", "image_url": {"url": image_b64}}]}]


def reference_caption_body(cfg: RuntimeConfig, role: str, system: str, user: str, image_b64: str, *, system_role: bool) -> dict:
    body = cfg.models.request_defaults(role)
    body["messages"] = _vision_messages(system, user, image_b64, system_role)
    return body


def synthesis_user(cap_a: str, cap_b: str, *, bias_filter: bool) -> str:
    end = "Prüfe dabei den BIAS-FILTER." if bias_filter else ""
    return (
        'Hier sind die zwei unabhängigen visuellen Befunde:\n\n'
        f'[BEFUND A – Qwen]\n"""\n{cap_a}\n"""\n\n'
        f'[BEFUND B – Gemma]\n"""\n{cap_b}\n"""\n\n'
        'Erstelle den konsolidierten visuellen Befund basierend auf beiden Quellen und dem Originalbild. '
        + end
    ).rstrip()


def synthesis_body(cfg: RuntimeConfig, role: str, system: str, user: str, image_b64: str) -> dict:
    body = cfg.models.request_defaults(role)
    body["messages"] = _vision_messages(system, user, image_b64, system_role=False)
    return body


def _ist_leer(text: Optional[str]) -> bool:
    if not text:
        return True
    t = text.strip().lower()
    return len(t) < 3 or any(t == m or t == m + "." or t.startswith(m) for m in _LEER_MARKER)


def _parse_abschnitte(text: str) -> dict[int, str]:
    out: dict[int, str] = {}; current: Optional[int] = None; buf: list[str] = []
    def flush():
        nonlocal buf
        if current is not None:
            out[current] = "\n".join(buf).strip()
        buf = []
    for line in re.split(r"\r?\n", text):
        m = _HEADER_RE.match(line)
        if m:
            flush(); current = int(m.group(1))
        elif current is not None:
            buf.append(line)
    flush(); return out


def _bereinige(text: Optional[str]) -> str:
    if not text: return ""
    lines = [re.sub(r"^[#*\-\s]+", "", z).strip() for z in re.split(r"\r?\n", text)]
    return re.sub(r"\s+", " ", " ".join(z for z in lines if z)).strip()


def _block(sections: dict[int,str], nums: list[int]) -> str:
    parts=[]
    for n in nums:
        raw=sections.get(n)
        if raw and not _ist_leer(raw):
            clean=_bereinige(raw)
            if clean: parts.append(clean)
    return " ".join(parts)


def decompose(cfg: RuntimeConfig, obj_id: str, asset_ref: dict, master: str, cap_a: str, cap_b: str, tokens_total: int = 0) -> dict:
    sections=_parse_abschnitte(master or "")
    trans_raw=sections.get(5, ""); sens_raw=sections.get(7, "")
    prov=cfg.models.provenance
    return {
        "obj_id": obj_id, "asset_ref": asset_ref or {}, "master_caption": master,
        "res_qwen": cap_a or "", "res_gemma": cap_b or "",
        "text_visuell": _block(sections,[1,3,4]), "text_kontext": _block(sections,[2,6]),
        "transkription": "" if _ist_leer(trans_raw) else _bereinige(trans_raw),
        "hat_transkription": not _ist_leer(trans_raw), "sensitiv_flag": not _ist_leer(sens_raw),
        "parse_ok": all(n in sections for n in (1,2,3)), "tokens_total": tokens_total or 0,
        "modell": prov.get("caption_model",""), "version": prov.get("caption_version",""),
    }

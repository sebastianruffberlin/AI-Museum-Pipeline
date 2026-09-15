from __future__ import annotations

import json
import re
from typing import Any

from ..configuration import RuntimeConfig
from .jsonutil import clean_and_parse


def _norm(value: Any) -> str:
    return str("" if value is None else value).strip().lower()


class TaggingPolicy:
    """Deterministic post-processing driven entirely by the museum profile."""

    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg
        self.profile = cfg.museum.tagging
        self.policy = cfg.museum.tagging_policy
        self.clusters = list(self.profile.get("clusters") or [])
        self.meta_keys = list(self.profile.get("meta_keys") or [])
        classes = self.policy.get("error_classes") or {}
        self.discard_classes = set(classes.get("discard") or [])
        self.repair_classes = set(classes.get("repair") or [])
        self.move_class = str(classes.get("move") or "")
        self.date_re = re.compile(str(self.policy.get("date_pattern") or r"$^"), re.I)
        bias_path = cfg.museum.root / cfg.museum.data["tagging"].get("debias_map", "tagging/debias_map.json")
        if not bias_path.exists():
            bias_path = cfg.museum.root / "tagging" / "debias_map.json"
        self.debias_map: dict[str, dict] = json.loads(bias_path.read_text(encoding="utf-8")) if bias_path.exists() else {}
        self.bias_lookup = {_norm(k): {"original": k, **v} for k, v in self.debias_map.items()}
        self.repair_drop = {_norm(x) for x in (self.policy.get("repair_drop") or [])}
        self.repair_replace = {_norm(k): str(v) for k, v in (self.policy.get("repair_replace") or {}).items()}

    def build_empty_skeleton(self, note: str) -> dict:
        audit_fields = list(self.profile.get("audit_fields") or [])
        restricted = (self.profile.get("protokoll_status_values") or ["Restricted Access"])[-1]
        skel: dict[str, Any] = {
            "_decolonial_audit_log": {k: "" for k in audit_fields},
            "Protokoll_Status": restricted,
            "_provenance_critique": None,
            "Kritischer_Hinweis": note,
        }
        for c in self.clusters:
            skel[c] = []
        return skel

    def _apply_bias(self, parsed: dict, warnings: list[str]) -> None:
        for key, value in list(parsed.items()):
            if key in self.meta_keys or not isinstance(value, list):
                continue
            kept = []
            for entry in value:
                if not entry or not isinstance(entry, dict) or not isinstance(entry.get("term"), str):
                    kept.append(entry)
                    continue
                rule = self.bias_lookup.get(_norm(entry["term"]))
                if not rule:
                    kept.append(entry); continue
                action = str(rule.get("action") or "")
                if action == "DROP":
                    warnings.append(f"Begriff '{entry['term']}' automatisch entfernt ({rule.get('category','Policy')}).")
                    continue
                if action == "REPLACE" and rule.get("replacement"):
                    replacement = rule["replacement"][0] if isinstance(rule["replacement"], list) else rule["replacement"]
                    warnings.append(f"Begriff '{entry['term']}' ersetzt durch '{replacement}' ({rule.get('category','Policy')}).")
                    entry["term"] = replacement
                elif action == "CONTEXTUALIZE":
                    if "[sic!]" not in entry["term"]:
                        entry["term"] = f"{entry['term']} [sic!]"
                    warnings.append(f"SENSITIV: Begriff '{rule.get('original', entry['term'])}' markiert ({rule.get('category','Policy')}).")
                kept.append(entry)
            parsed[key] = kept

    def _derive_status_and_move(self, parsed: dict) -> None:
        moves = []
        for cluster in self.clusters:
            arr = parsed.get(cluster) if isinstance(parsed.get(cluster), list) else []
            for item in arr:
                if not isinstance(item, dict):
                    continue
                flags = item.get("fehlerklassen") if isinstance(item.get("fehlerklassen"), list) else []
                status = "green"
                if any(f in self.discard_classes for f in flags):
                    status = "red"
                elif any(f in self.repair_classes for f in flags):
                    status = "yellow"
                item["status"] = status
                target = item.get("correct_cluster")
                if status != "red" and self.move_class in flags and target in self.clusters and target != cluster:
                    moves.append((cluster, target, item))
        for source, target, item in moves:
            if item in parsed.get(source, []):
                parsed[source].remove(item)
            parsed.setdefault(target, []).append(item)

    def _apply_green_nets(self, parsed: dict, warnings: list[str]) -> None:
        seen: set[str] = set()
        for cluster in self.clusters:
            for item in parsed.get(cluster) if isinstance(parsed.get(cluster), list) else []:
                if not isinstance(item, dict) or item.get("status") != "green" or not isinstance(item.get("term"), str):
                    continue
                if self.date_re.search(item["term"]):
                    item["status"] = "red"
                    item["judge_comment"] = ((item.get("judge_comment", "") + " | ") if item.get("judge_comment") else "") + "CODE-NET: Datierung -> entfernt."
                    warnings.append(f"Datierung '{item['term']}' per Code entfernt.")
                    continue
                key = _norm(item["term"])
                if key in seen:
                    item["status"] = "red"
                    item["judge_comment"] = ((item.get("judge_comment", "") + " | ") if item.get("judge_comment") else "") + "CODE-NET: exakte Dopplung -> entfernt."
                    warnings.append(f"Dopplung '{item['term']}' per Code entfernt.")
                else:
                    seen.add(key)

    def process(self, content_string: str) -> dict:
        parsed = clean_and_parse(content_string)
        if parsed.get("_parsing_error") or parsed.get("error"):
            raw = parsed.get("raw_text", "")
            parsed = self.build_empty_skeleton("AUTO-FLAG: Audit-Antwort nicht parsebar – Objekt ohne Tags durchgereicht.")
            parsed["_llm3_unparsable"] = True
            parsed["_llm3_raw"] = raw
        warnings: list[str] = []
        self._apply_bias(parsed, warnings)
        self._derive_status_and_move(parsed)
        self._apply_green_nets(parsed, warnings)
        if warnings:
            existing = (parsed.get("Kritischer_Hinweis") + " | ") if parsed.get("Kritischer_Hinweis") else ""
            parsed["Kritischer_Hinweis"] = existing + "AUTO-FLAG: " + " ".join(dict.fromkeys(warnings))
        valid: dict[str, Any] = {k: parsed[k] for k in self.meta_keys if k in parsed}
        rejected: dict[str, Any] = {k: parsed[k] for k in self.meta_keys if k in parsed}
        has_red = False
        for cluster in self.clusters:
            value = parsed.get(cluster) if isinstance(parsed.get(cluster), list) else []
            valid[cluster] = [x for x in value if x and x.get("status") == "green"]
            rejected[cluster] = [x for x in value if not x or x.get("status") != "green"]
            has_red = has_red or bool(rejected[cluster])
        parsed["payload_valid"] = valid
        parsed["payload_rejected"] = rejected
        parsed["has_red_status"] = has_red
        return parsed

    def bias_screen(self, raw: str) -> dict | None:
        term = str(raw or "").strip()
        if not term:
            return None
        norm = _norm(term)
        if norm in self.repair_drop:
            return {"term": term, "drop": True}
        if norm in self.repair_replace:
            return {"term": self.repair_replace[norm], "drop": False}
        return {"term": term, "drop": False}

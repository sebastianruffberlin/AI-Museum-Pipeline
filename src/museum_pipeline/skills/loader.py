from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..configuration import RuntimeConfig


class SkillLoader:
    """Loads reusable skill contracts and museum-profile prompt overrides.

    The model never reads files itself. The harness loads the selected skill,
    profile prompt and schema and builds the request context deterministically.
    """
    def __init__(self, cfg: RuntimeConfig):
        self.cfg=cfg
        self.skills_root=Path(__file__).resolve().parent

    def schema(self, skill: str, name: str = "schema") -> dict[str, Any]:
        path=self.skills_root/skill/f"{name}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def prompt(self, prompt_name: str) -> str:
        return self.cfg.museum.prompt(prompt_name)

    def variant_prompt(self, mapping: dict, base_key: str) -> str:
        if self.cfg.settings.prompt_variant == "cache" and f"{base_key}_cache" in mapping:
            return self.prompt(mapping[f"{base_key}_cache"])
        return self.prompt(mapping[base_key])

from __future__ import annotations

import json
import re
from typing import Any


def clean_and_parse(text: str | None) -> dict[str, Any]:
    if not text:
        return {"error": "Empty content"}
    cleaned = re.sub(r"^```json\s*", "", text, flags=re.I)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    a, b = cleaned.find("{"), cleaned.rfind("}")
    if a != -1 and b != -1:
        cleaned = cleaned[a:b + 1]
    try:
        return json.loads(cleaned)
    except Exception:
        try:
            return json.loads(cleaned.replace('\\"', '"'))
        except Exception:
            return {"_parsing_error": True, "raw_text": text}

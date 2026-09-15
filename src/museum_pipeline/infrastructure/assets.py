from __future__ import annotations

import base64
import time

import requests

from ..configuration import RuntimeConfig
from . import logsetup


_log = logsetup.get()


class AssetClient:
    """
    Provider boundary for image assets.

    The runtime only knows a canonical asset_ref:

        {"mode": "s3",  "value": "objects/123.jpg"}
        {"mode": "url", "value": "https://museum.example/123.jpg"}

    S3 presigning and embedding-service payload details stay inside this
    infrastructure adapter.
    """

    SUPPORTED_MODES = {"s3", "url"}

    def __init__(self, cfg: RuntimeConfig):
        self.cfg = cfg
        self.s = cfg.settings

    @classmethod
    def _parts(cls, asset_ref: dict) -> tuple[str, str]:
        if not isinstance(asset_ref, dict):
            raise RuntimeError("Invalid asset_ref: expected mapping")

        mode = str(asset_ref.get("mode") or "").strip().lower()
        value = str(asset_ref.get("value") or "").strip()

        if mode not in cls.SUPPORTED_MODES:
            raise RuntimeError(f"Unsupported asset mode: {mode or '<empty>'}")
        if not value:
            raise RuntimeError("Invalid asset_ref: empty value")

        return mode, value

    def presign_s3(self, obj_id: str, key: str) -> str:
        if not self.s.presign_url:
            raise RuntimeError("PRESIGN_URL is required for S3 assets")
        r = requests.post(
            self.s.presign_url,
            json={
                "obj_id": obj_id,
                "s3_key": key,
                "expires": self.s.presign_expires,
            },
            timeout=self.s.presign_timeout,
        )
        r.raise_for_status()
        data = r.json()
        urls = data.get("urls") or []

        if not urls or not urls[0].get("url"):
            raise RuntimeError(f"Presign returned no URL for {obj_id}")

        return urls[0]["url"]

    def load_image(self, obj_id: str, asset_ref: dict) -> tuple[str, bytes]:
        mode, value = self._parts(asset_ref)

        if mode == "s3":
            url = self.presign_s3(obj_id, value)
        else:
            url = value

        t0 = time.time()
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        raw = r.content

        content_type = (r.headers.get("content-type") or "").split(";", 1)[0].strip()
        if content_type.startswith("image/"):
            mime = content_type
        elif url.lower().split("?", 1)[0].endswith(".png"):
            mime = "image/png"
        else:
            mime = "image/jpeg"

        b64 = base64.b64encode(raw).decode("ascii")

        _log.info(
            "Bild geladen: %s %d KB (%.2fs)",
            obj_id,
            len(raw) // 1024,
            time.time() - t0,
        )

        return f"data:{mime};base64,{b64}", raw

    def embed_image(self, obj_id: str, asset_ref: dict) -> dict:
        mode, value = self._parts(asset_ref)

        payload = {"obj_id": obj_id}
        if mode == "s3":
            payload["s3_key"] = value
        else:
            payload["image_url"] = value

        r = requests.post(
            f"{self.s.embed_base}/embed/image",
            json=payload,
            timeout=self.s.embed_timeout,
        )
        r.raise_for_status()
        return r.json()

    def embed_text(self, items: list[dict], sparse: bool = True) -> dict:
        r = requests.post(
            f"{self.s.embed_base}/embed/text",
            json={"items": items, "sparse": sparse},
            timeout=self.s.embed_timeout,
        )
        r.raise_for_status()
        return r.json()

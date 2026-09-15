"""
Eigenstaendiger S3-Presign-Dienst - herausgeloest aus embed/app.py (Zeilen 349-384).
Signiert zeitlich begrenzte GET-URLs fuer privaten S3-kompatiblen Object Storage.
KEIN Modell, KEINE GPU, KEIN torch/transformers - nur fastapi + boto3.

Response-Format ist BYTE-GENAU wie das Original:
    {"expires_in": <int>, "urls": [{"obj_id":.., "s3_key":.., "url":..}, ...]}
immer ein urls-Array (auch bei Einzel-key), damit bestehende Aufrufer
unveraendert weiterlaufen (sie lesen urls[0].url).

Eingabe (drei Varianten, wie Original):
    {"s3_key": "objects/123.jpg"}
    {"keys": ["objects/1.jpg", "objects/2.jpg"]}
    {"items": [{"obj_id": "DEMO-001", "s3_key": "objects/1.jpg"}]}
    Optional: {"expires": 900}
"""
import os
from typing import List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

S3_ENDPOINT   = os.environ.get("S3_ENDPOINT", "")
S3_BUCKET     = os.environ.get("S3_BUCKET", "")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "")

_s3_client = None


def _s3_endpoint_url(value: str) -> str:
    """Normalize an S3-compatible endpoint; legacy host-only values stay valid."""
    value = value.strip().rstrip("/")
    if not value:
        return value
    if "://" in value:
        return value
    return f"https://{value}"


def get_s3():
    """boto3-Client, erst bei Bedarf erzeugt. Identisch zum Original."""
    global _s3_client
    if _s3_client is None:
        if not (S3_ENDPOINT and S3_BUCKET and S3_ACCESS_KEY and S3_SECRET_KEY):
            raise HTTPException(500, "S3 nicht konfiguriert (S3_ENDPOINT/BUCKET/KEYS fehlen)")
        import boto3
        from botocore.client import Config
        _s3_client = boto3.client(
            "s3",
            endpoint_url=_s3_endpoint_url(S3_ENDPOINT),
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            config=Config(signature_version="s3v4"),
        )
    return _s3_client

app = FastAPI(title="presign-only")

class PresignRequest(BaseModel):
    obj_id: Optional[str] = None
    s3_key: Optional[str] = None
    keys: Optional[List[str]] = None
    items: Optional[List[dict]] = None
    expires: int = 900

@app.get("/health")
def health():
    return {"ok": True, "s3_configured": bool(S3_ENDPOINT and S3_BUCKET and S3_ACCESS_KEY and S3_SECRET_KEY)}

@app.post("/s3/presign")
def s3_presign(req: PresignRequest):
    """1:1 aus embed/app.py herausgeloest - identisches Verhalten und Format."""
    s3 = get_s3()
    pairs: List[Tuple] = []
    if req.items:
        pairs = [(i.get("obj_id"), i.get("s3_key")) for i in req.items]
    elif req.keys:
        pairs = [(None, k) for k in req.keys]
    elif req.s3_key:
        pairs = [(req.obj_id, req.s3_key)]
    else:
        raise HTTPException(400, "Weder s3_key noch keys noch items angegeben")
    out = []
    for obj_id, key in pairs:
        if not key:
            continue
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET, "Key": key},
            ExpiresIn=req.expires,
        )
        out.append({"obj_id": obj_id, "s3_key": key, "url": url})
    return {"expires_in": req.expires, "urls": out}

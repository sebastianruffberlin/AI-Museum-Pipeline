"""
Embedding-Service fuer die Museums-Suchmaschine.

Drei lazy-geladene Encoder hinter einer FastAPI, nach dem Vorbild des
GLiNER2-Service. Jedes Modell wird erst beim ersten Request in den VRAM
geladen und dann gehalten -- so belegt nur das, was tatsaechlich genutzt wird.

Endpoints:
  GET  /health                     -> Status + geladene Modelle
  POST /embed/siglip   {image}     -> Bild-Embedding (SigLIP 2, 1152 dim)
  POST /embed/dino     {image}     -> Bild-Embedding (DINOv2, 768 dim)
  POST /embed/text     {text}      -> Text-Embedding (BGE-M3, 1024 dim, +sparse)

Bild-Input ("image"): entweder
  - {"image_url": "https://..."}   Service laedt selbst (gegen SSRF gehaertet,
                                    siehe load_image/_validate_and_resolve_url)
  - {"image_b64": "<base64>"}      Aufrufer schickt das Bild mit
Batch: {"items": [ {...}, {...} ]} an allen Endpoints moeglich.

Alle Vektoren sind L2-normalisiert -> Cosine == Dot-Product.
"""

import base64
import io
import ipaddress
import os
import socket
from typing import List, Optional
from urllib.parse import urlsplit

import numpy as np
import requests
import torch
from fastapi import FastAPI, HTTPException
from PIL import Image
from pydantic import BaseModel

app = FastAPI(title="Museum Embedding Service", version="1.0")

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32
HTTP_TIMEOUT = int(os.environ.get("IMG_TIMEOUT", "30"))

# ---------------------------------------------------------------- SSRF-Schutz
#
# image_url stammt aus Objektdaten (Museumsdatenbank / Import), nicht aus
# vertrauenswuerdiger Konfiguration. Ohne Haertung koennte ein manipuliertes
# Objekt den Service dazu bringen, interne/private Netzadressen abzufragen.
MAX_IMAGE_DOWNLOAD_BYTES = int(
    os.environ.get("IMG_MAX_DOWNLOAD_BYTES", str(25 * 1024 * 1024))
)
MAX_IMAGE_PIXELS = int(os.environ.get("IMG_MAX_PIXELS", str(64_000_000)))
IMAGE_URL_ALLOWED_SCHEMES = {"http", "https"}
# Optionale institutionelle Allowlist fuer Museen mit tatsaechlich privat
# liegenden Bildservern (kommagetrennte Hostnamen), z.B. "images.intranet".
_ALLOWED_PRIVATE_HOSTS = {
    h.strip().lower()
    for h in os.environ.get("IMG_ALLOWED_PRIVATE_HOSTS", "").split(",")
    if h.strip()
}


def _is_blocked_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _validate_and_resolve_url(url: str) -> None:
    """Raise HTTPException if url is not a safe, public http(s) target."""
    parts = urlsplit(url)
    if parts.scheme.lower() not in IMAGE_URL_ALLOWED_SCHEMES:
        raise HTTPException(400, f"Nicht erlaubtes URL-Schema: {parts.scheme!r}")
    hostname = parts.hostname
    if not hostname:
        raise HTTPException(400, "image_url ohne Hostname")
    if hostname.lower() in _ALLOWED_PRIVATE_HOSTS:
        return
    try:
        infos = socket.getaddrinfo(hostname, None)
    except socket.gaierror as exc:
        raise HTTPException(400, f"image_url nicht aufloesbar: {exc}") from exc
    for info in infos:
        addr = info[4][0]
        if _is_blocked_ip(addr):
            raise HTTPException(
                400,
                f"image_url zeigt auf gesperrten Adressbereich: {addr}",
            )


def _safe_get_image(url: str) -> bytes:
    """Streamed, groessenbegrenzter, redirect-sicherer Bild-Download."""
    _validate_and_resolve_url(url)
    session = requests.Session()
    next_url = url
    for _ in range(5):  # max. 5 Redirects, jeder erneut validiert
        _validate_and_resolve_url(next_url)
        resp = session.get(
            next_url,
            timeout=HTTP_TIMEOUT,
            stream=True,
            allow_redirects=False,
        )
        if resp.is_redirect or resp.is_permanent_redirect:
            location = resp.headers.get("Location")
            resp.close()
            if not location:
                raise HTTPException(400, "Redirect ohne Location-Header")
            next_url = location
            continue
        resp.raise_for_status()
        content_length = resp.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_IMAGE_DOWNLOAD_BYTES:
            resp.close()
            raise HTTPException(413, "Bild ueberschreitet maximale Groesse")
        chunks = bytearray()
        for chunk in resp.iter_content(chunk_size=65536):
            chunks.extend(chunk)
            if len(chunks) > MAX_IMAGE_DOWNLOAD_BYTES:
                resp.close()
                raise HTTPException(413, "Bild ueberschreitet maximale Groesse")
        resp.close()
        return bytes(chunks)
    raise HTTPException(400, "Zu viele Redirects bei image_url")

# S3-compatible object storage - optional, only when s3_key is used
S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "")
S3_BUCKET = os.environ.get("S3_BUCKET", "")
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
    """boto3-Client, erst bei Bedarf erzeugt."""
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

# Modell-IDs (ueberschreibbar per Env)
SIGLIP_ID = os.environ.get("SIGLIP_ID", "google/siglip2-giant-opt-patch16-384")
# DINOv3 ist gated (HF-Token noetig) und steht unter der DINOv3-Lizenz von Meta:
# kommerzielle Nutzung erlaubt, aber bei Weitergabe muss "Built with DINOv3"
# prominent genannt und die Lizenz mitgeliefert werden.
# Apache-2.0-Alternative ohne Auflagen: facebook/dinov2-base
DINO_ID = os.environ.get("DINO_ID", "facebook/dinov3-vitl16-pretrain-lvd1689m")
BGE_ID = os.environ.get("BGE_ID", "BAAI/bge-m3")
# Cross-Encoder fuer Phase 3. Auf Deutsch klar besser als
# Qwen3-Reranker-0.6B; Apache 2.0, 568M Parameter.
RERANK_ID = os.environ.get("RERANK_ID", "BAAI/bge-reranker-v2-m3")

# ---------------------------------------------------------------- Lazy Registry
_models = {}   # name -> geladenes Modell/Objekt


def _load_siglip():
    from transformers import AutoModel, AutoProcessor
    model = AutoModel.from_pretrained(SIGLIP_ID, dtype=DTYPE).to(DEVICE).eval()
    proc = AutoProcessor.from_pretrained(SIGLIP_ID)
    return {"model": model, "proc": proc}


def _load_dino():
    from transformers import AutoModel, AutoImageProcessor
    # DINOv3 in float32 laden: in fp16 entstehen bei manchen Bildern
    # NaN-Werte im pooler_output, die sich nicht serialisieren lassen.
    # Der Mehrbedarf ist bei ViT-L unerheblich (~1,2 GB statt 0,6 GB).
    model = AutoModel.from_pretrained(DINO_ID, dtype=torch.float32).to(DEVICE).eval()
    proc = AutoImageProcessor.from_pretrained(DINO_ID)
    return {"model": model, "proc": proc}


def _load_bge():
    from FlagEmbedding import BGEM3FlagModel
    model = BGEM3FlagModel(BGE_ID, use_fp16=(DEVICE == "cuda"))
    return {"model": model}


def _load_reranker():
    """
    Cross-Encoder fuer Phase 3 des Retrievals.

    Anders als die Bi-Encoder oben sieht er Query UND Dokument
    gemeinsam - deshalb praeziser, aber zu langsam fuer die erste
    Stufe. Nur ueber die Top-K der Fusion laufen lassen.

    bge-reranker-v2-m3 statt Qwen3-Reranker: auf Deutsch deutlich
    staerker (57,6 vs. 51,0 im Querit-Benchmark ueber 18 Sprachen)
    und mit 568M schnell genug fuer interaktive Suche.

    Direkt ueber transformers geladen, nicht ueber FlagEmbedding:
    dessen Wrapper nutzt tokenizer.prepare_for_model, das in
    neueren transformers-Versionen entfernt wurde.
    """
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(RERANK_ID)
    model = AutoModelForSequenceClassification.from_pretrained(
        RERANK_ID, dtype=DTYPE).to(DEVICE).eval()
    return {"model": model, "tok": tok}


_LOADERS = {"siglip": _load_siglip, "dino": _load_dino,
            "bge": _load_bge, "rerank": _load_reranker}


def get_model(name: str):
    if name not in _models:
        if name not in _LOADERS:
            raise HTTPException(400, f"Unbekanntes Modell: {name}")
        _models[name] = _LOADERS[name]()
    return _models[name]


# ---------------------------------------------------------------- Bild laden

def load_image(image_url: Optional[str], image_b64: Optional[str],
               s3_key: Optional[str] = None) -> Image.Image:
    """
    Drei Wege, ein Bild zu bekommen:
      s3_key    -> direkt aus dem privaten S3-kompatiblen Bucket, kein Presigning
      image_b64 -> Aufrufer schickt das Bild mit
      image_url -> Service laedt selbst per HTTP (SSRF-gehaertet, siehe
                   _safe_get_image: Schema-Whitelist, DNS-Aufloesung gegen
                   private/loopback/link-local/reserved gesperrt, jeder
                   Redirect erneut geprueft, Downloadgroesse begrenzt)
    """
    if s3_key:
        obj = get_s3().get_object(Bucket=S3_BUCKET, Key=s3_key)
        return Image.open(io.BytesIO(obj["Body"].read())).convert("RGB")
    if image_b64:
        # optionalen data:-Praefix entfernen
        if "," in image_b64 and image_b64.strip().startswith("data:"):
            image_b64 = image_b64.split(",", 1)[1]
        raw = base64.b64decode(image_b64)
        if len(raw) > MAX_IMAGE_DOWNLOAD_BYTES:
            raise HTTPException(413, "Bild ueberschreitet maximale Groesse")
        img = Image.open(io.BytesIO(raw))
    elif image_url:
        raw = _safe_get_image(image_url)
        img = Image.open(io.BytesIO(raw))
    else:
        raise HTTPException(400, "Weder s3_key noch image_url noch image_b64 angegeben")
    if img.width * img.height > MAX_IMAGE_PIXELS:
        raise HTTPException(413, "Bild ueberschreitet maximale Pixelzahl")
    return img.convert("RGB")


# ---------------------------------------------------------------- Schemas

class ImageItem(BaseModel):
    obj_id: Optional[str] = None
    image_url: Optional[str] = None
    image_b64: Optional[str] = None
    s3_key: Optional[str] = None


class ImageRequest(BaseModel):
    # Einzeln ODER Batch
    obj_id: Optional[str] = None
    image_url: Optional[str] = None
    image_b64: Optional[str] = None
    s3_key: Optional[str] = None
    items: Optional[List[ImageItem]] = None


class TextItem(BaseModel):
    obj_id: Optional[str] = None
    text: str


class PresignRequest(BaseModel):
    """Einzeln oder Batch: s3_key(s) -> zeitlich begrenzte URLs."""
    obj_id: Optional[str] = None
    s3_key: Optional[str] = None
    keys: Optional[List[str]] = None
    items: Optional[List[dict]] = None      # [{obj_id, s3_key}, ...]
    expires: int = 900                       # Sekunden, Standard 15 Min


class TextRequest(BaseModel):
    obj_id: Optional[str] = None
    text: Optional[str] = None
    items: Optional[List[TextItem]] = None
    sparse: bool = False        # BGE-M3 kann zusaetzlich Sparse-Vektoren liefern


def _as_items_image(req: ImageRequest) -> List[ImageItem]:
    if req.items:
        return req.items
    return [ImageItem(obj_id=req.obj_id, image_url=req.image_url,
                      image_b64=req.image_b64, s3_key=req.s3_key)]


def _as_items_text(req: TextRequest) -> List[TextItem]:
    if req.items:
        return req.items
    if req.text is None:
        raise HTTPException(400, "Weder text noch items angegeben")
    return [TextItem(obj_id=req.obj_id, text=req.text)]


# ---------------------------------------------------------------- Encoder

def _as_tensor(out):
    """
    Vereinheitlicht den Rueckgabewert der Encoder.
    Je nach transformers-Version liefern get_image_features()/forward()
    entweder direkt einen Tensor oder ein Output-Objekt
    (BaseModelOutputWithPooling). Beides wird hier auf [B, dim] gebracht.
    """
    if torch.is_tensor(out):
        return out
    pooled = getattr(out, "pooler_output", None)
    if pooled is not None:
        return pooled
    hidden = getattr(out, "last_hidden_state", None)
    if hidden is not None:
        return hidden[:, 0]          # Class-Token
    if isinstance(out, (tuple, list)) and torch.is_tensor(out[0]):
        return out[0]
    raise RuntimeError(f"Unerwarteter Encoder-Output: {type(out)}")


@torch.no_grad()
def _embed_images(name: str, imgs: List[Image.Image]) -> np.ndarray:
    m = get_model(name)
    proc, model = m["proc"], m["model"]
    inputs = proc(images=imgs, return_tensors="pt").to(DEVICE)
    if name == "siglip":
        feats = _as_tensor(model.get_image_features(**inputs))
    else:
        # DINOv2/v3: Class-Token an Position 0.
        # (DINOv3 hat danach 4 Register-Tokens, dann die Patch-Tokens --
        #  fuer Bildaehnlichkeit brauchen wir nur den Class-Token.)
        feats = _as_tensor(model(**inputs))
    return _finalize(feats)


def _finalize(feats: torch.Tensor) -> np.ndarray:
    """
    In float32 normalisieren und JSON-tauglich machen.
    fp16 kann bei sehr kleinen Normen ueberlaufen -> NaN/Inf, die sich
    nicht serialisieren lassen. eps in der Normalisierung + nan_to_num
    faengt das ab.
    """
    feats = feats.float()
    feats = torch.nan_to_num(feats, nan=0.0, posinf=0.0, neginf=0.0)
    feats = torch.nn.functional.normalize(feats, p=2, dim=-1, eps=1e-8)
    arr = feats.cpu().numpy().astype(np.float32)
    return np.nan_to_num(arr, nan=0.0, posinf=0.0, neginf=0.0)


# ---------------------------------------------------------------- Endpoints

@app.get("/health")
def health():
    return {
        "status": "ok",
        "device": DEVICE,
        "geladen": list(_models.keys()),
        "verfuegbar": list(_LOADERS.keys()),
    }


@app.post("/embed/siglip")
def embed_siglip(req: ImageRequest):
    items = _as_items_image(req)
    imgs = [load_image(i.image_url, i.image_b64, i.s3_key) for i in items]
    vecs = _embed_images("siglip", imgs)
    return {"model": SIGLIP_ID, "dim": int(vecs.shape[1]),
            "embeddings": [{"obj_id": it.obj_id, "vector": v.tolist()}
                           for it, v in zip(items, vecs)]}


@app.post("/embed/dino")
def embed_dino(req: ImageRequest):
    items = _as_items_image(req)
    imgs = [load_image(i.image_url, i.image_b64, i.s3_key) for i in items]
    vecs = _embed_images("dino", imgs)
    return {"model": DINO_ID, "dim": int(vecs.shape[1]),
            "embeddings": [{"obj_id": it.obj_id, "vector": v.tolist()}
                           for it, v in zip(items, vecs)]}


@app.post("/embed/image")
def embed_image_both(req: ImageRequest):
    """
    Beide Bildmodelle in EINEM Durchgang.
    Das Bild wird nur einmal geladen -- spart bei grossen Bestaenden
    die Haelfte der Downloads.
    """
    items = _as_items_image(req)
    imgs = [load_image(i.image_url, i.image_b64, i.s3_key) for i in items]
    sig = _embed_images("siglip", imgs)
    din = _embed_images("dino", imgs)
    return {
        "models": {"siglip": SIGLIP_ID, "dino": DINO_ID},
        "dims": {"siglip": int(sig.shape[1]), "dino": int(din.shape[1])},
        "embeddings": [
            {"obj_id": it.obj_id,
             "siglip": s.tolist(),
             "dino": d.tolist()}
            for it, s, d in zip(items, sig, din)
        ]
    }


@app.post("/embed/siglip_text")
def embed_siglip_text(req: TextRequest):
    """
    Query-Seite fuer die Bildsuche: Text -> SigLIP-Textturm -> Vektor,
    der im selben Raum liegt wie die Bildvektoren.

    WICHTIG (HF-Doku): SigLIP wurde mit padding="max_length" und
    max_length=64 trainiert. Ohne diese Vorgabe weichen die Vektoren ab.
    """
    items = _as_items_text(req)
    m = get_model("siglip")
    proc, model = m["proc"], m["model"]
    with torch.no_grad():
        inputs = proc(text=[it.text for it in items],
                      padding="max_length", max_length=64,
                      truncation=True, return_tensors="pt").to(DEVICE)
        feats = _as_tensor(model.get_text_features(**inputs))
    vecs = _finalize(feats)
    return {"model": SIGLIP_ID, "dim": int(vecs.shape[1]),
            "embeddings": [{"obj_id": it.obj_id, "vector": v.tolist()}
                           for it, v in zip(items, vecs)]}


@app.post("/s3/presign")
def s3_presign(req: PresignRequest):
    """
    Erzeugt zeitlich begrenzte URLs fuer Objekte im privaten Bucket.

    Damit koennen nachgelagerte Dienste (Caption-Modelle etc.) Bilder
    laden, ohne die S3-Zugangsdaten zu kennen und ohne den Bucket
    oeffentlich zu machen.

    Eingabe (drei Varianten):
      {"s3_key": "objects/123.jpg"}
      {"keys": ["objects/1.jpg", "objects/2.jpg"]}
      {"items": [{"obj_id": "DEMO-001", "s3_key": "objects/1.jpg"}]}

    Optional: {"expires": 900}   Gueltigkeit in Sekunden (Standard 15 Min)
    """
    s3 = get_s3()

    # Eingabe vereinheitlichen zu [(obj_id, s3_key), ...]
    pairs: List[tuple] = []
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


class RerankItem(BaseModel):
    obj_id: Optional[str] = None
    text: str


class RerankRequest(BaseModel):
    """
    Phase 3: Kandidaten neu sortieren.

    Der Cross-Encoder liest Query und Dokument GEMEINSAM - er kann
    damit Bezuege erkennen, die getrennt kodierte Vektoren nicht
    erfassen. Preis: ein Modelldurchlauf pro Kandidat, deshalb nur
    ueber die Top-K der Fusion (20-50), nicht ueber den Bestand.
    """
    query: str
    items: List[RerankItem]
    top_k: Optional[int] = None      # None = alle zurueckgeben
    normalize: bool = True           # Scores auf 0..1 (Sigmoid)


@app.post("/rerank")
def rerank(req: RerankRequest):
    if not req.items:
        return {"model": RERANK_ID, "results": []}

    m = get_model("rerank")
    model, tok = m["model"], m["tok"]

    paare = [[req.query, it.text] for it in req.items]

    # In Batches, damit lange Kandidatenlisten nicht den VRAM sprengen
    scores = []
    BATCH = 16
    with torch.no_grad():
        for i in range(0, len(paare), BATCH):
            teil = paare[i:i + BATCH]
            inputs = tok(teil, padding=True, truncation=True,
                         max_length=512, return_tensors="pt").to(DEVICE)
            logits = model(**inputs).logits.view(-1).float()
            if req.normalize:
                logits = torch.sigmoid(logits)     # -> 0..1
            scores.extend(logits.cpu().tolist())

    ergebnis = [
        {"obj_id": it.obj_id, "score": float(s), "rang_vorher": i + 1}
        for i, (it, s) in enumerate(zip(req.items, scores))
    ]
    ergebnis.sort(key=lambda x: -x["score"])
    for rang, e in enumerate(ergebnis, start=1):
        e["rang_nachher"] = rang

    if req.top_k:
        ergebnis = ergebnis[:req.top_k]

    return {"model": RERANK_ID, "anzahl": len(ergebnis), "results": ergebnis}


@app.post("/embed/text")
def embed_text(req: TextRequest):
    items = _as_items_text(req)
    m = get_model("bge")["model"]
    texts = [it.text for it in items]
    out = m.encode(texts, return_dense=True, return_sparse=req.sparse,
                   return_colbert_vecs=False)
    dense = np.asarray(out["dense_vecs"], dtype=np.float32)
    dense = np.nan_to_num(dense, nan=0.0, posinf=0.0, neginf=0.0)
    result = []
    for idx, it in enumerate(items):
        entry = {"obj_id": it.obj_id, "vector": dense[idx].tolist()}
        if req.sparse:
            # lexical_weights: {token_id: gewicht} -> fuer Qdrant Sparse
            lw = out["lexical_weights"][idx]
            entry["sparse"] = {str(k): float(v) for k, v in lw.items()
                               if np.isfinite(v)}
        result.append(entry)
    return {"model": BGE_ID, "dim": int(dense.shape[1]),
            "embeddings": result}

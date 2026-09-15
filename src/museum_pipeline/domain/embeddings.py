from __future__ import annotations

from ..infrastructure.assets import AssetClient
from ..persistence.postgres import PostgresStore


def image_embeddings(store: PostgresStore, assets: AssetClient, conn, obj_id: str, asset_ref: dict) -> None:
    resp = assets.embed_image(obj_id, asset_ref)
    for entry in resp.get("embeddings", []):
        store.write_image_embeddings(conn, str(entry.get("obj_id") or obj_id), entry["siglip"], entry["dino"])


_TEXT_KINDS = [
    ("text_basis", "text_basis"),
    ("text_erschliessung", "text_erschliessung"),
    ("text_visuell", "text_visuell"),
    ("text_kontext", "text_kontext"),
    ("text_fliesstext", "text_fliesstext"),
]


def text_embeddings(store: PostgresStore, assets: AssetClient, conn, obj_id: str) -> int:
    row = store.text_embedding_row(conn, obj_id)
    items=[]
    for col, kind in _TEXT_KINDS:
        text=row.get(col)
        if text and str(text).strip():
            items.append({"obj_id":f"{obj_id}|{kind}","text":str(text)})
    if not items: return 0
    resp=assets.embed_text(items,sparse=True); written=0
    for entry in resp.get("embeddings",[]):
        combined=str(entry.get("obj_id") or ""); cut=combined.rfind("|")
        if cut<0: continue
        store.write_text_embedding(conn,combined[:cut],combined[cut+1:],entry["vector"],entry.get("sparse")); written+=1
    return written

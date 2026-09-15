from types import SimpleNamespace

import museum_pipeline.infrastructure.assets as assets_module
from museum_pipeline.infrastructure.assets import AssetClient
from museum_pipeline.persistence.postgres import PostgresStore


def _store(source):
    cfg = SimpleNamespace(
        settings=SimpleNamespace(),
        museum=SimpleNamespace(metadata={"source": source}),
    )
    return PostgresStore(cfg)


def test_new_s3_asset_profile_normalizes_to_asset_ref():
    store = _store(
        {
            "table": "museum.raw_objects",
            "id_column": "object_id",
            "asset": {
                "mode": "s3",
                "column": "image_ref",
                "key": {
                    "marker": "/objects/",
                    "prefix": "objects/",
                },
            },
        }
    )

    assert store.asset_mode == "s3"
    assert store.asset_col == "image_ref"
    assert store._asset_ref(
        "https://bucket.example/objects/123.jpg"
    ) == {
        "mode": "s3",
        "value": "objects/123.jpg",
    }


def test_url_asset_profile_preserves_direct_url():
    store = _store(
        {
            "table": "museum.raw_objects",
            "id_column": "object_id",
            "asset": {
                "mode": "url",
                "column": "public_image_url",
            },
        }
    )

    url = "https://museum.example/images/123.jpg"

    assert store.asset_mode == "url"
    assert store._asset_ref(url) == {
        "mode": "url",
        "value": url,
    }


def test_legacy_image_url_column_remains_supported_as_s3():
    store = _store(
        {
            "table": "museum.raw_objects",
            "id_column": "object_id",
            "image_url_column": "s3_url",
            "image_key": {
                "marker": "/objects/",
                "prefix": "objects/",
            },
        }
    )

    assert store.asset_mode == "s3"
    assert store._asset_ref(
        "https://bucket.example/objects/legacy.jpg"
    ) == {
        "mode": "s3",
        "value": "objects/legacy.jpg",
    }


class _Response:
    def __init__(self, *, data=None, content=b"", content_type=""):
        self._data = data or {}
        self.content = content
        self.headers = {"content-type": content_type}

    def raise_for_status(self):
        return None

    def json(self):
        return self._data


def _asset_client():
    settings = SimpleNamespace(
        presign_url="https://presign.example/s3/presign",
        presign_expires=3600,
        presign_timeout=30,
        embed_base="https://embed.example",
        embed_timeout=300,
    )
    return AssetClient(SimpleNamespace(settings=settings))


def test_embed_image_uses_s3_payload_for_s3_asset(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return _Response(data={"embeddings": []})

    monkeypatch.setattr(assets_module.requests, "post", fake_post)

    client = _asset_client()
    client.embed_image(
        "OBJ-1",
        {"mode": "s3", "value": "objects/1.jpg"},
    )

    assert calls[0][1] == {
        "obj_id": "OBJ-1",
        "s3_key": "objects/1.jpg",
    }


def test_embed_image_uses_image_url_for_url_asset(monkeypatch):
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return _Response(data={"embeddings": []})

    monkeypatch.setattr(assets_module.requests, "post", fake_post)

    client = _asset_client()
    client.embed_image(
        "OBJ-2",
        {
            "mode": "url",
            "value": "https://museum.example/images/2.jpg",
        },
    )

    assert calls[0][1] == {
        "obj_id": "OBJ-2",
        "image_url": "https://museum.example/images/2.jpg",
    }


def test_direct_url_image_load_does_not_presign(monkeypatch):
    post_calls = []
    get_calls = []

    def fake_post(*args, **kwargs):
        post_calls.append((args, kwargs))
        raise AssertionError("URL assets must not use the presign service")

    def fake_get(url, timeout):
        get_calls.append((url, timeout))
        return _Response(
            content=b"PNGDATA",
            content_type="image/png",
        )

    monkeypatch.setattr(assets_module.requests, "post", fake_post)
    monkeypatch.setattr(assets_module.requests, "get", fake_get)

    client = _asset_client()
    encoded, raw = client.load_image(
        "OBJ-3",
        {
            "mode": "url",
            "value": "https://museum.example/images/3.png",
        },
    )

    assert not post_calls
    assert get_calls == [
        ("https://museum.example/images/3.png", 60)
    ]
    assert raw == b"PNGDATA"
    assert encoded.startswith("data:image/png;base64,")

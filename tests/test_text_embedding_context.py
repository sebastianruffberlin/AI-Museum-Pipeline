from pathlib import Path
from types import SimpleNamespace

import pytest

from museum_pipeline.persistence.postgres import PostgresStore


ROOT = Path(__file__).resolve().parents[1]


def _store():
    metadata = {
        "source": {
            "table": "collection.objects",
            "id_column": "accession_number",
            "asset": {
                "mode": "url",
                "column": "image_url",
            },
        },
        "fields": [
            {
                "id": "object_type",
                "source": "object_name",
                "label": "Objektart",
            },
            {
                "id": "title",
                "source": "title",
                "label": "Titel",
            },
            {
                "id": "dating",
                "source": "date_text",
                "label": "Datierung",
            },
            {
                "id": "description",
                "source": "notes",
                "label": "Beschreibung",
            },
        ],
        "text_embeddings": {
            "basis": {
                "include": [
                    "object_type",
                    "title",
                    "dating",
                    "description",
                ],
                "labels": {
                    "dating": "Datierung",
                },
            },
            "flowing_text": {
                "include": ["description"],
            },
            "keywords_label": "Schlagworte",
        },
    }

    cfg = SimpleNamespace(
        settings=SimpleNamespace(),
        museum=SimpleNamespace(metadata=metadata),
    )
    return PostgresStore(cfg)


def test_text_embedding_context_uses_profile_mapping():
    store = _store()

    source = {
        "accession_number": "ABC-1",
        "object_name": "Fotografie",
        "title": "Straßenszene",
        "date_text": "um 1920",
        "notes": "Menschen auf einer Straße.",
    }

    store.fetch_source_row = lambda conn, obj_id: source

    def fake_fetch_one(conn, sql, params=None):
        if "string_agg" in sql:
            return {"value": "Straße, Mensch"}
        if "text_visuell" in sql:
            return {
                "text_visuell": "Schwarzweiße Außenaufnahme.",
                "text_kontext": "Urbaner Straßenraum.",
            }
        raise AssertionError(sql)

    store.fetch_one = fake_fetch_one

    row = store.text_embedding_row(None, "ABC-1")

    basis = (
        "Fotografie. Straßenszene. Datierung: um 1920. "
        "Menschen auf einer Straße."
    )

    assert row == {
        "obj_id": "ABC-1",
        "text_basis": basis,
        "text_erschliessung": basis + ". Schlagworte: Straße, Mensch",
        "text_visuell": basis + ". Schwarzweiße Außenaufnahme.",
        "text_kontext": basis + ". Urbaner Straßenraum.",
        "text_fliesstext": "Menschen auf einer Straße.",
    }


def test_text_embedding_context_rejects_unknown_profile_field():
    store = _store()

    with pytest.raises(RuntimeError, match="unknown metadata field"):
        store._text_from_profile_fields(
            {},
            {"include": ["does_not_exist"]},
        )


def test_core_no_longer_depends_on_v_text_embeddings():
    text = (
        ROOT / "src/museum_pipeline/persistence/postgres.py"
    ).read_text(encoding="utf-8")

    assert "museum.v_text_embeddings" not in text

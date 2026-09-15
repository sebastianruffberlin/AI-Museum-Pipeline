from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "database" / "core.sql"


def _sql() -> str:
    return SCHEMA.read_text(encoding="utf-8")


def test_core_schema_contains_required_core_tables():
    sql = _sql()

    required = [
        "museum.embeddings",
        "museum.enrichment_captions",
        "museum.enrichment_derived",
        "museum.enrichment_keywords",
    ]

    for table in required:
        assert table in sql


def test_core_schema_excludes_institution_source_tables():
    sql = _sql().lower()

    forbidden = [
        "raw_objects",
        "inv_nr",
        "sammlung",
        "sammlungsbereich",
        "objektbezeichnung",
    ]

    for token in forbidden:
        assert token not in sql


def test_core_schema_excludes_optional_module_models():
    sql = _sql().lower()

    forbidden = [
        "schwerpunkt_",
        "resonanz_",
        "emotion_lauf",
        "concept_family",
        "objekt_lesart",
    ]

    for token in forbidden:
        assert token not in sql


def test_core_schema_has_no_deployment_owner():
    sql = _sql().lower()

    assert "owner to" not in sql
    assert "alter owner" not in sql


def test_core_schema_supports_runtime_upsert_keys():
    sql = " ".join(_sql().lower().split())

    assert "primary key (obj_id, kind, modell)" in sql
    assert "unique (obj_id, modell)" in sql
    assert "obj_id text primary key" in sql

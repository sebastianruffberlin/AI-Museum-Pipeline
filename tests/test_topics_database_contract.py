from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "src" / "museum_pipeline" / "persistence" / "postgres.py"
TOPICS_SQL = ROOT / "database" / "modules" / "topics.sql"
MIGRATION_SQL = ROOT / "database" / "migrations" / "002_topics_generic.sql"


def test_runtime_uses_generic_topic_result_tables():
    text = STORE.read_text(encoding="utf-8")

    assert "museum.topic_assignments" in text
    assert "museum.topic_runs" in text

    assert "museum.schwerpunkt_bezug" not in text
    assert "museum.schwerpunkt_lauf" not in text


def test_topics_module_schema_is_generic():
    text = TOPICS_SQL.read_text(encoding="utf-8").lower()

    required = [
        "museum.topic_assignments",
        "museum.topic_runs",
        "topic",
        "relation_types",
        "rationale",
        "taxonomy_version",
        "object_findings",
        "assignment_count",
    ]

    for token in required:
        assert token in text

    for token in [
        "schwerpunkt_",
        "qwen3.6",
        "gemma-4",
        "owner to",
    ]:
        assert token not in text


def test_topic_taxonomy_is_not_owned_by_generic_database_module():
    text = TOPICS_SQL.read_text(encoding="utf-8").lower()

    forbidden = [
        "museum.schwerpunkt_wissen",
        "museum.schwerpunkt_unterthema",
        "museum.schwerpunkt_vokabular",
    ]

    for token in forbidden:
        assert token not in text


def test_existing_installations_have_explicit_topic_migration():
    text = MIGRATION_SQL.read_text(encoding="utf-8")

    assert "museum.schwerpunkt_bezug" in text
    assert "museum.schwerpunkt_lauf" in text
    assert "museum.topic_assignments" in text
    assert "museum.topic_runs" in text

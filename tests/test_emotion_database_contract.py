from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

STORE = ROOT / "src/museum_pipeline/persistence/postgres.py"
DOMAIN = ROOT / "src/museum_pipeline/domain/emotion.py"
MODULE = ROOT / "database/modules/emotion.sql"
MIGRATION = ROOT / "database/migrations/003_emotion_generic.sql"


def test_runtime_uses_generic_emotion_result_tables():
    text = STORE.read_text(encoding="utf-8")

    assert "museum.emotion_assignments" in text
    assert "museum.emotion_runs" in text

    assert "museum.emotion_lauf" not in text
    assert "INSERT INTO museum.emotion\n" not in text


def test_emotion_module_is_independent_of_reference_vocabulary():
    text = MODULE.read_text(encoding="utf-8").lower()

    assert "museum.emotion_assignments" in text
    assert "museum.emotion_runs" in text

    for token in [
        "resonanz_",
        "concept_family",
        "concept_relation",
        "machine_proposal",
        "'v4'",
        "owner to",
    ]:
        assert token not in text


def test_emotion_run_provenance_is_explicit():
    domain = DOMAIN.read_text(encoding="utf-8")
    schema = MODULE.read_text(encoding="utf-8").lower()

    assert '"vocabulary_version":str(self.profile.get("vocabulary_version",""))' in domain

    assert "vocabulary_version" in schema
    assert "default 'v4'" not in schema


def test_existing_installations_have_emotion_migration():
    text = MIGRATION.read_text(encoding="utf-8")

    assert "museum.emotion" in text
    assert "museum.emotion_lauf" in text
    assert "museum.emotion_assignments" in text
    assert "museum.emotion_runs" in text

    for new_column in [
        "reading_count",
        "visible_findings",
        "depicted_situations",
        "free_effects",
        "unmappable_effects",
        "considered_rejected",
        "no_reading_reason",
    ]:
        assert new_column in text

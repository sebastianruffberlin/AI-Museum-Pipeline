from pathlib import Path

import json
import yaml

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT / "profiles" / "stadtmuseum-berlin"
TEMPLATE = ROOT / "profiles" / "_template"


def test_reference_profile_does_not_ship_private_database_resources():
    assert not (PROFILE / "resources").exists()
    assert not (PROFILE / "seeds").exists()


def test_reference_profile_ships_machine_heart_but_no_institution_topics():
    emotion = yaml.safe_load((PROFILE / "emotion/profile.yaml").read_text(encoding="utf-8"))
    assert emotion["resources"]["source"] == "file"
    assert not (PROFILE / "topics").exists()
    profile = yaml.safe_load((PROFILE / "profile.yaml").read_text(encoding="utf-8"))
    assert "topics" not in profile


def test_public_starter_contains_topic_blueprint_only():
    topic_dir = TEMPLATE / "topics"
    assert (topic_dir / "framework.template.md").is_file()
    assert (topic_dir / "taxonomy.template.json").is_file()
    assert (topic_dir / "profile.example.yaml").is_file()
    assert not (topic_dir / "framework.md").exists()
    assert not (topic_dir / "taxonomy.json").exists()


def test_machine_heart_standard_counts_match_runtime_contract():
    concepts = json.loads((TEMPLATE / "emotion/concepts.json").read_text(encoding="utf-8"))
    runtime = json.loads((TEMPLATE / "emotion/vocabulary.runtime.json").read_text(encoding="utf-8"))
    assert len(concepts) == 146
    assert len(runtime) == 121
    assert all(x.get("concept_id") and x.get("begriff") and x.get("definition") for x in runtime)


def test_install_manifest_requires_no_private_profile_sql():
    install = yaml.safe_load((PROFILE / "install.yaml").read_text(encoding="utf-8"))
    assert install["database_sql"] == []

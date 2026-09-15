from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_machine_heart_authoring_and_runtime_projection_match():
    for profile in ("_template", "stadtmuseum-berlin"):
        base = ROOT / "profiles" / profile / "emotion"
        concepts = json.loads((base / "concepts.json").read_text(encoding="utf-8"))
        runtime = json.loads((base / "vocabulary.runtime.json").read_text(encoding="utf-8"))
        active = {x["concept_id"] for x in concepts if x.get("concept_role") == "resonance_reading"}
        runtime_ids = {x["concept_id"] for x in runtime}
        assert len(concepts) == 146
        assert len(runtime) == 121
        assert runtime_ids == active
        for item in runtime:
            assert item.get("concept_id")
            assert item.get("begriff")
            assert item.get("definition")


def test_keyword_reference_has_exactly_eleven_clusters():
    import yaml
    for profile in ("_template", "stadtmuseum-berlin"):
        data = yaml.safe_load((ROOT / "profiles" / profile / "tagging" / "profile.yaml").read_text(encoding="utf-8"))
        assert len(data["clusters"]) == 11


def test_public_prompts_do_not_use_n8n_expression_syntax():
    for profile in ("_template", "stadtmuseum-berlin"):
        for path in (ROOT / "profiles" / profile / "prompts").glob("*.txt"):
            text = path.read_text(encoding="utf-8")
            assert "{{" not in text, path
            assert "$json" not in text, path
            assert "$('" not in text, path


def test_tagging_policy_contains_no_unreachable_material_technik_class():
    for profile in ("_template", "stadtmuseum-berlin"):
        text = (ROOT / "profiles" / profile / "tagging" / "policy.yaml").read_text(encoding="utf-8")
        assert "MATERIAL_TECHNIK" not in text


def test_colour_mapping_fixtures_are_synthetic_and_provider_neutral():
    text = (ROOT / "services" / "farbnamen" / "farbnamen_mapping.py").read_text(encoding="utf-8")
    assert "DEMO-COLOR-001" in text
    assert "DEMO-COLOR-002" in text
    assert "DEMO-COLOR-003" in text
    assert "DB-Lauf (Hetzner)" not in text
    assert "Kapitel 24.5" not in text


def test_design_decisions_are_documented():
    text = (ROOT / "docs" / "MUSEUM_DESIGN_DECISIONS.md").read_text(encoding="utf-8")
    for token in ("11 Cluster", "Keyword-Generator", "Farbsystem", "institutionellen Topics-Modul", "Machine Heart"):
        assert token.lower() in text.lower()

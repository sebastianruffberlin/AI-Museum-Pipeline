from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_license_and_security_files_exist():
    for rel in ("LICENSE", "THIRD_PARTY_NOTICES.md", "SECURITY.md", "CONTRIBUTING.md"):
        assert (ROOT / rel).is_file(), rel


def test_ci_and_dependency_update_config_exist():
    for rel in (
        ".github/workflows/ci.yml",
        ".github/dependabot.yml",
    ):
        assert (ROOT / rel).is_file(), rel


def test_deployment_example_starts_with_core_workflow():
    data = yaml.safe_load((ROOT / "deployment.example.yaml").read_text(encoding="utf-8"))
    assert data["workflow"] == "core"


def test_gpu_runtime_secret_file_is_outside_checkout():
    text = (ROOT / "src/museum_pipeline/installer/runner.py").read_text(encoding="utf-8")
    assert 'f"{gpu.config_dir}/runtime.env"' in text
    assert 'f"{gpu.install_path}/gpu.env"' not in text
    assert 'chmod 600' in text


def test_development_history_material_is_not_in_public_tree():
    assert not (ROOT / "docs/v1-reference").exists()
    assert not (ROOT / "profiles/stadtmuseum-berlin/tools/v1-reference").exists()
    for rel in (
        "docs/V1_V2_MAP.md",
        "docs/REGRESSION.md",
        "docs/TEST_A_HARDENING.md",
        "docs/STATUS_QUO_2026-09.md",
    ):
        assert not (ROOT / rel).exists(), rel


def test_readme_is_single_public_product_document():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert text.count("# 🏛️ AI Museum Pipeline") == 1
    assert "AI Museum Pipeline V2" not in text
    assert "Masterdokument V3" not in text


def test_public_tree_contains_no_institution_specific_topic_contents():
    assert not (ROOT / "profiles/stadtmuseum-berlin/topics").exists()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    topic_doc = (ROOT / "docs/TOPIC_KNOWLEDGE_BASE.md").read_text(encoding="utf-8")
    assert "public reference profile contains a small" not in readme
    for label in ("Stadtökologie", "Stadtentwicklung", "Geteilte Stadt", "Vergnügen"):
        assert label not in topic_doc
    demo = (ROOT / "examples/DEMO-001.json").read_text(encoding="utf-8")
    assert "Stadtentwicklung" not in demo


def test_demo_object_covers_all_pipeline_output_tables():
    import json
    demo = json.loads((ROOT / "examples/DEMO-001.json").read_text(encoding="utf-8"))
    for table in (
        "museum.enrichment_derived",
        "museum.embeddings",
        "museum.enrichment_captions",
        "museum.enrichment_keywords",
        "museum.emotion_runs",
        "museum.emotion_assignments",
        "museum.topic_assignments",
    ):
        assert table in demo, table
    # illustrates both the repair and the discard path, not only the happy path
    statuses = {kw.get("status") for kw in demo["museum.enrichment_keywords"]}
    audit1s = {kw.get("audit1") for kw in demo["museum.enrichment_keywords"]}
    assert "red" in statuses
    assert "PLURAL" in audit1s
    assert "KEINE_EVIDENZ" in audit1s


def test_machine_heart_public_standard_is_complete():
    import json
    base = ROOT / "profiles/_template/emotion"
    concepts = json.loads((base / "concepts.json").read_text(encoding="utf-8"))
    runtime = json.loads((base / "vocabulary.runtime.json").read_text(encoding="utf-8"))
    assert len(concepts) == 146
    assert len(runtime) == 121


def test_real_reference_object_contains_no_private_topic_content():
    """examples/92-45.json is a real production object (public domain).

    Its museum.emotion_assignments came from a query joined on
    annotation_set_id and originally included rows from an unrelated,
    more sensitive object (a WWI military ceremony scene, obj_id
    '37-WK I') that happened to share the same daily run. Its
    institutional topic data (museum.schwerpunkt_lauf /
    museum.schwerpunkt_bezug) is exactly the private thematic knowledge
    base the public repository never ships. Both must stay excluded even
    though the object itself is public domain and safe to publish.
    """
    demo = (ROOT / "examples/92-45.json").read_text(encoding="utf-8")
    for forbidden in (
        "Kolonialismus", "Kamerun", "Übersee", "Geteilte Stadt",
        "Vergnügen", "Stadtentwicklung", "Stadtökologie",
        "Feldmesse", "Soldaten",
        "anspannung", "disziplin", "feierlichkeit", "gemeinschaftlichkeit",
        "your-objectstorage", "fsn1",
    ):
        assert forbidden not in demo, forbidden

    import json
    data = json.loads(demo)
    assert all(
        a.get("obj_id") == "92/45"
        for a in data["museum.emotion_assignments"]
        if "obj_id" in a
    )

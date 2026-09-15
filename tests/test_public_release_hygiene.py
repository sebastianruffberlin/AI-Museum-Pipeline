from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_license_and_security_files_exist():
    for rel in ("LICENSE", "THIRD_PARTY_NOTICES.md", "SECURITY.md"):
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


def test_machine_heart_public_standard_is_complete():
    import json
    base = ROOT / "profiles/_template/emotion"
    concepts = json.loads((base / "concepts.json").read_text(encoding="utf-8"))
    runtime = json.loads((base / "vocabulary.runtime.json").read_text(encoding="utf-8"))
    assert len(concepts) == 146
    assert len(runtime) == 121

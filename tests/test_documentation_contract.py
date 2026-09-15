from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED = [
    "docs/START_HERE.md",
    "docs/WORKFLOW.md",
    "docs/MUSEOLOGICAL_PRINCIPLES.md",
    "docs/MUSEUM_DESIGN_DECISIONS.md",
    "docs/SYSTEM_ARCHITECTURE.md",
    "docs/PROFILES.md",
    "docs/ROADMAP.md",
    "docs/TOPIC_KNOWLEDGE_BASE.md",
    "THIRD_PARTY_NOTICES.md",
    "SECURITY.md",
    "infra/cpu/INSTALL.md",
    "infra/gpu/INSTALL.md",
    "infra/gpu/stadtmuseum-berlin/h100-80gb/INSTALL.md",
    "infra/gpu/stadtmuseum-berlin/h100-80gb/model-manifest.tsv",
    "infra/gpu/stadtmuseum-berlin/h100-80gb/verify-model-files.py",
]


def test_documentation_entrypoints_exist():
    for rel in REQUIRED:
        p = ROOT / rel
        assert p.is_file(), rel
        assert p.stat().st_size > 100, rel


def test_workflow_documents_all_modules():
    text = (ROOT / "docs/WORKFLOW.md").read_text(encoding="utf-8")

    for module in (
        "image_embeddings",
        "image_features",
        "captions",
        "tagging",
        "emotion",
        "topics",
        "text_embeddings",
    ):
        assert module in text


def test_museological_principles_cover_critical_boundaries():
    text = (
        ROOT / "docs/MUSEOLOGICAL_PRINCIPLES.md"
    ).read_text(encoding="utf-8")

    for concept in (
        "Quelle und Anreicherung",
        "Beobachtung ist nicht Interpretation",
        "GND",
        "Emotionserkennung",
        "Institutionelle Themen",
        "Embeddings",
    ):
        assert concept in text


def test_profile_docs_cover_all_configuration_layers():
    text = (ROOT / "docs/PROFILES.md").read_text(encoding="utf-8")

    for term in (
        "Museum Profile",
        "Model Profile",
        "Hardware Profile",
        "Workflow",
        "Deployment-Konfiguration",
        "profiles/_template/",
    ):
        assert term in text


def test_generic_install_docs_do_not_assume_reference_provider():
    text = "\n".join(
        [
            (ROOT / "infra/cpu/INSTALL.md").read_text(encoding="utf-8"),
            (ROOT / "infra/gpu/INSTALL.md").read_text(encoding="utf-8"),
        ]
    ).lower()

    for forbidden in (
        "museumopen",
        "scaleway",
        "netcup",
        "hetzner",
    ):
        assert forbidden not in text


def test_readme_has_human_entrypoint():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "docs/START_HERE.md" in text


def test_cpu_compose_project_is_configurable():
    text = (ROOT / "infra/cpu/compose.yml").read_text(encoding="utf-8")
    assert "CPU_COMPOSE_PROJECT" in text

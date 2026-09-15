from pathlib import Path

from museum_pipeline.configuration import RuntimeConfig
from museum_pipeline.settings import Settings


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "profiles" / "_template"


def _settings(monkeypatch):
    monkeypatch.setenv("MUSEUM_PROFILE", "_template")
    monkeypatch.setenv("MODEL_PROFILE", "reference")
    monkeypatch.setenv("HARDWARE_PROFILE", "h100-80gb")
    monkeypatch.setenv("WORKFLOW", "core")

    monkeypatch.setenv("PG_HOST", "localhost")
    monkeypatch.setenv("PG_DB", "museum_test")
    monkeypatch.setenv("PG_USER", "museum")
    monkeypatch.setenv("PG_PASSWORD", "test")
    monkeypatch.setenv("LCPP_AUTH", "Bearer test")

    return Settings.from_env(ROOT)


def test_template_loads_as_independent_museum_profile(monkeypatch):
    settings = _settings(monkeypatch)
    cfg = RuntimeConfig.load(settings, workflow="core")

    assert cfg.museum.data["id"] == "museum-template"

    source = cfg.museum.metadata["source"]
    assert source["id_column"] == "object_id"
    assert source["asset"]["mode"] == "url"
    assert source["asset"]["column"] == "image_url"

    assert cfg.museum.emotion['method'] == 'machine-heart'
    assert cfg.museum.topics == {}
    assert cfg.museum.authority["enabled"] is False


def test_template_core_prompts_resolve(monkeypatch):
    settings = _settings(monkeypatch)
    cfg = RuntimeConfig.load(settings, workflow="core")

    names = list(cfg.museum.data["captions"]["prompts"].values())
    names += list(cfg.museum.tagging["prompts"].values())
    names += list(cfg.museum.emotion["prompts"].values())

    for name in names:
        assert cfg.museum.prompt(name).strip(), f"empty prompt: {name}"


def test_template_contains_no_reference_institution_or_deployment_names():
    forbidden = (
        "stadtmuseum",
        "museumopen",
        "hetzner",
        "scaleway",
        "netcup",
        "4,5 millionen",
        "40 teilsammlungen",
    )

    for path in TEMPLATE.rglob("*"):
        if not path.is_file():
            continue

        text = path.read_text(encoding="utf-8").lower()

        for token in forbidden:
            assert token not in text, (
                f"{token!r} leaked into starter profile: {path}"
            )


def test_template_ships_machine_heart_default_and_topic_blueprint():
    import json
    concepts = json.loads((TEMPLATE / "emotion" / "concepts.json").read_text(encoding="utf-8"))
    runtime = json.loads((TEMPLATE / "emotion" / "vocabulary.runtime.json").read_text(encoding="utf-8"))
    assert len(concepts) == 146
    assert len(runtime) == 121
    assert all(x["concept_id"] for x in runtime)
    assert (TEMPLATE / "topics" / "framework.template.md").is_file()
    assert (TEMPLATE / "topics" / "taxonomy.template.json").is_file()
    assert not (TEMPLATE / "topics" / "framework.md").exists()

from pathlib import Path

import pytest

from museum_pipeline.settings import Settings


ROOT = Path(__file__).resolve().parents[1]


def test_museum_profile_is_required(monkeypatch):
    monkeypatch.delenv("MUSEUM_PROFILE", raising=False)

    with pytest.raises(
        RuntimeError,
        match="Missing required environment variable: MUSEUM_PROFILE",
    ):
        Settings.from_env(ROOT)


def test_generic_runtime_files_do_not_name_reference_deployment():
    paths = [
        ROOT / "src/museum_pipeline/settings.py",
        ROOT / "src/museum_pipeline/infrastructure/tracing.py",
        ROOT / "services/embedding/compose-block.yml",
        ROOT / "services/embedding/app.py",
        ROOT / "services/presign/presign_app.py",
    ]

    forbidden = (
        "museumopen",
        "stadtmuseum-berlin",
        "scaleway",
        "hetzner",
        "fsn1.your-objectstorage",
    )

    for path in paths:
        text = path.read_text(encoding="utf-8").lower()
        for token in forbidden:
            assert token not in text, f"{token!r} leaked into generic file {path}"


def test_tracing_uses_canonical_collection_term():
    text = (
        ROOT / "src/museum_pipeline/infrastructure/tracing.py"
    ).read_text(encoding="utf-8")

    assert "museum.collection" in text
    assert "museum.sammlung" not in text

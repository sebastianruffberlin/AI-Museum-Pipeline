from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_generic_installation_defaults_to_core():
    env = read(".env.example")
    settings = read("src/museum_pipeline/settings.py")

    assert "WORKFLOW=core" in env
    assert 'workflow=_opt("WORKFLOW", "core")' in settings


def test_museum_profile_remains_explicit():
    settings = read("src/museum_pipeline/settings.py")

    assert 'museum_profile=_req("MUSEUM_PROFILE")' in settings


def test_presign_is_conditional_on_s3():
    settings = read("src/museum_pipeline/settings.py")
    config = read("src/museum_pipeline/configuration.py")
    assets = read("src/museum_pipeline/infrastructure/assets.py")

    assert 'presign_url=_opt("PRESIGN_URL", "")' in settings
    assert "asset mode 's3' requires PRESIGN_URL" in config
    assert "PRESIGN_URL is required for S3 assets" in assets


def test_env_example_contains_optional_s3_configuration():
    env = read(".env.example")

    for variable in (
        "S3_ENDPOINT=",
        "S3_BUCKET=",
        "S3_ACCESS_KEY=",
        "S3_SECRET_KEY=",
    ):
        assert variable in env


def test_s3_services_accept_full_endpoint_urls():
    for rel in (
        "services/embedding/app.py",
        "services/presign/presign_app.py",
    ):
        source = read(rel)

        assert "def _s3_endpoint_url(" in source
        assert "endpoint_url=_s3_endpoint_url(S3_ENDPOINT)" in source
        assert 'endpoint_url=f"https://{S3_ENDPOINT}"' not in source


def test_presign_compose_is_optional():
    compose = read("services/presign/compose-block.yml")

    assert 'profiles: ["s3"]' in compose
    assert "S3_ENDPOINT=${S3_ENDPOINT:-}" in compose
    assert "127.0.0.1:${PRESIGN_PORT:-8082}:8082" in compose

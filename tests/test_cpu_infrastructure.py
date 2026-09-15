from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
COMPOSE = ROOT / "infra/cpu/compose.yml"


def compose():
    return yaml.safe_load(COMPOSE.read_text(encoding="utf-8"))


def test_cpu_compose_has_base_services():
    services = compose()["services"]

    assert "postgres" in services
    assert "embeddings" in services

    assert "profiles" not in services["postgres"]
    assert "profiles" not in services["embeddings"]


def test_optional_services_use_profiles():
    services = compose()["services"]

    assert services["presign"]["profiles"] == ["s3"]
    assert services["gnd_opensearch"]["profiles"] == ["gnd"]


def test_services_are_not_globally_named():
    for service in compose()["services"].values():
        assert "container_name" not in service


def test_exposed_ports_are_loopback_only():
    for service in compose()["services"].values():
        for port in service.get("ports") or []:
            assert str(port).startswith("127.0.0.1:")


def test_cpu_compose_does_not_own_museum_source_data():
    source = COMPOSE.read_text(encoding="utf-8").lower()

    for forbidden in (
        "raw_objects",
        "source.objects",
        "stadtmuseum",
        "museumopen",
        "hetzner",
        "scaleway",
        "netcup",
    ):
        assert forbidden not in source


def test_cpu_compose_does_not_install_database_schema():
    source = COMPOSE.read_text(encoding="utf-8").lower()

    assert "docker-entrypoint-initdb.d" not in source
    assert "database/core.sql" not in source


def test_env_example_points_to_local_cpu_services():
    env = (ROOT / ".env.example").read_text(encoding="utf-8")

    assert "EMBED_BASE=http://127.0.0.1:8081" in env
    assert "OS_MSEARCH=http://127.0.0.1:9200/_msearch" in env

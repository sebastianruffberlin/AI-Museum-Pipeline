from pathlib import Path

import yaml

from museum_pipeline.installer.config import (
    build_runtime_env,
    load_deployment,
    load_env,
    merge_generated_secrets,
)


ROOT = Path(__file__).resolve().parents[1]


def test_deployment_example_loads(tmp_path):
    source = ROOT / "deployment.example.yaml"
    deployment = load_deployment(source, root=ROOT)

    assert deployment.model_profile == "reference"
    assert deployment.hardware_profile == "h100-80gb"
    assert deployment.gpu.mode == "managed"
    assert deployment.features.s3 is True
    assert deployment.features.gnd is True
    assert deployment.workflow == "core"


def test_installer_env_parser_preserves_bearer(tmp_path):
    path = tmp_path / ".env"
    path.write_text(
        'LCPP_AUTH="Bearer example-token"\n'
        'HF_TOKEN="hf_example"\n',
        encoding="utf-8",
    )

    values = load_env(path)

    assert values["LCPP_AUTH"] == "Bearer example-token"
    assert values["HF_TOKEN"] == "hf_example"


def test_generated_secrets_are_stable(tmp_path):
    path = tmp_path / "generated.env"

    one = merge_generated_secrets({}, path)
    two = merge_generated_secrets({}, path)

    assert one["PG_PASSWORD"] == two["PG_PASSWORD"]
    assert one["LITELLM_MASTER_KEY"] == two["LITELLM_MASTER_KEY"]
    assert one["LLAMA_SWAP_API_KEY"] == two["LLAMA_SWAP_API_KEY"]


def test_managed_gpu_builds_runtime_endpoint(tmp_path):
    deployment_path = tmp_path / "deployment.yaml"
    deployment_path.write_text(
        """
museum_profile: _template
model_profile: reference
hardware_profile: h100-80gb
workflow: core
repository:
  url: https://example.invalid/repo.git
features:
  s3: false
  gnd: false
gpu:
  mode: managed
  host: 192.0.2.20
  domain: gpu.example.org
""".strip()
        + "\n",
        encoding="utf-8",
    )

    deployment = load_deployment(
        deployment_path,
        root=ROOT,
    )

    secrets = {
        "PG_PASSWORD": "postgres-secret",
        "LITELLM_MASTER_KEY": "llm-secret",
        "LLAMA_SWAP_API_KEY": "swap-secret",
    }

    env = build_runtime_env(deployment, secrets)

    assert (
        env["LCPP_URL"]
        == "https://gpu.example.org/v1/chat/completions"
    )
    assert env["LCPP_AUTH"] == "Bearer llm-secret"
    assert env["PG_HOST"] == "127.0.0.1"
    assert env["PRESIGN_URL"] == ""
    assert env["OS_MSEARCH"] == ""


def test_reference_profile_uses_public_emotion_and_no_private_topics():
    install = yaml.safe_load(
        (ROOT / "profiles/stadtmuseum-berlin/install.yaml").read_text(encoding="utf-8")
    )
    emotion = yaml.safe_load(
        (ROOT / "profiles/stadtmuseum-berlin/emotion/profile.yaml").read_text(encoding="utf-8")
    )
    profile = yaml.safe_load(
        (ROOT / "profiles/stadtmuseum-berlin/profile.yaml").read_text(encoding="utf-8")
    )

    assert install["database_sql"] == []
    assert emotion["resources"]["source"] == "file"
    assert "topics" not in profile
    assert not (ROOT / "profiles/stadtmuseum-berlin/topics").exists()


def test_template_profile_has_empty_installer_manifest():
    path = ROOT / "profiles/_template/install.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))

    assert data["database_sql"] == []

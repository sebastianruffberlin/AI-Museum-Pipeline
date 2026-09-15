import subprocess
from pathlib import Path

import yaml

import pytest

from museum_pipeline.installer.config import (
    InstallerConfigError,
    build_runtime_env,
    load_deployment,
    load_env,
    merge_generated_secrets,
)
from museum_pipeline.installer.runner import Runner


ROOT = Path(__file__).resolve().parents[1]


def test_ssh_host_key_checking_defaults_to_accept_new(monkeypatch):
    monkeypatch.delenv("SSH_STRICT_HOST_KEY_CHECKING", raising=False)
    monkeypatch.delenv("SSH_KNOWN_HOSTS_FILE", raising=False)
    runner = Runner(root=ROOT)
    assert runner._ssh_host_key_options() == [
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]


def test_ssh_host_key_checking_can_be_pinned(monkeypatch, tmp_path):
    known_hosts = tmp_path / "pinned-known-hosts"
    monkeypatch.setenv("SSH_STRICT_HOST_KEY_CHECKING", "yes")
    monkeypatch.setenv("SSH_KNOWN_HOSTS_FILE", str(known_hosts))
    runner = Runner(root=ROOT)
    assert runner._ssh_host_key_options() == [
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        f"UserKnownHostsFile={known_hosts}",
    ]


def test_deployment_example_loads(tmp_path):
    # deployment.example.yaml intentionally omits repository.url and relies
    # on git-origin auto-detection (see the comment in the file); mirror a
    # real checkout so that detection has something to find.
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "remote", "add", "origin", "https://example.invalid/repo.git"],
        cwd=tmp_path,
        check=True,
    )

    source = ROOT / "deployment.example.yaml"
    deployment = load_deployment(source, root=tmp_path)

    assert deployment.model_profile == "reference"
    assert deployment.hardware_profile == "h100-80gb"
    assert deployment.gpu.mode == "managed"
    assert deployment.features.s3 is False
    assert deployment.features.gnd is False
    assert deployment.repository.url == "https://example.invalid/repo.git"
    assert deployment.workflow == "core"
    assert deployment.gpu.deployment_path == "infra/gpu/generic"


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
  deployment_path: infra/gpu/generic
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


def test_managed_gpu_without_deployment_path_fails_loudly(tmp_path):
    """There is no institution-specific default for gpu.deployment_path.

    A managed-GPU deployment.yaml that omits it must fail with an
    actionable error, not silently fall back to any particular museum's
    reference deployment.
    """
    deployment_yaml = tmp_path / "deployment.yaml"
    deployment_yaml.write_text(
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

    with pytest.raises(InstallerConfigError, match="gpu.deployment_path"):
        load_deployment(deployment_yaml, root=ROOT)


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

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import os
import re
import secrets
import subprocess

import yaml


class InstallerConfigError(ValueError):
    pass


@dataclass(frozen=True)
class RepositoryConfig:
    url: str
    ref: str = "main"


@dataclass(frozen=True)
class FeatureConfig:
    s3: bool = False
    gnd: bool = False


@dataclass(frozen=True)
class CPUConfig:
    mode: str = "local"


@dataclass(frozen=True)
class GPUConfig:
    mode: str
    host: str = ""
    ssh_user: str = "root"
    domain: str = ""
    install_path: str = "/opt/museum-pipeline"
    config_dir: str = "/opt/museum-pipeline-gpu-config"
    models_dir: str = "/mnt/models"
    # No institution-specific default: managed GPU installs must set
    # gpu.deployment_path explicitly in deployment.yaml (see load_deployment).
    deployment_path: str = ""


@dataclass(frozen=True)
class DeploymentConfig:
    museum_profile: str
    model_profile: str
    hardware_profile: str
    workflow: str
    repository: RepositoryConfig
    features: FeatureConfig
    cpu: CPUConfig
    gpu: GPUConfig


_ENV_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _required(data: dict[str, Any], key: str) -> Any:
    value = data.get(key)
    if value is None or value == "":
        raise InstallerConfigError(f"Missing deployment setting: {key}")
    return value


def _git_origin(root: Path) -> str:
    try:
        value = subprocess.check_output(
            ["git", "-C", str(root), "remote", "get-url", "origin"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        return value
    except Exception:
        return ""


def load_deployment(path: str | Path, root: str | Path = ".") -> DeploymentConfig:
    path = Path(path)
    root = Path(root).resolve()

    if not path.is_file():
        raise InstallerConfigError(f"Deployment file not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise InstallerConfigError("deployment.yaml must contain a mapping")

    repo_raw = raw.get("repository") or {}
    feature_raw = raw.get("features") or {}
    cpu_raw = raw.get("cpu") or {}
    gpu_raw = raw.get("gpu") or {}

    repo_url = str(repo_raw.get("url") or _git_origin(root))
    if not repo_url:
        raise InstallerConfigError(
            "repository.url is missing and git origin could not be detected"
        )

    gpu_mode = str(gpu_raw.get("mode") or "external")
    if gpu_mode not in {"managed", "external"}:
        raise InstallerConfigError("gpu.mode must be managed or external")

    gpu = GPUConfig(
        mode=gpu_mode,
        host=str(gpu_raw.get("host") or ""),
        ssh_user=str(gpu_raw.get("ssh_user") or "root"),
        domain=str(gpu_raw.get("domain") or ""),
        install_path=str(
            gpu_raw.get("install_path") or "/opt/museum-pipeline"
        ),
        config_dir=str(
            gpu_raw.get("config_dir") or "/opt/museum-pipeline-gpu-config"
        ),
        models_dir=str(gpu_raw.get("models_dir") or "/mnt/models"),
        deployment_path=str(gpu_raw.get("deployment_path") or ""),
    )

    if gpu.mode == "managed":
        if not gpu.host:
            raise InstallerConfigError("managed GPU requires gpu.host")
        if not gpu.domain:
            raise InstallerConfigError("managed GPU requires gpu.domain")
        if not gpu.deployment_path:
            raise InstallerConfigError(
                "managed GPU requires gpu.deployment_path "
                "(e.g. infra/gpu/generic or a calibrated infra/gpu/<profile>/<gpu> "
                "reference directory; there is no institution-specific default)"
            )

    return DeploymentConfig(
        museum_profile=str(_required(raw, "museum_profile")),
        model_profile=str(raw.get("model_profile") or "reference"),
        hardware_profile=str(
            raw.get("hardware_profile") or "h100-80gb"
        ),
        workflow=str(raw.get("workflow") or "core"),
        repository=RepositoryConfig(
            url=repo_url,
            ref=str(repo_raw.get("ref") or "main"),
        ),
        features=FeatureConfig(
            s3=bool(feature_raw.get("s3", False)),
            gnd=bool(feature_raw.get("gnd", False)),
        ),
        cpu=CPUConfig(
            mode=str(cpu_raw.get("mode") or "local"),
        ),
        gpu=gpu,
    )


def load_env(path: str | Path) -> dict[str, str]:
    path = Path(path)

    if not path.exists():
        return {}

    result: dict[str, str] = {}

    for lineno, raw in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[7:].lstrip()

        if "=" not in line:
            raise InstallerConfigError(
                f"{path}:{lineno}: expected KEY=VALUE"
            )

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not _ENV_KEY.fullmatch(key):
            raise InstallerConfigError(
                f"{path}:{lineno}: invalid environment key {key!r}"
            )

        if (
            len(value) >= 2
            and value[0] == value[-1]
            and value[0] in {"'", '"'}
        ):
            value = value[1:-1]

        result[key] = value

    return result


def merge_generated_secrets(
    secret_env: dict[str, str],
    generated_path: str | Path,
) -> dict[str, str]:
    generated_path = Path(generated_path)
    generated = load_env(generated_path)

    def ensure(key: str, factory) -> None:
        if secret_env.get(key):
            generated[key] = secret_env[key]
        elif not generated.get(key):
            generated[key] = factory()

    ensure("PG_PASSWORD", lambda: secrets.token_urlsafe(32))
    ensure(
        "LITELLM_MASTER_KEY",
        lambda: "sk-" + secrets.token_urlsafe(32),
    )
    ensure(
        "LLAMA_SWAP_API_KEY",
        lambda: "sk-" + secrets.token_urlsafe(32),
    )

    generated_path.parent.mkdir(parents=True, exist_ok=True)
    write_env(generated_path, generated, mode=0o600)

    merged = dict(secret_env)
    merged.update(generated)
    return merged


def _quote_env(value: str) -> str:
    value = str(value)
    value = value.replace("\\", "\\\\")
    value = value.replace('"', '\\"')
    value = value.replace("\n", "\\n")
    return f'"{value}"'


def write_env(
    path: str | Path,
    values: dict[str, str],
    mode: int = 0o600,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    text = "\n".join(
        f"{key}={_quote_env(value)}"
        for key, value in sorted(values.items())
        if value is not None
    )
    path.write_text(text + "\n", encoding="utf-8")
    os.chmod(path, mode)


def build_runtime_env(
    deployment: DeploymentConfig,
    secrets_env: dict[str, str],
) -> dict[str, str]:
    env: dict[str, str] = {
        "MUSEUM_PROFILE": deployment.museum_profile,
        "MODEL_PROFILE": deployment.model_profile,
        "HARDWARE_PROFILE": deployment.hardware_profile,
        "WORKFLOW": deployment.workflow,
        "PG_HOST": "127.0.0.1",
        "PG_PORT": secrets_env.get("PG_PORT", "5432"),
        "PG_DB": secrets_env.get("PG_DB", "museum"),
        "PG_USER": secrets_env.get("PG_USER", "museum"),
        "PG_PASSWORD": secrets_env["PG_PASSWORD"],
        "LLM_BACKEND": "gpu",
        "EMBED_BASE": "http://127.0.0.1:8081",
        "HF_TOKEN": secrets_env.get("HF_TOKEN", ""),
        "OS_INDEX": secrets_env.get(
            "OS_INDEX",
            "gnd_sachbegriffe",
        ),
    }

    if deployment.features.s3:
        for key in (
            "S3_ENDPOINT",
            "S3_BUCKET",
            "S3_ACCESS_KEY",
            "S3_SECRET_KEY",
        ):
            env[key] = secrets_env.get(key, "")
        env["PRESIGN_URL"] = "http://127.0.0.1:8082"
    else:
        env["PRESIGN_URL"] = ""
        env["S3_ENDPOINT"] = ""
        env["S3_BUCKET"] = ""
        env["S3_ACCESS_KEY"] = ""
        env["S3_SECRET_KEY"] = ""

    if deployment.features.gnd:
        env["OS_MSEARCH"] = "http://127.0.0.1:9200/_msearch"
    else:
        env["OS_MSEARCH"] = ""

    if deployment.gpu.mode == "managed":
        env["LCPP_URL"] = (
            f"https://{deployment.gpu.domain}/v1/chat/completions"
        )
        env["LCPP_AUTH"] = (
            "Bearer " + secrets_env["LITELLM_MASTER_KEY"]
        )
    else:
        url = secrets_env.get("LCPP_URL", "")
        auth = secrets_env.get("LCPP_AUTH", "")
        if not url:
            raise InstallerConfigError(
                "external GPU mode requires LCPP_URL in .env"
            )
        if not auth:
            raise InstallerConfigError(
                "external GPU mode requires LCPP_AUTH in .env"
            )
        env["LCPP_URL"] = url
        env["LCPP_AUTH"] = auth

    return env

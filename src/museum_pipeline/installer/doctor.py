from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import urllib.request

from .config import DeploymentConfig


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""


def _http(
    url: str,
    *,
    auth: str = "",
) -> tuple[bool, str]:
    try:
        headers = {}
        if auth:
            headers["Authorization"] = auth

        request = urllib.request.Request(
            url,
            headers=headers,
        )

        with urllib.request.urlopen(
            request,
            timeout=15,
        ) as response:
            return (
                200 <= response.status < 300,
                f"HTTP {response.status}",
            )
    except Exception as exc:
        return False, str(exc)


def run_doctor(
    root: Path,
    deployment: DeploymentConfig,
    runtime_env: dict[str, str],
) -> list[Check]:
    checks: list[Check] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        checks.append(Check(name, ok, detail))

    add(
        "museum profile",
        (root / "profiles" / deployment.museum_profile).is_dir(),
        deployment.museum_profile,
    )

    add(
        "model profile",
        (root / "models" / f"{deployment.model_profile}.yaml").is_file(),
        deployment.model_profile,
    )

    add(
        "hardware profile",
        (
            root
            / "hardware"
            / f"{deployment.hardware_profile}.yaml"
        ).is_file(),
        deployment.hardware_profile,
    )

    add(
        "workflow",
        (
            root
            / "workflows"
            / f"{deployment.workflow}.yaml"
        ).is_file(),
        deployment.workflow,
    )

    try:
        proc = subprocess.run(
            [
                "docker",
                "compose",
                "--env-file",
                str(root / ".museum-pipeline/runtime.env"),
                "-f",
                str(root / "infra/cpu/compose.yml"),
                "ps",
            ],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        add(
            "CPU compose",
            proc.returncode == 0,
            "docker compose ps",
        )
    except Exception as exc:
        add("CPU compose", False, str(exc))

    ok, detail = _http(
        runtime_env.get(
            "EMBED_BASE",
            "http://127.0.0.1:8081",
        )
        + "/health"
    )
    add("embedding service", ok, detail)

    if deployment.features.s3:
        ok, detail = _http(
            runtime_env.get(
                "PRESIGN_URL",
                "http://127.0.0.1:8082",
            )
            + "/health"
        )
        add("presign service", ok, detail)

    if deployment.features.gnd:
        ok, detail = _http(
            "http://127.0.0.1:9200/_cluster/health"
        )
        add("OpenSearch", ok, detail)

    lcpp = runtime_env.get("LCPP_URL", "")
    auth = runtime_env.get("LCPP_AUTH", "")

    if lcpp:
        models_url = lcpp.rsplit("/", 2)[0] + "/models"
        ok, detail = _http(
            models_url,
            auth=auth,
        )
        add("GPU endpoint", ok, detail)

    try:
        env = os.environ.copy()
        env.update(runtime_env)

        proc = subprocess.run(
            [
                str(root / ".venv/bin/museum-pipeline"),
                "validate-config",
            ],
            cwd=root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        add(
            "pipeline configuration",
            proc.returncode == 0,
            proc.stdout.strip()[-300:],
        )
    except Exception as exc:
        add("pipeline configuration", False, str(exc))

    return checks


def print_doctor(checks: list[Check]) -> bool:
    print()
    print("AI Museum Pipeline doctor")
    print("=" * 72)

    for check in checks:
        marker = "✓" if check.ok else "✗"
        detail = f" — {check.detail}" if check.detail else ""
        print(f"{marker} {check.name}{detail}")

    ok = all(c.ok for c in checks)

    print("=" * 72)
    print(
        "DOCTOR: PASS"
        if ok
        else "DOCTOR: FAIL"
    )

    return ok

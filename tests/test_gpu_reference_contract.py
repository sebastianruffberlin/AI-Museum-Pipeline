from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_h100_reference_contract():
    script = ROOT / "infra/gpu/verify_h100_contract.py"

    proc = subprocess.run(
        [sys.executable, str(script)],
        cwd=ROOT,
        text=True,
        capture_output=True,
    )

    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr
    assert "CONTRACT: PASS" in proc.stdout


def test_generic_gpu_deployment_has_no_reference_museum_or_provider():
    root = ROOT / "infra/gpu/generic"

    text = "\n".join(
        p.read_text(encoding="utf-8")
        for p in root.rglob("*")
        if p.is_file()
    ).lower()

    for forbidden in (
        "museumopen",
        "stadtmuseum",
        "scaleway",
        "netcup",
        "hetzner",
        "qwen3.6",
        "gemma-4",
    ):
        assert forbidden not in text


def test_generic_gpu_compose_does_not_pin_h100_concurrency():
    text = (
        ROOT / "infra/gpu/generic/compose.yml"
    ).read_text(encoding="utf-8")

    assert "-np" not in text
    assert "65536" not in text
    assert "32768" not in text

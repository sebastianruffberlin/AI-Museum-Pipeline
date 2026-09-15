#!/usr/bin/env python3
from __future__ import annotations

import shlex
import sys
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]

HARDWARE = ROOT / "hardware/h100-80gb.yaml"
LLAMA = (
    ROOT
    / "infra/gpu/stadtmuseum-berlin/h100-80gb/llama-swap.yaml"
)

EXPECTED = {
    "qwen3.6-35b-a3b-mtp-q4": (65536, 8, 8192),
    "gemma-4-26b-a4b-qat":    (32768, 4, 8192),
    "gemma-4-12b-qat":         (32768, 4, 8192),
    "qwen3.6-27b-mtp":         (32768, 2, 16384),
    "gemma-4-31b-it":          (32768, 1, 32768),
    "qwen3.6-35b-mtp":         (65536, 8, 8192),
    "qwen3.6-27b-mtp-64k":     (65536, 1, 65536),
    "gemma-4-31b-it-64k":      (65536, 2, 32768),
}


def option(tokens: list[str], name: str, default=None):
    if name not in tokens:
        return default
    i = tokens.index(name)
    if i + 1 >= len(tokens):
        raise ValueError(f"{name} has no value")
    return tokens[i + 1]


def load_runtime():
    hw = yaml.safe_load(HARDWARE.read_text(encoding="utf-8"))
    llama = yaml.safe_load(LLAMA.read_text(encoding="utf-8"))
    return hw, llama


def verify() -> list[str]:
    hw, llama = load_runtime()

    errors: list[str] = []
    models = llama.get("models") or {}
    hw_models = hw.get("models") or {}

    if set(models) != set(EXPECTED):
        errors.append(
            "llama-swap aliases differ from pinned reference: "
            f"actual={sorted(models)}, expected={sorted(EXPECTED)}"
        )

    for model, (expected_c, expected_np, expected_min) in EXPECTED.items():
        if model not in models:
            continue

        tokens = shlex.split(str(models[model]["cmd"]))

        actual_c = int(option(tokens, "-c"))
        # llama.cpp default when -np is omitted in our verified reference.
        actual_np = int(option(tokens, "-np", 1))

        h = hw_models.get(model)
        if not h:
            errors.append(f"{model}: missing hardware profile entry")
            continue

        hw_c = int(h["context_pool"])
        hw_np = int(h["parallel_slots"])
        hw_min = int(h["min_context_per_slot"])

        if (actual_c, actual_np) != (expected_c, expected_np):
            errors.append(
                f"{model}: llama.cpp drift: "
                f"-c/-np={actual_c}/{actual_np}, "
                f"pinned={expected_c}/{expected_np}"
            )

        if (hw_c, hw_np, hw_min) != (
            expected_c,
            expected_np,
            expected_min,
        ):
            errors.append(
                f"{model}: hardware profile drift: "
                f"{hw_c}/{hw_np}/{hw_min}, "
                f"pinned={expected_c}/{expected_np}/{expected_min}"
            )

        if hw_c != actual_c:
            errors.append(
                f"{model}: hardware context_pool {hw_c} != llama -c {actual_c}"
            )

        if hw_np != actual_np:
            errors.append(
                f"{model}: hardware parallel_slots {hw_np} != llama -np {actual_np}"
            )

        if actual_c < actual_np * hw_min:
            errors.append(
                f"{model}: context pool insufficient: "
                f"{actual_c} < {actual_np} * {hw_min}"
            )

    phase = (hw.get("phase_overrides") or {}).get("tagging.authority") or {}

    if int(phase.get("outer_workers", 0)) != 1:
        errors.append(
            "tagging.authority outer_workers drifted; pinned value is 1"
        )

    if phase.get("inner_workers_from_model") != "authority.gnd":
        errors.append(
            "tagging.authority inner_workers_from_model drifted; "
            "pinned value is authority.gnd"
        )

    return errors


def main() -> int:
    hw, llama = load_runtime()
    models = llama.get("models") or {}
    hw_models = hw.get("models") or {}

    print("H100 CONCURRENCY CONTRACT")
    print("=" * 92)
    print(
        f"{'model':32} {'llama -c':>10} {'llama -np':>10} "
        f"{'hw pool':>10} {'hw slots':>10} {'min/slot':>10}"
    )
    print("-" * 92)

    for model in EXPECTED:
        cmd = shlex.split(str(models[model]["cmd"]))
        c = int(option(cmd, "-c"))
        np = int(option(cmd, "-np", 1))
        h = hw_models[model]

        print(
            f"{model:32} "
            f"{c:10d} {np:10d} "
            f"{int(h['context_pool']):10d} "
            f"{int(h['parallel_slots']):10d} "
            f"{int(h['min_context_per_slot']):10d}"
        )

    print("-" * 92)

    phase = hw["phase_overrides"]["tagging.authority"]
    print(
        "GND: outer_workers="
        f"{phase['outer_workers']} | inner_workers_from_model="
        f"{phase['inner_workers_from_model']}"
    )

    errors = verify()

    if errors:
        print()
        print("CONTRACT: FAIL")
        for error in errors:
            print("  -", error)
        return 1

    print()
    print("CONTRACT: PASS")
    print("All eight H100 -c/-np pairs are pinned and aligned.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

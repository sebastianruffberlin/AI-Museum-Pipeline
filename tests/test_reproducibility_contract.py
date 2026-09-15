import csv
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / "infra/gpu/stadtmuseum-berlin/h100-80gb"


def test_cpu_defaults_match_verified_reference():
    text = (ROOT / "infra/cpu/compose.yml").read_text(encoding="utf-8")

    assert "${POSTGRES_IMAGE:-postgres:16}" in text
    assert (
        "${OPENSEARCH_IMAGE:-opensearchproject/opensearch:3.8.0}"
        in text
    )

    assert "postgres:16-alpine" not in text
    assert "opensearchproject/opensearch:2.19.1" not in text


def test_embedding_hf_cache_is_persistent():
    compose = (ROOT / "infra/cpu/compose.yml").read_text(
        encoding="utf-8"
    )

    assert "HF_HOME: ${HF_HOME:-/models/huggingface}" in compose
    assert "- embedding-models:/models" in compose

    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "HF_HOME=/models/huggingface" in env


def test_gnd_is_explicitly_rolling():
    data = json.loads(
        (
            ROOT / "infra/cpu/reference/gnd-source.json"
        ).read_text(encoding="utf-8")
    )

    assert data["policy"] == "rolling"
    assert data["filename"] == (
        "authorities-gnd-sachbegriff_lds.jsonld.gz"
    )
    assert data["source_url"] == (
        "https://data.dnb.de/opendata/"
        "authorities-gnd-sachbegriff_lds.jsonld.gz"
    )


def test_six_physical_model_sources_are_complete():
    data = json.loads(
        (REF / "model-sources.json").read_text(encoding="utf-8")
    )

    models = data["models"]
    assert len(models) == 6
    assert data["download_policy"]["default"] == "rolling"

    expected = {
        "qwen3.6-35b-a3b-mtp-q4": "UD-Q4_K_XL",
        "gemma-4-26b-a4b-qat": "UD-Q4_K_XL",
        "gemma-4-12b-qat": "UD-Q4_K_XL",
        "qwen3.6-27b-mtp": "UD-Q6_K_XL",
        "gemma-4-31b-it": "UD-Q4_K_XL",
        "qwen3.6-35b-mtp": "UD-Q6_K_XL",
    }

    assert {
        m["local_alias"]: m["quantization"] for m in models
    } == expected

    for m in models:
        assert m["quant_provider"] == "unsloth"
        assert m["hf_repository"].startswith("unsloth/")
        assert m["model_file"].endswith(".gguf")
        assert m["mmproj_file"] == "mmproj-BF16.gguf"
        assert re.fullmatch(
            r"[0-9a-f]{64}", m["reference_model_sha256"]
        )
        assert re.fullmatch(
            r"[0-9a-f]{64}", m["reference_mmproj_sha256"]
        )


def test_reference_manifest_has_twelve_files():
    with (REF / "model-manifest.tsv").open(
        encoding="utf-8", newline=""
    ) as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    assert len(rows) == 12

    for row in rows:
        assert row["path"].endswith(".gguf")
        assert int(row["bytes"]) > 100_000_000
        assert re.fullmatch(r"[0-9a-f]{64}", row["sha256"])


def test_model_download_helper_is_rolling_not_reference_blocked():
    text = (REF / "download-models.py").read_text(encoding="utf-8")

    assert "resolve/main" in text
    assert "--check-reference" in text
    assert "DIFF (allowed in rolling mode)" in text


def test_gpu_compose_accepts_image_pins():
    text = (
        ROOT / "infra/gpu/generic/compose.yml"
    ).read_text(encoding="utf-8")

    assert "CADDY_IMAGE" in text
    assert "LITELLM_IMAGE" in text
    assert "LLAMA_SWAP_IMAGE" in text


def test_reference_gpu_env_uses_digests():
    text = (
        REF / ".env.example"
    ).read_text(encoding="utf-8")

    assert "CADDY_IMAGE=caddy@sha256:" in text
    assert "LITELLM_IMAGE=ghcr.io/berriai/litellm@sha256:" in text
    assert (
        "LLAMA_SWAP_IMAGE=ghcr.io/mostlygeek/llama-swap@sha256:"
        in text
    )


def test_manual_stack_excludes_cpu_llm_inference():
    docs = "\n".join(
        [
            (ROOT / "infra/cpu/INSTALL.md").read_text(encoding="utf-8"),
            (ROOT / "docs/SYSTEM_ARCHITECTURE.md").read_text(
                encoding="utf-8"
            ),
            (ROOT / "docs/REPRODUCIBILITY.md").read_text(
                encoding="utf-8"
            ),
        ]
    ).lower()

    assert "llama-swap-cpu" not in docs
    assert "cpu-llm-fallback" not in docs


def test_fresh_host_checklist_exists():
    text = (
        ROOT / "docs/FRESH_HOST_CHECKLIST.md"
    ).read_text(encoding="utf-8")

    for phrase in (
        "CPU / Orchestrator",
        "GPU",
        "Ende-zu-Ende",
        "Fachliche Prüfung",
        "Provenienz",
        "Installer",
    ):
        assert phrase in text


def test_opensearch_38_container_startup_contract():
    compose = (ROOT / "infra/cpu/compose.yml").read_text(
        encoding="utf-8"
    )

    assert (
        "DISABLE_INSTALL_DEMO_CONFIG: "
        "${DISABLE_INSTALL_DEMO_CONFIG:-true}"
        in compose
    )
    assert (
        "DISABLE_SECURITY_PLUGIN: "
        "${DISABLE_SECURITY_PLUGIN:-true}"
        in compose
    )
    assert (
        "OPENSEARCH_JAVA_OPTS: "
        "${OPENSEARCH_JAVA_OPTS:--Xms2g -Xmx2g}"
        in compose
    )

    # This setting alone is too late for the Docker entrypoint and must
    # not be the canonical startup mechanism.
    assert 'plugins.security.disabled: "true"' not in compose

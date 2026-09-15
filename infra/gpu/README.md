# GPU inference deployments

Museum Pipeline separates the generic GPU transport from calibrated
institution/hardware reference deployments.

## Architecture

The reference architecture is:

    CPU/orchestrator
        -> HTTPS
        -> Caddy
        -> LiteLLM
        -> llama-swap
        -> llama.cpp
        -> GPU

The pipeline itself only requires an OpenAI-compatible inference endpoint.
A museum may therefore either use this deployment stack or provide another
compatible endpoint.

## Generic deployment

    infra/gpu/generic/

Contains only the provider-neutral deployment mechanism:

- Caddy
- LiteLLM
- llama-swap
- NVIDIA GPU access
- configurable model/config mounts
- deployment-specific DNS/IP/secrets via environment

It contains no museum-specific model selection and no hardware-specific
llama.cpp concurrency tuning.

## Calibrated reference deployment

    infra/gpu/stadtmuseum-berlin/h100-80gb/

Contains the tested Stadtmuseum Berlin reference configuration for an
NVIDIA H100 PCIe 80 GB.

Its llama.cpp context pools and parallel slot counts are intentionally
pinned. They correspond to:

    hardware/h100-80gb.yaml

The contract is checked by:

    infra/gpu/verify_h100_contract.py

For all eight API aliases the verifier requires:

    hardware context_pool  == llama.cpp -c
    hardware parallel_slots == llama.cpp -np

If `-np` is omitted for the verified `gemma-4-31b-it` command, its effective
reference value is 1.

The verifier additionally pins the known-good values themselves, so changing
both files together does not silently redefine the H100 reference.

## GND concurrency

The GND authority phase is a deliberate two-level special case:

    outer object workers = 1
    inner workers        = capacity of authority.gnd
    H100 qwen3.6-35b-mtp = 8 llama.cpp slots

This prevents object-level concurrency from multiplying the internal
term-level GND requests.

## Important

A hardware profile is not a generic performance suggestion.

Values calibrated for the H100 reference deployment must not be copied to
another GPU merely because the model fits into VRAM. Create and validate a
separate hardware/deployment profile instead.


<!-- GPU-INSTALL-LINK -->
## Manual installation

Generic fresh GPU host:

[`INSTALL.md`](INSTALL.md)

Calibrated Stadtmuseum H100 reference:

[`stadtmuseum-berlin/h100-80gb/INSTALL.md`](stadtmuseum-berlin/h100-80gb/INSTALL.md)

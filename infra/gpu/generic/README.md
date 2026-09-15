# Generic GPU deployment

This directory contains the provider-neutral GPU inference transport:

    client
      -> HTTPS / Caddy
      -> LiteLLM
      -> llama-swap
      -> llama.cpp / GPU

It deliberately contains no museum-specific models and no hardware tuning.

The concrete model aliases, llama.cpp flags, context pools and parallel slot
counts belong to a calibrated deployment profile.

Required deployment inputs:

- GPU_DOMAIN
- ALLOWED_REMOTE_IP
- GPU_CONFIG_DIR
- MODELS_DIR
- authentication secrets

Calibrated institution- and hardware-specific deployments are kept
separately from this generic transport layer, for example under:

    infra/gpu/<institution>/<hardware>/

Do not copy concurrency values from one GPU type to another without
hardware-specific calibration.

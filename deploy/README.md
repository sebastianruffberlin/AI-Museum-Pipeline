# Deployment

V2 does not bundle the GPU model server. It expects the same OpenAI-compatible endpoint architecture as the reference V1 stack (e.g. LiteLLM/llama-swap/llama.cpp).

`hardware/h100-80gb.yaml` is the source of truth for **pipeline-side** parallelism and documents the matching context-pool assumptions. Keep the actual llama.cpp server slots aligned with that profile.

For a different GPU, create another hardware profile and calibrate it; do not change museum prompts or model quality settings just to increase parallelism.

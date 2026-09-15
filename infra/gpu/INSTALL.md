# Manuelle Installation: GPU-Inferenzhost

Dieses Dokument ist providerneutral.

Der GPU-Host stellt der Pipeline eine OpenAI-kompatible API bereit.

Referenztransport:

    Caddy
      -> LiteLLM
      -> llama-swap
      -> llama.cpp
      -> NVIDIA GPU


## Voraussetzungen

- Linux
- Docker Engine
- Docker Compose Plugin
- NVIDIA-Treiber
- NVIDIA Container Toolkit

Prüfen:

    nvidia-smi

    docker run --rm --gpus all \
      nvidia/cuda:12.8.0-base-ubuntu24.04 \
      nvidia-smi


## Repository

    git clone <repository-url> /opt/museum-pipeline
    cd /opt/museum-pipeline


## Deployment wählen

Generischer Transport:

    infra/gpu/generic/

Ein konkretes Deployment ergänzt:

    llama-swap.yaml
    litellm.yaml
    Hardwareprofil
    Modellquellen


## Modelle

Modellbeschaffung ist bewusst explizit.

Der generische Stack lädt nicht automatisch ein beliebiges Modell und
tuned keine unbekannte GPU automatisch.

Das konkrete Deployment legt fest:

- Anbieter,
- Repository,
- Quantisierung,
- Dateinamen,
- lokale Verzeichnisstruktur.


## Environment

Ausgangspunkt:

    infra/gpu/generic/.env.example

Mindestens:

    GPU_DOMAIN
    ALLOWED_REMOTE_IP
    GPU_CONFIG_DIR
    MODELS_DIR
    LITELLM_MASTER_KEY
    LLAMA_SWAP_API_KEY

Image-Variablen:

    CADDY_IMAGE
    LITELLM_IMAGE
    LLAMA_SWAP_IMAGE


## Compose prüfen

    docker compose \
      --env-file /path/to/gpu.env \
      -f infra/gpu/generic/compose.yml \
      config


## Start

    docker compose \
      --env-file /path/to/gpu.env \
      -f infra/gpu/generic/compose.yml \
      up -d


## API prüfen

    curl \
      -H "Authorization: Bearer <MASTER_KEY>" \
      https://<GPU_DOMAIN>/v1/models


## Testcall

    curl \
      -H "Authorization: Bearer <MASTER_KEY>" \
      -H "Content-Type: application/json" \
      https://<GPU_DOMAIN>/v1/chat/completions \
      -d '{
        "model": "<MODEL_ALIAS>",
        "messages": [
          {"role": "user", "content": "Antworte nur mit OK."}
        ],
        "max_tokens": 8
      }'


## Hardware

`-c`, `-np` und Workerwerte sind Hardware-/Runtime-Kalibrierung.

Werte eines H100-Profils dürfen nicht ungeprüft auf andere GPUs
übertragen werden.

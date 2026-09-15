# Manuelle Installation: Stadtmuseum H100-Referenzdeployment

Dieses Manual rekonstruiert den getesteten H100-Referenzstack.

Hardware:

    NVIDIA H100 PCIe 80 GB


## 1. Voraussetzungen

    nvidia-smi
    docker --version
    docker compose version

NVIDIA-Containerzugriff muss funktionieren.


## 2. Repository

    git clone <repository-url> /opt/museum-pipeline
    cd /opt/museum-pipeline


## 3. Modellquellen ansehen

    cat \
      infra/gpu/stadtmuseum-berlin/h100-80gb/model-sources.json

Es werden sechs physische Modellsets verwendet.

Die acht API-Aliase teilen sich teilweise dieselben Dateien.


## 4. Modell-Download

Standard ist Rolling Mode:

    python3 \
      infra/gpu/stadtmuseum-berlin/h100-80gb/download-models.py \
      --models-dir /mnt/models

Vorher nur anzeigen:

    python3 \
      infra/gpu/stadtmuseum-berlin/h100-80gb/download-models.py \
      --models-dir /mnt/models \
      --dry-run

Rolling bedeutet:

- Unsloth bleibt Anbieter,
- Repository bleibt fest,
- Quantisierung bleibt fest,
- Dateiname bleibt fest,
- `main` darf upstream aktualisiert werden.

Nach dem Download entsteht:

    /mnt/models/.museum-pipeline-model-provenance.json

Darin stehen die tatsächlich geladenen Größen und SHA256.


## 5. Referenzsnapshot vergleichen

Schneller Größencheck:

    python3 \
      infra/gpu/stadtmuseum-berlin/h100-80gb/verify-model-files.py \
      /mnt/models

Bytegenauer historischer Vergleich:

    python3 \
      infra/gpu/stadtmuseum-berlin/h100-80gb/verify-model-files.py \
      /mnt/models \
      --sha256

Ein Unterschied zum Referenzhash ist bei einem aktuellen Rolling-Download
nicht automatisch ein Fehler.


## 6. Environment

    cp \
      infra/gpu/stadtmuseum-berlin/h100-80gb/.env.example \
      /opt/museum-pipeline-h100.env

Setzen:

    GPU_DOMAIN
    ALLOWED_REMOTE_IP
    MODELS_DIR
    LITELLM_MASTER_KEY
    LLAMA_SWAP_API_KEY

Die Referenz-Environment enthält die am 13.09.2026 verifizierten
Container-Digests.


## 7. H100-Contract

Vor jedem Start:

    python3 infra/gpu/verify_h100_contract.py

Erwartet:

    CONTRACT: PASS

Bei einem Fehler werden `-c`, `-np` oder Worker nicht spontan geändert.


## 8. Compose validieren

    docker compose \
      --env-file /opt/museum-pipeline-h100.env \
      -f infra/gpu/generic/compose.yml \
      config


## 9. Start

    docker compose \
      --env-file /opt/museum-pipeline-h100.env \
      -f infra/gpu/generic/compose.yml \
      up -d


## 10. Modellliste

    curl \
      -H "Authorization: Bearer <MASTER_KEY>" \
      https://<GPU_DOMAIN>/v1/models

Erwartet werden acht API-Aliase.


## 11. Testcall

    curl \
      -H "Authorization: Bearer <MASTER_KEY>" \
      -H "Content-Type: application/json" \
      https://<GPU_DOMAIN>/v1/chat/completions \
      -d '{
        "model": "gemma-4-12b-qat",
        "messages": [
          {"role": "user", "content": "Antworte nur mit OK."}
        ],
        "max_tokens": 8
      }'


## 12. Abschluss

    python3 infra/gpu/verify_h100_contract.py

Erwartet erneut:

    CONTRACT: PASS


## Referenzdaten

    REFERENCE.md
    runtime-reference.json
    model-sources.json
    model-manifest.tsv

Die H100-Concurrency-Werte werden durch diese Installationsanleitung
nicht verändert.

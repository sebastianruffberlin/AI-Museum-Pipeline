# Manuelles Deployment der AI Museum Pipeline

Dieses Dokument ist der Einstieg für ein vollständiges manuelles Deployment.

Ziel ist, dass ein Museum das System allein anhand dieses Repositories auf
neuen Hosts nachbauen kann.

## Architektur

```text
CPU / Orchestrator
  Python Pipeline
  PostgreSQL
  SigLIP2
  DINOv3
  BGE-M3
  Presign optional
  OpenSearch + GND optional
          |
          | HTTPS
          v
GPU / Inference
  Caddy
  LiteLLM
  llama-swap
  llama.cpp
  Qwen / Gemma
```

Generative LLM/VLM-Inferenz läuft im Referenzdeployment ausschließlich auf
dem GPU-Host.

---

## 1. Welchen Installationsweg verwenden?

### Getestete Referenz: NVIDIA H100 PCIe 80 GB

GPU:

`infra/gpu/stadtmuseum-berlin/h100-80gb/INSTALL.md`

CPU:

`infra/cpu/INSTALL.md`

Danach wird die CPU über `LCPP_URL` und `LCPP_AUTH` mit dem GPU-Endpunkt
verbunden.

### Bereits vorhandener OpenAI-kompatibler Endpoint

Ein Museum muss den mitgelieferten GPU-Stack nicht verwenden.

Erforderlich ist ein kompatibler Endpoint für:

```text
POST /v1/chat/completions
```

Die Modellaliase des aktiven Model Profiles müssen dort bereitgestellt
werden.

Auf der CPU:

```text
LCPP_URL=https://<ENDPOINT>/v1/chat/completions
LCPP_AUTH=Bearer <TOKEN>
```

### Andere GPU-Hardware

`infra/gpu/generic/` enthält den generischen Transportstack.

Die Werte aus

```text
hardware/h100-80gb.yaml
```

und

```text
infra/gpu/stadtmuseum-berlin/h100-80gb/
```

sind ausschließlich für die H100-Referenz kalibriert.

Für andere GPUs müssen Context Pool, parallele Slots und llama.cpp-Parameter
neu bestimmt werden.

---

# Teil A — GPU

## 2. Voraussetzungen

Für das vollständige Referenzdeployment:

- Linux, Referenz Ubuntu 24.04
- NVIDIA H100 PCIe 80 GB
- NVIDIA-Treiber
- NVIDIA Container Toolkit
- Docker
- Docker Compose
- Git
- Python 3
- curl
- DNS-Name
- bekannte Egress-IP des CPU-Orchestrators
- ausreichend Modellstorage

Prüfen:

```bash
nvidia-smi
docker --version
docker compose version
```

NVIDIA Container Runtime:

```bash
docker run --rm \
  --gpus all \
  nvidia/cuda:12.8.0-base-ubuntu24.04 \
  nvidia-smi
```

## 3. Repository

```bash
git clone <repository-url> /opt/museum-pipeline
cd /opt/museum-pipeline
git rev-parse HEAD
```

## 4. Modellstorage

Beispiel:

```bash
mkdir -p /mnt/models
```

Alternativ kann ein separater großer Scratch-/Block-Storage verwendet werden.

Der gewählte Pfad wird später als `MODELS_DIR` eingetragen.

## 5. Modelle

Quellen:

```text
infra/gpu/stadtmuseum-berlin/h100-80gb/model-sources.json
```

Es gibt sechs physische Modellsets und acht API-Aliase.

Dry Run:

```bash
python3 \
  infra/gpu/stadtmuseum-berlin/h100-80gb/download-models.py \
  --models-dir /mnt/models \
  --dry-run
```

Download:

```bash
python3 \
  infra/gpu/stadtmuseum-berlin/h100-80gb/download-models.py \
  --models-dir /mnt/models
```

Danach existiert:

```text
/mnt/models/.museum-pipeline-model-provenance.json
```

Darin stehen Größe und SHA256 der tatsächlich geladenen Dateien.

Die Modellbeschaffung ist bewusst rolling: Repository, Quantisierung und
Dateiname bleiben fest, die Bytes auf Hugging Face `main` dürfen sich ändern.

## 6. DNS

`GPU_DOMAIN` muss auf die öffentliche IP des GPU-Hosts zeigen.

Beispiel:

```text
gpu.example.org -> GPU-IP
```

Prüfen:

```bash
getent ahostsv4 gpu.example.org
```

Ports 80 und 443 müssen für Caddy erreichbar sein.

## 7. CPU-Egress-IP

`ALLOWED_REMOTE_IP` ist die Source-/Egress-IP, unter der der CPU-Host die GPU
erreicht.

Es ist nicht:

- die Docker-IP
- eine interne Container-IP
- die IP des GPU-Hosts

## 8. GPU-Environment

```bash
cp \
  infra/gpu/stadtmuseum-berlin/h100-80gb/.env.example \
  /opt/museum-pipeline-h100.env

chmod 600 /opt/museum-pipeline-h100.env
```

Eintragen:

```text
GPU_DOMAIN=<DNS-NAME>
ALLOWED_REMOTE_IP=<CPU-EGRESS-IP>

GPU_CONFIG_DIR=/opt/museum-pipeline/infra/gpu/stadtmuseum-berlin/h100-80gb
MODELS_DIR=/mnt/models

LITELLM_MASTER_KEY=<SECRET>
LLAMA_SWAP_API_KEY=<SECRET>
```

Secrets beispielsweise:

```bash
openssl rand -hex 32
```

Produktive Secrets niemals committen.

## 9. H100-Contract

```bash
python3 infra/gpu/verify_h100_contract.py
```

Erwartet:

```text
CONTRACT: PASS
```

## 10. GPU-Compose

Prüfen:

```bash
docker compose \
  --env-file /opt/museum-pipeline-h100.env \
  -f infra/gpu/generic/compose.yml \
  config
```

Start:

```bash
docker compose \
  --env-file /opt/museum-pipeline-h100.env \
  -f infra/gpu/generic/compose.yml \
  up -d
```

Status:

```bash
docker compose \
  --env-file /opt/museum-pipeline-h100.env \
  -f infra/gpu/generic/compose.yml \
  ps
```

## 11. GPU-Sicherheit

Das Referenzdeployment besitzt zwei Schutzschichten:

```text
Caddy Source-IP-Allowlist
+
LiteLLM API Authentication
```

Nicht erlaubte externe IP:

```text
/metrics   -> HTTP 403
/v1/models -> HTTP 403
```

Erlaubter CPU-Host:

```text
/metrics              -> HTTP 200
/v1/models ohne Token -> HTTP 401
```

## 12. Modellliste

Vom erlaubten CPU-Host:

```bash
curl \
  -H "Authorization: Bearer <LITELLM_MASTER_KEY>" \
  https://<GPU_DOMAIN>/v1/models
```

Erwartet:

```text
qwen3.6-35b-a3b-mtp-q4
gemma-4-26b-a4b-qat
gemma-4-12b-qat
qwen3.6-27b-mtp
gemma-4-31b-it
qwen3.6-35b-mtp
qwen3.6-27b-mtp-64k
gemma-4-31b-it-64k
```

## 13. Reale GPU-Inferenz

```bash
curl \
  -H "Authorization: Bearer <LITELLM_MASTER_KEY>" \
  -H "Content-Type: application/json" \
  https://<GPU_DOMAIN>/v1/chat/completions \
  -d '{
    "model": "gemma-4-12b-qat",
    "messages": [
      {"role": "user", "content": "Antworte kurz mit OK."}
    ],
    "max_tokens": 64
  }'
```

Für eine vollständige Betriebsabnahme sollten alle acht Aliase einmal
inferieren.

---

# Teil B — CPU / Orchestrator

## 14. Voraussetzungen

Referenz:

- Ubuntu 24.04
- Python 3.11+
- Docker
- Docker Compose
- Git
- curl

## 15. Repository und Python

```bash
git clone <repository-url> /opt/museum-pipeline
cd /opt/museum-pipeline

python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

## 16. Runtime-Environment

```bash
cp .env.example .env
chmod 600 .env
```

Für einen hostseitig gestarteten Pipelineprozess wird PostgreSQL über den
lokal veröffentlichten Port erreicht:

```text
PG_HOST=127.0.0.1
PG_PORT=5432
```

Referenzprofile:

```text
MUSEUM_PROFILE=stadtmuseum-berlin
MODEL_PROFILE=reference
HARDWARE_PROFILE=h100-80gb
WORKFLOW=full
LLM_BACKEND=gpu
```

GPU:

```text
LCPP_URL=https://<GPU_DOMAIN>/v1/chat/completions
LCPP_AUTH=Bearer <LITELLM_MASTER_KEY>
```

Embeddings:

```text
EMBED_BASE=http://127.0.0.1:8081
```

Für DINOv3 ist ein Hugging-Face-Token mit Zugriffsrecht auf

```text
facebook/dinov3-vitl16-pretrain-lvd1689m
```

erforderlich.

## 17. `.env` für Hostkommandos

Die Runtime-Datei ist eine dotenv-Datei und wird nicht als Shellscript
interpretiert.

Für Hostkommandos:

```bash
eval "$(.venv/bin/python tools/dotenv_exports.py .env)"
```

## 18. CPU-Basisdienste

```bash
docker compose \
  --env-file .env \
  -f infra/cpu/compose.yml \
  up -d --build postgres embeddings
```

Optional S3:

```bash
docker compose \
  --env-file .env \
  -f infra/cpu/compose.yml \
  --profile s3 \
  up -d --build postgres embeddings presign
```

Optional GND:

```bash
docker compose \
  --env-file .env \
  -f infra/cpu/compose.yml \
  --profile gnd \
  up -d gnd_opensearch
```

## 19. Embedding-Modelle

Standard:

```text
google/siglip2-giant-opt-patch16-384
facebook/dinov3-vitl16-pretrain-lvd1689m
BAAI/bge-m3
```

Der Modellcache liegt persistent unter:

```text
/models/huggingface
```

Health:

```bash
curl -fsS http://127.0.0.1:8081/health
```

## 20. Datenbankschemata

Core:

```bash
docker compose \
  --env-file .env \
  -f infra/cpu/compose.yml \
  exec -T postgres \
  sh -lc 'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < database/core.sql
```

Optional Emotion:

```bash
docker compose \
  --env-file .env \
  -f infra/cpu/compose.yml \
  exec -T postgres \
  sh -lc 'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < database/modules/emotion.sql
```

Optional Topics:

```bash
docker compose \
  --env-file .env \
  -f infra/cpu/compose.yml \
  exec -T postgres \
  sh -lc 'psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < database/modules/topics.sql
```

## 21. Optionale semantische Ressourcen

### Emotion / Machine Heart

Das öffentliche Starterprofil enthält die vollständige museumsagnostische
Machine-Heart-Standardkonfiguration als file-backed Resource:

```text
profiles/_template/emotion/concepts.json
profiles/_template/emotion/vocabulary.runtime.json
```

`core-emotion` kann damit ohne eigene Emotionsdaten aktiviert werden. Ein Museum
kann alternativ eine eigene Datei oder eine database-backed Vocabulary-Query
verwenden; der Vertrag ist in `docs/EMOTION_METHOD.md` beschrieben.

### Institutionelle Topics

Das Repository enthält absichtlich **keine** institutionellen Schwerpunkte. Vor
`core-topics` oder `full` muss das Museum selbst anlegen:

```text
profiles/<museum>/topics/framework.md
profiles/<museum>/topics/taxonomy.json
profiles/<museum>/topics/profile.yaml
```

Bauplan: `profiles/_template/topics/` und `docs/TOPIC_KNOWLEDGE_BASE.md`.

Solange Topics nicht konfiguriert sind, validiere `core` oder `core-emotion`:

```bash
eval "$(.venv/bin/python tools/dotenv_exports.py .env)"
.venv/bin/museum-pipeline validate-config --workflow core
.venv/bin/museum-pipeline validate-config --workflow core-emotion
```

`full` ist erst gültig, nachdem das Museum seine eigene Topics-Wissensbasis
konfiguriert hat.

## 22. S3 / Presign

Bei privaten S3-Assets:

```text
S3_ENDPOINT
S3_BUCKET
S3_ACCESS_KEY
S3_SECRET_KEY
PRESIGN_URL=http://127.0.0.1:8082/s3/presign
```

Health:

```bash
curl -fsS http://127.0.0.1:8082/health
```

Zusätzlich muss ein realer Bildrequest gegen ein vorhandenes Testobjekt
funktionieren.

## 23. OpenSearch / GND

Bei GND:

```text
OS_MSEARCH=http://127.0.0.1:9200/_msearch
OS_INDEX=gnd_sachbegriffe
```

Auf Linux:

```bash
sysctl -w vm.max_map_count=262144
```

Health:

```bash
curl -fsS http://127.0.0.1:9200/_cluster/health
```

GND-Dump:

```bash
mkdir -p data/gnd

curl -fL \
  -o data/gnd/authorities-gnd-sachbegriff_lds.jsonld.gz \
  https://data.dnb.de/opendata/authorities-gnd-sachbegriff_lds.jsonld.gz

sha256sum data/gnd/authorities-gnd-sachbegriff_lds.jsonld.gz
```

Import:

```bash
eval "$(.venv/bin/python tools/dotenv_exports.py .env)"

export GND_INPUT_FILE="$PWD/data/gnd/authorities-gnd-sachbegriff_lds.jsonld.gz"

.venv/bin/python tools/import_gnd_subjects.py
```

Die GND ist eine Rolling Resource.

## 24. Museumsquelldaten

Museumsobjektdaten selbst liegen nicht im Repository.

Das aktive Museum Profile definiert das Mapping:

```text
profiles/<museum>/metadata.yaml
```

Für neue Institutionen:

```text
profiles/_template/
```

## 25. CPU → GPU prüfen

```bash
eval "$(.venv/bin/python tools/dotenv_exports.py .env)"

GPU_BASE="${LCPP_URL%/v1/chat/completions}"

curl \
  -H "Authorization: $LCPP_AUTH" \
  "$GPU_BASE/v1/models"
```

## 26. Pipeline validieren

```bash
.venv/bin/museum-pipeline validate-config
.venv/bin/museum-pipeline show-config
```

## 27. Erster Lauf

Core:

```bash
.venv/bin/museum-pipeline run \
  --workflow core \
  --ids 'OBJECT-ID' \
  -v
```

Full:

```bash
.venv/bin/museum-pipeline run \
  --workflow full \
  --ids 'OBJECT-ID' \
  --force \
  -v
```

`--force` entfernt Ergebnisse der aktivierten Module für die ausgewählten
Objekte und berechnet sie neu.

## 28. Fehler / Resume

Fehlgeschlagene Pflichtphasen führen zu einem Nicht-Null-Exitcode.

Retry:

```bash
.venv/bin/museum-pipeline run \
  --workflow full \
  --ids 'OBJECT-ID' \
  --retry-failed \
  -v
```

---

# Abschluss

Die Installation ist vollständig, wenn:

- CPU-Dienste laufen
- GPU-Dienste laufen
- H100-Contract grün ist
- CPU den GPU-Endpunkt erreicht
- Embedding-Modelle inferieren
- optionale S3-/GND-Dienste funktionieren
- `validate-config` grün ist
- ein reales `core`-Objekt erfolgreich läuft
- bei vollständigem Profil ein reales `full`-Objekt erfolgreich läuft

Zusätzliche Checkliste:

[`FRESH_HOST_CHECKLIST.md`](FRESH_HOST_CHECKLIST.md)

Reproduzierbarkeit:

[`REPRODUCIBILITY.md`](REPRODUCIBILITY.md)

# Manuelle Installation: CPU / Orchestrator

Dieses Manual beschreibt einen frischen CPU-/Orchestrator-Host.

Auf diesem Host läuft **keine LLM/VLM-Inferenz**.


## Dienste

Pflicht:

- Python-Pipeline,
- PostgreSQL,
- Embedding-Service.

Optional:

- Presign bei privatem S3,
- OpenSearch + GND.


## 1. Voraussetzungen

Referenz:

- Ubuntu 24.04,
- Docker Engine,
- Docker Compose Plugin,
- Git,
- Python 3.11+,
- ausreichend RAM und Speicher.

DINOv3 ist gated und kann einen Hugging-Face-Token benötigen.


## 2. Repository

    git clone <repository-url> /opt/museum-pipeline
    cd /opt/museum-pipeline

    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -e .


## 3. Environment

    cp .env.example .env

Mindestens konfigurieren:

    MUSEUM_PROFILE
    MODEL_PROFILE
    HARDWARE_PROFILE
    WORKFLOW

    PG_DB
    PG_USER
    PG_PASSWORD

    LCPP_URL
    LCPP_AUTH

    EMBED_BASE

Optional zusätzlich S3/GND.


## 4. Environment für CLI laden

Die `.env` wird von einer separat gestarteten Shell nicht automatisch
exportiert.

    eval "$(.venv/bin/python tools/dotenv_exports.py .env)"

    .venv/bin/museum-pipeline validate-config


## 5. CPU-Basisdienste

    docker compose \
      --env-file .env \
      -f infra/cpu/compose.yml \
      up -d --build postgres embeddings

Bei S3:

    docker compose \
      --env-file .env \
      -f infra/cpu/compose.yml \
      --profile s3 \
      up -d --build postgres embeddings presign

Bei GND:

    docker compose \
      --env-file .env \
      -f infra/cpu/compose.yml \
      --profile gnd \
      up -d gnd_opensearch


## 6. Datenbankschema

    docker compose \
      --env-file .env \
      -f infra/cpu/compose.yml \
      exec -T postgres \
      sh -c 'psql -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
      < database/core.sql

Für Emotion zusätzlich:

    database/modules/emotion.sql

Für Themen zusätzlich:

    database/modules/topics.sql


## 7. GND — aktueller Rolling Dump

Nur wenn GND aktiviert ist.

    mkdir -p data/gnd

    curl -fL \
      -o data/gnd/authorities-gnd-sachbegriff_lds.jsonld.gz \
      https://data.dnb.de/opendata/authorities-gnd-sachbegriff_lds.jsonld.gz

    sha256sum \
      data/gnd/authorities-gnd-sachbegriff_lds.jsonld.gz

Der Link und Dateiname sind persistent.

Der Inhalt verändert sich mit der GND.

Danach:

    export GND_INPUT_FILE="$PWD/data/gnd/authorities-gnd-sachbegriff_lds.jsonld.gz"

    .venv/bin/python tools/import_gnd_subjects.py

Die zukünftige Zahl importierter Begriffe muss nicht dem historischen
September-2026-Wert entsprechen.


## 8. Quellsystem

Das Repository erzeugt keine Museumsquelldaten.

Das Museumprofil definiert:

- Quelltabelle,
- Objekt-ID,
- Metadatenmapping,
- Assetreferenz.

Für ein neues Museum:

    profiles/_template/


## 9. GPU-Endpunkt

Der CPU-Host erwartet:

    OpenAI-compatible /v1/chat/completions

`LCPP_URL` und `LCPP_AUTH` zeigen auf den separaten GPU-Host.


## 10. Health

    docker compose \
      --env-file .env \
      -f infra/cpu/compose.yml \
      ps

    curl -fsS \
      http://127.0.0.1:${EMBEDDING_PORT:-8081}/health

Optional:

    curl -fsS \
      http://127.0.0.1:${PRESIGN_PORT:-8082}/health

    curl -fsS \
      http://127.0.0.1:${OPENSEARCH_PORT:-9200}/_cluster/health


## 11. Smoke Test

Environment laden:

    eval "$(.venv/bin/python tools/dotenv_exports.py .env)"

Konfiguration:

    .venv/bin/museum-pipeline show-config
    .venv/bin/museum-pipeline validate-config

Ein Objekt:

    .venv/bin/museum-pipeline run \
      --workflow core \
      --count 1 \
      -v


## 12. Referenzprovenienz

Siehe:

    infra/cpu/REFERENCE.md
    infra/cpu/reference/runtime-reference.json
    docs/REPRODUCIBILITY.md

<!-- HF-CACHE-DINO-ACCESS -->

## Embedding-Modellcache und DINOv3-Zugriff

Der Embedding-Service mountet ein persistentes Docker-Volume nach:

    /models

Der Hugging-Face-Cache muss deshalb ebenfalls innerhalb dieses Volumes liegen:

    HF_HOME=/models/huggingface

Damit bleiben heruntergeladene Modelle erhalten, wenn der
Embedding-Container neu erzeugt wird.

Für DINOv3 genügt es nicht, irgendeinen `HF_TOKEN` zu setzen.

Der zugehörige Hugging-Face-Account muss Zugriff auf das gated Repository

    facebook/dinov3-vitl16-pretrain-lvd1689m

haben.

Vor einer frischen Installation sollte der Zugriff geprüft werden, ohne den
Token auszugeben, zum Beispiel durch einen authentifizierten Request auf:

    https://huggingface.co/facebook/dinov3-vitl16-pretrain-lvd1689m/resolve/main/config.json

Erwartet wird HTTP 200.

HTTP 401 oder 403 bedeutet:

- Token fehlt oder ist ungültig, oder
- der Account hat den Zugriff auf das gated Repository noch nicht erhalten.

SigLIP2 und BGE-M3 benötigen diese DINOv3-Freigabe nicht.

<!-- OPENSEARCH-38-CONTAINER-STARTUP -->

## OpenSearch 3.8: Security-Plugin beim Containerstart deaktivieren

Die Referenzarchitektur betreibt den GND-Index ausschließlich lokal auf dem
CPU-Orchestrator und veröffentlicht OpenSearch nicht ins öffentliche Netz.

Für das getestete Image

    opensearchproject/opensearch:3.8.0

müssen deshalb bereits für den Docker-Entrypoint beide Variablen gesetzt sein:

    DISABLE_SECURITY_PLUGIN=true
    DISABLE_INSTALL_DEMO_CONFIG=true

`plugins.security.disabled=true` in der OpenSearch-Konfiguration allein genügt
nicht. Der Docker-Entrypoint führt sonst vor dem eigentlichen OpenSearch-Start
den Security-Demo-Installer aus. Seit OpenSearch 2.12 verlangt dieser ein
`OPENSEARCH_INITIAL_ADMIN_PASSWORD` und beendet den Container ohne Passwort.

Die getestete Referenzkonfiguration verwendet außerdem:

    OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g

OpenSearch bleibt dabei ausschließlich an `127.0.0.1` gebunden.

<!-- S3-SECRETS-EXTERNAL-PREREQUISITE -->

## S3-Zugangsdaten sind externe Voraussetzungen

Der Presign-Dienst benötigt:

    S3_ENDPOINT
    S3_BUCKET
    S3_ACCESS_KEY
    S3_SECRET_KEY

Diese Werte gehören nicht ins Repository und können bei einer frischen
Installation nicht aus dem Quellcode rekonstruiert werden.

Sie müssen vom Betreiber des S3-kompatiblen Object Storage bereitgestellt und
als Secrets in der Installationsumgebung hinterlegt werden.

Vor dem Start des Presign-Dienstes muss geprüft werden, dass alle vier Werte
gesetzt sind. Dabei dürfen Access Key und Secret Key nicht in Logs oder
Diagnoseausgaben geschrieben werden.

Ein fehlender S3-Zugang ist kein Fehler des Presign-Dienstes, sondern eine
nicht erfüllte externe Installationsvoraussetzung.

<!-- DOTENV-NOT-SHELL-CONTRACT -->

## `.env` ist keine Shell-Datei

Die Installationskonfiguration wird als dotenv-/Compose-Datei geführt.

Sie darf nicht direkt mit

    source .env

oder

    . ./.env

in eine Shell geladen werden.

Grund: gültige Konfigurationswerte können Leerzeichen oder andere
Shell-Sonderzeichen enthalten. Beispiele aus der Referenzinstallation sind:

    LCPP_AUTH=Bearer <TOKEN>
    OPENSEARCH_JAVA_OPTS=-Xms2g -Xmx2g

Docker Compose liest solche Werte korrekt aus einer `--env-file`.
Eine Shell würde sie dagegen als Befehlsbestandteile interpretieren.

Für hostseitige Pipeline-Kommandos wird die Datei deshalb als Daten gelesen
und sicher für die aktuelle Shell gequotet:

    eval "$(.venv/bin/python tools/dotenv_exports.py .env)"

Danach können beispielsweise ausgeführt werden:

    .venv/bin/museum-pipeline validate-config --workflow core
    .venv/bin/museum-pipeline validate-config --workflow full

`tools/dotenv_exports.py` wertet keine Shell-Ausdrücke aus. Schlüssel werden
validiert und Werte ausschließlich mit POSIX-Shell-Quoting exportiert.

`LCPP_AUTH` enthält bei der Referenzarchitektur den vollständigen Wert des
HTTP-Headers, also einschließlich des Präfixes:

    Bearer <TOKEN>

Secrets dürfen bei Prüfung oder Fehlersuche nicht ausgegeben werden.

<!-- S3-ENV-CONTAINER-LIFECYCLE -->

### S3-Konfiguration gilt für Presign und Embeddings

Bei einem Museumsprofil mit `source.asset.mode: s3` benötigen nicht nur der
Presign-Dienst, sondern auch die CPU-Embeddings Zugriff auf die
S3-Konfiguration:

- `S3_ENDPOINT`
- `S3_BUCKET`
- `S3_ACCESS_KEY`
- `S3_SECRET_KEY`

Diese Werte müssen deshalb **vor dem ersten Erzeugen der betreffenden
Container** in der Laufzeit-`.env` vorhanden sein.

Eine spätere Änderung der `.env` verändert die Environment-Variablen eines
bereits laufenden Docker-Containers nicht. Nach einer Änderung müssen die
betroffenen Container neu erzeugt werden; persistente Modell- und
Daten-Volumes bleiben dabei erhalten.

Für den Embedding-Dienst beispielsweise:

    docker compose \
      --env-file .env \
      -f infra/cpu/compose.yml \
      --profile s3 \
      up -d --no-deps --force-recreate --no-build embeddings

Vor einem echten Pipeline-Lauf muss bei einem S3-Profil ein realer
`/embed/image`-Request erfolgreich sein. Ein grünes `/health` allein beweist
nur die Dienstverfügbarkeit, nicht den Zugriff auf den Objektspeicher.

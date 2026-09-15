# Systemarchitektur

## Zielbild

Die Pipeline trennt drei technische Verantwortungsbereiche:

    Quellsystem / Assets
            │
            ▼
    CPU / Orchestrator
            │
            │ OpenAI-kompatible API
            ▼
       LLM-Inferenz
      GPU oder extern
            │
            ▼
        Ergebnisdaten


# CPU-/Orchestrator-Seite

Die CPU-Seite führt den Python-Workflow aus und hält die für den Flow
notwendigen nicht-generativen Dienste.

Im Referenzbetrieb führt dieser Host **keine LLM/VLM-Inferenz** aus.
Alle generativen Modellaufrufe gehen an einen separaten
OpenAI-kompatiblen GPU-Inferenzhost.

Der kanonische Compose-Stack liegt unter:

    infra/cpu/compose.yml

Er enthält:

## PostgreSQL

Speichert:

- Enrichment-Ergebnisse,
- Run-State,
- bei Bedarf Profilressourcen.

Das Quellsystem des Museums wird dadurch nicht automatisch ersetzt.


## Embedding-Service

FastAPI-Service für:

- SigLIP2-Bildvektoren,
- DINOv3-Bildvektoren,
- BGE-M3-Textvektoren.

Diese Modelle laufen im Referenzdeployment auf CPU.


## Presign-Service

Nur notwendig, wenn ein Museum private S3-kompatible Assets benutzt.

Bei direkten HTTP(S)-Bild-URLs ist dieser Dienst nicht erforderlich.


## OpenSearch / GND

Optional.

Wird im deutschen Referenzsetup für das Retrieval von
GND-Sachbegriffen benutzt.

Wird GND im Museumprofil abgeschaltet, ist OpenSearch für diesen Zweck nicht
notwendig.


# LLM-Seite

Die Pipeline kommuniziert mit einem OpenAI-kompatiblen Endpoint.

Die Referenzarchitektur lautet:

    Pipeline
       │
       │ HTTPS
       ▼
     Caddy
       │
       ▼
    LiteLLM
       │
       ▼
   llama-swap
       │
       ▼
   llama.cpp
       │
       ▼
      GPU


## Caddy

Übernimmt:

- TLS,
- externen Endpoint,
- optional IP-Allowlisting.


## LiteLLM

Stellt die OpenAI-kompatible API bereit und mappt Modellnamen auf
llama-swap.


## llama-swap

Startet und beendet llama.cpp-Modellserver bedarfsorientiert.

Dadurch müssen nicht alle großen Modelle gleichzeitig im VRAM liegen.


## llama.cpp

Führt die konkreten GGUF-Modelle aus.


# Warum die Pipeline nur eine OpenAI-kompatible API kennt

Der Core soll nicht wissen, ob hinter dem Endpoint:

- llama.cpp,
- ein anderer lokaler Inferenzserver,
- ein Cloud-Endpunkt,
- ein institutioneller AI Gateway

steht.

Die Modellrollen werden über `models/*.yaml` konfiguriert.


# Hardware und Concurrency

Hardwarekapazität gehört nicht in Prompts und nicht in Museumprofile.

Sie liegt unter:

    hardware/

Das H100-Referenzprofil speichert unter anderem:

- `parallel_slots`
- `context_pool`
- `min_context_per_slot`
- phasenspezifische Worker-Regeln.


## Kritischer H100-Vertrag

Im kalibrierten H100-Deployment müssen zwei Ebenen übereinstimmen:

    hardware/h100-80gb.yaml
             ↕
    llama.cpp -c / -np

Für jedes Referenzmodell gilt:

    context_pool   == llama.cpp -c
    parallel_slots == llama.cpp -np

Der Vertrag wird geprüft durch:

    infra/gpu/verify_h100_contract.py


## GND-Sonderfall

Der GND-Schritt hat zwei Parallelitätsebenen.

Nicht:

    8 Objekte
      ×
    8 GND-Aufrufe

sondern:

    1 Objekt
      └── bis zu 8 GND-Aufrufe

Daher ist im H100-Referenzprofil festgelegt:

    tagging.authority:
      outer_workers: 1
      inner_workers_from_model: authority.gnd

Diese Einstellung ist funktional relevant und kein beliebiger
Performance-Tuning-Wert.


# Asset-Grenze

Der Core kennt eine kanonische Asset-Referenz:

    {"mode": "s3", "value": "objects/123.jpg"}

oder:

    {"mode": "url", "value": "https://museum.example/image.jpg"}

S3-Zugang, Presigning und URL-Auflösung bleiben Infrastrukturdetails.


# Datenbankgrenze

Generische Ergebnis-Tabellen werden durch

    database/core.sql

angelegt.

Optionale Module:

    database/modules/emotion.sql
    database/modules/topics.sql

Museumsspezifische Quelltabellen werden vom generischen Bootstrap nicht
erzeugt.


# Sicherheitsprinzip

Ein typisches Zwei-Host-Deployment exponiert nur den HTTPS-Endpunkt des
Inferenzhosts.

PostgreSQL, OpenSearch, Embeddings und Presign können lokal bzw. auf
Loopback gebunden bleiben.

Domains, IP-Adressen, Passwörter und API-Keys sind Deploymentwerte und
gehören nicht in generischen Sourcecode.


# Observability

Die Pipeline unterstützt optional OpenTelemetry/Phoenix.

Tracing ist kein fachlicher Bestandteil des Flows und kann abgeschaltet
werden.

Es dient zur Analyse von:

- Modellaufrufen,
- Latenzen,
- Tokenverbrauch,
- Fehlern,
- Objektläufen.

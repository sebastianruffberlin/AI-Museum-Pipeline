# Systemarchitektur

Dieses Dokument hat zwei Teile: **Teil A** beschreibt, wie die Pipeline
*konzeptionell* konfiguriert ist (die fünf Profil-Achsen im Python-Code).
**Teil B** beschreibt, wie sie *tatsächlich betrieben* wird (CPU/GPU-Topologie,
Services, Hardware-Vertrag). Wer nur verstehen will, welche Datei was
konfiguriert, findet das in Teil A. Wer ein Deployment aufsetzt oder debuggt,
braucht Teil B.

---

# Teil A — Konfigurationsmodell

## Fünf unabhängige Konfigurationsachsen

1. **Harness** — Ausführung, Batching, State, Retry, Validierung, Tracing.
2. **Workflow** — welche Module laufen.
3. **Museum Profile** — institutionsspezifische Semantik und Quell-Mapping.
4. **Model Profile** — Modellidentitäten und qualitätsrelevante Generierungs-/Reasoning-Einstellungen.
5. **Hardware Profile** — Laufzeit-Parallelität/Context-Pool-Kapazität für ein Deployment.

Diese Trennung verhindert, dass eine museumsspezifische Taxonomie in
Python-Ausführungscode einsickert, und verhindert, dass Hardware-Tuning
(`np`) mit einer Modell-/Skill-Eigenschaft verwechselt wird.

Details zu den fünf Profiltypen und was ein neues Museum typischerweise
anpasst: siehe [`PROFILES.md`](PROFILES.md).

## Kern-Abhängigkeitsgraph

```text
image_embeddings ─┐
image_features ────┤
captions ──────────┼─ core-Ergebnisse ─┬─ emotion (optional)
tagging ───────────┤                   ├─ topics (optional)
text_embeddings ──┘                    └─ zukünftige Module
```

Emotion und Topics sind Geschwister-Module. Beide konsumieren fertige
Caption- und Tagging-Informationen, haben aber keine Abhängigkeit
zueinander.

## Phasen-Scheduler

`WorkflowRunner` expandiert die aktivierten Module zu atomaren Phasen. Jede
Phase läuft über alle Kandidatenobjekte, mit einer Worker-Zahl, die aus dem
Hardware Profile abgeleitet wird. Modellrollen werden über `models/*.yaml`
aufgelöst; der Workflow benennt nie ein konkretes Modell direkt.

Die GND-Authority-Phase ist ein besonderer Fall zweistufiger Parallelität:
Die äußere Objekt-Parallelität ist im H100-Referenzprofil bewusst 1, weil ein
einzelnes Objekt intern mehrere begriffsebenen-LLM-Aufrufe erzeugt.

## Persistenzgrenze

Die Pipeline legt ein kanonisches Museums-Ergebnisschema in PostgreSQL an
(`museum.enrichment_*`, Emotion-/Topics-Tabellen, Embeddings). Rohe
Quellspalten sind dem Harness nicht bekannt: `profiles/<museum>/metadata.yaml`
mappt sie auf kanonische Feld-IDs, die von `ContextBuilder` genutzt werden.

Scratch-/Resume-Daten liegen getrennt in `MUSEUM_RUN_SCHEMA`.

---

# Teil B — Infrastruktur & Deployment

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


## CPU-/Orchestrator-Seite

Die CPU-Seite führt den Python-Workflow aus und hält die für den Flow
notwendigen nicht-generativen Dienste.

Im Referenzbetrieb führt dieser Host **keine LLM/VLM-Inferenz** aus.
Alle generativen Modellaufrufe gehen an einen separaten
OpenAI-kompatiblen GPU-Inferenzhost.

Der kanonische Compose-Stack liegt unter:

    infra/cpu/compose.yml

Er enthält:

### PostgreSQL

Speichert:

- Enrichment-Ergebnisse,
- Run-State,
- bei Bedarf Profilressourcen.

Das Quellsystem des Museums wird dadurch nicht automatisch ersetzt.


### Embedding-Service

FastAPI-Service für:

- SigLIP2-Bildvektoren,
- DINOv3-Bildvektoren,
- BGE-M3-Textvektoren.

Diese Modelle laufen im Referenzdeployment auf CPU.

Lädt ein Objekt ein Bild per `image_url` statt aus dem privaten S3-Bucket,
ist dieser Dienst der Punkt, an dem die Pipeline mit einer vom Museumsdatensatz
kontrollierten URL selbst einen HTTP-Request stellt. Der Service ist deshalb
gegen SSRF gehärtet: Schema-Whitelist (nur `http`/`https`), DNS-Auflösung
gegen private/loopback/link-local/reservierte Adressbereiche gesperrt, jeder
Redirect wird erneut geprüft, Downloadgröße und Pixelzahl sind begrenzt
(`IMG_MAX_DOWNLOAD_BYTES`, `IMG_MAX_PIXELS`). Museen mit einem tatsächlich
privat liegenden Bildserver können einzelne Hosts über
`IMG_ALLOWED_PRIVATE_HOSTS` explizit freischalten.


### Presign-Service

Nur notwendig, wenn ein Museum private S3-kompatible Assets benutzt.

Bei direkten HTTP(S)-Bild-URLs ist dieser Dienst nicht erforderlich.


### OpenSearch / GND

Optional.

Wird im deutschen Referenzsetup für das Retrieval von
GND-Sachbegriffen benutzt.

Wird GND im Museumprofil abgeschaltet, ist OpenSearch für diesen Zweck nicht
notwendig.


## LLM-Seite

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


### Caddy

Übernimmt:

- TLS,
- externen Endpoint,
- optional IP-Allowlisting.


### LiteLLM

Stellt die OpenAI-kompatible API bereit und mappt Modellnamen auf
llama-swap.


### llama-swap

Startet und beendet llama.cpp-Modellserver bedarfsorientiert.

Dadurch müssen nicht alle großen Modelle gleichzeitig im VRAM liegen.


### llama.cpp

Führt die konkreten GGUF-Modelle aus.


## Warum die Pipeline nur eine OpenAI-kompatible API kennt

Der Core soll nicht wissen, ob hinter dem Endpoint:

- llama.cpp,
- ein anderer lokaler Inferenzserver,
- ein Cloud-Endpunkt,
- ein institutioneller AI Gateway

steht.

Die Modellrollen werden über `models/*.yaml` konfiguriert.


## Hardware und Concurrency

Hardwarekapazität gehört nicht in Prompts und nicht in Museumprofile.

Sie liegt unter:

    hardware/

Das H100-Referenzprofil speichert unter anderem:

- `parallel_slots`
- `context_pool`
- `min_context_per_slot`
- phasenspezifische Worker-Regeln.


### Kritischer H100-Vertrag

Im kalibrierten H100-Deployment müssen zwei Ebenen übereinstimmen:

    hardware/h100-80gb.yaml
             ↕
    llama.cpp -c / -np

Für jedes Referenzmodell gilt:

    context_pool   == llama.cpp -c
    parallel_slots == llama.cpp -np

Der Vertrag wird geprüft durch:

    infra/gpu/verify_h100_contract.py


### GND-Sonderfall

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


## Asset-Grenze

Der Core kennt eine kanonische Asset-Referenz:

    {"mode": "s3", "value": "objects/123.jpg"}

oder:

    {"mode": "url", "value": "https://museum.example/image.jpg"}

S3-Zugang, Presigning und URL-Auflösung bleiben Infrastrukturdetails.


## Datenbankgrenze

Generische Ergebnis-Tabellen werden durch

    database/core.sql

angelegt.

Optionale Module:

    database/modules/emotion.sql
    database/modules/topics.sql

Museumsspezifische Quelltabellen werden vom generischen Bootstrap nicht
erzeugt.


## Sicherheitsprinzip

Ein typisches Zwei-Host-Deployment exponiert nur den HTTPS-Endpunkt des
Inferenzhosts.

PostgreSQL, OpenSearch, Embeddings und Presign können lokal bzw. auf
Loopback gebunden bleiben.

Domains, IP-Adressen, Passwörter und API-Keys sind Deploymentwerte und
gehören nicht in generischen Sourcecode. Für GPU-Installer-Deployments gilt
zusätzlich: `gpu.deployment_path` hat keinen institutionsspezifischen
Default mehr und muss in `deployment.yaml` explizit gesetzt werden (siehe
[`INSTALLER.md`](INSTALLER.md)).


## Observability

Die Pipeline unterstützt optional OpenTelemetry/Phoenix.

Tracing ist standardmäßig deaktiviert (`PHOENIX_ENABLED=0`) und kein
fachlicher Bestandteil des Flows.

Es dient zur Analyse von:

- Modellaufrufen,
- Latenzen,
- Tokenverbrauch,
- Fehlern,
- Objektläufen.

Da Tracing-Spans Objekt-IDs und ggf. Prompt-/Antwortausschnitte enthalten
können, siehe [`../SECURITY.md`](../SECURITY.md) für den Umgang mit
Museumsdaten in Tracing und Logs.

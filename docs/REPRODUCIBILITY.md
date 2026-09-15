# Reproduzierbarkeit

Die Pipeline unterscheidet bewusst zwischen **reproduzierbarer
Architektur** und einem vollständig eingefrorenen Daten-/Modellstand.

Das ist für dieses Projekt wichtig, weil sowohl Normdaten als auch
veröffentlichte Modellgewichte weiterentwickelt werden.


## Vier Arten von Reproduzierbarkeit

### 1. Fachlicher Vertrag

Fest sind:

- Workflowstufen,
- Museumprofil,
- Modellrollen,
- kontrollierte Vokabulare,
- Prompt-/Policy-Dateien,
- Authority-Regeln,
- Datenbankschemata.

Änderungen daran sind fachliche Änderungen.


### 2. Hardware-/Runtime-Vertrag

Für den verifizierten H100-Referenzfall sind fest:

- Modellalias,
- llama.cpp-Flags,
- `-c`,
- `-np`,
- Workerlogik,
- GND-Outer-/Inner-Parallelität.

Diese Werte werden durch

    infra/gpu/verify_h100_contract.py

geschützt.

Sie dürfen nicht stillschweigend neu getunt werden.


### 3. Rolling Upstream Resources

Einige Quellen sollen absichtlich aktuell bleiben.

Dazu gehört die GND.

Fest sind:

- Anbieter,
- persistente Download-URL,
- Dateiname,
- Importer,
- Zielindex.

Nicht fest ist der Inhalt des Dumps.

Die GND wächst und wird korrigiert.

Deshalb protokolliert eine Installation:

- Downloadzeitpunkt,
- SHA256 des tatsächlich geladenen Dumps.

Eine spätere Installation darf mehr Datensätze enthalten.


### 4. Rolling Models + Reference Snapshot

Für LLM/VLM-Modelle ist fest:

- Modellfamilie,
- Quant-Anbieter: Unsloth,
- Hugging-Face-Repository,
- gewählte Quantisierung,
- Modell-Dateiname,
- mmproj-Dateiname.

Standardmäßig wird von `main` geladen.

Unsloth darf eine Quantisierung später aktualisieren.

Deshalb ist die SHA256 des Referenzservers **kein generelles
Download-Verbot**, sondern Provenienz:

> Mit diesen Bytes wurde der Referenzstand vom 13.09.2026 getestet.

Nach einem neuen Download werden Größe und SHA256 erneut lokal
protokolliert.

Eine Abweichung zum Referenzhash ist im Rolling-Modus zulässig.


## Warum Größen und Hashes trotzdem gespeichert werden

Sie beantworten später Fragen wie:

- Ist dies wirklich dieselbe Datei wie beim Referenztest?
- Hat sich eine Quantisierung upstream verändert?
- Ist ein Download beschädigt?
- Warum verhält sich ein neuer Server geringfügig anders?


## Embedding-Modelle

Dasselbe Prinzip gilt für:

- SigLIP2,
- DINOv3,
- BGE-M3.

Das Repository hält die Modell-ID fest.

`infra/cpu/reference/runtime-reference.json` dokumentiert zusätzlich
die auf dem verifizierten Referenzhost beobachteten Hugging-Face-
Revisionen.


## Zwei Reproduktionsziele

**Praktische Reproduktion**

    gleiche Architektur
    + gleiche Modellfamilien
    + gleiche Quantisierung
    + aktuelle Upstream-Dateien
    + dokumentierte lokale Provenienz

Dies ist der Standardfall.

**Historische Referenzprüfung**

    vorhandene Modellfiles
    + Referenzgröße
    + Referenz-SHA256

Dafür gibt es:

    verify-model-files.py --sha256

Eine historische Byte-Reproduktion aus dem Internet ist nur garantiert,
wenn der jeweilige Upstream-Anbieter die historische Revision weiterhin
bereitstellt.


## Nicht Teil des Referenzstacks

CPU-basierte LLM-Inferenz auf dem Orchestrator ist nicht Bestandteil
dieser Architektur.

Der Referenzweg ist:

    CPU-Orchestrator
        -> HTTPS
        -> separater GPU-Inferenzhost

<!-- DOTENV-REPRODUCIBILITY -->

### Reproduzierbares Laden der Laufzeitkonfiguration

Die `.env` wird nicht als Shellscript interpretiert. Für manuelle
hostseitige Kommandos gilt:

    eval "$(.venv/bin/python tools/dotenv_exports.py .env)"

Damit werden auch Referenzwerte mit Leerzeichen bytegetreu als ein
Environment-Wert übernommen.

<!-- MANDATORY-LLM-FAIL-FAST -->

### Pflichtphasen mit LLM-Inferenz sind fail-fast

Transport-, API- oder Modellfehler in verpflichtenden Captioning- und
Tagging-Phasen dürfen nicht durch einen statischen Fallbacktext oder einen
Leerstring in einen erfolgreichen Phasenstatus umgewandelt werden.

Für verpflichtende Modellphasen gilt deshalb:

- Exceptions des LLM-Clients propagieren bis zum zentralen Phasenrunner.
- Leere erfolgreiche Modellantworten erzeugen ebenfalls einen Phasenfehler.
- Der zentrale Runner persistiert den Fehler im Laufzustand.
- Der CLI-Lauf endet bei fehlgeschlagenen Objekten mit einem
  Nicht-Null-Exitcode.
- Ein Fallback darf nur dort existieren, wo er ausdrücklich als fachliche
  Best-Effort-Strategie definiert und dokumentiert ist.

Der Clean-room-Test im September 2026 zeigte den Grund für diese Regel:
Ein nicht akzeptiertes Gateway-Credential führte zunächst zu statischen
Caption-Fallbacks beziehungsweise leeren Tagging-Captions, obwohl die
betreffenden Phasen als erfolgreich geloggt wurden.

<!-- PROFILE-RESOURCE-CONTRACT -->

### Museum-profile resources

Generic database schemas contain only the pipeline persistence model, not
institution-specific controlled vocabularies or strategic frameworks.

The public repository ships the complete Machine Heart default as file-backed
affective resources. Institution-specific Topics are deliberately **not** bundled;
only the engine and construction templates are public.

A museum may intentionally use database-backed Emotion or Topics resources if it
manages its vocabulary/taxonomy in PostgreSQL. In that case the profile query must
return the same logical resources expected by the module. See `EMOTION_METHOD.md`
and `TOPIC_KNOWLEDGE_BASE.md` for the adapter contracts.

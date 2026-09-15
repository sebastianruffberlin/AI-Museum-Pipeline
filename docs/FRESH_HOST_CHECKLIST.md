# Fresh-Host Acceptance Checklist

Diese Checkliste definiert, wann die manuelle Reproduktion als gelungen
gilt.

Sie ist zugleich die spätere Spezifikation für den Installer.


## A. CPU / Orchestrator

- Repository auf frischem Linux-Host vorhanden.
- Python-Venv installiert.
- Museum-, Modell-, Hardware- und Workflowprofil validieren.
- PostgreSQL läuft.
- Embedding-Service läuft.
- SigLIP2 lädt.
- DINOv3 lädt.
- BGE-M3 lädt.
- Optional Presign funktioniert.
- Optional OpenSearch funktioniert.
- Optional aktueller GND-Dump wurde importiert.
- Museum-Quelltabelle ist erreichbar.


## B. GPU

- NVIDIA-Treiber funktioniert.
- NVIDIA Container Runtime funktioniert.
- sechs Modellsets wurden aus den definierten Unsloth-Quellen geladen.
- lokale Provenienzdatei wurde geschrieben.
- Caddy läuft.
- LiteLLM läuft.
- llama-swap läuft.
- `/v1/models` zeigt acht Aliase.
- H100-Contract ist PASS.


## C. Ende-zu-Ende

- CPU erreicht GPU über HTTPS.
- ein einfacher Chat-Completion-Test funktioniert.
- Embedding-Health ist grün.
- `museum-pipeline validate-config` ist grün.
- ein Objekt läuft durch `core`.
- ein Objekt läuft durch `full`, wenn optionale Module konfiguriert sind.
- Ergebniszeilen landen in den vorgesehenen Enrichment-Tabellen.


## D. Fachliche Prüfung

Das Ergebnis zeigt erkennbar getrennt:

- Quellmetadaten,
- visuellen Befund,
- maschinelle Erschließung,
- optionale interpretative Anreicherung.

GND ist optional.

Emotion und institutionelle Themen sind optional.

Das Museumprofil kann gewechselt werden, ohne `src/museum_pipeline/`
institutionsspezifisch zu verändern.


## E. Provenienz

Für eine Installation sind nachvollziehbar:

- Git-Commit des Repositories,
- aktives Museumprofil,
- Model Profile,
- Hardware Profile,
- Workflow,
- GPU-Modellquellen,
- tatsächlich geladene Modell-SHA256,
- Containerimages,
- GND-Downloadzeitpunkt und SHA256, falls genutzt.


## Übergang zum Installer

Ein Installer darf nur Schritte automatisieren, die in den manuellen
Installationsanleitungen und dieser Checkliste bereits beschrieben sind.

<!-- EMBEDDING-CACHE-ACCEPTANCE -->

### Zusätzliche Embedding-Abnahme

Für einen Blank-State-Test gilt zusätzlich:

- der Hugging-Face-Cache beginnt ohne die drei Referenzmodelle,
- `HF_HOME` zeigt auf `/models/huggingface`,
- SigLIP2 wird aus dem leeren Cache geladen und inferiert,
- DINOv3 wird mit tatsächlich autorisiertem `HF_TOKEN` geladen und inferiert,
- BGE-M3 wird aus dem leeren Cache geladen und inferiert,
- der Embedding-Container wird anschließend neu erzeugt,
- die Modellfiles bleiben im persistenten Volume erhalten,
- beim zweiten Start ist kein vollständiger Neu-Download nötig.

<!-- CPU-S3-OPENSEARCH-PREFLIGHT -->

### CPU-Preflight: S3 und OpenSearch

Vor dem Start der optionalen CPU-Dienste:

- bei aktiviertem Presign müssen `S3_ENDPOINT`, `S3_BUCKET`,
  `S3_ACCESS_KEY` und `S3_SECRET_KEY` vorhanden sein,
- Secrets werden nur auf Vorhandensein geprüft und niemals ausgegeben,
- OpenSearch 3.8 startet mit `DISABLE_SECURITY_PLUGIN=true`,
- OpenSearch 3.8 startet mit `DISABLE_INSTALL_DEMO_CONFIG=true`,
- die Referenzkonfiguration verwendet `-Xms2g -Xmx2g`,
- OpenSearch ist nur über den lokalen Host-Port erreichbar,
- ein frischer GND-Test beginnt mit einem leeren OpenSearch-Volume und
  ohne bereits vorhandenen GND-Index.

<!-- SAFE-DOTENV-LOADING -->

### Hostseitige `.env`-Nutzung

- `.env` nicht mit `source` oder `. ./.env` ausführen.
- Docker Compose erhält die Datei über `--env-file`.
- Hostseitige Pipeline-Kommandos laden sie über
  `tools/dotenv_exports.py`.
- Werte mit Leerzeichen müssen unverändert erhalten bleiben.
- `LCPP_AUTH` enthält den vollständigen Authorization-Headerwert
  einschließlich `Bearer `.
- Secrets werden niemals in Diagnoseausgaben ausgegeben.

<!-- S3-EMBEDDING-PREFLIGHT -->

### S3-Preflight

Für Profile mit S3-Assets:

- S3-Konfiguration vor dem ersten Start von `presign` und `embeddings`
  bereitstellen.
- Nach Änderungen an S3-Werten die betroffenen Container neu erzeugen.
- Persistentes Embedding-Modellvolume dabei beibehalten.
- Nicht nur `/health`, sondern einen realen `/embed/image`-Request mit einem
  vorhandenen Testobjekt prüfen.
- Ein Pipeline-Lauf mit Objektfehler muss einen Prozess-Exitcode ungleich
  `0` liefern.

# Installer

Der Installer automatisiert das bereits dokumentierte manuelle Deployment.

Er erfindet keine neue Architektur und provisioniert weder Cloud-Accounts
noch DNS-Zonen noch die Museums-Quelldaten.

Die manuelle Deployment-Dokumentation bleibt der Referenzvertrag.

## Was das Museum vorbereitet

### Infrastruktur

CPU-/Orchestrator-Host:

- Linux;
- SSH-/Admin-Zugang;
- Docker Engine;
- Docker-Compose-Plugin;
- Git;
- Python 3.11+;
- ausreichend RAM/Storage für PostgreSQL und Embedding-Modelle.

Managed-GPU-Host:

- Linux;
- SSH-/Admin-Zugang;
- Docker Engine;
- Docker-Compose-Plugin;
- funktionierender NVIDIA-Treiber (`nvidia-smi`);
- NVIDIA Container Runtime;
- ausreichend VRAM/Storage für das gewählte kalibrierte Deployment;
- Ports 80/443 aus dem Internet erreichbar für Caddy/TLS.

Zusätzlich:

- DNS für die GPU-Domain zeigt bereits auf den GPU-Host;
- S3/Object Storage existiert, wenn private S3-Assets genutzt werden;
- Museums-Quelldaten existieren bereits und sind erreichbar.

Der Installer bestellt bewusst keine Server, legt keine DNS-Einträge an und
erstellt nicht die primäre Sammlungsdatenbank des Museums.

## Was das Museum fachlich konfiguriert

Profil anlegen:

    museum-pipeline init-profile mein-museum

Der Profilname muss ein Slug sein (Kleinbuchstaben, Ziffern, Bindestriche,
beginnend mit einem Buchstaben). Der Befehl trägt `id`/`name` im neuen
`profile.yaml` automatisch passend ein.

Dann bearbeiten:

    profiles/mein-museum/

Die wichtigen Bereiche:

### `metadata.yaml`

Pflicht.

Definiert:

- Quelltabelle / Quellobjekt;
- Objekt-Identifikator;
- Metadatenfeld-Mapping;
- Asset-Referenz;
- welche Metadatenfelder welchem Pipeline-Kontext offenstehen.

### `prompts/`

Funktionierende Vorlagen-Prompts werden mitgeliefert.

Ein Museum muss sie nur ändern, wenn Terminologie, Zielgruppe,
Erschließungspolitik oder Interpretationsregeln abweichen.

### `tagging/`

Bei Nutzung von Tagging konfigurieren:

- kontrollierte Cluster;
- Audit-/Repair-Policy;
- Terminologie-/Debias-Regeln.

### `authority/`

Festlegen, ob Normdaten-Anreicherung wie GND aktiviert ist, und deren
Policy konfigurieren.

### `emotion/`

Zur Laufzeit optional, aber das Starterprofil enthält bereits den
vollständigen museumsagnostischen **Machine-Heart**-Default. Ein Museum
kann ihn unverändert aktivieren, nur das Runtime-Vokabular ersetzen, eine
museumsspezifische Vokabular-DB anbinden, oder Methode/Prompt-Konfiguration
ersetzen. Siehe `EMOTION_METHOD.md`.

### `topics/`

Optional und institutionseigen. Der Starter enthält nur Templates; keine
echten Themennamen oder Wissensbasis-Inhalte sind enthalten. Framework und
Taxonomie müssen erstellt werden, bevor ein Topics-Workflow aktiviert wird.
Siehe `TOPIC_KNOWLEDGE_BASE.md`.

Normale Museumsanpassung sollte keine Änderungen an
`src/museum_pipeline/` erfordern.

## Was in `deployment.yaml` gehört

`deployment.yaml` enthält nicht-geheime Deployment-Entscheidungen:

    museum_profile: mein-museum
    model_profile: reference
    hardware_profile: h100-80gb
    workflow: core

    features:
      s3: false
      gnd: false

    gpu:
      mode: managed
      host: 203.0.113.20
      ssh_user: root
      domain: gpu.meinmuseum.de
      deployment_path: infra/gpu/generic

`repository.url` kann in der Regel ganz entfallen: Der Installer erkennt den
Git-Origin des aktuellen Checkouts automatisch. Nur explizit setzen, wenn
aus einem Checkout ohne konfigurierten Origin-Remote deployt wird.

**`gpu.deployment_path` ist bei `gpu.mode: managed` Pflicht und hat keinen
institutionsspezifischen Default.** Für den generischen Einstieg
`infra/gpu/generic` verwenden. Für exakt kalibrierte H100-80GB-Hardware kann
auch direkt auf die real getestete Referenzkonfiguration
`infra/gpu/stadtmuseum-berlin/h100-80gb` verwiesen werden — das ist eine
technische Hardware-Referenz, kein museumsspezifischer Inhalt. Fehlt der
Wert bei `mode: managed`, bricht der Installer mit einer klaren
Fehlermeldung ab, statt stillschweigend auf ein bestimmtes Museum
zurückzufallen.

Diese Datei kann vom Museum bei Bedarf versioniert werden.

## Was in `.env` gehört

Nur Secrets oder extern vergebene Zugangsdaten.

Typisches frisches Managed-Deployment:

    HF_TOKEN=...

    S3_ENDPOINT=...
    S3_BUCKET=...
    S3_ACCESS_KEY=...
    S3_SECRET_KEY=...

Interne Secrets werden bei der Erstinstallation generiert und persistiert
unter:

    .museum-pipeline/generated.env

Dazu gehören:

- PostgreSQL-Passwort;
- LiteLLM-Master-Key;
- llama-swap-API-Key.

Für einen bereits existierenden externen GPU-Endpoint stattdessen:

    LCPP_URL=https://...
    LCPP_AUTH=Bearer ...

Optional, für den Embedding-Service (SSRF-Härtung, siehe
`SYSTEM_ARCHITECTURE.md`):

    IMG_MAX_DOWNLOAD_BYTES=26214400
    IMG_MAX_PIXELS=64000000
    IMG_ALLOWED_PRIVATE_HOSTS=

`IMG_ALLOWED_PRIVATE_HOSTS` ist eine kommagetrennte Liste von Hostnamen, die
trotz privater/interner IP-Adresse erlaubt werden sollen — nur setzen, wenn
der eigene Bildserver tatsächlich intern liegt.

## Installieren

Vorbereiten:

    cp deployment.example.yaml deployment.yaml
    cp installer.env.example .env
    chmod 600 .env

Museumsprofil anlegen/konfigurieren.

Dann:

    museum-pipeline install

Die vorgesehene Ausführungsreihenfolge:

    preflight
      -> Managed-GPU-Deployment oder Validierung des externen Endpoints
      -> CPU-Compose-Stack
      -> generische Datenbankschemas
      -> profilspezifische Datenbankressourcen
      -> optionaler GND-Import
      -> validate-config
      -> doctor

## Dry-Run

Vor Änderungen an der Infrastruktur:

    museum-pipeline install --dry-run

Für eine bestehende GPU, auf der Modelle bereits vorhanden sind:

    museum-pipeline install --skip-model-download

## Doctor

Jederzeit:

    museum-pipeline doctor

Der Doctor prüft den aktuellen Installationsvertrag, statt ihn
stillschweigend zu reparieren.

## SSH-Host-Key-Verifikation

Für Managed-GPU-Installationen nutzt der Installer standardmäßig
`StrictHostKeyChecking=accept-new` (Trust-on-first-use): bequem, aber beim
allerersten Verbindungsaufbau zu einem Host theoretisch MITM-anfällig, weil
der präsentierte Host-Key ungeprüft akzeptiert wird.

Für ein gehärtetes Deployment kann der Host-Key vorab außerhalb dieses
Kanals verifiziert (z. B. über eine Server-Konsole, IPMI/iDRAC-Fingerabdruck
oder den Fingerabdruck des Hosting-Providers) und gepinnt werden:

    # Host-Key vorab einsammeln (noch ungeprüft, nur zum Vorbereiten der Datei)
    ssh-keyscan -H gpu-host.example.org > /pfad/zu/pinned-known-hosts

    # den eingesammelten Fingerabdruck GEGEN EINE UNABHÄNGIGE QUELLE prüfen
    # (Server-Konsole, Provider-Panel, o.ä.) — erst dann als vertrauenswürdig behandeln

    export SSH_STRICT_HOST_KEY_CHECKING=yes
    export SSH_KNOWN_HOSTS_FILE=/pfad/zu/pinned-known-hosts

    museum-pipeline install

Mit `SSH_STRICT_HOST_KEY_CHECKING=yes` bricht jede SSH-/SCP-Verbindung des
Installers ab, wenn der Host-Key nicht exakt in `SSH_KNOWN_HOSTS_FILE`
steht — inklusive späterer Neuinstallationen, falls sich der Host-Key
unerwartet ändert.

## Idempotenz

Der Installer ist auf Wiederholbarkeit ausgelegt.

Er nutzt:

- Docker-Compose-Sollzustand;
- `CREATE ... IF NOT EXISTS` / idempotentes SQL, wo mitgeliefert;
- persistente Docker-Volumes;
- persistente generierte Secrets;
- deterministische Profil-/Modell-/Hardware-/Workflow-Auswahl.

Ein erneuter Lauf generiert absichtlich keine neuen Zugangsdaten und ersetzt
keine Museumsprofile.

## Scope

Der erste Installer setzt voraus, dass OS-Voraussetzungen bereits vorhanden
sind.

Das ist beabsichtigt: Linux-Distributions-Provisionierung,
NVIDIA-Treiberinstallation und providerspezifische Cloud-APIs sind separate
Belange und dürfen nicht im Museums-Applikations-Installer versteckt werden.

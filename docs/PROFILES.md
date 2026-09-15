# Profile und Individualisierung

Das zentrale Prinzip lautet:

> Ein anderes Museum soll den Core nachnutzen können, ohne Python-Code unter
> `src/` ändern zu müssen.


# 1. Museum Profile

Ort:

    profiles/<museum>/

Ein Museumprofil beantwortet fachliche Fragen.

Zum Beispiel:

- Wo liegen die Quelldaten?
- Wie heißt die Objekt-ID?
- Welche Metadatenfelder existieren?
- Welche Felder fließen in Tagging, Emotion oder Themen ein?
- Wie wird das Bild gefunden?
- Welche Prompts gelten?
- Welche Schlagwortcluster existieren?
- Wird GND benutzt?
- Gibt es ein Wirkungsvokabular?
- Gibt es institutionelle Themen?


## Startpunkt für ein neues Museum

Verwende:

    profiles/_template/

als museumsagnostischen Starter.

Das öffentliche Stadtmuseum-Profil zeigt eine reale Core-/Emotion-Konfiguration,
enthält aber bewusst **keine institutionellen Themenschwerpunkte**. Für Topics
steht ausschließlich der Bauplan unter `profiles/_template/topics/` bereit.


# 2. Model Profile

Ort:

    models/<name>.yaml

Ein Model Profile beantwortet:

> Welche Modellrolle wird von welchem konkreten Modell übernommen?

Beispiele für Rollen:

    caption.primary
    caption.secondary
    caption.synthesis
    tagging.generator
    tagging.audit
    authority.gnd
    emotion.generator
    emotion.judge
    topics.generator
    topics.judge

Der fachliche Workflow referenziert Rollen und nicht direkt einen
Inferenzserver.


# 3. Hardware Profile

Ort:

    hardware/<name>.yaml

Ein Hardwareprofil beantwortet:

> Wie darf die Pipeline auf dieser kalibrierten Laufzeit parallel arbeiten?

Dazu gehören:

- Modellslots,
- Context-Pools,
- minimale Kontexte pro Slot,
- CPU-Worker,
- Service-Worker,
- besondere Phasenregeln.

Wichtig:

> Hardwarewerte dürfen nicht geraten und anschließend als "verified"
> veröffentlicht werden.

Das H100-Profil ist ein gemessener Referenzfall.


# 4. Workflow

Ort:

    workflows/<name>.yaml

Ein Workflow beantwortet:

> Welche fachlichen Module sollen laufen?

Mitgeliefert werden:

- `core`
- `core-emotion`
- `core-topics`
- `full`


# 5. Deployment-Konfiguration

Domains, IP-Adressen, Secrets, Ports oder Bucketnamen sind weder Museum- noch
Hardwareprofil.

Sie gehören in:

- `.env`
- deployment-spezifische Compose-Konfiguration
- Secret Management


# Was ein neues Museum typischerweise anpasst

## Fast immer

- `profiles/<museum>/profile.yaml`
- `metadata.yaml`
- Tagging-Regeln und Prompts


## Nur wenn gewünscht

- GND-Konfiguration
- eigenes Emotionsvokabular bzw. eigene Emotionsmethode (wenn Machine Heart nicht genutzt wird)
- Themenframework
- Taxonomie


## Nur bei anderer Modellstrategie

- `models/<name>.yaml`


## Nur bei anderer Hardware / anderer Laufzeit

- `hardware/<name>.yaml`
- entsprechendes Inferenzdeployment


# Was normalerweise nicht geändert werden sollte

    src/museum_pipeline/

Wenn ein neues Museum dort institutionsspezifischen Code einbauen muss, ist
das ein Hinweis auf eine fehlende Profil-Abstraktion.


# Beispiel: öffentliches Bild statt S3

Museum A:

    asset:
      mode: s3
      column: s3_url

Museum B:

    asset:
      mode: url
      column: image_url

Der restliche Workflow bleibt gleich.


# Beispiel: keine GND

Im Authority-Profil:

    enabled: false

Dann entfällt die GND-Anreicherung.

Ein anderes Authority-System ist nicht automatisch Teil der aktuellen
Referenzarchitektur.


# Beispiel: eigene Sammlungsthemen

Die Themen des Stadtmuseums werden nicht kopiert, nur weil dasselbe
Python-Paket benutzt wird.

Ein anderes Museum definiert:

- eigenes Framework,
- eigene Taxonomie,
- eigene Vokabulare,
- eigene Entscheidungsregeln.


# Profilierung ist auch Governance

Profile sind nicht nur Konfigurationsdateien.

Sie dokumentieren institutionelle Entscheidungen.

Damit kann später nachvollzogen werden:

- welche fachlichen Regeln galten,
- welche Modellrollen benutzt wurden,
- auf welcher Hardwarekonfiguration Ergebnisse erzeugt wurden,
- welcher Workflow aktiv war.

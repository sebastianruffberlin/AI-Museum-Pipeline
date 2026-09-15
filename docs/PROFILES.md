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


# Schritt für Schritt: ein neues Museum einrichten

Ausgangspunkt ist immer das museumsagnostische Starterprofil:

    museum-pipeline init-profile mein-museum

Der Profilname muss ein Slug sein (Kleinbuchstaben, Ziffern, Bindestriche,
beginnend mit einem Buchstaben, z. B. `mein-museum`). Der Befehl kopiert
`profiles/_template/` nach `profiles/mein-museum/` und trägt `id`/`name` im
neuen `profile.yaml` automatisch korrekt ein. Normale Anpassung sollte keine
Änderungen unter `src/` erfordern.

## 1. Metadaten

`profiles/<museum>/metadata.yaml` definiert Quelltabelle/-objekt, ID-Spalte,
Asset-Referenz, kanonisches Feld-Mapping und welche Felder welches Modul
sehen darf.

## 2. Kern-Tagging

Clusternamen in `tagging/profile.yaml`, deterministische Audit-/Repair-Regeln
in `tagging/policy.yaml`, Terminologie-/Debias-Regeln in
`tagging/debias_map.json`, institutionsspezifischer Prompt-Wortlaut unter
`prompts/`.

## 3. Emotion / Wirkungslesarten

Optional. Der Starter liefert den kompletten museumsagnostischen
Machine-Heart-Default mit, der mögliche *Wirkungen/Lesarten* von Aussagen
über den psychischen Zustand einer dargestellten Person trennt.
Unverändert nutzen, mit eigenem Vokabular/eigener Datenbank verbinden, oder
die Methode ganz ersetzen. Ein Workflow ohne `emotion` deaktiviert das Modul
vollständig. Siehe [`EMOTION_METHOD.md`](EMOTION_METHOD.md).

## 4. Institutionelle Themen

Optional. `topics/framework.md` und `topics/taxonomy.json` bereitstellen.
Siehe [`TOPIC_KNOWLEDGE_BASE.md`](TOPIC_KNOWLEDGE_BASE.md) für die getestete
Wissensstruktur und den Inhaltsvertrag. Keine institutionellen Themeninhalte
sind Teil des öffentlichen Repos.

## 5. Normdaten

Die Referenzintegration nutzt GND. `authority/profile.yaml: enabled: false`
setzen, wenn keine Normdaten-Anreicherung gewünscht ist.

## 6. Modelle und Hardware

Gehören nicht ins Museum Profile. Modellrollen-Mapping gehört nach
`models/`, Hardware-Parallelität und Context-Kapazität nach `hardware/`.

## 7. GPU-Deployment (falls `gpu.mode: managed`)

`gpu.deployment_path` in `deployment.yaml` hat **keinen** institutions-
spezifischen Default. Für den generischen Einstieg `infra/gpu/generic`
verwenden; für exakt kalibrierte H100-80GB-Hardware kann auch direkt auf
`infra/gpu/stadtmuseum-berlin/h100-80gb` verwiesen werden (echte, getestete
Referenzkonfiguration, kein museumsspezifischer Inhalt). Siehe
[`INSTALLER.md`](INSTALLER.md).


# Öffentliche semantische Defaults

Der öffentliche Starter liefert Machine Heart als optionale Emotion-Methode
mit; siehe `EMOTION_METHOD.md` für Datei-/Datenbankverträge und wie man die
Methode ersetzt.

Topics sind anders: Das Repository liefert nur Engine und Templates. Keine
institutionellen Themeninhalte sind enthalten. Ein Museum muss eigenes
Framework und eigene Taxonomie erstellen, bevor Topics aktiviert werden kann;
siehe `TOPIC_KNOWLEDGE_BASE.md`.

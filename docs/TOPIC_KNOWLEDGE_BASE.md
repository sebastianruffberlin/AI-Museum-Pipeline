# Aufbau einer institutionsspezifischen Themen-Wissensbasis

Das Topics-Modul ist eine **generische Engine**. Das öffentliche Repository
liefert bewusst **keine institutionellen Themenschwerpunkte und kein
zugrundeliegendes Strategiedokument**. Diese Inhalte gehören dem Museum, das
die Pipeline einsetzt.

Die Engine erwartet zwei institutionseigene Ressourcen: ein Framework in
Fließtext und eine kontrollierte Taxonomie. Sie führt dann einen
unabhängigen **Generator → Judge**-Prozess gegen jedes konfigurierte Thema
aus.

## Was getestet wurde

Die Methode wurde mit einer realen institutionellen Wissensbasis entwickelt
und getestet, die mehrere strategische Themen umfasste. Das private
Ausgangsdokument und die Themeninhalte sind nicht veröffentlicht.
Veröffentlicht ist hier der strukturelle Vertrag, der sich bewährt hat. In
der getesteten Implementierung hatte die Taxonomie **8 Themen, 64
Unterthemen und 104 kontrollierte Begriffe**. Diese Zahlen sind Beispiele
für eine funktionierende Größenordnung, **keine Anforderungen**.

Die getestete Wissensbasis enthielt pro Thema:

1. **Erkenntnisinteresse / Scope** — was das Thema über Objekte aufdecken soll;
2. **includes** — wiederkehrende Facetten und relevante Beziehungstypen;
3. **excludes / not sufficient** — typische Falsch-Positive;
4. **Evidenzregeln** — was ein einzelnes Objekt tatsächlich belegen muss;
5. optionale **Retrieval-Anker** — Orte, Ereignisse, Personen, Organisationen
   oder Begriffe, die beim Auffinden helfen, aber nie allein eine Beziehung
   beweisen;
6. **Sensitivitäts-/Reviewregeln** — Fälle, die strengere Evidenz oder
   Review erfordern.

Die Taxonomie lieferte dann stabile IDs für Unterthemen und kontrollierte
Begriffe sowie `use_when`/`do_not_use_when`-Hinweise.

## Benötigte Dateien

Innerhalb von `profiles/<museum>/topics/` anlegen:

```text
profile.yaml
framework.md
taxonomy.json
```

Ausgangspunkt ist `profiles/_template/topics/`. Das Starterprofil aktiviert
Topics nicht automatisch. Sobald die Inhalte existieren, ergänzen:

```yaml
topics:
  config: topics/profile.yaml
```

in `profiles/<museum>/profile.yaml`.

## `framework.md`

Einen Abschnitt pro institutionellem Thema schreiben. Mindestens
beschreiben:

```text
THEMA
  Erkenntnisinteresse / Scope
  includes
  not sufficient / exclusions
  Evidenzregel
  optionale Retrieval-Anker
  Sensitivitäts-/Reviewregeln
```

Die zentrale Regel: **Framework-Wissen ist Kontext, kein Beleg über ein
einzelnes Objekt.** Ein im Framework genanntes Datum, ein Ort, eine Person
oder ein Begriff kann dem Modell helfen, das Thema zu verstehen — beweist
aber nicht, dass ein Objekt dazugehört.

## `taxonomy.json`

Der Loader akzeptiert eine Liste von Themen-Objekten. Eine robuste
Themendefinition enthält:

```json
[
  {
    "slug": "THEMA_SLUG",
    "label": "THEMA_LABEL",
    "subtopics": [
      {
        "id": "THEMA_01",
        "label": "UNTERTHEMA_LABEL",
        "definition": "Institutionseigene Definition",
        "positive_indicators": [],
        "not_sufficient": [],
        "active": true,
        "version": "1.0"
      }
    ],
    "vocabulary": [
      {
        "id": "THEMA_SW_01",
        "label": "KONTROLLIERTER_BEGRIFF",
        "subtopics": ["THEMA_01"],
        "use_when": "Objektspezifische Evidenzregel",
        "do_not_use_when": "Falsch-Positiv-Regel",
        "origin": "institutional",
        "active": true,
        "version": "1.0"
      }
    ]
  }
]
```

Stabile IDs sind wichtiger als die exakte Feldanzahl. Generator und Judge
müssen unterscheiden können: **was das Thema bedeutet**, **was als
Objektbeleg zählt**, und **welche kontrollierten Begriffe erlaubt sind**.

## Generator und Judge

Die mitgelieferten generischen Topic-Prompts implementieren zwei Rollen:

1. **Generator** — prüft das Objekt gegen alle konfigurierten Themen und
   schlägt nur objektspezifische Beziehungen mit Evidenz, Unterthemen und
   kontrollierten Begriffen vor.
2. **Judge** — bewertet alle konfigurierten Themen unabhängig erneut und
   kann eine Beziehung bestätigen, korrigieren, herabstufen, entfernen oder
   ergänzen.

Die Methode trennt bewusst das institutionelle Wissen von der Modelllogik.
Ein Museum kann sein Framework/seine Taxonomie deshalb ersetzen, ohne `src/`
zu verändern.

## Datenbankbasiertes Wissen ist ebenfalls möglich

`TopicsModule` unterstützt auch `resources.source: database`. In diesem
Fall muss die konfigurierte Query eine Zeile zurückgeben, die enthält:

- `framework` — die Fließtext-Wissensbasis als Text;
- `taxonomy` (oder `taxonomie`) — die Taxonomie als JSON oder JSON-String.

Das interne Datenbankschema ist institutionsdefiniert; nur dieser
Adaptervertrag wird von der Pipeline verlangt.

## Alte Datenbank-Migrationsnamen

Frische Installationen nutzen die generischen Schemas
`museum.topic_assignments` und `museum.topic_runs`.
`database/migrations/002_topics_generic.sql` erwähnt zusätzlich historische
deutsche Tabellennamen wie `schwerpunkt_bezug`, ausschließlich damit
bestehende Installationen migriert werden können. Diese Bezeichner
enthalten kein Themenwissen und sind **nicht** Teil des
Topics-Bauvertrags.

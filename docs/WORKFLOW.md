# Workflow: Was passiert mit einem Museumsobjekt?

Dieses Dokument beschreibt den Flow gleichzeitig aus zwei Perspektiven:

- **museologisch:** Warum gibt es den Schritt?
- **technisch:** Was tut die Pipeline konkret?


## Ausgangspunkt

Ein Museumsobjekt besteht für die Pipeline zunächst aus zwei Informationsarten:

1. **vorhandene Museumsmetadaten**
2. **mindestens einem digitalen Bild/Asset**

Die Metadaten stammen aus einem externen Primärsystem oder einer
bereitgestellten Datenbanktabelle.

Die Pipeline besitzt das Quellsystem nicht.

Das Museumprofil übersetzt institutionsspezifische Felder in eine kanonische
Form.

Beispiel:

    lokale Spalte "objektbezeichnung"
        ↓
    kanonisches Feld "object_type"

Dadurch muss der Core keine Spaltennamen einzelner Museen kennen.


# Gesamtfluss

    Quelle
      │
      ├── Metadaten
      └── Bild
           │
           ▼
    1. image_embeddings
           │
    2. image_features
           │
    3. captions
           │
    4. tagging
           │
           ├── optional: GND
           │
    5. emotion      optional
           │
    6. topics       optional
           │
    7. text_embeddings
           │
           ▼
    getrennte Enrichment-Daten


# 1. Bild-Embeddings

## Museologische Idee

Museumsobjekte können sich visuell ähneln, obwohl ihre historischen
Metadaten sehr unterschiedlich sind.

Eine klassische Datenbank kann diese Beziehung oft nicht ausdrücken.

Embeddings ermöglichen Fragen wie:

- Welche Objekte sehen diesem Objekt ähnlich?
- Welche unerwarteten visuellen Nachbarschaften gibt es?
- Welche visuellen Cluster gibt es quer durch Teilsammlungen?
- Welche Objekte sind visuelle Ausreißer?

Ein Embedding ist dabei **keine Interpretation des Objekts**.

Es ist eine mathematische Repräsentation für Ähnlichkeitsberechnungen.


## Technische Umsetzung

Der Referenzdienst berechnet zwei Bildvektoren:

- SigLIP2
- DINOv3

Sie erfassen unterschiedliche Aspekte visueller Ähnlichkeit.

Die Ergebnisse werden in `museum.embeddings` gespeichert.


# 2. Technische Bildmerkmale

## Museologische Idee

Nicht jede Erschließung braucht ein generatives Sprachmodell.

Bestimmte Merkmale können reproduzierbar aus Pixeln berechnet werden.

Solche Werte sind besonders nützlich für:

- Facetten,
- visuelle Exploration,
- Farbsuche,
- Sortierung,
- kreative digitale Formate.


## Technische Umsetzung

Das Modul `image_features` analysiert das geladene Bild mit klassischer
Bildverarbeitung und schreibt abgeleitete Werte nach
`museum.enrichment_derived`.

Dieser Schritt ist vom LLM unabhängig.


# 3. Captions: einen belastbaren visuellen Befund erzeugen

## Museologische Idee

Ein einzelnes Vision-LLM soll nicht allein bestimmen, was auf einem
Museumsbild zu sehen ist.

Der Referenzflow nutzt deshalb mehrere Modellperspektiven.

Das Ziel ist nicht:

> eine schöne Bildunterschrift schreiben

sondern:

> einen möglichst belastbaren visuellen Arbeitsbefund erzeugen, der für
> nachfolgende Erschließungsschritte benutzt werden kann.


## Technische Umsetzung

Der Referenzflow arbeitet in drei Schritten:

    Vision-Modell A
          │
          ├──────┐
          │      │
    Vision-Modell B
          │      │
          └──┬───┘
             ▼
         Synthese
             │
             ▼
       Master Caption

Rollen im Referenzmodellprofil:

- `caption.primary`
- `caption.secondary`
- `caption.synthesis`

Die Master Caption wird gemeinsam mit den Einzelbefunden gespeichert.


# 4. Tagging: strukturierte Erschließung

## Museologische Idee

Freie KI-Schlagworte sind für eine Museumssammlung nur begrenzt hilfreich,
wenn nicht nachvollziehbar ist:

- warum ein Begriff vergeben wurde,
- worauf er sich stützt,
- ob er problematische Zuschreibungen enthält,
- ob er für Suche und Recherche geeignet ist.

Der Stadtmuseum-Referenzflow trennt deshalb Erzeugung, Prüfung und
Normdatenabgleich.


## Technische Logik

Vereinfacht:

    Metadaten + Bild + Caption
              │
              ▼
           Generator
              │
              ▼
        strukturierte Begriffe
              │
              ▼
             Audit
              │
         ┌────┴────┐
         │         │
       grün      zurückhalten
         │
         ▼
      optional
       GND


Die Pipeline speichert nicht nur den Begriff, sondern auch
Begründungs-/Prüfinformationen und Status.


## GND

Nur Begriffe, die für den Normdatenabgleich geeignet und fachlich
durchgelassen wurden, werden gegen die GND geprüft.

Der Ablauf ist:

    erzeugter Begriff
          │
          ▼
    OpenSearch-Retrieval
    mehrere GND-Kandidaten
          │
          ▼
       LLM-Prüfung
          │
       ┌──┴───┐
       │      │
      Match  no_match

Eine GND-ID wird nicht erfunden.

Ein nicht passender GND-Treffer ist schlechter als kein Treffer.


# 5. Emotion / Machine Heart

Dieses Modul ist optional.

## Museologische Idee

Hier geht es ausdrücklich **nicht** um Emotionserkennung.

Die Pipeline behauptet weder:

> Das Objekt ist melancholisch.

noch:

> Die dargestellte Person ist traurig.

Stattdessen lautet die epistemische Form:

> Das Objekt **kann wirken als** ...

Der mitgelieferte Machine-Heart-Standard bezeichnet diese Ergebnisse deshalb als
`machine_proposal`.


## Vier Ebenen

Der mitgelieferte Machine-Heart-Standard trennt:

A. sichtbarer Befund
B. dargestellte Situation
C. mögliche Wirkung
D. psychischer Zustand einer Person

Getaggt wird nur Ebene C.

Ebene D wird nicht erschlossen.


## Generator + Judge

Der Generator schlägt mögliche Wirkungslesarten aus einem kontrollierten
Vokabular vor.

Ein zweites Modell prüft:

- Evidenz,
- Leitplanken,
- Psychologisierung,
- Verwechslung von Form und Wirkung,
- unzulässige Ableitungen.

Auch Spannungen sind zulässig.

Ein Objekt kann gleichzeitig gegenläufige Wirkungen tragen.


# 6. Themenbezüge

Dieses Modul ist optional.

## Museologische Idee

Institutionelle Sammlungsschwerpunkte sind keine neutralen Eigenschaften
eines Objekts.

Sie sind kuratorische und strategische Rahmungen.

Deshalb lautet die Frage nicht:

> Welchem Thema gehört dieses Objekt?

sondern:

> Zu welchen Themen lässt sich ein nachvollziehbarer Bezug herstellen?

Mehrfachbezüge sind ausdrücklich möglich.


## Technische Umsetzung

Das Modul arbeitet mit:

- institutionellem Framework,
- Taxonomie,
- kontrolliertem Vokabular,
- Objektmetadaten,
- Master Caption,
- bereits geprüften Inhaltsbegriffen.

Ein Generator schlägt Beziehungen vor.

Ein Judge prüft sie.

Das Topics-Modul prüft alle im jeweiligen Museumsprofil definierten Schwerpunkte. Diese
Themen sind **kein Bestandteil des generischen Core**.


# 7. Text-Embeddings

## Museologische Idee

Klassische Volltextsuche findet gleiche Wörter.

Semantische Suche soll zusätzlich ähnliche Bedeutungen finden.

Dafür erzeugt die Pipeline mehrere kontrollierte Textrepräsentationen eines Objekts.


## Technische Umsetzung

Das Museumprofil bestimmt, welche kanonischen Metadatenfelder in welche
Textrepräsentation einfließen.

Der Referenzdienst nutzt BGE-M3 und erzeugt:

- dichte Vektoren,
- optional Sparse-Gewichte.

Die Vektoren landen ebenfalls in `museum.embeddings`.


# Workflow-Presets

Die Pipeline liefert vier Presets.

## `core`

    image_embeddings
    image_features
    captions
    tagging
    text_embeddings

Ohne Emotion und ohne institutionelle Themen.


## `core-emotion`

`core` plus Emotion.


## `core-topics`

`core` plus Themenbezüge.


## `full`

Alle Module.


# Was ist Ergebnis und was Quelle?

Der Flow hält diese Ebenen getrennt:

    Museumsquelle
        ↓
    maschineller Befund
        ↓
    maschinelle Erschließung
        ↓
    maschinelle Interpretation

Je weiter man nach unten geht, desto wichtiger werden:

- Provenienz,
- Begründung,
- kontrollierte Vokabulare,
- Modalisierung,
- institutionelle Leitplanken.

Diese Trennung ist bewusst Teil der Architektur und nicht nur
Dokumentationsstil.

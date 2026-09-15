# Wirkungslesarten: Machine-Heart-Default und eigene Emotionssysteme

Das Emotion-Modul ist optional, aber anders als institutionelle Topics
liefert das Repository eine **vollständige museumsagnostische
Standardmethode** mit: **Machine Heart**.

Ein Museum hat damit drei Optionen:

1. **aus** — ein Workflow ohne Emotion nutzen (`core` oder `core-topics`);
2. **Machine-Heart-Default** — die mitgelieferte Methode und das
   kontrollierte Vokabular unverändert nutzen;
3. **eigenes Emotionssystem** — die Pipeline-Schnittstelle beibehalten, aber
   Vokabular und ggf. Prompts/Methodenkonfiguration ersetzen.

## Was der Default enthält

`profiles/_template/emotion/` enthält die vollständige veröffentlichte
redaktionelle Ressource:

- `concepts.json` — **146 kuratierte Konzepte** mit Rollen, Lesemodi,
  semantischen Domänen, Evidenz-/Kontextanforderungen, Ausschlüssen,
  theoretischer/redaktioneller Provenienz und PAD-Metadaten;
- `vocabulary.runtime.json` — die **121 `resonance_reading`-Konzepte**, die
  der Produktions-Query tatsächlich an Generator/Judge weitergibt;
- `profile.yaml` — Konfiguration der Machine-Heart-Methode.

Der Unterschied 146 → 121 ist beabsichtigt, keine reduzierte öffentliche
Ausgabe. Die Produktions-Runtime-Query wählte ausschließlich Konzepte mit
`concept_role = resonance_reading` und schloss veraltete Konzepte aus. Die
übrigen Konzepte bleiben Teil des redaktionellen Wissensmodells, werden aber
aktuell nicht automatisch in den Generator-/Judge-Prompt-Kontext injiziert
(siehe [`MUSEUM_DESIGN_DECISIONS.md`](MUSEUM_DESIGN_DECISIONS.md), Kapitel
zu Machine Heart, für die genaue Begründung).

Die generischen Machine-Heart-Generator-/Judge-Prompts sind im Starterprofil
enthalten. `core-emotion` aktiviert den Schritt.

## Runtime-Vokabular-Vertrag

Das Emotion-Modul benötigt letztlich ein JSON-Array von Konzepten. Jedes
Runtime-Konzept muss stabile Semantik haben. Die minimal notwendigen Felder
sind:

```json
{
  "concept_id": "stabile_maschinen_id",
  "begriff": "Menschenlesbares Label",
  "definition": "Was diese Lesart bedeutet",
  "nicht_verwenden_wenn": ["Explizite Falsch-Positiv-Regel"]
}
```

Anforderungen:

- `concept_id` muss eindeutig und über Läufe hinweg stabil sein;
- `begriff` muss für die konfigurierte Ausgabesprache geeignet sein;
- `definition` muss das Konzept von benachbarten Lesarten abgrenzen;
- `nicht_verwenden_wenn` ist technisch optional, aber dringend empfohlen;
- das resultierende aktive Vokabular darf nicht leer sein;
- `vocabulary_version` in `emotion/profile.yaml` sollte sich ändern, sobald
  sich Semantik oder Konzeptbestand ändern.

## Dateibasiertes eigenes Vokabular

Die einfachste Anpassung:

```yaml
resources:
  source: file
  file_fallback: vocabulary.runtime.json
```

Die Runtime-JSON ersetzen und `vocabulary_version` erhöhen. Ändern sich nur
die kontrollierten Begriffe, können die mitgelieferten Machine-Heart-Prompts
weiterverwendet werden.

## Datenbankbasiertes eigenes Vokabular

Ein Museum kann sein eigenes Emotionsvokabular in PostgreSQL oder einer
anderen, per PostgreSQL-Query erreichbaren Quelle halten. Die Pipeline
verlangt **kein** bestimmtes internes Tabellenschema. Die konfigurierte
SQL-Query ist der Adapter.

Verwenden:

```yaml
resources:
  source: database
  vocabulary_query: vocabulary.sql
  file_fallback: vocabulary.runtime.json
```

Der Query-Vertrag ist knapp, aber strikt:

- genau eine logische Zeile zurückgeben;
- eine Spalte namens `value` bereitstellen;
- `value` enthält das vollständige Runtime-Vokabular als JSON-Array oder
  JSON-Text;
- jedes Konzept folgt dem oben genannten Runtime-Vokabular-Vertrag;
- das Ergebnis muss für eine gegebene Vokabularversion deterministisch sein.

`profiles/_template/emotion/vocabulary-query.example.sql` zeigt das
Adapter-Muster. Die interne redaktionelle Datenbank eines Museums kann
deutlich mehr Felder enthalten.

## Empfohlenes Redaktionsmodell für ein neues Emotionssystem

Machine Hearts 146-Konzepte-Redaktionsmodell ist nicht verpflichtend, aber
ein ernsthafter Ersatz sollte mindestens erfassen können:

- stabile Konzept-ID + bevorzugtes Label + alternative Labels;
- Definition;
- konzeptuelle Rolle / Lesart-Typ;
- Kontext- oder Evidenzanforderung;
- Abgrenzung zu benachbarten Konzepten;
- `do_not_use_when` / Falsch-Positiv-Regeln;
- kulturelle Hinweise oder Geltungsbereich, wo relevant;
- Provenienz / theoretische oder redaktionelle Grundlage;
- redaktioneller Status und Versionierung.

Je interpretativer das Vokabular, desto wichtiger werden explizite
Ausschlüsse und Provenienz.

## Die Methode ersetzen, nicht nur das Vokabular

Wenn der Ansatz eines Museums konzeptionell von Machine Heart abweicht,
sollten die Emotion-Prompt-/Konfigurationsdateien ins eigene Profil kopiert
und gemeinsam geändert werden. Das Python-Modul verlangt lediglich, dass der
konfigurierte Generator/Judge die veröffentlichten JSON-Schemas und die
Runtime-Vokabular-Schnittstelle einhält.

Ein eigenes System sollte deshalb als **neue Methodenimplementierung**
behandelt werden, nicht nur als umbenanntes Machine-Heart-Vokabular.

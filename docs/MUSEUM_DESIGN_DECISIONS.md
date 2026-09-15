# Museumsseitige Design-Entscheidungen

Dieses Dokument erklärt die wichtigsten **museumsspezifischen und
museumsmethodologischen Entscheidungen**, die mit dem Referenzprofil
mitgeliefert werden.

Es existiert, weil eine nachnutzbare Pipeline unterscheiden sollte zwischen:

- Software-Verträgen, die tatsächlich generisch sind;
- Methoden, die bewusst als nachnutzbare Defaults mitgeliefert werden;
- Entscheidungen, die im getesteten Museumsworkflow funktioniert haben, aber
  keine universellen Fachstandards sind;
- Wissen, das jede Institution selbst erstellen muss.

## Referenzprofil und Starter-Template

Zwei öffentliche Profil-Ebenen sind bewusst vorhanden:

```text
profiles/_template/
    generalisierte Starter-Konfiguration

profiles/stadtmuseum-berlin/
    öffentliche Referenzkonfiguration, abgeleitet aus der getesteten Implementierung
```

Diese Unterscheidung ist beim Lesen der Prompts wichtig. Das Starter-Template
entfernt institutionsspezifischen Größen-/Kontext-Wortlaut, wo möglich. Das
öffentliche Referenzprofil behält Teile des realen getesteten Wortlauts,
damit Design-Entscheidungen nachvollzogen werden können. Keines von beiden
ist ein normativer Museumsstandard.

Das Referenzprofil darf Methodenentscheidungen wie Tagging-Policy,
GND-Setup und Machine Heart veröffentlichen, weil diese nachnutzbar bzw.
einsehbar sein sollen. Es veröffentlicht **nicht** die institutionsspezifische
Topics-Wissensbasis oder das private Dokument dahinter.

Kurzfassung:

| Bereich | Was das Repository liefert | Wie damit umgehen |
| --- | --- | --- |
| 11 Schlagwortcluster | vollständiges getestetes Referenzdesign | nützlicher Default, konfigurierbar, **keine universelle Museumsontologie** |
| Keyword-Generator + Audit + Policy | vollständige getestete Methode | nachnutzbare Referenzmethode, anpassen wo lokale Policy abweicht |
| Farbextraktion | deterministische Bildmethode | nachnutzbare technische Schicht |
| Farbbenennung | mitgelieferte Referenz-/Such-Vokabularschicht | optionale Nachbearbeitung; Quelle/Provenienz ist wichtig |
| Machine Heart | vollständiger museumsagnostischer Default | optionale nachnutzbare Methode oder durch eigenes Emotionssystem ersetzbar |
| Topics | nur generische Engine + Bauvertrag | **Museum muss alle Themeninhalte selbst liefern** |
| GND | optionaler Adapter | nützliche Normdatenschicht in geeigneten Kontexten, nie verpflichtend |

---

# 1. Warum sind Schlagwörter in 11 Cluster aufgeteilt?

Das Default-Tagging-Profil nutzt:

1. `Objekttyp`
2. `Thema_Phänomen`
3. `Inhalt_Motiv`
4. `Funktion_Zweck`
5. `Visuelle_Merkmale`
6. `Form_Gestalt`
7. `Bestandteile`
8. `Gebrauchskontext`
9. `Kultureller_Kontext`
10. `Emotion_Atmosphäre`
11. `Farbe_Nuancen`

## 1.1 Kein Anspruch auf einen Erschließungsstandard

Die Zahl **11** ist in diesem Repository nicht aus einer veröffentlichten
Museumsontologie abgeleitet und sollte nicht als theoretisch kanonisch
gelesen werden.

Die Cluster sind ein pragmatisches Design, das aus dem getesteten Ziel
entstand:

> öffentlich nutzbare Erschließungsbegriffe aus heterogener
> Museumsdokumentation und Bildern erzeugen, ohne unterschiedliche Arten von
> Aussagen in eine flache Schlagwortliste zu quetschen.

Sie stehen damit näher an **semantischen Suchfacetten** als an einem Ersatz
für einen Sammlungsthesaurus.

Ein Museum kann sie beibehalten, umbenennen, Cluster hinzufügen/entfernen
oder ein anderes System bauen, solange Prompts, Policy und nachgelagerte
Erwartungen konsistent bleiben.

## 1.2 Das Problem einer flachen Schlagwortliste

Ohne semantische Trennung könnte ein Ergebnis mischen:

```text
Fotografie
Straßenbahn
öffentlicher Nahverkehr
Straßenleben
Rechteck
verblasst
blau
```

Alles kann nützlich sein, aber es beantwortet unterschiedliche Fragen.

Das Cluster-Design trennt diese Fragen:

| Cluster | Beantwortet welche Frage | Warum es existiert |
| --- | --- | --- |
| `Objekttyp` | Was ist das übergeordnete physische/dokumentarische Objekt? | gibt sofortige Objektorientierung |
| `Thema_Phänomen` | Welches übergeordnete Subjekt oder gesellschaftlich-historische Phänomen ist beteiligt? | trennt abstraktes Subjekt vom Dargestellten |
| `Inhalt_Motiv` | Was ist konkret abgebildet oder benannt? | unterstützt wörtliche Motiv-/Objektsuche |
| `Funktion_Zweck` | Wofür ist es / welche Funktion oder Handlung ist beteiligt? | trennt Zweck von Typ und Subjekt |
| `Visuelle_Merkmale` | Welcher sichtbare Zustand/welche Erscheinung ist direkt beobachtbar? | erfasst öffentliche visuelle Suchbegriffe, die oft in Katalogen fehlen |
| `Form_Gestalt` | Was ist die Form oder Geometrie? | macht Form suchbar, ohne sie mit Zustand zu verwechseln |
| `Bestandteile` | Welche nennenswerten Teile sind vorhanden? | unterstützt Teil-Ganzes-Erschließung |
| `Gebrauchskontext` | In welcher Aktivität/Lebenswelt/Nutzungssituation tritt es auf? | erfasst soziale Praxis statt nur physischer Funktion |
| `Kultureller_Kontext` | Welcher historisch/gesellschaftlich spezifische Kontext ist tatsächlich belegt? | erlaubt Kontext bei hoher Evidenzschwelle |
| `Emotion_Atmosphäre` | Welcher einfache, stark belegte Atmosphäre-Begriff trifft zu? | gibt ein leichtgewichtiges Erschließungsvokabular, keine vollständige Emotionsanalyse |
| `Farbe_Nuancen` | Welche Farbwörter beschreiben Objekt/Bild? | gibt einen sprachlichen Farbsuchkanal |

## 1.3 Die Cluster sollen semantisches Auslaufen reduzieren

Der Referenzprompt enthält explizite Anti-Redundanz-Regeln. Ein Begriff
sollte normalerweise in dem Cluster erscheinen, in dem er semantisch am
stärksten ist, statt überall kopiert zu werden.

Das ermöglicht zum Beispiel die Unterscheidung von:

```text
Gegenstand         ≠ Subjekt
Subjekt            ≠ dargestelltes Motiv
Motiv              ≠ Funktion
Funktion           ≠ Nutzungskontext
visueller Zustand  ≠ Form
Form               ≠ Farbe
historischer Kontext ≠ aus dem Erscheinungsbild erschlossene Identität
```

Die Unterscheidung ist sowohl für Qualitätskontrolle als auch für
Suchoberflächen nützlich.

## 1.4 Das Cluster reist mit dem Schlagwort

Das Persistenzmodell speichert `cluster` neben jedem Schlagwort. Der
optionale GND-Adapter erhält ebenfalls Begriff und Cluster.

Das bedeutet, semantischer Kontext überlebt über den Prompt hinaus und kann
genutzt werden für:

- Facettierung;
- Audit (`FALSCHER_CLUSTER`);
- Normdaten-Abgleich;
- Suchgewichtung;
- spätere Auswertung.

## 1.5 Warum `Emotion_Atmosphäre` neben Machine Heart existiert

Das Schlagwort-Cluster ist bewusst flach gehalten.

Es ist für einfache, stark belegte Suchbegriffe gedacht, die sich wie
normale Schlagwörter verhalten. Es wird nach denselben Regeln auditiert wie
der Rest des Schlagwortsets.

Machine Heart ist eine **andere Schicht**:

- kontrolliertes affektives Vokabular;
- explizite Lesart-Scopes;
- Evidenz pro Lesart;
- mögliche Gegenevidenz/Spannung;
- Generator + unabhängiger Judge;
- keine Psychologisierung dargestellter Personen.

Ein Museum kann daher Atmosphäre-Schlagwörter nutzen, ohne Machine Heart zu
aktivieren, oder Machine Heart nutzen und trotzdem die normale
Erschließungsschicht behalten.

## 1.6 Warum `Farbe_Nuancen` neben deterministischer Farbanalyse existiert

Das Schlagwort-Cluster ist eine **sprachliche/multimodale Aussage**, die vom
Keyword-Modell erzeugt wird.

Der Bildmerkmale-Pfad ist eine **aus Pixeln abgeleitete Messung**.

Beide zu behalten erlaubt es, zwei unterschiedliche Signale zu bewahren:

```text
was der multimodale Sprachprozess die Farbe nennt
versus
was deterministische LAB-Analyse in den Pixeln misst
```

Für reproduzierbare Farbfacetten ist der deterministische Pfad die stärkere
Quelle. Für öffentlichsprachliche Erschließung kann das sprachliche
Schlagwort trotzdem nützlich sein.

---

# 2. Warum ist der Keyword-Generator-Prompt so aufgebaut?

Der mitgelieferte Generator-Prompt ist bewusst meinungsstark. Er ist nicht
nur eine Anfrage nach "guten Museums-Tags".

Er kodiert die getestete Erschließungspolitik.

## 2.1 Die primäre Nutzerin ist keine Fachperson

Der Referenzprompt definiert die Zielgruppe explizit als Menschen, die
weder die Sammlungsstruktur noch Fachterminologie kennen.

Das führt zu zwei Kernregeln.

### Folksonomie-Regel

Das Modell soll an plausible Alltagssuchsprache denken, nicht nur an
internes Fachvokabular.

### Brückenregel

Ein Fachbegriff sollte von einem verständlichen Oberbegriff begleitet
werden, wenn diese Brücke für die Auffindbarkeit nötig ist.

Der Zweck ist nicht, Fachlichkeit zu entfernen. Es geht darum, eine Brücke
zwischen Fachdokumentation und öffentlicher Recherche zu bauen.

## 2.2 Der Prompt erhält mehrere Evidenzkanäle

Der Tagging-Schritt kann nutzen:

- Originalbild;
- konsolidierte `master_caption`;
- rohe visuelle Beobachtung A;
- rohe visuelle Beobachtung B;
- Museums-Quellmetadaten.

Der Prompt enthält eine Konfliktpolitik, weil diese Quellen widersprüchlich
oder asymmetrisch sein können.

Das vorgesehene Verhalten:

- Museumsmetadaten für dokumentierte Fakten nutzen, die visuell nicht
  sichtbar sind;
- offensichtliche visuelle Eigenschaften ergänzen, die historische
  Dokumentation nie erfasst hat;
- unsichere visuelle Beobachtungen vorsichtig behandeln;
- nie einen Fakt erfinden, der in keinem der Evidenzkanäle existiert.

## 2.3 Der Prompt kopiert bewusst nicht jedes Quellfeld in Schlagwörter

Die Default-Erschließungspolitik schließt mehrere Klassen aus, die normalerweise
in strukturierte Katalogfelder gehören statt in freie Erschließungs-Tags:

- reines Material;
- Herstellungstechnik;
- Daten/Jahrhunderte;
- bloße geografische Namen;
- Künstler-/Personennamen.

Das ist eine Design-Entscheidung, keine Aussage, dass diese Daten
unwichtig sind. Sie bleiben als strukturierte Metadaten verfügbar. Die
Anreicherungsschicht soll neuen Erschließungswert hinzufügen, statt die
Katalogzeile als Tokens zu duplizieren.

## 2.4 Singular, Substantive und kontrollierte Granularität

Der Prompt bevorzugt Substantive im Singular und vermeidet unkontrollierte
Adjektivformen oder improvisierte Komposita.

Die Gründe sind operativ:

- einfachere Deduplizierung;
- stabilerer Normdaten-Abgleich;
- sauberere Facetten;
- konsistenteres Erschließungsvokabular.

Der Prompt erlaubt sorgfältig definierte Ausnahmen, z. B. direkt
beobachtbare Zustände in `Visuelle_Merkmale`.

## 2.5 Jedes Schlagwort muss sich selbst erklären

Der Generator gibt aus:

```json
{
  "term": "...",
  "why": "kurze evidenzbasierte Begründung"
}
```

Das `why`-Feld ist ein Selbstdisziplinierungsmechanismus und ein
Audit-Input.

Kann der Generator keine vertretbare Evidenzgrundlage formulieren, sagt die
Referenzmethode, dass der Begriff nicht ausgegeben werden soll.

## 2.6 Kritische/dekoloniale Prüfung ist evidenzgebunden

Der Referenzprompt enthält Prüfungen auf koloniale/rassistische
Darstellung, Gewalt, problematische Provenienzsprache und sensibles
Material.

Er enthält außerdem explizit eine **Anti-Überkennzeichnungs**-Regel.

Die Absicht:

> Macht/Gewalt benennen, wo Objekt oder Dokumentation es hergeben — aber
> nicht jedem neutralen Objekt eine erfundene kritische Erzählung
> aufzwingen.

Der Prompt versucht außerdem, zeitlose ethnisierende Beschreibung zu
verhindern, und verlangt historisch verortete Formulierungen.

Andere Institutionen dürfen diese Policy-Sprache sinnvoll anpassen. Der
wichtige architektonische Punkt ist, dass diese Policy im Museumsprofil
sichtbar ist statt im Anwendungscode versteckt.

---

# 3. Warum gibt es einen Audit/Judge-Prompt als zweiten Modellschritt?

Beim normalen Schlagwort-Tagging ist das zweite Modell am besten als
**Fehlerklassen-Audit** zu verstehen, nicht als zweiter freier Generator.

## 3.1 Generator und Prüfer haben unterschiedliche Aufgaben

Der Generator versucht, unter den Profilregeln möglichst viele nützliche
Erschließungsbegriffe zu maximieren.

Das Audit ist bewusst enger gefasst. Es prüft die vorgeschlagenen Begriffe
gegen Bild, Caption, Metadaten und Policy und vergibt feste
Fehlerklassen.

Der Audit-Prompt sagt explizit, dass er **keinen** finalen
Grün/Gelb/Rot-Status vergeben darf.

## 3.2 Feste Fehlerklassen machen Modellkritik handlungsfähig

Der aktuelle Audit-Katalog umfasst:

```text
PLURAL
ADJEKTIV
KOMPOSITUM
FEHLENDE_BRUECKE
FALSCHER_CLUSTER
KEINE_EVIDENZ
HALLUZINATION
MATERIAL_PUR
MATERIAL_KOMPOSITUM
DATIERUNG
GEOGRAFIE_EIGENNAME
SPEKULATION_ZIRKEL
ASYMMETRIE
REDUNDANZ
```

Das ist nützlicher als eine generische "sieht gut aus / sieht schlecht
aus"-Bewertung, weil die nächste Stufe deterministisch auf der
Klassifikation handeln kann.

## 3.3 Eine deterministische Policy entscheidet über die Konsequenz

`tagging/policy.yaml` gruppiert Fehlerklassen zu Aktionen.

Konzeptionell:

```text
kein Fehler
  → keep

reparierbares Formproblem
  → repair

falsches semantisches Cluster
  → move

nicht belegt / halluziniert / verbotener Inhalt
  → discard
```

Das ist eine bewusste Trennung von Verantwortlichkeiten:

```text
LLM: die Art des Problems identifizieren
Code: die operative Policy anwenden
```

Der Prüfer kann den Workflow damit weniger leicht stillschweigend von
Objekt zu Objekt neu definieren.

## 3.4 Warum ein separates Repair-Modell?

Manche Probleme bedeuten, dass das zugrundeliegende Konzept nützlich ist,
aber die Oberflächenform falsch.

Beispiele:

- Plural → Singular;
- Adjektiv → Substantiv;
- zerlegbares Kompositum;
- fehlende Laiensprache-Brücke;
- material-präfigiertes Kompositum, bei dem das Nicht-Material-Substantiv
  nützlich bleibt.

Die Policy kann nur diese Begriffe zur Reparatur schicken. Eine
zurückgewiesene Halluzination wird nicht zu einem neuen erfundenen Fakt
"repariert".

## 3.5 Warum kommt GND erst nach Audit/Repair?

Normdaten-Abgleich sollte einen schlechten generierten Begriff nicht
legitimieren.

Nur Begriffe, die die Qualitätspolicy überstehen, werden an die optionale
GND-Retrieval-/Abgleichsstufe geschickt.

Das vermeidet einen häufigen Fehlerfall, bei dem ein Modell einen
zweifelhaften Begriff erfindet und ein nachfolgender Normdaten-Lookup die
Ausgabe autoritativer wirken lässt, nur weil ein plausibler Identifikator
gefunden wurde.

---

# 4. Was steckt hinter dem Farbsystem?

Das Repository enthält **zwei getrennte Farbmechanismen**, die nicht
vermischt werden sollten.

## 4.1 Deterministische Bildfarbmerkmale

`src/museum_pipeline/domain/image_features.py` führt klassische
Bildverarbeitung aus, keine generative Inferenz.

Der Referenzalgorithmus:

1. lädt das Bild als RGB;
2. verkleinert proportional für begrenzte Verarbeitung;
3. sampelt bis zu ca. 40.000 Pixel;
4. konvertiert sRGB nach CIE LAB (D65);
5. berechnet mittlere Helligkeit und Chroma;
6. berechnet Farbtonstreuung für farbige Pixel;
7. leitet eine grobe Farbigkeitsklasse ab;
8. führt deterministisches k-Means (`k=6`, 8 Iterationen) in LAB aus;
9. bewertet Cluster-Salienz über Distanz, Chroma und Fläche;
10. speichert die fünf salientesten Farben als LAB, Hex, Anteil und Salienz.

Die groben Farbigkeitsklassen:

```text
graustufen
monochrom_getönt
farbig
```

Der Zweck ist reproduzierbare Such-/Facettendaten, die nicht von einem
Modell-Prompt abhängen.

## 4.2 Warum LAB?

LAB wird genutzt, weil die nachfolgende Benennungsschicht einen Farbraum
braucht, in dem Helligkeit und chromatische Komponenten getrennt behandelt
werden können. Der Benennungsalgorithmus des Repositories kann so Fehler
vermeiden wie das Zuordnen eines hellen Grautons zu einer gesättigten
Farbe, nur weil ein RGB-Wert zufällig numerisch nah liegt.

Das Projekt beansprucht keine archivarische Farbmetrik. Eingabebilder
können Scan-, Weißabgleich-, Alterungs-, Reproduktions- oder
Kompressionseffekte enthalten.

## 4.3 Die menschenlesbare Farbnamen-Bibliothek

`services/farbnamen/` liefert eine zusätzliche Nachschlage-Schicht.

Die kombinierte Bibliothek enthält aktuell 6.811 Einträge:

- 477 deutsche Namen aus dem Meodai-Ökosystem;
- 148 CSS-Farbnamen;
- 110 Werner-Namen (1821);
- 1.117 Ridgway-Namen (1912);
- 4.959 Einträge aus der kuratierten Meodai-`bestof`-Liste.

Einträge behalten ihre Quelle, statt in ein anonymes Vokabular
zusammengefasst zu werden.

Die Bibliothek wird ohne quellübergreifende Deduplizierung aufgebaut, weil
derselbe Name bei Werner, Ridgway und einer modernen Liste legitim
leicht unterschiedliche Referenzfarben meinen kann.

## 4.4 Fünf Rollen eines Farbnamens

Der Mapping-Code trennt mehrere Ausgaben:

### `grundfarbe`

Eine kompakte kontrollierte Grundfarbe für Facettierung.

### `deskriptor`

Ein deterministischer deutscher Deskriptor, abgeleitet aus LAB, inklusive
grober Helligkeits- oder Sättigungsmodifikatoren, wo passend.

### `anzeige`

Ein naheliegender belegter deutscher Farbname, aber nur wenn
Farbton-/Helligkeits-/Chroma-Leitplanken den Treffer als sicher genug
einstufen.

### `synonyme`

Nächstliegende Namen aus der breiten Bibliothek. Vor allem als
Erschließungsvokabular nützlich, nicht als autoritative Anzeige-Labels.

### `fach`

Nächstliegende historische Fachnamen von Werner/Ridgway, bewusst getrennt
vom gewöhnlichen modernen Anzeige-Vokabular gehalten.

## 4.5 Gewichtete Distanz und Leitplanken

Der Mapper nutzt eine gewichtete LAB/LCh-Distanz. Farbton-Abweichung wird
für gesättigte Farben wichtiger; Farbton wird für nahezu neutrale Farben
weniger gewichtet, wo der Winkel instabil wird.

Zusätzliche Leitplanken verhindern offensichtliche Fehler wie:

- ein helles Grau erhält einen farbigen Namen;
- ein warmes Neutral wird auf einen starken Gegenfarbton gemappt;
- ein dunkles gesättigtes Rot wird automatisch zu Braun zusammengefasst.

## 4.6 Historische Farbnamen sind Referenzen, keine Wahrheit

Werner (1821) und Ridgway (1912) sind historisch interessante Vokabulare.
Das Repository speichert digitalisierte Näherungswerte ihrer Farben.

Diese Werte eignen sich für Nächste-Nachbar-Benennung und Exploration,
**nicht für den Anspruch einer exakten Rekonstruktion der originalen
historischen Farbtafel**.

Die öffentliche Provenienz-/Lizenzgrundlage ist dokumentiert in
`services/farbnamen/SOURCES.md` und `THIRD_PARTY_NOTICES.md`.

## 4.7 Aktueller Integrationsstand

Der Haupt-Runner berechnet die deterministischen Bildmerkmale automatisch.

Der menschenlesbare Farbnamen-Mapper ist aktuell ein **mitgeliefertes
Nachbearbeitungswerkzeug**, das das `farbnamen`-JSON-Feld in
`museum.enrichment_derived` aktualisieren kann; er wird derzeit nicht als
normale Runner-Phase aufgerufen.

Dieser Status sollte in der Dokumentation explizit bleiben, bis das
Werkzeug in den normalen Workflow integriert oder bewusst getrennt
gehalten wird.

---

# 5. Was steckt hinter dem institutionellen Topics-Modul?

Topics werden bewusst **nicht** mit einer Default-Wissensbasis
ausgeliefert.

Der Grund ist konzeptionell, nicht nur datenschutzbezogen:

> Ein institutioneller Sammlungsschwerpunkt ist eine kuratorisch-strategische
> Beziehung, keine intrinsische Eigenschaft jedes Museumsobjekts.

Das öffentliche Repository enthält deshalb die Topics-Engine, aber kein
reales institutionelles Strategiedokument und keine echten
Themennamen/-definitionen/-anker.

## 5.1 Was das getestete System nutzte

Die private getestete Implementierung nutzte eine substanzielle
institutionelle Wissensbasis in folgender Größenordnung:

```text
8 Themen
64 Unterthemen
104 kontrollierte Begriffe
```

Diese Zahlen werden nur veröffentlicht, um eine getestete Größenordnung zu
zeigen. Sie sind **keine** Anforderungen, und die zugrundeliegenden
Inhalte sind bewusst nicht veröffentlicht.

## 5.2 Was ein Museum bereitstellen muss

Ein Topics-aktiviertes Profil braucht:

```text
profiles/<museum>/topics/
  profile.yaml
  framework.md
  taxonomy.json
```

### Framework

Für jedes Thema die empfohlene Struktur:

- Erkenntnisinteresse / Scope;
- includes;
- explizite Ausschlüsse / `not sufficient`-Fälle;
- Evidenzregeln;
- optionale Retrieval-Anker;
- Sensitivitäts-/Reviewregeln.

### Taxonomie

Die Taxonomie liefert stabile Maschinen-IDs für:

- Themen;
- Unterthemen;
- kontrollierte Begriffe;
- `use_when`-Hinweise;
- `do_not_use_when`-Hinweise.

Die exakte Taxonomiegröße ist institutionsdefiniert.

## 5.3 Die wichtigste Regel: Framework ist kein Objektbeleg

Eine Wissensbasis darf ein Datum, einen Ort, eine Person, ein Ereignis oder
ein Konzept erwähnen, weil es hilft, das Thema zu definieren.

Diese Erwähnung beweist **nicht**, dass ein bestimmtes Objekt diese
Themenbeziehung hat.

Der Generator muss die Beziehung in den eigenen Metadaten, dem Bild oder
der konsolidierten visuellen Evidenz des Objekts begründen.

Diese Unterscheidung verhindert, dass ein Framework zu einer
maschinenlesbaren Quelle selbsterfüllender Assoziationen wird.

## 5.4 Warum Generator + Judge?

Themenzuordnung ist interpretativ und institutionsspezifisch. Die
getestete Methode hat deshalb zwei unabhängige Rollen:

### Generator

Prüft das Objekt gegen alle konfigurierten Themen und schlägt
evidenzbasierte Beziehungen, Unterthemen und kontrollierte Begriffe vor.

### Judge

Bewertet das komplette Themenset erneut unabhängig und kann:

- bestätigen;
- korrigieren;
- herabstufen;
- entfernen;
- eine übersehene Beziehung ergänzen.

Der Judge ist nicht darauf beschränkt, nur zu prüfen, was der Generator
bereits gewählt hat.

Das ist nützlich, weil der wichtigste Themenfehler **Auslassung** sein
kann, nicht nur falsch-positive Zuordnung.

## 5.5 Warum kein reduzierter öffentlicher Ersatz?

Eine vereinfachte Nachahmung des vertraulichen Themenframeworks einer
Institution wäre irreführend. Sie würde wie die
Produktions-Wissensbasis aussehen, ohne die Definitionen und den
strategischen Kontext zu haben, die das getestete System funktionieren
ließen.

Das öffentliche Repository veröffentlicht deshalb den
**Bauvertrag**, keine anonymisierte Pseudo-Version des privaten
Inhalts.

Siehe [`TOPIC_KNOWLEDGE_BASE.md`](TOPIC_KNOWLEDGE_BASE.md) für den
Dateivertrag und Starter-Beispiele.

---

# 6. Wie diese Entscheidungen nachgenutzt werden sollten

Ein neues Museum muss keine Alles-oder-nichts-Entscheidung treffen.

Ein sinnvoller Übernahmepfad:

```text
1. generischen Python-Core beibehalten
2. lokale Metadatenfelder mappen
3. das Referenz-Keyword-System an einem kleinen Testset laufen lassen
4. entscheiden, ob das 11-Cluster-Design zu lokalen Suchzielen passt
5. Prompts/Policy anpassen, wo lokale Erschließungs- oder Ethikpolitik abweicht
6. GND nur aktivieren, wenn nützlich
7. Machine Heart aktivieren, falls gewünscht, mit Default- oder eigenem Vokabular
8. Topics erst bauen, nachdem die Institution eine explizite Themen-Wissensbasis hat
9. mit echten Sammlungsbeispielen evaluieren, bevor skaliert wird
```

Das Repository ist am stärksten, wenn seine Referenzentscheidungen als
**einsehbare Ausgangspunkte** behandelt werden, nicht als unsichtbare
Defaults, die jede Institution übernehmen muss.

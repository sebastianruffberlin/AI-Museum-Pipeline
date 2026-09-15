<div align="center">

# 🏛️ AI Museum Pipeline

**Eine profilgesteuerte, selbst gehostete Anreicherungs-Pipeline für Museumssammlungen**

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Deployment](https://img.shields.io/badge/Deployment-Self--Hosted-5b5b5b)
![Core](https://img.shields.io/badge/Core-Museum--Agnostic-7b61ff)
![Profiles](https://img.shields.io/badge/Configuration-Profiles-0a7ea4)
![Skills](https://img.shields.io/badge/Architecture-Skills-b35c00)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791)
![OpenSearch](https://img.shields.io/badge/Authority-GND%20%2F%20OpenSearch-005eb8)
![Embeddings](https://img.shields.io/badge/Embeddings-SigLIP2%20%7C%20DINOv3%20%7C%20BGE--M3-6c757d)
![API](https://img.shields.io/badge/LLM%20API-OpenAI--Compatible-111111)
![Inference](https://img.shields.io/badge/Inference-llama.cpp%20%7C%20LiteLLM%20%7C%20llama--swap-444444)
![Reference GPU](https://img.shields.io/badge/Reference%20GPU-NVIDIA%20H100-76b900)
[![CI](https://github.com/sebastianruffberlin/AI-Museum-Pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/sebastianruffberlin/AI-Museum-Pipeline/actions/workflows/ci.yml)

</div>

AI Museum Pipeline reichert bestehende Museumssammlungsdaten an mit
deterministischer Bildanalyse, multimodalen Beschreibungen, auditierten
Suchschlagwörtern, optionalen Normdaten-Verknüpfungen, Embeddings und
optionalen interpretativen Modulen.

Sie ist kein Ersatz für ein Sammlungsmanagementsystem und behandelt
LLM-Ausgaben nicht als Katalogwahrheit. Das Projekt basiert auf einer
einfachen Idee:

> **Quelldokumentation und maschinell generierte Anreicherung getrennt
> halten, jeden Anreicherungsschritt einsehbar machen, und
> museumsspezifische Entscheidungen in explizite Profile verlagern statt
> sie im Anwendungscode zu verstecken.**

Die Pipeline ist aus einem produktiv eingesetzten Museums-Erschließungsflow
entstanden. Das aktuelle Repository überführt diese Erfahrung in eine
modulare Python-Architektur, die von anderen Institutionen übernommen werden
kann, ohne die Datenbank, Strategie oder Infrastruktur eines einzelnen
Museums zu reproduzieren.

---

## Wo finde ich was? (Einsteiger · Intermediate · Profi × museologisch · technisch)

Die vollständige Navigation nach Erfahrungsstufe und Themenseite steht in
[`docs/START_HERE.md`](docs/START_HERE.md). Kurzfassung: Wer neu ist, startet
hier in der README und bei
[`docs/MUSEOLOGICAL_PRINCIPLES.md`](docs/MUSEOLOGICAL_PRINCIPLES.md). Wer das
eigene Museum einrichtet, braucht
[`docs/WORKFLOW.md`](docs/WORKFLOW.md) und
[`docs/PROFILES.md`](docs/PROFILES.md). Wer die strategischen Prinzipien
hinter jedem Prompt verstehen oder tief in die Infrastruktur will, findet das
in [`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md) bzw.
[`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md).

---

## Warum dieses Projekt existiert

Museums-Sammlungsdatenbanken sind reichhaltig, aber uneinheitlich. Sie
enthalten oft jahrzehntelange Fachdokumentation, lokale Terminologie, sich
wandelnde Erschließungspraxis, unterbeschriebenes Bildmaterial und Felder,
die nie für die öffentliche Suche gedacht waren.

Generative KI kann nützliche Zugangspunkte hinzufügen, aber ein einzelner
Prompt, der ein paar unkontrollierte Tags schreibt, schafft neue Probleme:

- das Modell kann Evidenz erfinden;
- technische Museumsterminologie kann für Laien unzugänglich bleiben;
- visuelle Beobachtung und Interpretation können vermischt werden;
- sensible historische oder identitätsbezogene Aussagen können überinterpretiert werden;
- dasselbe Konzept kann in mehreren inkonsistenten Formen auftauchen;
- es gibt möglicherweise keine Aufzeichnung, warum ein Begriff vorgeschlagen wurde;
- ein scheinbar präziser Normdaten-Treffer kann schlicht falsch sein;
- institutionsspezifische kuratorische Rahmenwerke können mit universellen
  Objekteigenschaften verwechselt werden.

AI Museum Pipeline adressiert diese Probleme als **Workflow- und
Datendesign-Problem**, nicht nur als Prompting-Problem.

Die Referenzarchitektur kombiniert:

- mehrere Modellperspektiven;
- explizite semantische Cluster;
- evidenztragende Ausgaben;
- Generator/Audit- bzw. Generator/Judge-Trennung;
- deterministische Policy nach Modell-Review;
- optionalen Normdaten-Abgleich;
- profileigene Museumssemantik;
- reproduzierbare Laufzeit- und Hardwarekonfiguration.

---

## Was die Pipeline erzeugen kann

Der vollständige Workflow unterstützt folgende Anreicherungsfamilien.

| Modul | Zweck | Typische Ausgabe |
| --- | --- | --- |
| Bildmerkmale | deterministische, pixelbasierte Beschreibung | Seitenformat, Farbigkeit, LAB-/Hex-Farbcluster, Helligkeit, Chroma |
| Bild-Embeddings | Ähnlichkeit und visuelle Exploration | SigLIP2- und DINOv3-Vektoren |
| Captions | konsolidierte visuelle Arbeitsbeschreibung | zwei unabhängige Beobachtungen + Master Caption |
| Schlagwörter | öffentlichkeitstaugliche strukturierte Erschließungsbegriffe | 11 semantische Schlagwortcluster, Evidenz, Audit-Status |
| Normdaten | optionaler kontrollierter Normdaten-Abgleich | GND-Kandidatenentscheidung, GND-ID oder `no_match` |
| Emotion / Machine Heart | optionale Wirkungslesart | kontrollierte mögliche Lesarten + Evidenz + Judge-Entscheidung |
| Institutionelle Themen | optionale institutionseigene Themenbeziehung | Themenbeziehung + Evidenz + Unterthema/kontrollierte Begriffe + Judge-Entscheidung |
| Text-Embeddings | semantisches Text-Retrieval | BGE-M3-Vektorrepräsentationen |

Die Module sind bewusst trennbar. Ein Museum kann nur die Kern-Sucherschließung
nutzen, Machine Heart ergänzen, ein eigenes Themenframework ergänzen, oder
einzelne Methoden ersetzen und dabei den umgebenden Harness behalten.

---

## Was ist generisch, was ist ein Default, und was gehört dem Museum?

Eine der wichtigsten Design-Entscheidungen dieses Repositories ist, dass
nicht jede nützliche Museumsentscheidung als universeller Standard
präsentiert wird.

| Schicht | Status in diesem Repository | Bedeutung |
| --- | --- | --- |
| Python-Harness, Persistenz-Schnittstellen, Workflow-Engine | **generischer Core** | soll institutionsübergreifend nachnutzbar sein |
| Metadaten-Mapping | **Museum Profile** | jede Institution mappt ihre eigenen Quellfelder |
| 11-Cluster-Schlagwortdesign | **getestetes Referenz-/Default-Design** | nützlich und mitgeliefert, aber kein Anspruch auf Museumsstandard |
| Keyword-Generator/Audit/Policy | **getestete Referenz-/Default-Methode** | im Museumsprofil anpassbar |
| GND-Adapter | **optionale nachnutzbare Integration** | nützlich im deutschsprachigen GLAM-Kontext, nicht verpflichtend |
| Machine Heart | **vollständige nachnutzbare Default-Methode** | museumsagnostische Wirkungslesart-Methode, vollständig enthalten |
| Farbextraktion | **generische deterministische Methode** | pixelbasierte Bildmerkmale |
| Farbnamen-Bibliothek | **mitgelieferte Referenz-/Suchschicht** | optionales Mapping von LAB-Farben auf menschenlesbare und historische Namen |
| Institutionelle Topics | **nur generische Engine** | jedes Museum muss eigenes Framework und eigene Taxonomie liefern |
| Modell-Mapping | **Model Profile** | Rollen sind stabil; konkrete Modelle können wechseln |
| H100-Einstellungen | **kalibriertes Hardware Profile** | Referenzwerte, keine portablen Defaults für jede GPU |

Für die Begründung hinter den museumsseitigen Entscheidungen siehe
[`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md).

### Starter-Template versus getestetes Referenzprofil

Das Repository enthält bewusst beides:

```text
profiles/_template/
    generalisierter Starter für ein anderes Museum

profiles/stadtmuseum-berlin/
    öffentliches Referenzprofil, das Teile des getesteten institutionellen Setups bewahrt
```

Das zweite Verzeichnis ist nützlich, weil es reale Design-Entscheidungen
einsehbar macht: Schlagwortcluster, Prompt-Policy, Terminologieregeln,
GND-Konfiguration und das Machine-Heart-Setup können mit dem generalisierten
Template verglichen werden. Es soll **nicht** als Anspruch gelesen werden,
dass jedes Museum den Wortlaut oder die Policy des Stadtmuseums Berlin
übernehmen sollte, und ein neues Museum sollte mit `_template` starten, nicht
mit dem Referenzprofil.

Das Referenzprofil ist außerdem **kein Zero-Konfiguration-Quick-Start**. Es
bewahrt bewusst Deployment-Annahmen aus dem getesteten Fall: seine
Quellbilder nutzen den S3-Asset-Pfad, und sein Authority-Profil aktiviert
GND. Eine neue Installation sollte `profiles/_template/` nutzen, sofern
diese Abhängigkeiten nicht bewusst reproduziert werden sollen.
Workflow-Dateien entscheiden, ob Emotion oder Topics laufen; Schlüssel im
Museumsprofil aktivieren optionale Module nicht stillschweigend.

Das öffentliche Stadtmuseum-Profil enthält **keine institutionelle
Topics-Wissensbasis**. Das private Themenframework bleibt außerhalb des
Repositories; nur die generische Topics-Engine und der Bauvertrag sind
öffentlich. Machine Heart ist anders: das vollständige museumsagnostische
Default-Vokabular/-Methode ist enthalten und kann direkt aus dem
Starterprofil genutzt werden.

---

## Ein Objekt durch die Pipeline

Das Repository liefert ein synthetisches Beispiel mit, damit das öffentliche
Projekt nicht von Publikationsrechten für ein reales Sammlungsobjekt
abhängt.

```text
Input
  object_id: DEMO-001
  object_type: Fotografie
  title: Urbane Straßenszene
  dating: 1970er Jahre
  description: ...
  image: https://example.org/demo-001.jpg

        │
        ├── deterministische Bildmerkmale
        │     Format, Farbigkeit, dominante LAB-/Hex-Farben
        │
        ├── Bild-Embeddings
        │     SigLIP2 + DINOv3
        │
        ├── visuelle Beobachtungen
        │     Modell A + Modell B
        │
        ├── Master Caption
        │     konsolidierte Beobachtung/Kontext
        │
        ├── Keyword-Generator
        │     11 semantische Cluster + why/Evidenz
        │
        ├── Keyword-Audit
        │     feste Fehlerklassen
        │
        ├── deterministische Policy + Repair
        │     keep / move / repair / reject
        │
        ├── optionaler GND-Abgleich
        │     Kandidaten-Retrieval + LLM-Entscheidung + no_match
        │
        ├── optionales Machine Heart
        │     Wirkungslesarten + Evidenz + Judge
        │
        ├── optionale institutionsspezifische Topics
        │     museumseigenes Framework + Taxonomie + Judge
        │
        └── Text-Embeddings
              semantische Retrieval-Vektoren
```

Siehe [`examples/DEMO-001.json`](examples/DEMO-001.json) für eine minimale
synthetische Illustration derselben Struktur.

## Reales Referenzobjekt: 92/45 (Spirituseisen)

Zur Veranschaulichung, was die Pipeline tatsächlich produziert, zeigt dieser
Abschnitt ein reales, produktiv verarbeitetes Objekt aus dem
Stadtmuseum-Berlin-Referenzdeployment: ein gemeinfreies technisches
Alltagsgerät (Spiritusbügeleisen, um 1910), keine Personenabbildung, kein
urheberrechtlicher Schutz. Die vollständigen Rohdaten stehen in
[`examples/92-45.json`](examples/92-45.json).

**Zwei Dinge wurden aus den Produktionsdaten bewusst entfernt, nicht nur
gekürzt** — unabhängig davon, dass das Objekt selbst gemeinfrei ist:

1. Die institutionelle Themenschwerpunkte-Zuordnung
   (`museum.schwerpunkt_lauf` / `museum.schwerpunkt_bezug`). Das ist genau
   die private institutionelle Wissensbasis, die dieses Repository
   grundsätzlich nicht veröffentlicht — das gilt auch für Beispieldaten.
2. Vier Machine-Heart-Lesarten eines völlig anderen Objekts, das über
   dieselbe `annotation_set_id` (Tages-Batch) mitgejoint wurde, aber nicht
   92/45 ist. Ein Join über `annotation_set_id` statt `obj_id` zieht bei
   einer manuellen Abfrage schnell falsche Zeilen mit — ein guter Grund,
   in eigenen Abfragen immer zusätzlich nach `obj_id` zu filtern.

Alles andere unten ist vollständig, nicht auszugsweise: die komplette
Caption, alle 28 Schlagwörter, alle 4 Machine-Heart-Lesarten.

![Spirituseisen, Stadtmuseum Berlin, Objekt 92/45](https://museumopen.de/2600/2600/1647228.jpg)

*Bildquelle: [Sammlung Online, Stadtmuseum Berlin](https://sammlung-online.stadtmuseum.de/Details/Index/1647228), Objekt 92/45. Gemeinfrei.*

### Quelldaten

| Feld | Wert |
| --- | --- |
| `object_id` | `92/45` |
| Sammlung / Bereich | Alltagskultur / Wohn-/Hauswirtschaftsgeräte |
| Titel | Spirituseisen |
| Datierung | 1847–1940 (Objekt: um 1910) |
| Maße | 15,5 × 8,5 × 27,0 cm |
| Material | Eisen, Holz, Metall |

Auf der Sammlungsseite ist jedes Feld mit **"Museum"** oder **"KI"**
gelabelt — genau die im ganzen Projekt zentrale Trennung von
Quelldokumentation und maschineller Anreicherung, hier an echten Daten:

**"Beschreibung" (Museum)** — von Menschen verfasste kuratorische
Institutionsdokumentation (`raw_objects.beschreibung`), existierte lange
bevor die Pipeline das Objekt je gesehen hat:

> Eisengußspiritusbügeleisen. Sehr spitz zulaufendes Spirituseisen mit
> querliegendem, faßähnlichem Tank. Im Bügelkörper befindet sich ein
> schmales Brennrohr. Durch einen Hebel ist der Innenraum des Bügelkörpers
> zu öffnen. Zum Händeln ist ein naturbelassener gerader Griff aus Holz an
> den Bügelkörper mittels zweier Schrauben angeschraubt. [...]
> Spirituseisen gab es nur eine kurze Zeit lang, nämlich von 1847–1940. Mit
> ihnen konnte immerhin 1 Stunde ohne Unterlaß gebügelt werden. [...]

Vollständiger Text (inkl. der historischen Einordnung zu Glättknochen,
Plissierstäben und Tolleisen seit dem Mittelalter) in
[`examples/92-45.json`](examples/92-45.json), Feld
`input.raw_objects_beschreibung`.

Die Pipeline **liest** diesen Text nur als Kontext-Evidenz für Caption und
Keywords — sie überschreibt ihn nie. Genau das meint Prinzip 1 in
[`docs/MUSEOLOGICAL_PRINCIPLES.md`](docs/MUSEOLOGICAL_PRINCIPLES.md):
"Quelle und Anreicherung bleiben getrennt".

### Deterministische Bildmerkmale (`museum.enrichment_derived`)

```text
format: quer
farbigkeit: farbig
helligkeit_mittel: 37.1   chroma_mittel: 6.6   hue_streuung: 0.183
dominante Farben (LAB → Hex, Anteil, Salienz):
  #c0a67c  Anteil 11.8%  Salienz 15.23   (hellbraun/ocker – Holzgriff)
  #ebeef0  Anteil 18.0%  Salienz  8.24   (fast weiß – Unterlage)
  #0c0f0c  Anteil 39.2%  Salienz  7.24   (fast schwarz – Hintergrund)
  #848275  Anteil 11.4%  Salienz  6.00   (mittelgrau – Metall)
  #202621  Anteil 12.0%  Salienz  4.54   (dunkelgrau-grün)
```

### Master Caption (`museum.enrichment_captions`, vollständig, 1205 Zeichen)

```text
### 1. OBJEKTTYP
Ein altes Dampfbügeleisen mit seitlichem Wasserbehälter.

### 2. OPTISCHE ERSCHEINUNG
Das Objekt besteht aus metallischen und hölzernen Bestandteilen. Das Metall
ist silbergrau mit deutlichen bräunlichen Oxidationsstellen und einer
unregelmäßigen, matten Textur. Der Griff ist aus hellbraunem bis
ockerfarbenem Holz gefertigt.

### 3. DARGESTELLT / SICHTBAR
*   Bügeleisenkörper (gewölbt, metallisch)
*   Holzgriff (waagerecht angebracht)
*   Seitlicher zylindrischer Wasserbehälter (Tank) mit rundem Deckel
*   Dampflöcher (zwei parallele Reihen kreisförmiger Öffnungen an der
    Unterseite)
*   Kleiner rötlich-brauner Knopf/Regler
*   Vertikaler Metallstift/Schraube
*   Befestigungsschrauben

### 4. SZENERIE / ANORDNUNG
Das Bügeleisen ist in der Seitenansicht auf einer hellgrauen, flachen
Unterlage vor einem schwarzen Hintergrund platziert.

### 5. SCHRIFT, ZEICHEN, NUMMERN
keine sichtbar

### 6. AUFFÄLLIGE VISUELLE MERKMALE
Deutliche Patina, Rostflecken und dunkle Oxidationsstellen auf der
Metalloberfläche; der Holzgriff weist Gebrauchsspuren auf.

### 7. SENSITIVITÄTS-HINWEIS
Keine.

### 8. KONFIDENZ / UNSICHERHEIT
Verworfen: Keine.
[unsicher]: Keine.
Bias-Bereinigung: Keine.
```

Konsolidiert aus zwei unabhängigen Vision-Modell-Beobachtungen (`text_visuell`,
`text_kontext` in der JSON-Datei) zu diesem strukturierten Befund.

### Öffentliche Anzeige ("Bildbeschreibung", KI)

Das einzige auf der Sammlungsseite mit **"KI"** gelabelte Beschreibungsfeld
(zusätzlich zu den ebenfalls KI-generierten Schlagworten) ist die
Bildbeschreibung — nicht die strukturierte interne `master_caption`,
sondern `text_visuell` und `text_kontext` aneinandergehängt, die beiden
rohen Vision-Modell-Beobachtungen, aus denen die `master_caption` erst
konsolidiert wird:

> Ein altes Dampfbügeleisen mit seitlichem Wasserbehälter. Bügeleisenkörper
> (gewölbt, metallisch) Holzgriff (waagerecht angebracht) Seitlicher
> zylindrischer Wasserbehälter (Tank) mit rundem Deckel Dampflöcher (zwei
> parallele Reihen kreisförmiger Öffnungen an der Unterseite) Kleiner
> rötlich-brauner Knopf/Regler Vertikaler Metallstift/Schraube
> Befestigungsschrauben Das Bügeleisen ist in der Seitenansicht auf einer
> hellgrauen, flachen Unterlage vor einem schwarzen Hintergrund platziert.
> Das Objekt besteht aus metallischen und hölzernen Bestandteilen. Das
> Metall ist silbergrau mit deutlichen bräunlichen Oxidationsstellen und
> einer unregelmäßigen, matten Textur. Der Griff ist aus hellbraunem bis
> ockerfarbenem Holz gefertigt. Deutliche Patina, Rostflecken und dunkle
> Oxidationsstellen auf der Metalloberfläche; der Holzgriff weist
> Gebrauchsspuren auf.

Zum Vergleich mit der oben gezeigten kuratorischen "Beschreibung (Museum)":
diese Bildbeschreibung beschreibt ausschließlich, was auf dem Foto zu sehen
ist — keine Herstellungsgeschichte, keine historische Einordnung. Genau die
Abgrenzung, die Prinzip 2 in `docs/MUSEOLOGICAL_PRINCIPLES.md`
("Beobachtung ist nicht Interpretation") und die Museum/KI-Kennzeichnung
auf der Seite selbst sichtbar machen.

### Schlagwörter (`museum.enrichment_keywords`, vollständig, alle 28 Zeilen)

| Cluster | Begriff | Status | GND |
| --- | --- | --- | --- |
| Objekttyp | Bügeleisen | grün | 4146855-7 |
| Objekttyp | Haushaltsgerät | grün | 4023740-0 |
| Objekttyp | Plätteisen | grün | `no_match` |
| Thema_Phänomen | Hausarbeit | grün | 4023699-7 |
| Thema_Phänomen | Haushalt | grün | 4023744-8 |
| Thema_Phänomen | Kleidungspflege | grün | 4438215-7 |
| Inhalt_Motiv | Griff | grün | 4402027-2 |
| Inhalt_Motiv | Hebel | grün | 4159328-5 |
| Inhalt_Motiv | Perforation | grün | 4745388-6 |
| Inhalt_Motiv | Tank | grün | 4125647-5 |
| Inhalt_Motiv | Bügeleisenschuh | grün | `no_match` |
| Funktion_Zweck | Bügeln | grün | 4476741-9 |
| Funktion_Zweck | Glätten | grün | `no_match` |
| Funktion_Zweck | Heizen | grün | `no_match` |
| Visuelle_Merkmale | Gebrauchsspuren | grün | 4297398-3 |
| Visuelle_Merkmale | Patina | grün | 4115514-2 |
| Visuelle_Merkmale | Rost | grün | 4178475-3 |
| Form_Gestalt | Zylinder | grün | `no_match` |
| Form_Gestalt | **Spitz** | **gelb** | – |
| Bestandteile | Deckel | grün | 4344172-5 |
| Bestandteile | Knopf | grün | 4246280-0 |
| Bestandteile | Niet | grün | 4171891-4 |
| Gebrauchskontext | Hauswirtschaft | grün | 4023828-3 |
| Gebrauchskontext | Reise | grün | 4049275-8 |
| Kultureller_Kontext | Alltagskultur | grün | 4122782-7 |
| Kultureller_Kontext | Industrialisierung | grün | 4026776-3 |
| Farbe_Nuancen | Braun | grün | 4707780-3 |
| Farbe_Nuancen | Grau | grün | 4502751-1 |

Drei Muster darin, die in [`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md)
beschrieben sind, live an echten Daten:

- **`no_match` ist normal, kein Fehler** — 6 von 28 Begriffen (`Plätteisen`,
  `Bügeleisenschuh`, `Glätten`, `Heizen`, `Zylinder`) haben keinen
  GND-Treffer. `Plätteisen` etwa ist ein laiensprachlicher Folksonomie-Begriff
  ohne eigenen Normdatensatz — bleibt trotzdem grün, weil er als
  Erschließungsbegriff nützlich ist.
- **`Spitz` zeigt den Repair-Pfad live**: Status `gelb`, das Audit erkennt
  eine unkontrollierte Adjektivform, die deterministische Policy schickt den
  Begriff zur Reparatur ("Spitzheit"/"spitze Form") statt ihn zu verwerfen
  oder unverändert zu akzeptieren.
- **`Gebrauchsspuren`** ist eine bewusst zugelassene Pluralform, weil sie als
  eigenständiger GND-Sachbegriff (`Gebrauchsspur`) belegt ist — die
  Singular-Regel gilt nicht ausnahmslos, sondern wo sie dem Normdaten-Bezug
  widerspräche.

### Machine Heart (`museum.emotion_assignments`, alle 4 Lesarten zu 92/45)

| Lesart | Judge | Begründung |
| --- | --- | --- |
| Fremdheit | ✅ bestätigt | Konstruktion (Tank/Brennrohr) weicht stark vom modernen Bügeleisen-Verständnis ab |
| Stille | ✅ bestätigt | Isolation vor schwarzem Hintergrund, Gegenüberstellung von einstiger Aktivität und musealer Ruhe |
| Kühle | ❌ **abgelehnt** | Leitplankenverstoß: Wirkung wurde allein aus Material (Metall/Guss) abgeleitet |
| Strenge | ❌ **abgelehnt** | Leitplankenverstoß: Wirkung wurde allein aus geometrischer Regelmäßigkeit abgeleitet (Form = Atmosphäre) |

Die beiden Ablehnungen sind kein Fehler, sondern zeigen die in
[`docs/MUSEOLOGICAL_PRINCIPLES.md`](docs/MUSEOLOGICAL_PRINCIPLES.md)
beschriebene Leitplanke in echter Anwendung: eine Formeigenschaft allein
(Material, Geometrie) darf keine affektive Lesart begründen. Genau dafür
gibt es den unabhängigen Judge-Schritt.

---

# Architektur

## Topologie im Überblick

```text
Museums-Quelldatenbank / exportierte Quelltabelle
                  │
                  ├──────── Metadaten
                  │
                  └──────── Bild-/Asset-Referenz
                                   │
                                   ▼
                         ┌──────────────────┐
                         │  Python-Harness  │
                         │                  │
                         │ State / Retries  │
                         │ Validierung      │
                         │ Profil-Ladung    │
                         │ Tracing          │
                         └────────┬─────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
           ▼                      ▼                      ▼
   deterministische CPU   Embedding-Services      generative Rollen
   Bildmerkmale           SigLIP2 / DINOv3       OpenAI-kompatible API
                                                     │
                                                     ▼
                                         Caddy → LiteLLM → llama-swap
                                                     │
                                                     ▼
                                                  llama.cpp

                                  │
                                  ▼
                         PostgreSQL-Anreicherung,
                         getrennt von den
                         Museums-Quelldatensätzen
```

Das Referenzdeployment trennt Orchestrierung und CPU-Services von der
GPU-Inferenz. Die Python-Pipeline kann auch einen bereits existierenden
kompatiblen OpenAI-artigen Endpoint nutzen.

## Das fünfteilige Konfigurationsmodell

Der Code trennt Belange, die üblicherweise in einen einzigen Workflow
hartcodiert werden:

```text
Museum Profile
+ Model Profile
+ Hardware Profile
+ Workflow
+ Deployment-Konfiguration
        ↓
     Pipeline-Lauf
```

### 1. Museum Profile

`profiles/<museum>/`

Enthält die Semantik, die der Institution oder der gewählten Referenzmethode
gehört:

- Mapping von lokalen Quellspalten auf kanonische Konzepte;
- Asset-Zugriffsregeln;
- Prompt-Texte;
- Schlagwortcluster-Definitionen;
- Audit- und Repair-Policy;
- Terminologie-/Debias-Regeln;
- Normdaten-Konfiguration;
- optionale Emotion-Konfiguration;
- optionales institutionseigenes Themenwissen.

Die vorgesehene Regel:

> Ein Museum sollte normalerweise Museumssemantik ändern können, ohne den
> Python-Core zu bearbeiten.

### 2. Model Profile

`models/*.yaml`

Mappt stabile logische Rollen auf konkrete Modelle und
Generierungseinstellungen.

Beispiele für Rollen:

```text
caption.primary
caption.secondary
caption.synthesis
tagging.generator
tagging.audit
tagging.repair
authority.gnd
emotion.generator
emotion.judge
topics.generator
topics.judge
```

Der Workflow hängt deshalb von **Rollen** ab, nicht direkt von einer
Modellmarke.

### 3. Hardware Profile

`hardware/*.yaml`

Speichert kalibrierte Inferenzbeschränkungen wie Context-Pools und
parallele Slots. Diese Werte sind operative Eigenschaften einer
Hardware-/Modell-Kombination, keine Museumssemantik und keine
Prompt-Einstellungen.

### 4. Workflow

`workflows/*.yaml`

Mitgelieferte Presets:

- `core`
- `core-emotion`
- `core-topics`
- `full`

Eine neue Institution sollte mit `core` starten.

### 5. Deployment-Konfiguration

`deployment.yaml` beschreibt nicht-geheime Infrastrukturentscheidungen.
`.env` trägt externe Secrets und Zugangsdaten. Generierte interne
Runtime-Secrets werden außerhalb des Git-Checkouts gehalten.

---

# Der Kern-Anreicherungsfluss

## 1. Bild-Embeddings

Zwei Bildrepräsentationen werden im Referenzstack genutzt:

- **SigLIP2** für semantische Bildähnlichkeit;
- **DINOv3** für stark visuelle/strukturelle Ähnlichkeit.

Die Trennung ermöglicht unterschiedliche Formen visueller Exploration, statt
vorzutäuschen, dass ein einziger Vektorraum jede Art von Ähnlichkeit erfasst.

Embeddings sind mathematische Retrieval-Werkzeuge. Sie werden nicht als
Museumsontologie oder historische Interpretation behandelt.

## 2. Deterministische Bildmerkmale

Die Bildmerkmale-Stufe vermeidet bewusst ein LLM.

`src/museum_pipeline/domain/image_features.py` berechnet:

- Querformat / Hochformat / annähernd quadratisch;
- mittlere LAB-Helligkeit;
- mittlere Chroma;
- Farbtonstreuung;
- eine grobe Farbigkeitsklasse (`graustufen`, `monochrom_getönt`, `farbig`);
- sechs LAB-k-Means-Cluster;
- einen Salienzwert pro Cluster;
- die fünf salientesten Farben als LAB + Hex + Bildanteil.

Die Referenzimplementierung verkleinert große Bilder, sampelt ca. 40.000
Pixel, konvertiert sRGB nach CIE LAB und führt deterministisches k-Means
mit demselben Schleifenverhalten aus, das der Vorgänger-Workflow nutzte.

### Menschenlesbare Farbnamen sind eine separate Schicht

Das Repository enthält zusätzlich `services/farbnamen/`. Das ist **nicht
dasselbe wie die Kern-Bildmerkmale-Berechnung**.

Der aktuelle Python-Runner schreibt die deterministischen Farbcluster nach
`museum.enrichment_derived`. Der Farbnamen-Service kann diese LAB-Farben
dann mappen auf:

- eine kompakte Grundfarbe, nützlich als Facette;
- einen deterministischen deutschen Deskriptor wie einen hellen/dunklen/
  matten/kräftigen Farbton;
- einen naheliegenden belegten deutschen Farbnamen, wenn ein sicherer
  Treffer existiert;
- Suchsynonyme aus einer breiten Farbnamen-Bibliothek;
- historische Fachnachbarn von Werner (1821) und Ridgway (1912).

Die kombinierte Bibliothek enthält aktuell 6.811 Quelleinträge aus
deutschen Meodai-Namen, CSS-Farben, Werner, Ridgway und der kuratierten
Meodai-`bestof`-Liste. Die Quellidentität bleibt bei jedem Eintrag erhalten.

Das Mapping nutzt eine gewichtete Farbdistanz im LAB/LCh-Raum plus
Leitplanken gegen offensichtlich irreführende Farbton- oder
Helligkeitswechsel. Historische Namen werden als historisches/Fach-Vokabular
präsentiert, nicht als farbmetrische Wahrheit.

**Wichtig:** der Farbnamen-Mapper ist aktuell ein mitgeliefertes
Nachbearbeitungswerkzeug; er wird nicht automatisch vom Haupt-Workflow-Runner
aufgerufen. Diese Unterscheidung ist für nachgelagerte Implementierer
nützlich und bewusst dokumentiert.

Siehe [`services/farbnamen/SOURCES.md`](services/farbnamen/SOURCES.md).

## 3. Visuelle Beobachtung und Master Caption

Der Referenzfluss lässt kein einzelnes Vision-Modell zur alleinigen
visuellen Quelle für spätere Anreicherung werden.

Er nutzt:

```text
Vision-Modell A ──┐
                  ├──> Synthese-Modell ──> Master Caption
Vision-Modell B ──┘
```

Der Zweck ist keine literarische Bildbeschreibung. Die Master Caption ist
ein **Arbeitsbefund** für spätere Maschinenstufen.

Die Keyword- und interpretativen Module sehen sowohl das Originalbild als
auch die konsolidierte Beschreibung. Die rohen Beobachtungen bleiben als
Fallback-Quellen verfügbar, wenn nötig.

---

# Schlagwort-Anreicherung: warum elf Cluster?

Das Default-Tagging-Profil nutzt elf Schlagwortcluster:

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

Diese elf Cluster werden **nicht als etablierter Museumsstandard oder
universelle Ontologie beansprucht**. Sie sind eine pragmatische Such- und
Beschreibungsarchitektur, die aus dem getesteten Anreicherungsworkflow
entstanden ist.

Das Designziel ist, zu verhindern, dass eine flache Schlagwortliste
semantisch inkompatible Dinge vermischt.

Zum Beispiel:

```text
Fotografie          → Objekttyp
Straßenbahn          → Inhalt_Motiv
öffentlicher Nahverkehr → Thema_Phänomen
Transport            → Funktion_Zweck / kontextabhängige Nutzung
Straßenleben          → Gebrauchskontext
urbanes Leben der 1970er → Kultureller_Kontext, nur wenn tatsächlich belegt
rechteckig            → Form_Gestalt
verblasst             → Visuelle_Merkmale
blau                  → Farbe_Nuancen
```

Die Trennung ermöglicht mehrere nachgelagerte Verhaltensweisen:

- verschiedene Suchfacetten können aus verschiedenen semantischen
  Dimensionen gebaut werden;
- der GND-Abgleich erhält das Schlagwort **und seinen Cluster-Kontext**;
- das Audit kann einen gültigen Begriff im falschen semantischen Cluster
  erkennen;
- clusterübergreifende Redundanz kann reduziert werden;
- das System kann unterscheiden, was ein Objekt **ist**, was ein Bild
  **zeigt**, wovon es **handelt**, wofür es **gedacht** war, und in welchem
  **sozialen/historischen Kontext** es beschrieben wird.

### Warum `Emotion_Atmosphäre`, wenn es Machine Heart gibt?

Sie dienen unterschiedlichen Zwecken.

`Emotion_Atmosphäre` in der Schlagwortschicht ist ein konservatives
Such-Cluster für einfache, stark belegte Atmosphäre-Begriffe. Es gehört zum
flachen Erschließungsvokabular und wird wie jedes andere Schlagwort
auditiert.

**Machine Heart** ist eine separate optionale interpretative Methode mit
eigenem kontrolliertem Vokabular, Lesart-Scopes, Evidenzmodell und
unabhängigem Judge. Es sollte nicht auf das Schlagwort-Cluster reduziert
werden, und das Schlagwort-Cluster sollte nicht mit vollständiger affektiver
Interpretation verwechselt werden.

### Warum `Farbe_Nuancen`, wenn es deterministische Farbanalyse gibt?

Auch hier sind die Schichten unterschiedlich.

`Farbe_Nuancen` ist ein sprachlicher Schlagwortkanal, der im multimodalen
Keyword-Prozess erzeugt wird und wie andere Begriffe an Suche und
Normdaten-Behandlung teilnehmen kann.

Der deterministische Bildmerkmale-/Farbnamen-Pfad ist pixelbasiert und
besser für reproduzierbare Farbfacetten und visuelle Exploration geeignet.
Beide zu behalten erlaubt es, sprachliche visuelle Beschreibung mit
deterministischer Bildstatistik zu vergleichen, statt vorzutäuschen, dass
es dasselbe Signal ist.

Für die vollständige Begründung und clusterweise Erklärung siehe
[`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md).

---

# Warum der Keyword-Generator-Prompt so streng ist

Der Keyword-Generator ist bewusst länger als ein konventioneller
Tagging-Prompt, weil er eine **Museums-Suchpolitik** kodiert statt einfach
nach Substantiven zu fragen.

Seine Hauptentscheidungen:

### Öffentliche Suche vor reiner Fachterminologie

Die Zielgruppe ist explizit die nicht-fachkundige Nutzerin. Der Generator
soll Fachterminologie und wahrscheinliche öffentliche Suchsprache
überbrücken.

Ein spezifischer Museumsbegriff kann bestehen bleiben, sollte aber von
einem Oberbegriff begleitet werden, wenn eine Laiin ihn sonst nicht finden
würde.

### Evidenz vor Inferenz

Der Generator erhält:

- das Originalbild;
- eine konsolidierte Master Caption;
- zwei rohe visuelle Beobachtungen;
- Museumsmetadaten.

Er wird angewiesen, im Bild fehlende Information zu nutzen, wenn die
Museumsmetadaten sie explizit liefern, und offensichtliche visuelle Evidenz
zu nutzen, auch wenn historische Erschließung sie nie erfasst hat.
Unbelegte Inferenz ist nicht erlaubt.

### `term` + `why`

Jedes vorgeschlagene Schlagwort trägt eine kurze evidenzbasierte
Begründung.

Das ist keine dekorative Erklärung. Es zwingt den Generierungsschritt, die
Grundlage für den Begriff offenzulegen, damit die nächste Stufe sie
auditieren kann.

### Trennung von bestehenden strukturierten Metadaten

Die Default-Policy schließt Information aus, die normalerweise bereits zu
anderen strukturierten Feldern gehört, darunter reines Material/Technik,
Daten und bloße Personen- oder geografische Namen. Das Ziel ist nicht, den
Quelldatensatz als Wortsammlung zu reproduzieren, sondern Erschließungswert
hinzuzufügen.

### Kontrollierter Umgang mit sensibler Interpretation

Der Prompt enthält eine evidenzgebundene kritische/dekoloniale Schicht. Er
soll Gewalt, rassistische Darstellung, kolonialen Kontext oder
problematische Provenienzsprache benennen, wenn Evidenz diese Lesart
stützt, wird aber explizit angewiesen, neutrale Objekte nicht standardmäßig
in eine kritische Erzählung zu verwandeln.

Das ist eine Referenzpolicy und kann von einer anderen Institution
angepasst werden.

---

# Warum es ein separates Audit statt eines einzelnen "vorsichtigen" Modells gibt

Bei der Schlagwort-Anreicherung heißt das zweite Modell **Audit**, nicht
ein freier zweiter Tagger.

Diese Unterscheidung ist wichtig.

Das Audit wird angewiesen, **keinen direkten Grün/Gelb/Rot-Status** zu
vergeben. Es klassifiziert jedes vorgeschlagene Schlagwort in eine feste
Menge von Fehlerklassen wie:

- Pluralform;
- Adjektiv statt bevorzugter Substantivform;
- Ad-hoc-Kompositum;
- fehlende Laiensprache-Brücke;
- falsches Cluster;
- keine Evidenz;
- Halluzination;
- Material-/Technik-Leck;
- Datums-Leck;
- bloßer geografischer/Personenname;
- Spekulation/Zirkelschluss;
- unbelegte asymmetrische/ethnisierende Interpretation;
- Redundanz.

Eine deterministische Policy übersetzt diese Fehlerklassen dann in
Maschinenaktionen:

```text
keine Fehlerklasse
      ↓
     keep

reparierbares Formproblem
      ↓
    repair

falsches Cluster
      ↓
     move

nicht belegt / halluziniert / verbotener Inhalt
      ↓
    reject
```

Dieses Design verhindert bewusst, dass dasselbe probabilistische
Review-Modell sowohl ein Problem identifiziert als auch die operative
Konsequenz erfindet.

Eine separate Repair-Rolle wird nur für Begriffe aufgerufen, die die
Policy als reparierbar einstuft. Nur akzeptierte/reparierte Begriffe gehen
weiter in den optionalen GND-Abgleich.

Diese Sequenz ist eine der zentralen Qualitätssicherungs-Ideen in der
Referenzimplementierung:

```text
generieren → Fehler klassifizieren → deterministische Policy → reparieren, wenn möglich → Normdaten
```

---

# Optionaler GND-Normdatenabgleich

Die GND-Integration ist optional und bleibt von der Schlagwortgenerierung
getrennt.

Das System erzeugt und auditiert zuerst einen nützlichen Museums-/
Suchbegriff. Es zwingt den Generator **nicht**, vorzugeben, dass jedes
gültige Schlagwort bereits ein Normdaten-Begriff sein muss.

Für akzeptierte Schlagwörter:

```text
Schlagwort + Cluster + Evidenz
          │
          ▼
OpenSearch-Retrieval gegen GND-Sachdaten
          │
          ▼
mehrere Kandidaten
          │
          ▼
LLM-Abgleich
          │
      ┌───┴────┐
      │        │
   Treffer  no_match
```

`no_match` ist ein legitimes Ergebnis. Ein falscher Normdaten-Identifikator
ist schlimmer als ein nicht gemappter, aber nützlicher Erschließungsbegriff.

Der GND-Datensatz selbst wird nicht als statischer Repository-Snapshot
mitgeliefert; das Import-Tooling zeichnet die Upstream-Provenienz auf.

---

# Machine Heart: optionale Wirkungslesarten

Das Emotion-Modul ist optional. Anders als Topics liefert das Repository
aber eine vollständige museumsagnostische Default-Methode namens
**Machine Heart**.

Ein Museum hat drei Optionen:

1. Emotion nicht laufen lassen;
2. Machine Heart wie mitgeliefert nutzen;
3. Vokabular und/oder Prompts durch eine andere Methode ersetzen, bei
   gleichbleibender Pipeline-Schnittstelle.

## Was Machine Heart tut — und was nicht

Machine Heart beansprucht **nicht**, die Emotion einer dargestellten Person
zu erkennen, und erklärt nicht, dass ein Objekt objektiv melancholisch,
nostalgisch oder bedrohlich *ist*.

Seine epistemische Form:

> **Dieses Objekt kann gelesen werden als / kann die Wirkung haben ...**

Die Methode trennt vier Ebenen:

```text
A  sichtbarer Befund
B  dargestellte Situation
C  mögliche affektive Wirkung   ← getaggt
D  psychischer Zustand einer Person  ← nie erschlossen
```

Das mitgelieferte redaktionelle Wissensmodell enthält **146 Konzepte**. Die
getestete Runtime-Sicht gibt **121 `resonance_reading`-Konzepte** an
Generator und Judge weiter; die restlichen Konzepte bleiben Teil des
redaktionellen Modells, sind aber keine Runtime-Lesarten.

Für v1.0 reproduziert die Runtime-Projektion bewusst den getesteten
Produktionsadapter. Jedes der 121 aktiven Konzepte gibt nur eine minimale
Feldmenge weiter: `concept_id`, `begriff`, `definition` und, wo definiert,
`nicht_verwenden_wenn`. Die reichhaltigere 146-Konzepte-Redaktionsdatei
erfasst zusätzlich Rollen, Kontextanforderungen, Abgrenzungen, Provenienz
und PAD-Metadaten. Diese reichhaltigeren Felder sind für Methodentransparenz
und zukünftige/eigene Adapter veröffentlicht, werden aber **nicht
automatisch in den aktuellen Generator-/Judge-Prompt-Kontext injiziert**. Da
die Runtime-Projektion bereits auf `resonance_reading` gefiltert hat,
geschieht die Rollenauswahl vor dem Prompt. Ein Museum, das reichhaltigere
Runtime-Constraints will, sollte seinen Vokabular-Adapter und die Prompts
gemeinsam versionieren und die Methode neu validieren.

Jede Lesart sollte durch Evidenz gestützt sein, und der Judge prüft auf
häufige Fehler wie Psychologisierung von Personen, Nostalgie-Ableitung
allein aus Alter/Sepia, Verwechslung von Formeigenschaft mit Wirkung, oder
das Glattbügeln bedeutsamer Spannung.

Eine eigene Emotionsdatenbank kann ein völlig anderes internes Schema
haben. Sie muss nur den veröffentlichten Runtime-Vokabular-Vertrag
erfüllen.

Siehe [`docs/EMOTION_METHOD.md`](docs/EMOTION_METHOD.md).

---

# Institutionelle Topics: Engine öffentlich, Wissen privat

Institutionelle Sammlungsschwerpunkte unterscheiden sich grundlegend von
Machine Heart.

Das Repository veröffentlicht die **Topics-Engine**, Schemas, Prompts und
den Bauvertrag. Es veröffentlicht bewusst **nicht** das tatsächliche
Themenframework der Institution oder das private Ausgangsdokument, aus dem
dieses Framework entwickelt wurde.

Ein Museum, das `core-topics` oder `full` nutzen will, muss deshalb seine
eigene Wissensbasis bereitstellen.

## Benötigte institutionseigene Ressourcen

```text
profiles/<museum>/topics/
  profile.yaml
  framework.md
  taxonomy.json
```

Ein nützliches `framework.md` sollte für jedes Thema definieren:

- Erkenntnisinteresse / Scope;
- was eingeschlossen ist;
- was explizit nicht ausreicht;
- Evidenzregeln auf Objektebene;
- optionale Retrieval-Anker;
- Sensitivitäts-/Reviewregeln.

Eine nützliche `taxonomy.json` sollte stabile Unterthema- und
kontrollierte-Begriff-IDs plus `use_when`/`do_not_use_when`-Hinweise
ergänzen.

Die produktionsgetestete Implementierung nutzte eine Wissensbasis in der
Größenordnung von **8 Themen, 64 Unterthemen und 104 kontrollierten
Begriffen**. Diese Zahlen werden offengelegt, um eine getestete
Größenordnung zu zeigen. Die Themennamen, Definitionen, Anker und das
zugrundeliegende Strategiedokument sind nicht Teil des öffentlichen
Repositories.

Die entscheidende epistemische Regel:

> **Das Framework erklärt, was ein Thema bedeutet. Es ist kein Beleg, dass
> ein bestimmtes Objekt zum Thema gehört.**

Der Generator schlägt evidenzbasierte Beziehungen vor. Der unabhängige
Judge bewertet alle konfigurierten Themen erneut und kann eine Beziehung
bestätigen, korrigieren, herabstufen, entfernen oder ergänzen.

Die aktuellen maschinenlesbaren Topic-Schemas behalten noch einige deutsche
Schlüsselnamen aus der getesteten Implementierung (zum Beispiel
`schwerpunkte`). Diese Schlüssel sind ein Detail des versionierten
API-Vertrags; sie legen **nicht** die Themennamen, Definitionen oder das
strategische Wissen der Institution offen.

Die SQL-Dateien unter `database/migrations/` sind Upgrade-Hilfen für
Installationen von vor der Veröffentlichung. Sie erwähnen notwendigerweise
frühere deutsche Ergebnistabellen-/Spaltennamen, enthalten aber **kein**
Themenframework, keine Taxonomie, keine Anker und keine kontrollierten
Begriffe. Frische Installationen nutzen die generischen Schemas unter
`database/core.sql` und `database/modules/`.

Siehe [`docs/TOPIC_KNOWLEDGE_BASE.md`](docs/TOPIC_KNOWLEDGE_BASE.md).

---

# Museologische Leitplanken

Das Projekt kodiert mehrere Grenzen, die für Implementierer sichtbar
bleiben sollen. Die vollständigen zwölf Prinzipien mit Beispielen stehen in
[`docs/MUSEOLOGICAL_PRINCIPLES.md`](docs/MUSEOLOGICAL_PRINCIPLES.md); hier
nur die Kurzfassung:

- **Quelle und Anreicherung bleiben getrennt** — die Pipeline besitzt ihre
  eigenen Ausgabetabellen und überschreibt historische Katalogdokumentation
  nicht still.
- **Beobachtung ist nicht Interpretation** — eine sichtbare Eigenschaft wie
  Symmetrie ist nicht automatisch eine Wirkung wie Ruhe oder Feierlichkeit.
- **KI-Ausgaben sind Vorschläge mit Herkunft** — Modellrolle, Begründung,
  Review-Entscheidung, Status und Evidenz werden wo sinnvoll gespeichert.
- **Mehrere Modelle erzeugen keine Wahrheit** — Generator/Judge-Strukturen
  sind Qualitätssicherung, keine epistemische Beglaubigung.
- **Normdaten sind optionaler Abgleich** — nicht jeder nützliche Museums-
  oder Erschließungsbegriff muss in einen Normdatensatz gezwungen werden.
- **Sensible Inferenz braucht stärkere Evidenz** — Erscheinung, Name, Datum
  oder geografische Nähe allein sollten keine identitätsbezogenen,
  politischen, kolonialen, migrationsbezogenen oder anderen sensiblen
  historischen Aussagen erzeugen.
- **Embedding-Nähe ist keine historische Bedeutung** — Vektor-Nachbarn sind
  algorithmische Ähnlichkeiten, keine kuratorische oder historische
  Identität.
- **Observability kann Museumsdaten enthalten** — Phoenix/OpenTelemetry-
  Tracing ist standardmäßig deaktiviert. Aktiviert, können LLM-Spans
  gekürzten Prompt-/Ausgabetext und Objekt-IDs enthalten. Ebenso geben `-v`
  und `-vv` bewusst zunehmend detaillierte Prompts, Antworten und
  Zwischenstrukturen aus. Tracing-Backends und Verbose-Logs als
  Datenziele behandeln, die unveröffentlichte Sammlungsinformationen oder
  personenbezogene Daten empfangen können; nur nach den üblichen
  Sicherheits-/Data-Governance-Regeln der Institution aktivieren.

Der Embedding-Service, der bei `image_url`-Assets selbst HTTP-Requests auf
museumsdatenbank-kontrollierte URLs stellt, ist zusätzlich gegen SSRF
gehärtet (Schema-Whitelist, Sperre privater/interner Adressbereiche,
Redirect-Rewalidierung, Downloadlimits) — siehe
[`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) und
[`SECURITY.md`](SECURITY.md).

---

# Installation

## Voraussetzungen

Für das Referenz-Zwei-Host-Deployment:

- Linux-CPU-/Orchestrator-Host;
- Docker + Compose;
- Git;
- Python 3.11+;
- ausreichend CPU-Host-Storage/RAM für das dockerisierte PostgreSQL und die
  Embedding-Services;
- vorbereiteter NVIDIA-GPU-Host **oder** ein existierender
  OpenAI-kompatibler Endpoint;
- optionaler S3-kompatibler Object Storage;
- Hugging-Face-Zugangsdaten, wo ein gated Upstream-Modell sie benötigt;
- Museums-Quelldaten und Bildzugriff.

Der Installer konfiguriert den Applikations-Stack. Er bestellt keine
Cloud-Server, legt keine DNS-Zonen an, erstellt keine S3-Accounts und
erfindet keine Quelldatenbank.

## CLI klonen und installieren

```bash
git clone https://github.com/sebastianruffberlin/AI-Museum-Pipeline.git
cd AI-Museum-Pipeline
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e .
```

Die folgenden Befehle nutzen den installierten `museum-pipeline`-Entrypoint.
Zuerst die virtuelle Umgebung aktivieren oder den Befehl mit `.venv/bin/`
voranstellen.

## Museumsprofil anlegen

```bash
museum-pipeline init-profile my-museum
```

Der Profilname muss ein Slug sein (Kleinbuchstaben, Ziffern, Bindestriche,
beginnend mit einem Buchstaben). `id`/`name` im neuen `profile.yaml` werden
automatisch passend gesetzt.

Dann prüfen und bearbeiten:

```text
profiles/my-museum/
  metadata.yaml
  profile.yaml
  prompts/
  tagging/
  authority/
  emotion/       # vollständiger Machine-Heart-Default; kann behalten oder ersetzt werden
  topics/        # nur Bauplan; institutionseigener Inhalt muss erstellt werden
```

Der Starter enthält bereits den für `core-emotion` benötigten
Metadaten-Kontext. Er enthält außerdem ein konservatives
`contexts.topics`-Beispiel, aber Topics bleibt deaktiviert, bis das Museum
`framework.md`, `taxonomy.json` und ein Topics-Profil liefert.

## Deployment-Konfiguration und Secrets

```bash
cp deployment.example.yaml deployment.yaml
cp installer.env.example .env
chmod 600 .env
```

Infrastrukturentscheidungen in `deployment.yaml`, Zugangsdaten in `.env`
halten. Das öffentliche Beispiel startet mit `features.s3: false` und
`features.gnd: false`; optionale Infrastruktur nur aktivieren, wenn das
Museumsprofil sie tatsächlich nutzt. Bei `gpu.mode: managed` muss
`gpu.deployment_path` explizit gesetzt werden — es gibt keinen
institutionsspezifischen Default; `infra/gpu/generic` ist der generische
Einstieg, `infra/gpu/stadtmuseum-berlin/h100-80gb` die real getestete
H100-Referenzkonfiguration. Generierte GPU-/Runtime-Secret-Dateien werden
außerhalb des Git-Checkouts gehalten.

## Installieren

```bash
museum-pipeline install --dry-run
museum-pipeline install
museum-pipeline doctor
```

`doctor` validiert Konfiguration und Service-Bereitschaft. Es sollte nicht
als vollständiger Akzeptanztest auf Anwendungsebene behandelt werden.

Siehe [`docs/INSTALLER.md`](docs/INSTALLER.md) und
[`docs/MANUAL_DEPLOYMENT.md`](docs/MANUAL_DEPLOYMENT.md).

---

# Minimale Laufzeitnutzung

```bash
museum-pipeline show-config
museum-pipeline validate-config
museum-pipeline run --workflow core --count 1 -v
```

Nützliche Lauf-Steuerungen:

```text
--ids
--ids-file
--collection
--force
--retry-failed
```

Mit einem kleinen, bekannten Objektset starten, bevor ein neues Profil
skaliert wird.

---

# Referenz-Modellstack

Das Repository enthält Modellkonfiguration, keine Modellgewichte.

Der verifizierte Referenzstack nutzt Qwen/Gemma-GGUF-Modelle hinter einem
OpenAI-kompatiblen Endpoint sowie folgende Embedding-Familien:

- SigLIP2;
- DINOv3;
- BGE-M3;
- BGE-Reranker (`BAAI/bge-reranker-v2-m3`) als optionaler Late-Ranking-Service-Endpoint.

Das H100-Hardware-Profil unter `hardware/h100-80gb.yaml` und das
entsprechende GPU-Referenzdeployment enthalten kalibrierte
Context-/Parallelitätswerte. Sie sollten nicht blind auf eine andere GPU
übertragen werden.

Das kalibrierte Bundle liegt aktuell unter
`infra/gpu/stadtmuseum-berlin/h100-80gb/`, weil es das gemessene
Referenzdeployment der ursprünglichen Implementierung dokumentiert. Der
Verzeichnisname ist Provenienz, keine museumssemantische Abhängigkeit: eine
andere Institution kann dasselbe Hardware-Bundle nutzen oder ein anderes
kalibriertes Deployment über `gpu.deployment_path` bereitstellen — der
museumsagnostische Standardeinstieg dafür ist `infra/gpu/generic`.

Modellgewichte und Upstream-Datensätze behalten ihre eigenen Lizenzen und
Zugangsbedingungen. Siehe [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

# Reproduzierbarkeit und Qualitäts-Gates

Das öffentliche Release ist darauf ausgelegt, die getestete Architektur
einsehbar zu machen. Das Repository enthält:

- CPU- und GPU-Compose-Verträge;
- Referenz-Runtime-Informationen;
- H100-Concurrency-Vertragsprüfung;
- Unit-/Contract-Tests;
- explizite Modell- und GND-Provenienzregeln;
- Clean-Room-Deployment-Dokumentation;
- einen manuell verifizierten CPU-↔-frischer-H100-Ende-zu-Ende-Pfad;
- Release-Secret-Scanning- und Dependency-Audit-Anleitung.

Siehe [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) und
[`docs/FRESH_HOST_CHECKLIST.md`](docs/FRESH_HOST_CHECKLIST.md).

---

# Repository-Karte

```text
database/        pipeline-eigene Persistenzschemas und optionale Module
deploy/          Pipeline-Container
profiles/        Museumsprofile und Starter-Template
models/          logische Model-Role-Profile
hardware/        kalibrierte Hardware-Profile
workflows/       Modul-Presets
src/             museumsagnostischer Python-Core und Skills
services/        Embedding-, Presign- und Farbnamen-Utilities
infra/           CPU-/GPU-Deployment-Definitionen
examples/        synthetische öffentliche Ausgabebeispiele
docs/            Architektur-, Methoden- und Deployment-Dokumentation
tests/           strukturelle, verhaltensbezogene und Release-Verträge
```

---

# Dokumentations-Leitfaden

Vollständige Navigation nach Erfahrungsstufe und Themenseite:
[`docs/START_HERE.md`](docs/START_HERE.md).

| Dokument | Lesen für |
| --- | --- |
| [`docs/START_HERE.md`](docs/START_HERE.md) | Orientierung, 3×2-Navigation (Einsteiger/Intermediate/Profi × museologisch/technisch) |
| [`docs/WORKFLOW.md`](docs/WORKFLOW.md) | Verarbeitungsfluss pro Objekt |
| [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) | Konfigurationsmodell, Services und Topologie |
| [`docs/PROFILES.md`](docs/PROFILES.md) | Profil-/Konfigurationsmodell, Schritt-für-Schritt-Einrichtung |
| [`docs/MUSEUM_DESIGN_DECISIONS.md`](docs/MUSEUM_DESIGN_DECISIONS.md) | **warum die 11 Cluster, Prompts/Audit, Farben und Topics so gestaltet sind** |
| [`docs/MUSEOLOGICAL_PRINCIPLES.md`](docs/MUSEOLOGICAL_PRINCIPLES.md) | interpretative Leitplanken |
| [`docs/EMOTION_METHOD.md`](docs/EMOTION_METHOD.md) | Machine Heart und eigener Emotion-Ressourcen-Vertrag |
| [`docs/TOPIC_KNOWLEDGE_BASE.md`](docs/TOPIC_KNOWLEDGE_BASE.md) | Bauvertrag für institutionseigene Topics |
| [`docs/INSTALLER.md`](docs/INSTALLER.md) | Installer-Verhalten |
| [`docs/MANUAL_DEPLOYMENT.md`](docs/MANUAL_DEPLOYMENT.md) | manuelles Deployment |
| [`docs/FRESH_HOST_CHECKLIST.md`](docs/FRESH_HOST_CHECKLIST.md) | Abnahme-Checkliste für frischen Host |
| [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | Reproduzierbarkeitspolicy |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | Stand und nächste Schritte |
| [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) | externe Modelle, Daten und Komponenten |
| [`SECURITY.md`](SECURITY.md) | Security-Meldung und Umgang mit Secrets |
| [`CONTRIBUTING.md`](CONTRIBUTING.md) | Mitwirken, Entwicklungsumgebung, Pull-Request-Erwartungen |

---

# Sprachhinweis

Die Repository-Dokumentation ist auf Deutsch geschrieben: Die Referenz-
integration nutzt die GND, die Referenzprompts und das getestete
Referenzdeployment richten sich an deutschsprachige Museumsdokumentation,
und die realistische Zielgruppe dieses Projekts sind deutschsprachige
Institutionen. Der Python-Core selbst ist sprachagnostisch — Feldnamen,
Rollen und Schemas im Code sind Englisch, aber nirgends von einer
bestimmten natürlichen Sprache abhängig. Ein Museum mit anderer
Zielsprache kann eigene Prompts, Terminologie und `output_language` im
Museumsprofil setzen, ohne den Core zu ändern.

---

# Lizenz

Originalcode und projekteigenes Material in diesem Repository stehen unter
der MIT-Lizenz; siehe [`LICENSE`](LICENSE).

Drittanbieter-Modellgewichte, Normdaten, Farbnamen-Quellen, Datensätze und
Laufzeitkomponenten behalten ihre eigenen Lizenzen und Bedingungen. Siehe
[`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

---

# Projektursprung

AI Museum Pipeline ist die modulare Python-Fortführung des früheren
[n8n-basierten AI-Museum-Tagging-Projekts](https://github.com/sebastianruffberlin/AI-Museum-Tagging).

Das Legacy-Repository dokumentiert den ursprünglichen n8n-/SeaTable-
Workflow. Dieses Repository enthält die aktuelle Architektur und wird als
aktive Implementierung gepflegt.

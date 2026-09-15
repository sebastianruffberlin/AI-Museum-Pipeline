# Museologische Prinzipien

Die Pipeline ist nicht nur ein technischer Workflow.

Ihre Architektur enthält fachliche Annahmen darüber, was maschinelle
Erschließung in einem Museum darf, leisten kann und sichtbar machen muss.


# 1. Quelle und Anreicherung bleiben getrennt

Vorhandene Museumsdokumentation ist nicht dasselbe wie KI-generierte
Anreicherung.

Die Pipeline schreibt Ergebnisse deshalb in eigene Tabellen und Felder.

Die Pipeline soll keine historische Dokumentation still überschreiben.


# 2. Beobachtung ist nicht Interpretation

Ein sichtbarer Befund ist etwas anderes als seine Deutung.

Beispiel:

    sichtbarer Befund:
        starke Symmetrie

    mögliche Wirkung:
        kann als streng oder feierlich wirken

Die zweite Aussage ist interpretativ und muss auch so behandelt werden.


# 3. KI-Ausgaben sind propositionale Daten

Die Pipeline behandelt generierte Aussagen als Vorschläge mit Herkunft,
nicht als automatische Wahrheit.

Deshalb werden wo sinnvoll gespeichert:

- verwendetes Modell,
- Prompt-/Vokabularversion,
- Begründung,
- Prüfentscheidung,
- Status,
- Quellen/Evidenz.


# 4. Mehrere Modelle statt einer einzigen Autorität

Der Referenzflow nutzt für zentrale interpretative Aufgaben
Generator-/Judge-Strukturen.

Das bedeutet nicht, dass zwei Modelle automatisch Wahrheit erzeugen.

Der Zweck ist vielmehr:

- Fehler sichtbar machen,
- verschiedene Modellperspektiven gegeneinander prüfen,
- Entscheidungen strukturiert dokumentieren.


# 5. Normdaten nur dort, wo sie passen

Die GND ist im deutschen Museums- und Bibliothekskontext eine wertvolle
Referenz.

Aber:

> Nicht jeder gute Museumsbegriff ist ein GND-Sachbegriff.

Deskriptive Begriffe, feine visuelle Eigenschaften oder
institutionsspezifische Konzepte werden deshalb nicht zwangsläufig auf eine
Normdatei gezwungen.

`no_match` ist ein legitimes Ergebnis.


# 6. Emotion ist keine Emotionserkennung

Das optionale Referenzmodul "Machine Heart" beschreibt mögliche
Wirkungslesarten.

Die Form lautet:

> kann wirken als ...

und nicht:

> ist ...

Dargestellten Menschen werden keine inneren Zustände zugeschrieben.

Alter, Sepia, Patina oder historische Datierung sind nicht automatisch
Belege für Nostalgie oder Melancholie.


# 7. Spannungen dürfen bestehen bleiben

Museumsobjekte sind nicht eindimensional.

Eine Darstellung kann zum Beispiel gleichzeitig:

- idyllisch und bedrohlich,
- feierlich und gewaltförmig,
- vertraut und fremd wirken.

Der Referenzansatz versucht solche Spannungen nicht automatisch aufzulösen.


# 8. Institutionelle Themen sind Beziehungen, keine Naturgesetze

Ein Sammlungsschwerpunkt ist eine Perspektive des Museums auf seinen
Bestand.

Deshalb wird ein Objekt nicht exklusiv einem Thema "einsortiert".

Stattdessen werden begründete Beziehungen vorgeschlagen.

Mehrfachbezüge sind möglich.

Auch "kein belastbarer Bezug" ist ein valides Ergebnis.


# 9. Institutionelle Entscheidungen gehören ins Profil

Welche Begriffe sinnvoll sind, welche Themen relevant sind oder welche
Metadaten als Evidenz gelten, ist keine rein technische Entscheidung.

Deshalb gehören solche Festlegungen in:

    profiles/<museum>/

und nicht in den museumsagnostischen Python-Core.


# 10. Embeddings sind Werkzeuge, keine Ontologie

Visuelle oder textuelle Nähe in einem Vektorraum bedeutet nicht automatisch
historische, semantische oder kuratorische Gleichheit.

Embeddings eignen sich hervorragend für:

- Exploration,
- Retrieval,
- Nachbarschaften,
- Cluster,
- Inspiration.

Ihre Ergebnisse müssen aber als algorithmische Nähe verstanden werden.


# 11. Nachvollziehbarkeit vor scheinbarer Präzision

Die Referenzarchitektur bevorzugt nachvollziehbare qualitative Aussagen vor
scheinpräzisen Zahlenwerten, wenn keine belastbare Kalibrierung existiert.

Insbesondere interpretative Module sollen keine mathematische Sicherheit
vortäuschen, die das Verfahren nicht besitzt.


# 12. Ein anderes Museum darf andere Entscheidungen treffen

Das Stadtmuseum-Profil ist kein Standard dafür,

- welche Themen Museen haben sollen,
- welche Wirkungen relevant sind,
- welche Metadatenfelder verwendet werden müssen.

Es ist ein dokumentierter Referenzfall.

Andere Häuser sollen die Pipeline fachlich verändern können, ohne den
technischen Core umzuschreiben.

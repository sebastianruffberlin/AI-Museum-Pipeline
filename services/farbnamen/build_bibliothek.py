#!/usr/bin/env python3
"""
Baut die vereinheitlichte Farbnamen-Bibliothek aus den fuenf Quelldateien.

Prinzipien:
  - Die Quelldateien sind die Wahrheit; dieses Skript fuegt nur zusammen.
  - KEINE Deduplizierung zwischen Quellen: "Prussian Blue" existiert in
    Werner, Ridgway und bestof mit jeweils leicht anderem Wert - das ist
    gewollt (1:n-Mapping). Jeder Eintrag kennt seine Quelle.
  - Innerhalb einer Quelle wird auf (name, hex) dedupliziert.
  - Alle LAB-Werte wurden mit den sRGB->LAB-Formeln (D65) aus
    bildmetadaten_v3_bmp.js berechnet - derselbe Raum wie
    enrichment_derived.farben.

Ausgabe: bibliothek_lab.json
  { meta: {...}, farben: [ {name, hex, L, a, b, chroma, quelle, sprache, ...} ] }
"""
import json, os, collections

QUELLEN = [
    "meodai_farbnamen_de_lab.json",   # de  - primaere Anzeigesprache
    "css_named_lab.json",             # en  - normierter Anker
    "werner_1821_lab.json",           # en  - historisch, Naturbeispiele
    "ridgway_1912_lab.json",          # en  - historisch, 1100+ Namen
    "meodai_bestof_lab.json",         # en  - breite Alltagsabdeckung
]

hier = os.path.dirname(os.path.abspath(__file__))
alle, stats = [], collections.OrderedDict()
for q in QUELLEN:
    d = json.load(open(os.path.join(hier, q)))
    gesehen, n = set(), 0
    for e in d["farben"]:
        k = (e["name"], e["hex"])
        if k in gesehen:
            continue
        gesehen.add(k)
        alle.append(e)
        n += 1
    stats[d["farben"][0]["quelle"]] = n

meta = {
    "beschreibung": "Vereinheitlichte Farbnamen-Bibliothek der Museums-Suchmaschine",
    "quellen": stats,
    "gesamt": len(alle),
    "sprachen": dict(collections.Counter(e["sprache"] for e in alle)),
    "lab": "sRGB->LAB D65, Formeln identisch mit bildmetadaten_v3_bmp.js",
    "hinweis": "Keine Deduplizierung zwischen Quellen (1:n-Mapping gewollt); Details und Lizenzen in den Quelldateien",
}
json.dump({"meta": meta, "farben": alle},
          open(os.path.join(hier, "bibliothek_lab.json"), "w"),
          ensure_ascii=False, indent=1)
print(json.dumps(meta, ensure_ascii=False, indent=2))

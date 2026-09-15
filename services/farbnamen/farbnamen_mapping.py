#!/usr/bin/env python3
"""
Farbnamen-Mapping: enrichment_derived.farben -> benannte Farben.

Liest die salienten LAB-Farben jedes Objekts und ordnet ihnen Namen
aus der Bibliothek (bibliothek_lab.json) zu - pro Farbe nach Rollen
getrennt nach funktionalen Rollen:

  grundfarbe   kontrolliertes Vokabular (~14 Worte) -> DIE Facette
  deskriptor   deterministischer deutscher Name aus LAB abgeleitet
               ("Dunkles Blaugruen") -> deckt per Konstruktion 100%
  anzeige      attestierter deutscher Name, falls nah genug
  synonyme     beste englische Namen aller Quellen -> BM25-Futter
  fach         Werner/Ridgway separat -> historisches Fachvokabular

Distanz: gewichtetes DeltaE in LCh-Zerlegung. Bei bunten Paaren wird
die Farbton-Komponente staerker gewichtet (ein sattes Rot darf nicht
"Braun" heissen); bei unbunten Farben (C<8) ist der Winkel Rauschen
und L entscheidet.

Aufruf:
  python3 farbnamen_mapping.py --test          eingebaute Fixtures
  python3 farbnamen_mapping.py                 DB-Lauf (PG_DSN), nur
                                               Zeilen ohne farbnamen
  python3 farbnamen_mapping.py --force         alles neu berechnen
Vorher einmalig:
  ALTER TABLE museum.enrichment_derived
    ADD COLUMN IF NOT EXISTS farbnamen jsonb;
"""
import argparse
import json
import math
import os
import sys

HIER = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------- Schwellen
DE_MAX      = 12.0   # Schwelle fuer synonyme/fach (wie hybrid_search-Philosophie)
DE_MAX_ANZ  = 18.0   # grosszuegiger fuer den attestierten deutschen Namen ...
HUE_WACHE   = 35.0   # ... aber nur, wenn der Farbtonwinkel nicht kippt (Grad)
C_UNBUNT    = 11.0   # darunter gilt die Farbe als unbunt
DL_WACHE    = 15.0   # Anzeige: Helligkeit des Namens darf nicht kippen
TOP_SYNONYME = 5
TOP_FACH     = 2


# ---------------------------------------------------------------- Distanz
def lch(e):
    C = math.hypot(e["a"], e["b"])
    h = math.degrees(math.atan2(e["b"], e["a"])) % 360
    return e["L"], C, h


def hue_diff(h1, h2):
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def gew_dE(f, e):
    """
    Gewichtetes DeltaE zwischen Objektfarbe f und Bibliothekseintrag e.

    Zerlegung in Helligkeit (dL), Buntheit (dC) und Farbton (dH wie in
    DeltaE94: 2*sqrt(C1*C2)*sin(dh/2)). Der Farbtonanteil wird mit der
    Buntheit hochgewichtet - je bunter beide, desto schwerer wiegt ein
    Winkelfehler. Unter C_UNBUNT faellt er ganz weg; stattdessen
    bestraft dC dort, dass unbunte Flaechen keine satten Namen ziehen.
    """
    L1, C1, h1 = lch(f)
    L2, C2, h2 = lch(e)
    dL = L1 - L2
    dC = C1 - C2
    if min(C1, C2) < C_UNBUNT:
        return math.sqrt(dL * dL + dC * dC)
    dh = math.radians(hue_diff(h1, h2))
    dH = 2 * math.sqrt(C1 * C2) * math.sin(dh / 2)
    wH = 1.0 + min(C1, C2) / 100.0          # 1.0 .. ~2.0
    return math.sqrt(dL * dL + dC * dC + (wH * dH) ** 2)


# ---------------------------------------------------------------- Deskriptor
# LAB-Hue-Anker (Grad): rot~25, gelb~90, gruen~160, blau~260, violett~315
TONE = [
    (0,   38,  "Rot"),
    (38,  62,  "Orange"),
    (62,  78,  "Gelborange"),
    (78,  102, "Gelb"),
    (102, 132, "Gelbgrün"),
    (132, 178, "Grün"),
    (178, 222, "Türkis"),
    (222, 240, "Blaugrün" ),   # petrolige Zone
    (240, 292, "Blau"),
    (292, 330, "Violett"),
    (330, 348, "Rotviolett"),
    (348, 361, "Rot"),
]


def deskriptor(L, a, b):
    """Deterministischer deutscher Farbname + Grundfarbe aus LAB."""
    C = math.hypot(a, b)
    h = math.degrees(math.atan2(b, a)) % 360

    # unbunt
    if C < C_UNBUNT:
        if L < 20:  return "Schwarz", "schwarz"
        if L > 85:  return "Weiß", "weiß"
        if L < 40:  return "Dunkelgrau", "grau"
        if L > 65:  return "Hellgrau", "grau"
        return "Grau", "grau"

    ton = next(t for lo, hi, t in TONE if lo <= h < hi)

    # Sonderfaelle im warmen Sektor. Braun nur in der Orange/Gelb-Zone -
    # ein dunkles sattes Rot (Weinrot) bleibt Rot, sonst wird jede
    # historische Fassung faelschlich "braun".
    if 30 <= h < 102 and L < 55 and C < 45:
        ton = "Braun"
    if ton == "Rot" and L > 68:
        ton = "Rosa"
    if ton in ("Gelborange", "Gelb") and L > 70 and C < 28:
        ton = "Beige"

    grund = {"Gelborange": "orange", "Gelbgrün": "grün", "Blaugrün": "blau",
             "Rotviolett": "violett"}.get(ton, ton.lower())

    # Attribute: Helligkeit vor Saettigung, maximal eines von jedem
    vor = []
    if L < 32:   vor.append("Dunkles")
    elif L > 72: vor.append("Helles")
    if C < 22:   vor.append("Gedecktes" if ton not in ("Braun", "Beige") else "")
    elif C > 55: vor.append("Kräftiges")
    name = " ".join(w for w in vor if w) + (" " if any(vor) else "") + ton
    return name.strip(), grund


# ---------------------------------------------------------------- Bibliothek
def lade_bibliothek():
    bib = json.load(open(os.path.join(HIER, "bibliothek_lab.json")))["farben"]
    return {
        "de":   [e for e in bib if e["sprache"] == "de"],
        "alle": bib,
        "fach": [e for e in bib if e["quelle"] in ("werner1821", "ridgway1912")],
    }


def beste(farbe, kandidaten, k, schwelle):
    scored = sorted(((gew_dE(farbe, e), e) for e in kandidaten), key=lambda x: x[0])
    return [(round(d, 1), e) for d, e in scored[:k] if d <= schwelle]


# ---------------------------------------------------------------- Kern
def benenne(farbe, bib):
    """farbe: {hex, L, a, b, anteil, salienz} -> Namensblock."""
    L, a, b = farbe["L"], farbe["a"], farbe["b"]
    desk, grund = deskriptor(L, a, b)
    _, C1, h1 = lch(farbe)

    # attestierter deutscher Name: grosszuegige Schwelle, aber drei Wachen -
    # Farbton, Helligkeit und (bei unbunten Objekten) Buntheit des Namens.
    anzeige = None
    schwelle_anz = DE_MAX if C1 < C_UNBUNT else DE_MAX_ANZ
    for d, e in beste(farbe, bib["de"], 5, schwelle_anz):
        L2, C2, h2 = lch(e)
        if abs(L - L2) > DL_WACHE:
            continue                      # "Dunkelgrau" fuer Hellgrau -> nein
        if C1 < C_UNBUNT:
            if C2 >= 9:
                continue                  # Grau bekommt keinen bunten Namen
            if C1 > 3 and C2 > 3 and hue_diff(h1, h2) > 90:
                continue                  # Farbstich-Richtung kippt (warm/kalt)
        if min(C1, C2) >= C_UNBUNT and hue_diff(h1, h2) > HUE_WACHE:
            continue                      # kippt in die Gegenfarbe -> nein
        anzeige = {"name": e["name"], "dE": d}
        break

    synonyme = [{"name": e["name"], "quelle": e["quelle"], "dE": d}
                for d, e in beste(farbe, bib["alle"], TOP_SYNONYME, DE_MAX)]
    fach = [{"name": e["name"], "quelle": e["quelle"], "dE": d}
            for d, e in beste(farbe, bib["fach"], TOP_FACH, DE_MAX)]

    return {
        "hex": farbe.get("hex"),
        "anteil": farbe.get("anteil"),
        "grundfarbe": grund,
        "deskriptor": desk,
        "anzeige": anzeige,
        "synonyme": synonyme,
        "fach": fach,
    }


def benenne_objekt(farben):
    """Liste der salienten Farben -> Namensbloecke + Objekt-Aggregat."""
    bib = _BIB
    bloecke = [benenne(f, bib) for f in farben]
    # Aggregat fuer die Facette: Grundfarben nach Flaechenanteil
    gewicht = {}
    for bl in bloecke:
        gewicht[bl["grundfarbe"]] = gewicht.get(bl["grundfarbe"], 0.0) + (bl["anteil"] or 0.0)
    facette = [g for g, _ in sorted(gewicht.items(), key=lambda x: -x[1]) if gewicht[g] >= 0.05]
    return {"farben": bloecke, "facette_grundfarben": facette}


_BIB = None


# ---------------------------------------------------------------- Fixtures
FIXTURES = {
    "DEMO-COLOR-001":      [{"L": 46.8, "a": 1.6,  "b": 19.7, "hex": "#7d6d4e", "anteil": 0.081},
                         {"L": 52.6, "a": 1.4,  "b": -9.0, "hex": "#787d8d", "anteil": 0.043},
                         {"L": 70.4, "a": -0.4, "b": 1.2,  "hex": "#acacaa", "anteil": 0.415},
                         {"L": 88.4, "a": -1.8, "b": 4.8,  "hex": "#dedfd5", "anteil": 0.043},
                         {"L": 77.0, "a": -0.5, "b": 1.4,  "hex": "#bebebc", "anteil": 0.258}],
    "DEMO-COLOR-002": [{"L": 65.9, "a": 10.1, "b": 57.2, "hex": "#cb9734", "anteil": 0.076},
                         {"L": 75.3, "a": -1.9, "b": 10.0, "hex": "#bebaa7", "anteil": 0.209},
                         {"L": 47.2, "a": -1.8, "b": 11.4, "hex": "#75705d", "anteil": 0.113},
                         {"L": 1.3,  "a": -0.9, "b": 0.9,  "hex": "#030502", "anteil": 0.416},
                         {"L": 22.6, "a": -3.7, "b": 5.2,  "hex": "#34372e", "anteil": 0.069}],
    "DEMO-COLOR-003":        [{"L": 19.3, "a": 27.2, "b": 1.4,  "hex": "#521c2e", "anteil": 0.08},
                         {"L": 56.4, "a": 7.9,  "b": 51.9, "hex": "#ab8027", "anteil": 0.016},
                         {"L": 36.7, "a": 1.3,  "b": -1.1, "hex": "#585658", "anteil": 0.268},
                         {"L": 70.0, "a": -0.8, "b": 1.6,  "hex": "#abaca8", "anteil": 0.243},
                         {"L": 78.3, "a": -0.8, "b": 0.1,  "hex": "#c0c2c1", "anteil": 0.15}],
}


# ---------------------------------------------------------------- Main
def main():
    global _BIB
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="Fixtures statt DB")
    ap.add_argument("--force", action="store_true", help="auch bereits benannte Zeilen")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    _BIB = lade_bibliothek()

    if args.test:
        for obj_id, farben in FIXTURES.items():
            print(f"\n=== {obj_id}")
            erg = benenne_objekt(farben)
            print("Facette:", erg["facette_grundfarben"])
            for bl in erg["farben"]:
                anz = bl["anzeige"]["name"] if bl["anzeige"] else "-"
                syn = ", ".join(s["name"] for s in bl["synonyme"][:3]) or "-"
                fach = ", ".join(f'{f["name"]} ({f["quelle"][:6]})' for f in bl["fach"]) or "-"
                print(f"  {bl['hex']}  [{bl['grundfarbe']:8s}] {bl['deskriptor']:22s}"
                      f" de: {anz:24s} syn: {syn}")
                print(f"           fach: {fach}")
        return

    # ---------------- Optionaler DB-Lauf ----------------
    import psycopg
    dsn = os.environ.get("PG_DSN")
    if not dsn:
        sys.exit("PG_DSN nicht gesetzt. Für den DB-Lauf eine PostgreSQL-Verbindungszeichenfolge bereitstellen.")
    wo = "" if args.force else "WHERE farbnamen IS NULL"
    lim = f"LIMIT {args.limit}" if args.limit else ""
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(f"SELECT obj_id, farben FROM museum.enrichment_derived {wo} ORDER BY obj_id {lim}")
        zeilen = cur.fetchall()
        print(f"{len(zeilen)} Objekte zu benennen")
        for i, (obj_id, farben) in enumerate(zeilen, 1):
            if isinstance(farben, str):
                farben = json.loads(farben)
            erg = benenne_objekt(farben or [])
            cur.execute(
                "UPDATE museum.enrichment_derived SET farbnamen = %s WHERE obj_id = %s",
                (json.dumps(erg, ensure_ascii=False), obj_id))
            if i % 200 == 0:
                conn.commit()
                print(f"  {i}/{len(zeilen)}")
        conn.commit()
    print("fertig")


if __name__ == "__main__":
    main()

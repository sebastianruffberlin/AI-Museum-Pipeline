"""
stage_000b.py — Bildelemente / Facetten (#000b_bildelemente_sub).

REINER 1:1-PORT des JS-Code-Nodes "Bildanalyse".
Kein ML-Modell, reine CPU-Mathematik: BMP-Decode -> LAB -> Farbstatistik ->
K-Means (k=6) -> Salienz -> Format/Farbigkeit. Schreibt enrichment_derived.

WICHTIG fuer "identisch im Ergebnis":
  - Alle Schwellwerte exakt uebernommen (chroma>8, chromaMittel<4,
    hueStreuung<0.18, ratio 1.15/0.87, TARGET 40000, k=6, iters=8, top-5).
  - Die Salienzformel ist bit-genau die des Originals.
  - K-Means-Initialisierung und Iterationsreihenfolge sind identisch:
    Zentren = points[floor(i*n/k)], Zuordnung in Pixel-(Sample-)Reihenfolge.
    Deshalb wird NICHT numpy-vektorisiert geclustert, sondern in genau der
    Schleifenlogik des JS-Codes — sonst koennten sich bei Gleichstand andere
    Cluster ergeben.

ABWEICHUNG ZUM BESTAND (bewusst, ergebnis-neutral):
  Der n8n-Flow erzeugt das BMP ueber einen Edit-Image-Node (ImageMagick,
  "resize, Maximum Area 500, Format bmp"), weil n8n require() sperrt. In
  Python haben wir Pillow — wir resizen selbst auf dieselbe "Maximum Area"
  (laengste Seite so, dass Flaeche ~ 500x500) und arbeiten direkt auf den
  RGB-Pixeln. Das Ergebnis der FARBSTATISTIK ist praktisch identisch, weil
  ohnehin auf ~40k Pixel gesubsamplet wird und die Facetten (Format,
  Farbigkeit, dominante Farben) gegen kleine Resampling-Unterschiede robust
  sind. Format kommt exakt aus dem Seitenverhaeltnis (unveraendert).

  >>> Diese eine Abweichung bitte bewusst absegnen. Wer 100% Bit-Treue auch
      hier will, muss den ImageMagick-BMP-Zwischenschritt nachbauen; das
      bringt aber keinen Ergebnisunterschied ausser Resampling-Rauschen.
"""

from __future__ import annotations

import io
import json
import math
from typing import Optional

import requests
from PIL import Image

from ..infrastructure import logsetup

_log = logsetup.get()


# ---------------------------------------------------------------------------
# sRGB -> LAB  (exakt die Koeffizienten des JS-Codes)
# ---------------------------------------------------------------------------
def _rgb2lab(r: float, g: float, b: float) -> tuple[float, float, float]:
    r /= 255.0; g /= 255.0; b /= 255.0
    r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
    g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
    b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722) / 1.0
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    def f(t: float) -> float:
        return t ** (1.0 / 3.0) if t > 0.008856 else (7.787 * t + 16.0 / 116.0)

    x = f(x); y = f(y); z = f(z)
    return (116.0 * y - 16.0, 500.0 * (x - y), 200.0 * (y - z))


def _lab2hex(L: float, a: float, b: float) -> str:
    y = (L + 16.0) / 116.0
    x = a / 500.0 + y
    z = y - b / 200.0

    def g3(t: float) -> float:
        t3 = t * t * t
        return t3 if t3 > 0.008856 else (t - 16.0 / 116.0) / 7.787

    x = 0.95047 * g3(x); y = 1.0 * g3(y); z = 1.08883 * g3(z)
    r = x * 3.2406 - y * 1.5372 - z * 0.4986
    gg = -x * 0.9689 + y * 1.8758 + z * 0.0415
    bb = x * 0.0557 - y * 0.2040 + z * 1.0570

    def gam(v: float) -> float:
        v = 12.92 * v if v <= 0.0031308 else 1.055 * (v ** (1.0 / 2.4)) - 0.055
        return max(0.0, min(1.0, v))

    def hx(v: float) -> str:
        return format(round(gam(v) * 255), "02x")

    return "#" + hx(r) + hx(gg) + hx(bb)


# ---------------------------------------------------------------------------
# K-Means (k=6, iters=8) — exakt die Schleifenlogik des JS-Codes.
# points: list[tuple[L,a,b]]  (Reihenfolge = Sample-Reihenfolge, wichtig!)
# ---------------------------------------------------------------------------
def _kmeans(points: list[tuple[float, float, float]], k: int, iters: int):
    n = len(points)
    cents = [list(points[(i * n) // k]) for i in range(k)]
    assign = [0] * n
    for _ in range(iters):
        for p in range(n):
            best = 0
            best_d = math.inf
            px = points[p]
            for c in range(k):
                dx = px[0] - cents[c][0]
                dy = px[1] - cents[c][1]
                dz = px[2] - cents[c][2]
                d = dx * dx + dy * dy + dz * dz
                if d < best_d:
                    best_d = d
                    best = c
            assign[p] = best
        sums = [[0.0, 0.0, 0.0, 0.0] for _ in range(k)]
        for p in range(n):
            c = assign[p]
            px = points[p]
            sums[c][0] += px[0]; sums[c][1] += px[1]
            sums[c][2] += px[2]; sums[c][3] += 1
        for c in range(k):
            if sums[c][3] > 0:
                cents[c] = [sums[c][0] / sums[c][3],
                            sums[c][1] / sums[c][3],
                            sums[c][2] / sums[c][3]]
    counts = [0] * k
    for a in assign:
        counts[a] += 1
    return [{"lab": cents[i], "anteil": counts[i] / n} for i in range(k)]


# ---------------------------------------------------------------------------
# Bild vorbereiten: "Maximum Area 500" wie im Edit-Image-Node, dann RGB.
# ---------------------------------------------------------------------------
def _load_rgb_maxarea(image_bytes: bytes, max_side_area: int = 500):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    # "Maximum Area": skaliere proportional, so dass die groessere Kante
    # auf max_side_area kommt (ImageMagick "500x500" bei Resize interpretiert
    # das als Bounding-Box; proportional).
    scale = min(max_side_area / w, max_side_area / h, 1.0)
    if scale < 1.0:
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))),
                         Image.BILINEAR)
    return img


# ---------------------------------------------------------------------------
# Hauptanalyse — Rueckgabe wie der JS-Node (dict fuer enrichment_derived).
# ---------------------------------------------------------------------------
def analyze(obj_id: str, image_bytes: bytes) -> dict:
    img = _load_rgb_maxarea(image_bytes)
    pw, ph = img.size
    px = img.load()

    # Pixel -> LAB + Statistik, Subsampling wie im Original.
    TARGET = 40000
    total = pw * ph
    step = math.ceil(total / TARGET) if total > TARGET else 1

    labs: list[tuple[float, float, float]] = []
    sumL = 0.0
    sumChroma = 0.0
    cosSum = 0.0
    sinSum = 0.0
    buntCount = 0

    for p in range(0, total, step):
        y, x = divmod(p, pw)
        r, g, b = px[x, y]
        lab = _rgb2lab(r, g, b)
        labs.append(lab)
        chroma = math.sqrt(lab[1] * lab[1] + lab[2] * lab[2])
        sumL += lab[0]
        sumChroma += chroma
        if chroma > 8:
            hue = math.atan2(lab[2], lab[1])
            cosSum += math.cos(hue)
            sinSum += math.sin(hue)
            buntCount += 1

    n = len(labs)
    helligkeitMittel = sumL / n
    chromaMittel = sumChroma / n

    hueStreuung = 0.0
    if buntCount > 20:
        R = math.sqrt(cosSum * cosSum + sinSum * sinSum) / buntCount
        hueStreuung = 1.0 - R

    if chromaMittel < 4:
        farbigkeit = "graustufen"
    elif hueStreuung < 0.18:
        farbigkeit = "monochrom_getönt"
    else:
        farbigkeit = "farbig"

    ratio = pw / ph
    if ratio > 1.15:
        fmt = "quer"
    elif ratio < 0.87:
        fmt = "hoch"
    else:
        fmt = "quadratisch"

    cluster = _kmeans(labs, 6, 8)

    # Salienz v2 — exakt die Formel des Originals.
    for c in cluster:
        dist = 0.0
        for other in cluster:
            dx = c["lab"][0] - other["lab"][0]
            dy = c["lab"][1] - other["lab"][1]
            dz = c["lab"][2] - other["lab"][2]
            dist += math.sqrt(dx * dx + dy * dy + dz * dz) * other["anteil"]
        chroma = math.sqrt(c["lab"][1] * c["lab"][1] + c["lab"][2] * c["lab"][2])
        c["salienz"] = dist * ((chroma + 12) / 40) * math.sqrt(c["anteil"])

    cluster.sort(key=lambda c: c["salienz"], reverse=True)
    farben = []
    for c in cluster[:5]:
        farben.append({
            "hex": _lab2hex(c["lab"][0], c["lab"][1], c["lab"][2]),
            "anteil": round(c["anteil"] * 1000) / 1000,
            "salienz": round(c["salienz"] * 100) / 100,
            "L": round(c["lab"][0] * 10) / 10,
            "a": round(c["lab"][1] * 10) / 10,
            "b": round(c["lab"][2] * 10) / 10,
        })

    _log.info("  #000b Bildmathe: %s/%s, %d Farben, chroma=%.1f, hell=%.1f",
              fmt, farbigkeit, len(farben),
              round(chromaMittel * 10) / 10, round(helligkeitMittel * 10) / 10)
    return {
        "obj_id": obj_id,
        "format": fmt,
        "farbigkeit": farbigkeit,
        "chroma_mittel": round(chromaMittel * 10) / 10,
        "hue_streuung": round(hueStreuung * 1000) / 1000,
        "helligkeit_mittel": round(helligkeitMittel * 10) / 10,
        "farben": json.dumps(farben, ensure_ascii=False),
    }

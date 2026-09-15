"""
logsetup.py — zentrales Logging fuer die Pipeline.

Stufen:
  (kein Flag)  -> INFO  : "Mittel". Pro LLM-Call eine Zeile (Modell, Dauer,
                          Prompt-/Antwortlaenge), DB-Writes mit Zeilenzahl,
                          Tag-Zaehlungen (gruen/gelb/rot), GND-Treffer.
  -v           -> INFO+ : zusaetzlich User-Prompt und Modell-Antwort VOLL.
  -vv          -> DEBUG : alles. Zwischenstrukturen (payload_valid/rejected,
                          Repair-Ergebnis, GND-Zuordnung) voll im Terminal.

Kuerzung: NUR die statischen, riesigen SYSTEM-Prompts (z.B. Tagging-System
24k Zeichen) werden auf erste/letzte 500 Zeichen gekuerzt — die aendern sich
nie und wuerden das Terminal fluten. User-Prompts (mit den echten
Objektdaten) und Modell-Antworten werden IMMER ungekuerzt gezeigt, sobald
die Stufe (-v/-vv) sie ueberhaupt ausgibt.

Kein Datei-Logging (bewusst): alles geht in die Konsole (stdout).
"""

from __future__ import annotations

import logging
import sys

# Log-Level fuer "Antwort/Prompt voll zeigen": ab INFO bei -v, sonst nur DEBUG.
# Wir steuern das ueber ein Modul-Flag, das main() setzt.
VERBOSE = 0            # 0 = mittel, 1 = -v, 2 = -vv
# Kuerzung greift nur bei wirklich langen Bloecken. HEAD/TAIL grosszuegig,
# damit mittelgrosse Prompts mit echten Objektdaten (GND-Kandidaten,
# Tagging-User, Emotion/Schwerpunkt) VOLL sichtbar bleiben — nur die
# statischen Riesen-Systemprompts (4k..24k Zeichen) werden gestutzt.
_SYS_PROMPT_HEAD = 1500
_SYS_PROMPT_TAIL = 1500

_log = logging.getLogger("pipeline")


def setup(verbose: int) -> None:
    """verbose: 0 (mittel) | 1 (-v) | 2 (-vv)."""
    global VERBOSE
    VERBOSE = verbose
    level = logging.DEBUG if verbose >= 2 else logging.INFO
    handler = logging.StreamHandler(sys.stdout)
    # Kompaktes Format: Zeit (nur Uhrzeit) + Level-Kuerzel + Nachricht
    fmt = logging.Formatter("%(asctime)s %(levelname).1s %(message)s",
                            datefmt="%H:%M:%S")
    handler.setFormatter(fmt)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # requests/urllib3 nicht mitfluten lassen
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get(name: str = "pipeline") -> logging.Logger:
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# Hilfen zum Anzeigen von Prompts/Antworten
# ---------------------------------------------------------------------------
def shorten(text: str) -> str:
    """Kuerzt lange statische Systemprompts auf Kopf/Schwanz."""
    if text is None:
        return ""
    n = len(text)
    if n <= _SYS_PROMPT_HEAD + _SYS_PROMPT_TAIL + 40:
        return text
    head = text[:_SYS_PROMPT_HEAD]
    tail = text[-_SYS_PROMPT_TAIL:]
    return f"{head}\n  … [{n-_SYS_PROMPT_HEAD-_SYS_PROMPT_TAIL} Zeichen gekuerzt] …\n{tail}"


def log_llm_call(model: str, body: dict, content: str, dur: float,
                 resp: dict | None = None) -> None:
    """
    Einheitliches Logging eines LLM-Calls: EINE Zeile mit Modell, Dauer,
    Prompt-/Antwortlaenge. Wenn die Antwort usage/timings enthaelt, zusaetzlich
    cached-Token und Tokens/s (fuer CPU-Performance-Analyse relevant).
    """
    sys_txt, user_txt = _extract_prompts(body)
    plen = len(sys_txt) + len(user_txt)

    extra = ""
    if resp:
        try:
            usage = resp.get("usage", {}) or {}
            details = usage.get("prompt_tokens_details", {}) or {}
            cached = details.get("cached_tokens")
            ptok = usage.get("prompt_tokens")
            ctok = usage.get("completion_tokens")
            tim = resp.get("timings", {}) or {}
            pps = tim.get("prompt_per_second")
            tps = tim.get("predicted_per_second")
            bits = []
            if ptok is not None:
                c = f"/{cached}c" if cached else ""
                bits.append(f"ptok={ptok}{c}")
            if ctok is not None:
                bits.append(f"ctok={ctok}")
            if pps is not None:
                bits.append(f"prefill={pps:.0f}t/s")
            if tps is not None:
                bits.append(f"gen={tps:.0f}t/s")
            if bits:
                extra = "  " + " ".join(bits)
        except Exception:
            pass

    _log.info("  LLM %-22s  %5.1fs  prompt=%d  antwort=%d%s",
              model, dur, plen, len(content or ""), extra)


def _extract_prompts(body: dict) -> tuple[str, str]:
    """Zieht System- und User-Text aus einem OpenAI-Chat-Body (auch wenn
    user ein Content-Array mit text+image ist)."""
    sys_txt, user_txt = "", ""
    for m in body.get("messages", []):
        role = m.get("role")
        content = m.get("content")
        if isinstance(content, list):
            texts = [c.get("text", "") for c in content if c.get("type") == "text"]
            imgs = sum(1 for c in content if c.get("type") == "image_url")
            joined = "\n".join(texts)
            if imgs:
                joined += f"\n[+{imgs} Bild(er) angehaengt]"
        else:
            joined = content or ""
        if role == "system":
            sys_txt += joined
        else:
            user_txt += joined
    return sys_txt, user_txt


def _indent(text: str, prefix: str = "      ") -> str:
    return "\n".join(prefix + line for line in (text or "").splitlines())


# ---------------------------------------------------------------------------
# Fortschritt + Werte-Auflistung fuer die Stages
# ---------------------------------------------------------------------------
# Gesamtzahl der Schritte pro Objekt (LLM-Phase). Nur fuer die [n/N]-Anzeige.
STEPS_LLM = 6      # 000b, 002, 001, 003, 004, (fertig)
STEPS_EMBED = 2    # 000a, 005


def step(main: int, main_total: int, label: str,
         sub: int = 0, sub_total: int = 0) -> None:
    """
    Fortschritts-Einzeiler.
      Nur Hauptschritt:   [3/6] ▶ #001 Tagging
      Mit Unterschritt:   [3/6 · 2/4] ▶ #001 Tagging: Audit-LLM3
      GND-Einzelcall:     [3/6 · GND 5/30] ▶ ...
    """
    if sub_total > 0:
        head = f"[{main}/{main_total} · {sub}/{sub_total}]"
    else:
        head = f"[{main}/{main_total}]"
    _log.info("  %s ▶ %s", head, label)


def step_gnd(main: int, main_total: int, done: int, total: int, term: str) -> None:
    """GND-Einzelcall-Fortschritt: [3/6 · GND 5/30] ▶ 'Buch'"""
    _log.info("  [%d/%d · GND %d/%d] ▶ %s",
              main, main_total, done, total, term)


def values(prefix: str, items, *, sep: str = ", ", empty: str = "(keine)") -> None:
    """
    Listet ALLE Werte vollstaendig auf (deine Vorgabe: volle Nennung).
    Bricht lange Listen auf mehrere Zeilen um, damit's lesbar bleibt.
    items: Liste von Strings (oder Tupeln, die zu 'a=b' werden).
    """
    def fmt(x):
        if isinstance(x, (tuple, list)) and len(x) == 2:
            return f"{x[0]}={x[1]}"
        return str(x)

    vals = [fmt(x) for x in (items or []) if x is not None and str(x) != ""]
    if not vals:
        _log.info("      %s %s", prefix, empty)
        return
    # Zeilenumbruch bei ~100 Zeichen, eingerueckt unter den prefix
    line = f"      {prefix} "
    out_lines = []
    cur = line
    for i, v in enumerate(vals):
        piece = v + (sep if i < len(vals) - 1 else "")
        if len(cur) + len(piece) > 100 and cur.strip() != prefix:
            out_lines.append(cur)
            cur = "        " + piece   # Folgezeile eingerueckt
        else:
            cur += piece
    out_lines.append(cur)
    for ol in out_lines:
        _log.info("%s", ol)

"""
tracing.py — Phoenix/OpenTelemetry Tracing fuer die Museums-Pipeline.

Konfiguration per Umgebungsvariablen (in .env setzen):
  PHOENIX_ENDPOINT   OTLP-Endpunkt des Phoenix-Servers
                     Default: http://phoenix:4318/v1/traces
                     (Phoenix laeuft intern auf Port 6006, extern gemappt auf 4318)
  PHOENIX_API_KEY    Bearer-Token aus Phoenix Settings -> API Keys
  PHOENIX_PROJECT    Projektname in der Phoenix UI (Default: museum-pipeline)
  PHOENIX_ENABLED    Tracing an/aus (1=an, 0=aus). Default: 0

Wenn Phoenix nicht erreichbar ist, laeuft die Pipeline normal weiter —
Tracing-Fehler werden nur geloggt, nie hochgereicht.

OpenInference Semantic Conventions (Stand August 2026):
  openinference.span.kind      -> "LLM" fuer Modell-Calls, "CHAIN" fuer Objekt-Laeufe
  llm.model_name               -> Modell-Alias
  llm.token_count.prompt       -> Prompt-Token
  llm.token_count.completion   -> Completion-Token
  llm.token_count.total        -> Gesamt-Token
  llm.invocation_parameters    -> JSON-String mit Body-Parametern
  input.value                  -> Prompt (gekuerzt auf 2000 Zeichen)
  output.value                 -> Antwort (gekuerzt auf 2000 Zeichen)
  metadata                     -> museum-spezifische Attribute (obj_id, phase etc.)

WICHTIG: Token-Counts NUR auf LLM-Spans setzen, NICHT auf CHAIN-Spans —
Phoenix zaehlt sonst doppelt (Issue #3164).
"""
from __future__ import annotations

import json
import logging
import os
from contextlib import contextmanager
from typing import Optional

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------
PHOENIX_ENDPOINT = os.environ.get(
    "PHOENIX_ENDPOINT", "http://phoenix:4318/v1/traces"
)
PHOENIX_API_KEY  = os.environ.get("PHOENIX_API_KEY", "")
PHOENIX_PROJECT  = os.environ.get("PHOENIX_PROJECT", "museum-pipeline")
PHOENIX_ENABLED  = os.environ.get("PHOENIX_ENABLED", "0").strip().lower() not in ("0", "false", "no", "off")

# ---------------------------------------------------------------------------
# TracerProvider — einmalig beim Modulimport initialisiert
# ---------------------------------------------------------------------------
_tracer      = None
_initialized = False


def _init() -> None:
    global _tracer, _initialized
    if _initialized:
        return
    _initialized = True

    if not PHOENIX_ENABLED:
        _log.info("Tracing deaktiviert (PHOENIX_ENABLED=0).")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({
            "service.name": PHOENIX_PROJECT,
            "service.version": "1.0",
        })
        provider = TracerProvider(resource=resource)

        # Auth-Header fuer Phoenix (PHOENIX_ENABLE_AUTH=true)
        headers = {"x-phoenix-project-name": PHOENIX_PROJECT}
        if PHOENIX_API_KEY:
            headers["authorization"] = f"Bearer {PHOENIX_API_KEY}"

        exporter = OTLPSpanExporter(
            endpoint=PHOENIX_ENDPOINT,
            headers=headers,
        )
        # BatchSpanProcessor: Spans gebundelt senden -> kein Latenz-Impact
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("museum-pipeline")
        _log.info("Phoenix Tracing initialisiert: %s (Projekt: %s)",
                  PHOENIX_ENDPOINT, PHOENIX_PROJECT)
    except ImportError as e:
        _log.warning("Tracing-Pakete fehlen (%s) — Tracing deaktiviert. "
                     "pip install arize-phoenix-otel opentelemetry-exporter-otlp "
                     "openinference-semantic-conventions", e)
    except Exception as e:
        _log.warning("Tracing-Init fehlgeschlagen (%s) — Pipeline laeuft ohne Tracing.", e)


def get_tracer():
    """Gibt den Tracer zurueck, oder None wenn Tracing deaktiviert/fehlgeschlagen."""
    _init()
    return _tracer


# ---------------------------------------------------------------------------
# LLM-Span (in llm.py verwendet)
# ---------------------------------------------------------------------------
@contextmanager
def llm_span(model: str, body: dict):
    """
    Context-Manager fuer einen einzelnen LLM-Call-Span.
    Token-Counts werden NACH dem Call via finish_llm_span gesetzt.
    """
    tracer = get_tracer()
    if tracer is None:
        yield None
        return

    try:
        with tracer.start_as_current_span(f"llm.{model}") as span:
            # OpenInference Pflicht-Attribute
            span.set_attribute("openinference.span.kind", "LLM")
            span.set_attribute("llm.model_name", model)

            # Invocation Parameters (max_tokens, reasoning_budget etc.)
            params = {k: v for k, v in body.items()
                      if k not in ("messages", "model")
                      and not isinstance(v, (list, dict))}
            if params:
                span.set_attribute("llm.invocation_parameters", json.dumps(params))

            # Input: letzter User-Message (gekuerzt)
            msgs = body.get("messages", [])
            if msgs:
                last_user = next(
                    (m.get("content", "") for m in reversed(msgs)
                     if m.get("role") == "user"), ""
                )
                if isinstance(last_user, str):
                    span.set_attribute("input.value", last_user[:2000])
                elif isinstance(last_user, list):
                    text = " ".join(p.get("text", "") for p in last_user
                                   if isinstance(p, dict) and p.get("type") == "text")
                    span.set_attribute("input.value", text[:2000])

            yield span
    except Exception as e:
        _log.debug("Tracing-Fehler (llm_span): %s", e)
        yield None


def finish_llm_span(span, resp: dict, dur: float,
                    obj_id: Optional[str] = None,
                    phase: Optional[str] = None) -> None:
    """
    Setzt Token-Counts, Output und Museum-Metadaten nach dem Call.
    Token-Counts NUR hier setzen — nicht im Parent-CHAIN-Span.
    """
    if span is None:
        return
    try:
        usage = resp.get("usage", {}) or {}
        prompt_tokens     = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens      = usage.get("total_tokens", prompt_tokens + completion_tokens)

        if prompt_tokens:
            span.set_attribute("llm.token_count.prompt", prompt_tokens)
        if completion_tokens:
            span.set_attribute("llm.token_count.completion", completion_tokens)
        if total_tokens:
            span.set_attribute("llm.token_count.total", total_tokens)

        # Output (gekuerzt)
        try:
            content = resp["choices"][0]["message"].get("content") or ""
            if content:
                span.set_attribute("output.value", content[:2000])
        except (KeyError, IndexError):
            pass

        span.set_attribute("llm.latency_ms", int(dur * 1000))

        # Museum-Metadaten
        meta = {}
        if obj_id:
            meta["museum.obj_id"] = obj_id
        if phase:
            meta["museum.phase"] = phase
        if meta:
            span.set_attribute("metadata", json.dumps(meta))

    except Exception as e:
        _log.debug("Tracing-Fehler (finish_llm_span): %s", e)


# ---------------------------------------------------------------------------
# Objekt-Span (in phasenlauf.py verwendet)
# ---------------------------------------------------------------------------
@contextmanager
def object_span(obj_id: str, collection: Optional[str] = None):
    """
    Uebergeordneter CHAIN-Span pro Objekt-Lauf.
    Alle LLM-Calls innerhalb erscheinen als Kind-Spans in Phoenix.
    KEIN Token-Count hier setzen — Phoenix zaehlt sonst doppelt.
    """
    tracer = get_tracer()
    if tracer is None:
        yield
        return

    try:
        with tracer.start_as_current_span(f"object.{obj_id}") as span:
            span.set_attribute("openinference.span.kind", "CHAIN")
            span.set_attribute("museum.obj_id", obj_id)
            if collection:
                span.set_attribute("museum.collection", collection)
            meta = {"obj_id": obj_id}
            if collection:
                meta["collection"] = collection
            span.set_attribute("metadata", json.dumps(meta))
            yield span
    except Exception as e:
        _log.debug("Tracing-Fehler (object_span): %s", e)
        yield

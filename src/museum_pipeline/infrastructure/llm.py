from __future__ import annotations

import contextlib
import threading
import time
import random
from typing import Any, Optional

import requests

from ..configuration import RuntimeConfig
from . import logsetup
try:
    from . import tracing as tracing_mod
except Exception:
    tracing_mod = None

_log = logsetup.get()


class LLMClient:
    def __init__(self, cfg: RuntimeConfig):
        self.cfg=cfg
        self.settings=cfg.settings
        self._lock=threading.Lock()
        self._semas: dict[str, threading.Semaphore] = {}

    def _sema(self, role: str) -> threading.Semaphore:
        model=self.cfg.models.logical_model(role)
        with self._lock:
            if model not in self._semas:
                self._semas[model]=threading.Semaphore(self.cfg.hardware.parallel_slots(model))
            return self._semas[model]

    def request_defaults(self, role: str) -> dict[str, Any]:
        return self.cfg.models.request_defaults(role)

    def chat_raw(self, role: str, body: dict[str, Any], *, timeout: Optional[int]=None) -> dict:
        s=self.settings
        timeout=timeout or s.lcpp_timeout
        headers={"Authorization":s.lcpp_auth,"Content-Type":"application/json"}
        model=self.cfg.models.logical_model(role)
        api_model=self.cfg.models.api_model(role)
        wire={**body,"model":api_model}
        last_exc: Optional[Exception]=None
        span_ctx=(tracing_mod.llm_span(model, wire) if tracing_mod else contextlib.nullcontext(None))
        with span_ctx as span:
            for attempt in range(s.lcpp_max_retries+1):
                try:
                    t0=time.time()
                    with self._sema(role):
                        r=requests.post(s.lcpp_url,json=wire,headers=headers,
                                        timeout=(s.lcpp_connect_timeout,timeout))
                    dur=time.time()-t0
                    if r.status_code>=500:
                        last_exc=RuntimeError(f"LLM {r.status_code}: {r.text[:300]}")
                        oom = "exited prematurely" in r.text or "out of memory" in r.text.lower()
                        self._backoff(attempt,long=oom)
                        continue
                    if r.status_code in (429,408):
                        last_exc=RuntimeError(f"LLM {r.status_code}: {r.text[:300]}")
                        retry_after=r.headers.get("Retry-After")
                        if retry_after and retry_after.isdigit():
                            time.sleep(min(int(retry_after),30))
                        else:
                            self._backoff(attempt,long=True)
                        continue
                    r.raise_for_status()
                    resp=r.json()
                    if tracing_mod:
                        tracing_mod.finish_llm_span(span,resp,dur)
                    logsetup.log_llm_call(model,wire,self.content_of(resp),dur,resp)
                    return resp
                except (requests.Timeout,requests.ConnectionError) as e:
                    last_exc=e
                    is_connect = isinstance(e, requests.ConnectionError) or \
                        "ConnectTimeout" in type(e).__name__ or "connect" in str(e).lower()
                    self._backoff(attempt,long=is_connect)
                except requests.HTTPError:
                    raise
        raise RuntimeError(f"LLM call failed for role={role}: {last_exc}")

    def chat_content(self, role: str, body: dict[str, Any], *, timeout: Optional[int]=None) -> str:
        return self.content_of(self.chat_raw(role,body,timeout=timeout))

    @staticmethod
    def content_of(resp: dict) -> str:
        try:
            msg=(resp["choices"][0].get("message") or {})
            return msg.get("content") or ""
        except Exception:
            return ""


    @staticmethod
    def usage_total(resp: dict) -> int:
        """Return actual token usage reported by the OpenAI-compatible backend."""
        try:
            usage = resp.get("usage") or {}

            total = usage.get("total_tokens")
            if total is not None:
                return int(total)

            prompt = usage.get("prompt_tokens") or 0
            completion = usage.get("completion_tokens") or 0
            return int(prompt) + int(completion)
        except (TypeError, ValueError, AttributeError):
            return 0

    @staticmethod
    def _backoff(attempt: int, long: bool=False):
        base=20 if long else 3
        time.sleep(base*(attempt+1)+random.uniform(0,base))

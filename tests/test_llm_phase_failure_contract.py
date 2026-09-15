from __future__ import annotations

import inspect
from types import SimpleNamespace

import pytest

from museum_pipeline.harness.runner import EmptyOutput, WorkflowRunner


class FakeMuseum:
    data = {
        "captions": {
            "prompts": {
                "system": "system",
                "user": "user",
                "fallback": "fallback",
                "synthesis_system": "synthesis_system",
            }
        }
    }

    def prompt(self, name):
        return f"prompt:{name}"


class FakeModels:
    """Minimal model registry needed by caption request builders."""

    def request_defaults(self, role):
        return {
            "model": f"fake-{role}",
        }


class FakeImages:
    def get(self, obj_id, asset_ref):
        return "data:image/jpeg;base64,AA==", b"image"


class FakeState:
    def __init__(self):
        self.values = {
            "tagging.caption.primary": "A",
            "tagging.caption.secondary": "B",
        }

    def set(self, conn, obj_id, key, value):
        self.values[key] = value

    def get(self, conn, obj_id, key, required=False):
        value = self.values.get(key)

        if required and not str(value or "").strip():
            return None

        return value


class FakeTagging:
    def caption_primary_body(self, image):
        return {}

    def caption_secondary_body(self, image):
        return {}

    def caption_synthesis_body(self, a, b, image):
        return {}

    def repair_body(self, master, ctx, yellows):
        return {}


class RaisingLLM:
    def chat_raw(self, role, body):
        raise RuntimeError("backend unavailable")

    def chat_content(self, role, body):
        raise RuntimeError("backend unavailable")

    def content_of(self, response):
        return ""

    def usage_total(self, response):
        return 0


class EmptyLLM:
    def chat_raw(self, role, body):
        return {
            "choices": [
                {
                    "message": {
                        "content": "",
                    }
                }
            ],
            "usage": {
                "total_tokens": 1,
            },
        }

    def chat_content(self, role, body):
        return ""

    def content_of(self, response):
        return (
            response["choices"][0]
            .get("message", {})
            .get("content")
            or ""
        )

    def usage_total(self, response):
        return int(
            (response.get("usage") or {})
            .get("total_tokens")
            or 0
        )


def make_runner(llm):
    cfg = SimpleNamespace(
        museum=FakeMuseum(),
        models=FakeModels(),
        hardware=SimpleNamespace(default_workers=1),
    )

    runtime = SimpleNamespace(
        cfg=cfg,
        llm=llm,
        images=FakeImages(),
        state=FakeState(),
        tagging=FakeTagging(),
    )

    return WorkflowRunner(runtime, workers=1)


def object_row():
    return {
        "obj_id": "TEST",
        "asset_ref": "objects/test.jpg",
    }


def test_caption_transport_error_propagates():
    runner = make_runner(RaisingLLM())
    phase = runner.caption_phases()[0]

    with pytest.raises(
        RuntimeError,
        match="backend unavailable",
    ):
        phase.handler(None, object_row())


def test_caption_empty_model_output_fails_phase():
    runner = make_runner(EmptyLLM())
    phase = runner.caption_phases()[0]

    with pytest.raises(
        EmptyOutput,
        match="caption.primary",
    ):
        phase.handler(None, object_row())


def test_tagging_caption_transport_error_propagates():
    runner = make_runner(RaisingLLM())
    phase = runner.tagging_phases()[0]

    with pytest.raises(
        RuntimeError,
        match="backend unavailable",
    ):
        phase.handler(None, object_row())


def test_tagging_caption_empty_model_output_fails_phase():
    runner = make_runner(EmptyLLM())
    phase = runner.tagging_phases()[0]

    with pytest.raises(
        EmptyOutput,
        match="tagging.caption.primary",
    ):
        phase.handler(None, object_row())


def test_caption_and_tagging_handlers_do_not_swallow_llm_exceptions():
    caption_source = inspect.getsource(
        WorkflowRunner.caption_phases
    )

    tagging_source = inspect.getsource(
        WorkflowRunner.tagging_phases
    )

    assert "except Exception" not in caption_source
    assert "except Exception" not in tagging_source

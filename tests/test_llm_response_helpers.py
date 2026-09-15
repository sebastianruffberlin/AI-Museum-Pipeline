from museum_pipeline.infrastructure.llm import LLMClient
from museum_pipeline.domain.tagging import TaggingModule


def test_reasoning_is_not_visible_content():
    resp = {
        "choices": [{
            "finish_reason": "length",
            "message": {
                "content": "",
                "reasoning_content": "INTERNE GEDANKEN",
            },
        }]
    }

    assert LLMClient.content_of(resp) == ""


def test_tagging_keeps_reasoning_separate():
    resp = {
        "choices": [{
            "message": {
                "content": "SICHTBARE ANTWORT",
                "reasoning_content": "INTERNE GEDANKEN",
            },
        }]
    }

    content, reasoning = TaggingModule.content_and_reasoning(resp)

    assert content == "SICHTBARE ANTWORT"
    assert reasoning == "INTERNE GEDANKEN"


def test_usage_total_prefers_backend_total():
    resp = {
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
            "total_tokens": 123,
        }
    }

    assert LLMClient.usage_total(resp) == 123


def test_usage_total_can_derive_total():
    resp = {
        "usage": {
            "prompt_tokens": 100,
            "completion_tokens": 20,
        }
    }

    assert LLMClient.usage_total(resp) == 120


def test_usage_total_missing_usage_is_zero():
    assert LLMClient.usage_total({}) == 0

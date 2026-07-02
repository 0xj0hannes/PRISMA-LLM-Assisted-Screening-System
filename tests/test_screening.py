"""Tests for src.screening.screen_record with the Gemini client mocked.

No API key or network access is needed: the module-level ``client`` and the
loaded ``config`` are monkeypatched.
"""
import json

import src.screening as screening

from tests.conftest import make_record


class _FakeResponse:
    def __init__(self, text):
        self.text = text


class _FakeModels:
    """Returns a canned response, or raises a canned exception."""

    def __init__(self, text=None, exc=None):
        self._text = text
        self._exc = exc

    def generate_content(self, **kwargs):
        if self._exc is not None:
            raise self._exc
        return _FakeResponse(self._text)


class _FakeClient:
    def __init__(self, text=None, exc=None):
        self.models = _FakeModels(text=text, exc=exc)


TWO_CRITERIA = {
    "IC1": {"name": "c1", "definition": "d", "signals": "s",
            "negative_indicators": "n"},
    "IC2": {"name": "c2", "definition": "d", "signals": "s",
            "negative_indicators": "n"},
}


def _patch_config(monkeypatch, max_retries=3):
    monkeypatch.setitem(screening.config, "CRITERIA", TWO_CRITERIA)
    monkeypatch.setitem(screening.config, "MODEL_NAME", "test-model")
    monkeypatch.setitem(screening.config, "MAX_RETRIES", max_retries)


def test_successful_screening_parses_all_criteria(monkeypatch):
    _patch_config(monkeypatch)
    payload = {
        "decision": "Include",
        "unmet_criteria": "",
        "notes": "looks good",
        "IC1": {"score": 0.9, "evidences": ["foo"], "rationale": "because"},
        "IC2": {"score": 0.7, "evidences": [], "rationale": "ok"},
    }
    monkeypatch.setattr(screening, "client",
                        _FakeClient(text=json.dumps(payload)))

    result = screening.screen_record(make_record(id="x"))

    assert result.record_id == "x"
    assert result.decision == "Include"
    assert result.model_version == "test-model"
    assert set(result.criteria) == {"IC1", "IC2"}
    assert result.criteria["IC1"].score == 0.9
    assert result.criteria["IC1"].evidences == ["foo"]


def test_missing_criterion_in_response_defaults_to_zero(monkeypatch):
    _patch_config(monkeypatch)
    payload = {"decision": "Maybe", "IC1": {"score": 0.5}}  # IC2 omitted
    monkeypatch.setattr(screening, "client",
                        _FakeClient(text=json.dumps(payload)))

    result = screening.screen_record(make_record())

    assert result.criteria["IC2"].score == 0.0
    assert result.criteria["IC2"].evidences == []


def test_persistent_error_returns_failed_maybe(monkeypatch):
    _patch_config(monkeypatch, max_retries=1)
    monkeypatch.setattr(screening.time, "sleep", lambda *_: None)
    monkeypatch.setattr(
        screening, "client",
        _FakeClient(exc=Exception("404 Model Not Found")),
    )

    result = screening.screen_record(make_record(id="y"))

    assert result.decision == "Maybe"
    assert "Failed after" in result.notes
    assert result.record_id == "y"

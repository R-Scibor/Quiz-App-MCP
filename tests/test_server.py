import json
import os

import respx
from httpx import Response

from quiz_authoring_mcp.server import (
    handle_export_quiz,
    handle_import_quiz,
    handle_list_quizzes,
    handle_resource_instructions,
    handle_resource_schema,
    handle_validate_quiz,
)

API = "https://quiz.test/api/v1/authoring"


def _env(monkeypatch):
    monkeypatch.setenv("QUIZ_APP_URL", "https://quiz.test")
    monkeypatch.setenv("QUIZ_APP_TOKEN", "secret-token")


@respx.mock
def test_list_quizzes_tool(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/tests/").mock(return_value=Response(200, json=[{"scope": "Poland"}]))
    text = handle_list_quizzes()
    assert json.loads(text)[0]["scope"] == "Poland"


@respx.mock
def test_validate_quiz_tool(monkeypatch):
    _env(monkeypatch)
    respx.post(f"{API}/validate/").mock(
        return_value=Response(200, json={"valid": False, "errors": [{"code": "EMPTY_QUESTIONS"}]})
    )
    text = handle_validate_quiz({"category": "X", "scope": "Y", "questions": []})
    body = json.loads(text)
    assert body["valid"] is False


@respx.mock
def test_import_aborts_body_on_400(monkeypatch):
    _env(monkeypatch)
    respx.post(f"{API}/import/").mock(
        return_value=Response(
            400, json={"error": "VALIDATION_FAILED", "errors": [{"code": "EMPTY_QUESTIONS"}]}
        )
    )
    text = handle_import_quiz({"category": "X", "scope": "Y", "questions": []})
    body = json.loads(text)
    assert body["error"] == "VALIDATION_FAILED"


@respx.mock
def test_schema_resource(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/schema/").mock(
        return_value=Response(200, json={"schema_version": 1, "examples": {"open-text": {}}})
    )
    body = json.loads(handle_resource_schema())
    assert body["schema_version"] == 1


@respx.mock
def test_instructions_resource(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/instructions/").mock(
        return_value=Response(200, json={"markdown": "You are an expert quiz author"})
    )
    assert "expert quiz author" in handle_resource_instructions()

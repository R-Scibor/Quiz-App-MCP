import json
import os

import respx
from httpx import Response

from quiz_authoring_mcp.server import (
    handle_add_question,
    handle_add_questions,
    handle_delete_question,
    handle_export_quiz,
    handle_get_question,
    handle_import_quiz,
    handle_list_quizzes,
    handle_resource_instructions,
    handle_resource_schema,
    handle_retire_question,
    handle_update_grading,
    handle_update_question,
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


TID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
QID = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"

EXPORT = {
    "test_id": TID,
    "category": "History",
    "scope": "Poland",
    "version": "1.0",
    "questions": [
        {
            "id": 1,
            "question_id": QID,
            "questionText": "Year?",
            "type": "open-text",
            "gradingCriteria": "966",
            "maxPoints": 2,
        }
    ],
}


@respx.mock
def test_add_question_posts_question_and_surfaces_validation_error(monkeypatch):
    _env(monkeypatch)
    import_route = respx.post(f"{API}/import/")
    create_route = respx.post(f"{API}/tests/{TID}/questions/").mock(
        return_value=Response(
            400,
            json={"error": "VALIDATION_FAILED", "errors": [{"code": "INVALID_QUESTION_TYPE"}]},
        )
    )
    text = handle_add_question(
        TID,
        {"questionText": "Bad", "type": "true-false"},
    )
    body = json.loads(text)
    assert body["error"] == "VALIDATION_FAILED"
    assert create_route.called
    assert not import_route.called
    assert create_route.calls.last.request.headers["Authorization"] == "Token secret-token"


@respx.mock
def test_update_grading_patches_question(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/tests/{TID}/questions/{QID}/").mock(
        return_value=Response(200, json={"question_id": QID})
    )
    patch_route = respx.patch(f"{API}/questions/{QID}/").mock(
        return_value=Response(
            200,
            json={"applied": True, "question": {"gradingCriteria": "Must mention 966", "maxPoints": 3}},
        )
    )
    text = handle_update_grading(TID, QID, grading_criteria="Must mention 966", max_points=3)
    body = json.loads(text)
    assert body["applied"] is True
    sent = json.loads(patch_route.calls.last.request.content)
    assert sent == {"gradingCriteria": "Must mention 966", "maxPoints": 3}


@respx.mock
def test_delete_question_passes_dry_run(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/tests/{TID}/questions/{QID}/").mock(
        return_value=Response(200, json={"question_id": QID})
    )
    delete_route = respx.delete(f"{API}/questions/{QID}/").mock(
        return_value=Response(200, json={"applied": False, "dry_run": True, "deleted": False})
    )
    text = handle_delete_question(TID, QID, dry_run=True)
    body = json.loads(text)
    assert body["dry_run"] is True
    assert delete_route.calls.last.request.url.params["dry_run"] == "true"


@respx.mock
def test_get_question_tool(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/tests/{TID}/questions/{QID}/").mock(
        return_value=Response(200, json={"question_id": QID, "questionText": "Year?"})
    )
    text = handle_get_question(TID, QID)
    assert json.loads(text)["questionText"] == "Year?"


@respx.mock
def test_update_question_tool(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/tests/{TID}/questions/{QID}/").mock(
        return_value=Response(200, json={"question_id": QID})
    )
    patch_route = respx.patch(f"{API}/questions/{QID}/").mock(
        return_value=Response(200, json={"applied": True, "question": {"questionText": "What year?"}})
    )
    text = handle_update_question(TID, QID, {"questionText": "What year?"})
    body = json.loads(text)
    assert body["applied"] is True
    assert json.loads(patch_route.calls.last.request.content) == {"questionText": "What year?"}


@respx.mock
def test_compose_question_not_found(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/tests/{TID}/questions/missing-qid/").mock(
        return_value=Response(404, json={"error": "QUESTION_NOT_FOUND", "message": "Question not found."})
    )
    text = handle_delete_question(TID, "missing-qid")
    body = json.loads(text)
    assert body["error"] == "QUESTION_NOT_FOUND"


@respx.mock
def test_add_questions_does_not_import_on_400(monkeypatch):
    _env(monkeypatch)
    import_route = respx.post(f"{API}/import/")
    respx.post(f"{API}/tests/{TID}/questions/batch/").mock(
        return_value=Response(400, json={"error": "VALIDATION_FAILED", "errors": []})
    )
    body = json.loads(handle_add_questions(TID, [{"questionText": "Bad", "type": "nope"}]))
    assert body["error"] == "VALIDATION_FAILED"
    assert not import_route.called


@respx.mock
def test_retire_question_does_not_patch_when_missing(monkeypatch):
    _env(monkeypatch)
    respx.get(f"{API}/tests/{TID}/questions/missing-qid/").mock(
        return_value=Response(404, json={"error": "QUESTION_NOT_FOUND", "message": "Question not found."})
    )
    patch = respx.patch(f"{API}/questions/missing-qid/")
    body = json.loads(handle_retire_question(TID, "missing-qid", True))
    assert body["error"] == "QUESTION_NOT_FOUND"
    assert not patch.called

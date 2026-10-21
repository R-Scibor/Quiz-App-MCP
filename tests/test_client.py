import json
import respx
from httpx import Response

from tests.conftest import API


@respx.mock
def test_validate_posts_json_and_token(client):
    route = respx.post(f"{API}/validate/").mock(
        return_value=Response(200, json={"valid": True, "errors": []})
    )
    quiz = {
        "category": "X",
        "scope": "Y",
        "questions": [
            {
                "id": 1,
                "questionText": "Q",
                "type": "open-text",
                "gradingCriteria": "c",
                "maxPoints": 1,
            }
        ],
    }
    body = client.validate_quiz(quiz)
    assert body == {"valid": True, "errors": []}
    assert route.called
    request = route.calls.last.request
    assert request.headers["Authorization"] == "Token secret-token"
    assert json.loads(request.content) == quiz


@respx.mock
def test_import_passes_dry_run_query(client):
    route = respx.post(f"{API}/import/").mock(
        return_value=Response(200, json={"applied": False, "dry_run": True})
    )
    client.import_quiz(
        {
            "category": "X",
            "scope": "Y",
            "questions": [
                {
                    "id": 1,
                    "questionText": "Q",
                    "type": "open-text",
                    "gradingCriteria": "c",
                    "maxPoints": 1,
                }
            ],
        },
        dry_run=True,
    )
    assert route.calls.last.request.url.params["dry_run"] == "true"


@respx.mock
def test_http_error_raises_with_body(client):
    respx.post(f"{API}/import/").mock(
        return_value=Response(400, json={"error": "VALIDATION_FAILED", "errors": []})
    )
    from quiz_authoring_mcp.client import AuthoringAPIError

    try:
        client.import_quiz({"category": "X", "scope": "Y", "questions": []})
        assert False, "expected AuthoringAPIError"
    except AuthoringAPIError as exc:
        assert exc.status_code == 400
        assert exc.body["error"] == "VALIDATION_FAILED"


@respx.mock
def test_list_quizzes(client):
    respx.get(f"{API}/tests/").mock(return_value=Response(200, json=[]))
    assert client.list_quizzes() == []


@respx.mock
def test_export_quiz(client):
    respx.get(f"{API}/tests/aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa/export/").mock(
        return_value=Response(
            200,
            json={"test_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "questions": []},
        )
    )
    doc = client.export_quiz("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    assert doc["test_id"].startswith("aaaa")


@respx.mock
def test_get_question(client):
    tid, qid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    respx.get(f"{API}/tests/{tid}/questions/{qid}/").mock(
        return_value=Response(200, json={"question_id": qid, "questionText": "Q"})
    )
    assert client.get_question(tid, qid)["questionText"] == "Q"


@respx.mock
def test_patch_metadata(client):
    tid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    respx.patch(f"{API}/tests/{tid}/").mock(
        return_value=Response(200, json={"scope": "New", "test_id": tid})
    )
    assert client.update_quiz_metadata(tid, scope="New")["scope"] == "New"


@respx.mock
def test_schema_and_instructions(client):
    respx.get(f"{API}/schema/").mock(
        return_value=Response(200, json={"schema_version": 1, "examples": {}})
    )
    respx.get(f"{API}/instructions/").mock(
        return_value=Response(200, json={"markdown": "# hi"})
    )
    assert client.get_schema()["schema_version"] == 1
    assert client.get_instructions()["markdown"] == "# hi"


@respx.mock
def test_create_question_posts_to_test(client):
    tid = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
    route = respx.post(f"{API}/tests/{tid}/questions/").mock(
        return_value=Response(201, json={"applied": True, "question": {"id": 2}})
    )
    body = client.create_question(tid, {"questionText": "Q", "type": "open-text", "gradingCriteria": "c", "maxPoints": 1})
    assert body["question"]["id"] == 2
    assert route.calls.last.request.headers["Authorization"] == "Token secret-token"


@respx.mock
def test_remove_question_dry_run(client):
    qid = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
    route = respx.delete(f"{API}/questions/{qid}/").mock(
        return_value=Response(200, json={"dry_run": True, "deleted": False})
    )
    client.remove_question(qid, dry_run=True)
    assert route.calls.last.request.url.params["dry_run"] == "true"

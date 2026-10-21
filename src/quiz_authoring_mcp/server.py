from __future__ import annotations

import argparse
import json
import os
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server.mcpserver import MCPServer as FastMCP

from quiz_authoring_mcp.client import AuthoringAPIError, AuthoringClient

mcp = FastMCP("quiz-authoring")


def _client() -> AuthoringClient:
    url = os.environ["QUIZ_APP_URL"]
    token = os.environ["QUIZ_APP_TOKEN"]
    timeout = float(os.environ.get("QUIZ_APP_TIMEOUT_SECONDS", "30"))
    return AuthoringClient(url, token, timeout=timeout)


def _dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _call(fn):
    try:
        return _dump(fn())
    except AuthoringAPIError as exc:
        return _dump(
            {
                "error": (exc.body or {}).get("error", "HTTP_ERROR")
                if isinstance(exc.body, dict)
                else "HTTP_ERROR",
                "status_code": exc.status_code,
                **(exc.body if isinstance(exc.body, dict) else {"message": str(exc.body)}),
            }
        )
    except KeyError as exc:
        return _dump({"error": "CONFIG", "message": f"Missing environment variable {exc}"})


def handle_list_quizzes() -> str:
    def go():
        c = _client()
        try:
            return c.list_quizzes()
        finally:
            c.close()

    return _call(go)


def handle_validate_quiz(quiz: dict) -> str:
    def go():
        c = _client()
        try:
            return c.validate_quiz(quiz)
        finally:
            c.close()

    return _call(go)


def handle_export_quiz(test_id: str) -> str:
    def go():
        c = _client()
        try:
            return c.export_quiz(test_id)
        finally:
            c.close()

    return _call(go)


def handle_import_quiz(quiz: dict, test_id: str | None = None, dry_run: bool = False) -> str:
    def go():
        c = _client()
        try:
            return c.import_quiz(quiz, test_id=test_id, dry_run=dry_run)
        finally:
            c.close()

    return _call(go)


def handle_update_quiz_metadata(
    test_id: str,
    category: str | None = None,
    scope: str | None = None,
    version: str | None = None,
    description: str | None = None,
) -> str:
    def go():
        c = _client()
        try:
            return c.update_quiz_metadata(
                test_id,
                category=category,
                scope=scope,
                version=version,
                description=description,
            )
        finally:
            c.close()

    return _call(go)


def handle_get_question(test_id: str, question_id: str) -> str:
    def go():
        c = _client()
        try:
            return c.get_question(test_id, question_id)
        finally:
            c.close()

    return _call(go)


def _confirm_question(client: AuthoringClient, test_id: str, question_id: str) -> None:
    """GET the question on this test so a foreign UUID is not patched or deleted."""
    client.get_question(test_id, question_id)


def handle_add_question(test_id: str, question: dict, dry_run: bool = False) -> str:
    def go():
        c = _client()
        try:
            return c.create_question(test_id, question, dry_run=dry_run)
        finally:
            c.close()

    return _call(go)


def handle_update_question(
    test_id: str, question_id: str, question: dict, dry_run: bool = False
) -> str:
    def go():
        c = _client()
        try:
            _confirm_question(c, test_id, question_id)
            return c.patch_question(question_id, question, dry_run=dry_run)
        finally:
            c.close()

    return _call(go)


def handle_delete_question(test_id: str, question_id: str, dry_run: bool = False) -> str:
    def go():
        c = _client()
        try:
            _confirm_question(c, test_id, question_id)
            return c.remove_question(question_id, dry_run=dry_run)
        finally:
            c.close()

    return _call(go)


def handle_update_grading(
    test_id: str,
    question_id: str,
    grading_criteria: str | None = None,
    max_points: int | None = None,
    dry_run: bool = False,
) -> str:
    fields: dict[str, Any] = {}
    if grading_criteria is not None:
        fields["gradingCriteria"] = grading_criteria
    if max_points is not None:
        fields["maxPoints"] = max_points

    def go():
        c = _client()
        try:
            _confirm_question(c, test_id, question_id)
            return c.patch_question(question_id, fields, dry_run=dry_run)
        finally:
            c.close()

    return _call(go)


def handle_search_catalog(
    q: str,
    test_id: str | None = None,
    tag: str | None = None,
    limit: int | None = None,
) -> str:
    def go():
        c = _client()
        try:
            return c.search_catalog(q, test_id=test_id, tag=tag, limit=limit)
        finally:
            c.close()

    return _call(go)


def handle_add_questions(test_id: str, questions: list, dry_run: bool = False) -> str:
    def go():
        c = _client()
        try:
            return c.add_questions(test_id, questions, dry_run=dry_run)
        finally:
            c.close()

    return _call(go)


def handle_retire_question(test_id: str, question_id: str, retired: bool = True) -> str:
    def go():
        c = _client()
        try:
            _confirm_question(c, test_id, question_id)
            return c.patch_question(question_id, {"retired": retired})
        finally:
            c.close()

    return _call(go)


def handle_list_tags() -> str:
    def go():
        c = _client()
        try:
            return c.list_tags()
        finally:
            c.close()

    return _call(go)


def handle_list_reports(status: str | None = None, limit: int | None = None) -> str:
    def go():
        c = _client()
        try:
            return c.list_reports(status=status, limit=limit)
        finally:
            c.close()

    return _call(go)


def handle_get_report(report_id: str) -> str:
    def go():
        c = _client()
        try:
            return c.get_report(report_id)
        finally:
            c.close()

    return _call(go)


def handle_set_report_status(
    report_id: str, status: str, resolution_note: str | None = None
) -> str:
    def go():
        c = _client()
        try:
            return c.set_report_status(report_id, status, resolution_note=resolution_note)
        finally:
            c.close()

    return _call(go)


def handle_resource_schema() -> str:
    def go():
        c = _client()
        try:
            return c.get_schema()
        finally:
            c.close()

    return _call(go)


def handle_resource_instructions() -> str:
    def go():
        c = _client()
        try:
            return c.get_instructions()["markdown"]
        finally:
            c.close()

    return _call(go)


def handle_resource_example(qtype: str) -> str:
    def go():
        c = _client()
        try:
            schema = c.get_schema()
            examples = schema.get("examples") or {}
            if qtype not in examples:
                return {"error": "NOT_FOUND", "message": f"No example for type {qtype}"}
            return examples[qtype]
        finally:
            c.close()

    return _call(go)


@mcp.tool()
def list_quizzes() -> str:
    """List quizzes in the catalog (id, category, scope, version, question counts)."""
    return handle_list_quizzes()


@mcp.tool()
def validate_quiz(quiz: dict) -> str:
    """Validate interchange quiz JSON. Always returns {valid, errors}; does not import."""
    return handle_validate_quiz(quiz)


@mcp.tool()
def export_quiz(test_id: str) -> str:
    """Export a quiz by test_id as interchange JSON including UUIDs."""
    return handle_export_quiz(test_id)


@mcp.tool()
def import_quiz(quiz: dict, test_id: str | None = None, dry_run: bool = False) -> str:
    """Upsert a full quiz document. Set dry_run=true to preview matching without writes. Prefer dry_run before large replaces."""
    return handle_import_quiz(quiz, test_id=test_id, dry_run=dry_run)


@mcp.tool()
def update_quiz_metadata(
    test_id: str,
    category: str | None = None,
    scope: str | None = None,
    version: str | None = None,
    description: str | None = None,
) -> str:
    """Patch test metadata only (category, scope, version, description). Does not change questions."""
    return handle_update_quiz_metadata(test_id, category, scope, version, description)


@mcp.tool()
def get_question(test_id: str, question_id: str) -> str:
    """Fetch one question in interchange shape."""
    return handle_get_question(test_id, question_id)


@mcp.tool()
def add_question(test_id: str, question: dict, dry_run: bool = False) -> str:
    """Create one question on a test. Set dry_run=true to validate without writing."""
    return handle_add_question(test_id, question, dry_run)


@mcp.tool()
def update_question(
    test_id: str, question_id: str, question: dict, dry_run: bool = False
) -> str:
    """Merge fields into an existing question. The question must belong to test_id."""
    return handle_update_question(test_id, question_id, question, dry_run)


@mcp.tool()
def delete_question(test_id: str, question_id: str, dry_run: bool = False) -> str:
    """Delete one question. The server refuses when the question has attempts."""
    return handle_delete_question(test_id, question_id, dry_run)


@mcp.tool()
def update_grading(
    test_id: str,
    question_id: str,
    gradingCriteria: str | None = None,
    maxPoints: int | None = None,
    dry_run: bool = False,
) -> str:
    """Patch gradingCriteria and/or maxPoints on one question."""
    return handle_update_grading(test_id, question_id, gradingCriteria, maxPoints, dry_run)


@mcp.tool()
def search_catalog(
    q: str,
    test_id: str | None = None,
    tag: str | None = None,
    limit: int | None = None,
) -> str:
    """Find tests and questions by scope, category, question text, or tag. q must be at least 2 characters."""
    return handle_search_catalog(q, test_id=test_id, tag=tag, limit=limit)


@mcp.tool()
def add_questions(test_id: str, questions: list, dry_run: bool = False) -> str:
    """Append questions in one transaction. A single invalid item writes nothing."""
    return handle_add_questions(test_id, questions, dry_run)


@mcp.tool()
def retire_question(test_id: str, question_id: str, retired: bool = True) -> str:
    """Hide a question from new sessions and the study queue, or restore it when retired is false."""
    return handle_retire_question(test_id, question_id, retired)


@mcp.tool()
def list_tags() -> str:
    """List tag names already used on at least one question, with counts."""
    return handle_list_tags()


@mcp.tool()
def list_reports(status: str | None = None, limit: int | None = None) -> str:
    """List reported issues. Defaults to status NEW on the server when status is omitted."""
    return handle_list_reports(status=status, limit=limit)


@mcp.tool()
def get_report(report_id: str) -> str:
    """Fetch one report plus the question in interchange shape."""
    return handle_get_report(report_id)


@mcp.tool()
def set_report_status(
    report_id: str, status: str, resolution_note: str | None = None
) -> str:
    """Set a report to IN_PROGRESS, RESOLVED, or REJECTED. Does not edit the question."""
    return handle_set_report_status(report_id, status, resolution_note=resolution_note)


@mcp.resource("quiz://schema")
def resource_schema() -> str:
    return handle_resource_schema()


@mcp.resource("quiz://instructions")
def resource_instructions() -> str:
    return handle_resource_instructions()


@mcp.resource("quiz://examples/{qtype}")
def resource_example(qtype: str) -> str:
    return handle_resource_example(qtype)


def main() -> None:
    parser = argparse.ArgumentParser(prog="quiz-authoring-mcp")
    parser.add_argument("--http", action="store_true", help="Serve Streamable HTTP instead of stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

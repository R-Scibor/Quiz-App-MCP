from __future__ import annotations

import argparse
import json
import os
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    from mcp.server.mcpserver import MCPServer as FastMCP

from quiz_authoring_mcp import compose
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


def _compose_and_save(test_id: str, mutator, dry_run: bool = False) -> str:
    c = _client()
    try:
        doc = c.export_quiz(test_id)
        try:
            doc = mutator(doc)
        except KeyError as exc:
            return _dump({"error": "QUESTION_NOT_FOUND", "message": str(exc)})
        report = c.validate_quiz(doc)
        if not report.get("valid"):
            return _dump(report)
        return _dump(c.import_quiz(doc, test_id=test_id, dry_run=dry_run))
    except AuthoringAPIError as exc:
        body = exc.body if isinstance(exc.body, dict) else {"message": str(exc.body)}
        return _dump(
            {
                "error": body.get("error", "HTTP_ERROR"),
                "status_code": exc.status_code,
                **body,
            }
        )
    except KeyError as exc:
        return _dump({"error": "CONFIG", "message": f"Missing environment variable {exc}"})
    finally:
        c.close()


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


def handle_add_question(test_id: str, question: dict, dry_run: bool = False) -> str:
    return _compose_and_save(test_id, lambda doc: compose.add_question(doc, question), dry_run)


def handle_update_question(
    test_id: str, question_id: str, question: dict, dry_run: bool = False
) -> str:
    return _compose_and_save(
        test_id, lambda doc: compose.update_question(doc, question_id, question), dry_run
    )


def handle_delete_question(test_id: str, question_id: str, dry_run: bool = False) -> str:
    return _compose_and_save(
        test_id, lambda doc: compose.delete_question(doc, question_id), dry_run
    )


def handle_update_grading(
    test_id: str,
    question_id: str,
    grading_criteria: str | None = None,
    max_points: int | None = None,
    dry_run: bool = False,
) -> str:
    return _compose_and_save(
        test_id,
        lambda doc: compose.update_grading(doc, question_id, grading_criteria, max_points),
        dry_run,
    )


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
    """Append a question, validate, then import the full document. Does not import if validation fails."""
    return handle_add_question(test_id, question, dry_run)


@mcp.tool()
def update_question(
    test_id: str, question_id: str, question: dict, dry_run: bool = False
) -> str:
    """Merge fields into an existing question (by question_id), validate, import."""
    return handle_update_question(test_id, question_id, question, dry_run)


@mcp.tool()
def delete_question(test_id: str, question_id: str, dry_run: bool = False) -> str:
    """Remove a question from the document and re-import. Questions with attempts may be blocked by the server."""
    return handle_delete_question(test_id, question_id, dry_run)


@mcp.tool()
def update_grading(
    test_id: str,
    question_id: str,
    gradingCriteria: str | None = None,
    maxPoints: int | None = None,
    dry_run: bool = False,
) -> str:
    """Patch gradingCriteria and/or maxPoints on an open question."""
    return handle_update_grading(test_id, question_id, gradingCriteria, maxPoints, dry_run)


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

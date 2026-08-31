from __future__ import annotations

import copy
from typing import Any


def _clone(doc: dict) -> dict:
    return copy.deepcopy(doc)


def _next_source_id(questions: list[dict]) -> int:
    ids = [q["id"] for q in questions if isinstance(q.get("id"), int)]
    return (max(ids) + 1) if ids else 1


def _find(questions: list[dict], question_id: str) -> int:
    for i, q in enumerate(questions):
        if q.get("question_id") == question_id:
            return i
    raise KeyError(f"question_id not found: {question_id}")


def add_question(doc: dict, question: dict) -> dict:
    out = _clone(doc)
    q = dict(question)
    if "id" not in q or q["id"] is None:
        q["id"] = _next_source_id(out["questions"])
    out["questions"].append(q)
    return out


def update_question(doc: dict, question_id: str, patch: dict) -> dict:
    out = _clone(doc)
    idx = _find(out["questions"], question_id)
    merged = dict(out["questions"][idx])
    merged.update(patch)
    out["questions"][idx] = merged
    return out


def delete_question(doc: dict, question_id: str) -> dict:
    out = _clone(doc)
    idx = _find(out["questions"], question_id)
    out["questions"].pop(idx)
    return out


def update_grading(
    doc: dict,
    question_id: str,
    grading_criteria: str | None = None,
    max_points: int | None = None,
) -> dict:
    patch: dict[str, Any] = {}
    if grading_criteria is not None:
        patch["gradingCriteria"] = grading_criteria
    if max_points is not None:
        patch["maxPoints"] = max_points
    return update_question(doc, question_id, patch)

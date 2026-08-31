from quiz_authoring_mcp.compose import (
    add_question,
    delete_question,
    update_grading,
    update_question,
)

DOC = {
    "test_id": "t1",
    "category": "History",
    "scope": "Poland",
    "version": "1.0",
    "questions": [
        {
            "id": 1,
            "question_id": "q1",
            "questionText": "Year?",
            "type": "open-text",
            "gradingCriteria": "966",
            "maxPoints": 2,
        }
    ],
}


def test_add_question_appends_and_assigns_next_id():
    q = {
        "questionText": "Who?",
        "type": "single-choice",
        "options": ["A", "B"],
        "correctAnswers": [0],
    }
    out = add_question(DOC, q)
    assert len(out["questions"]) == 2
    assert out["questions"][1]["id"] == 2
    assert out["questions"][1]["questionText"] == "Who?"
    assert len(DOC["questions"]) == 1  # original not mutated


def test_update_question_merges_by_question_id():
    out = update_question(DOC, "q1", {"questionText": "What year?"})
    assert out["questions"][0]["questionText"] == "What year?"
    assert out["questions"][0]["gradingCriteria"] == "966"


def test_update_question_missing_raises():
    try:
        update_question(DOC, "missing", {"questionText": "x"})
        assert False
    except KeyError as exc:
        assert "missing" in str(exc)


def test_delete_question():
    out = delete_question(DOC, "q1")
    assert out["questions"] == []


def test_update_grading():
    out = update_grading(DOC, "q1", grading_criteria="Must mention 966", max_points=3)
    assert out["questions"][0]["gradingCriteria"] == "Must mention 966"
    assert out["questions"][0]["maxPoints"] == 3

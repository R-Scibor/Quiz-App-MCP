from __future__ import annotations

from typing import Any

import httpx


class AuthoringAPIError(Exception):
    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body
        super().__init__(f"Authoring API {status_code}: {body}")


class AuthoringClient:
    def __init__(self, base_url: str, token: str, timeout: float = 30.0):
        origin = base_url.rstrip("/")
        self._http = httpx.Client(
            base_url=f"{origin}/api/v1/authoring",
            headers={"Authorization": f"Token {token}", "Accept": "application/json"},
            timeout=timeout,
        )

    def close(self) -> None:
        self._http.close()

    def _parse(self, response: httpx.Response) -> Any:
        try:
            body = response.json()
        except ValueError:
            body = {"error": "INVALID_RESPONSE", "message": response.text}
        if response.status_code >= 400:
            raise AuthoringAPIError(response.status_code, body)
        return body

    def get_schema(self) -> dict:
        return self._parse(self._http.get("/schema/"))

    def get_instructions(self) -> dict:
        return self._parse(self._http.get("/instructions/"))

    def validate_quiz(self, quiz: dict) -> dict:
        return self._parse(self._http.post("/validate/", json=quiz))

    def list_quizzes(self) -> list:
        return self._parse(self._http.get("/tests/"))

    def export_quiz(self, test_id: str) -> dict:
        return self._parse(self._http.get(f"/tests/{test_id}/export/"))

    def get_question(self, test_id: str, question_id: str) -> dict:
        return self._parse(self._http.get(f"/tests/{test_id}/questions/{question_id}/"))

    def update_quiz_metadata(self, test_id: str, **fields: Any) -> dict:
        payload = {k: v for k, v in fields.items() if v is not None}
        return self._parse(self._http.patch(f"/tests/{test_id}/", json=payload))

    def import_quiz(self, quiz: dict, test_id: str | None = None, dry_run: bool = False) -> dict:
        payload = dict(quiz)
        if test_id:
            payload["test_id"] = test_id
        params = {"dry_run": "true"} if dry_run else None
        return self._parse(self._http.post("/import/", json=payload, params=params))

    def create_question(self, test_id: str, question: dict, dry_run: bool = False) -> dict:
        params = {"dry_run": "true"} if dry_run else None
        return self._parse(
            self._http.post(f"/tests/{test_id}/questions/", json=question, params=params)
        )

    def patch_question(self, question_id: str, fields: dict, dry_run: bool = False) -> dict:
        params = {"dry_run": "true"} if dry_run else None
        return self._parse(
            self._http.patch(f"/questions/{question_id}/", json=fields, params=params)
        )

    def remove_question(self, question_id: str, dry_run: bool = False) -> dict:
        params = {"dry_run": "true"} if dry_run else None
        return self._parse(self._http.delete(f"/questions/{question_id}/", params=params))

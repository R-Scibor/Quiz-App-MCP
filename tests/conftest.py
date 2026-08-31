import pytest
import respx
from httpx import Response

from quiz_authoring_mcp.client import AuthoringClient

API = "https://quiz.test/api/v1/authoring"


@pytest.fixture
def client():
    return AuthoringClient(base_url="https://quiz.test", token="secret-token", timeout=5.0)

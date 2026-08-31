import sys
from unittest.mock import patch

import pytest

from quiz_authoring_mcp import server


def test_main_runs_stdio_by_default():
    with patch.object(sys, "argv", ["quiz-authoring-mcp"]), patch.object(
        server.mcp, "run"
    ) as mock_run:
        server.main()
        mock_run.assert_called_once_with(transport="stdio")


def test_main_runs_http():
    with patch.object(
        sys, "argv", ["quiz-authoring-mcp", "--http", "--host", "0.0.0.0", "--port", "9000"]
    ), patch.object(server.mcp, "run") as mock_run:
        server.main()
        mock_run.assert_called_once_with(transport="streamable-http", host="0.0.0.0", port=9000)

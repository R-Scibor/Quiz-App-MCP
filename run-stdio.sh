#!/usr/bin/env bash
# Load gitignored .env then exec the MCP server. Keeps QUIZ_APP_TOKEN out of client configs.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT}/.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "Missing ${ENV_FILE}. Copy .env.example and set QUIZ_APP_URL and QUIZ_APP_TOKEN." >&2
  exit 1
fi
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a
exec "${ROOT}/.venv/bin/quiz-authoring-mcp" "$@"

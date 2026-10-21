# Quiz Authoring MCP Server

An MCP (Model Context Protocol) server that enables AI agents to author, validate, export, import, and edit quizzes by interacting with the Quiz-App staff authoring HTTP API.

## Requirements

- Python 3.12+
- A running Quiz-App instance with the authoring API enabled (`/api/v1/authoring/*`).
- A Django user with staff privileges (`is_staff=True`) and a DRF Token. A normal login token is rejected with `403 PERMISSION_DENIED`.

## Install

```bash
git clone https://github.com/R-Scibor/Quiz-App-MCP.git
cd Quiz-App-MCP
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env
chmod +x run-stdio.sh
```

Edit `.env`. `QUIZ_APP_URL` is the Quiz-App origin with no trailing slash (`http://127.0.0.1:8050` when nginx publishes the app on that port). Put the staff token in `QUIZ_APP_TOKEN`.

If this directory is moved, recreate the virtualenv. The console-script shebang keeps the old path and will not start.

### Staff token

Create a superuser, or mark an existing user `is_staff=True`, then issue a token:

```bash
python manage.py createsuperuser
python manage.py shell -c "
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
User = get_user_model()
user = User.objects.get(username='<staff-username>')
token, _ = Token.objects.get_or_create(user=user)
print(token.key)
"
```

When Quiz-App runs in Docker, run those commands inside the web container (`docker exec -it django_web python manage.py …` in the homelab compose file). Write the key into `.env` and do not commit that file.

## Environment Variables

Configure environment variables (see `.env.example`):

- `QUIZ_APP_URL`: Base URL of the Quiz-App instance (e.g. `https://localhost:8050` or `http://localhost:8000`).
- `QUIZ_APP_TOKEN`: DRF Authentication token for the staff user.
- `QUIZ_APP_TIMEOUT_SECONDS`: (Optional) HTTP request timeout in seconds (default: `30`).

> **Security Note:** Never commit authentication tokens or environment files containing secrets.

## MCP client configuration (stdio)

Point the client at `run-stdio.sh`. The script loads `.env` and execs the server, so the token stays out of client config.

Grok, in `~/.grok/config.toml` (use the absolute path):

```toml
[mcp_servers.quiz-authoring]
command = "/absolute/path/to/Quiz-App-MCP/run-stdio.sh"
args = []
enabled = true
```

Check it with `grok mcp doctor quiz-authoring`. A healthy server reports a handshake and 10 tools. Open a new Grok session after the first successful doctor run so that session attaches the server.

Claude, Cursor, and other stdio clients:

```json
{
  "mcpServers": {
    "quiz-authoring": {
      "command": "/absolute/path/to/Quiz-App-MCP/run-stdio.sh"
    }
  }
}
```

If a client cannot run the script, call `.venv/bin/quiz-authoring-mcp` and pass `QUIZ_APP_URL` and `QUIZ_APP_TOKEN` in that client's env block. Do not commit that config.

An agent setting this up for someone should follow [AGENTS.md](AGENTS.md): ask whether to walk them through the commands or run the local steps, and never print the token.

## Available Tools and Resources

### Resources
- `quiz://schema`: Returns the full interchange JSON schema and supported question types with examples.
- `quiz://instructions`: Returns markdown guidance and instructions for authoring quizzes.
- `quiz://examples/{qtype}`: Returns an example interchange JSON structure for a specific question type.

### Document Tools
- `list_quizzes`: List quizzes in the catalog (ID, category, scope, version, question counts).
- `export_quiz(test_id)`: Export a quiz by `test_id` as interchange JSON including UUIDs.
- `validate_quiz(quiz)`: Validate interchange quiz JSON against business rules and schema.
- `import_quiz(quiz, test_id=None, dry_run=False)`: Upsert a full quiz document. Supports dry-run preview.
- `update_quiz_metadata(test_id, category=None, scope=None, version=None, description=None)`: Patch quiz metadata.

### Question tools
These call the per-question authoring endpoints. `update_question`, `delete_question`, and `update_grading` first confirm the question belongs to `test_id`.
- `get_question(test_id, question_id)`: Fetch a single question in interchange format.
- `add_question(test_id, question, dry_run=False)`: Create one question. Omitted `id` gets the next `source_id`.
- `update_question(test_id, question_id, question, dry_run=False)`: Merge the given fields into that question.
- `delete_question(test_id, question_id, dry_run=False)`: Delete one question. Questions with attempts come back as `DELETE_BLOCKED`.
- `update_grading(test_id, question_id, gradingCriteria=None, maxPoints=None, dry_run=False)`: Patch grading criteria and max points.

`import_quiz` is still the way to replace a whole document.

## HTTP Transport & Docker

You can run the server with Streamable HTTP transport:

```bash
quiz-authoring-mcp --http --host 0.0.0.0 --port 8080
```

Or using Docker:

```bash
docker build -t quiz-authoring-mcp .
docker run -p 8080:8080 -e QUIZ_APP_URL="https://host.docker.internal:8050" -e QUIZ_APP_TOKEN="<staff-token>" quiz-authoring-mcp
```

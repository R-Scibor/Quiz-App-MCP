# Quiz Authoring MCP Server

An MCP (Model Context Protocol) server that enables AI agents to author, validate, export, import, and edit quizzes by interacting with the Quiz-App staff authoring HTTP API.

## Requirements

- Python 3.12+
- A running Quiz-App instance with the authoring API enabled (`/api/v1/authoring/*`).
- A Django user with staff privileges (`is_staff=True`) and a DRF Token.

### Setting up a Staff Token in Quiz-App

1. Create a superuser or staff user in Quiz-App:
   ```bash
   python manage.py createsuperuser
   ```
2. Generate an API token for the staff user in Django Admin or via the Django shell:
   ```python
   from django.contrib.auth import get_user_model
   from rest_framework.authtoken.models import Token
   User = get_user_model()
   user = User.objects.get(username="<your-staff-username>")
   token, _ = Token.objects.get_or_create(user=user)
   print(token.key)
   ```

## Environment Variables

Configure environment variables (see `.env.example`):

- `QUIZ_APP_URL`: Base URL of the Quiz-App instance (e.g. `https://localhost:8050` or `http://localhost:8000`).
- `QUIZ_APP_TOKEN`: DRF Authentication token for the staff user.
- `QUIZ_APP_TIMEOUT_SECONDS`: (Optional) HTTP request timeout in seconds (default: `30`).

> **Security Note:** Never commit authentication tokens or environment files containing secrets.

## MCP Client Configuration (stdio)

To configure an MCP client (such as Claude Desktop or Antigravity) to use this server over stdio:

```json
{
  "mcpServers": {
    "quiz-authoring": {
      "command": "quiz-authoring-mcp",
      "env": {
        "QUIZ_APP_URL": "https://localhost:8050",
        "QUIZ_APP_TOKEN": "<staff-token>",
        "QUIZ_APP_TIMEOUT_SECONDS": "30"
      }
    }
  }
}
```

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

### Question Mutation Tools (Compose)
These tools fetch the latest quiz document, apply the change in-memory, validate the updated document, and import it:
- `get_question(test_id, question_id)`: Fetch a single question in interchange format.
- `add_question(test_id, question, dry_run=False)`: Append a question, validate, and import.
- `update_question(test_id, question_id, question, dry_run=False)`: Merge changes into an existing question, validate, and import.
- `delete_question(test_id, question_id, dry_run=False)`: Remove a question from a quiz, validate, and import.
- `update_grading(test_id, question_id, gradingCriteria=None, maxPoints=None, dry_run=False)`: Patch grading criteria and max points.

*Note: Question write tools currently use a compose loop (export -> patch -> validate -> import). Direct question-level PATCH endpoints may replace this in future versions.*

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

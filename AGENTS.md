# Agent setup

Use this when a user wants the Quiz Authoring MCP installed or reconnected. Human-facing detail is in `README.md`. Do the local steps yourself unless they ask to be walked through every command.

## Choose a mode

Ask once, then proceed:

- **Walk through.** Give the next command and wait. They run it.
- **Set it up.** You create the virtualenv, `.env`, and client config. They only supply the Quiz-App URL and a staff token, or they allow you to create the token.

Default to setting it up when they have already asked you to install it.

## Rules

- Never commit `.env` or put `QUIZ_APP_TOKEN` in `~/.grok/config.toml`, `.mcp.json`, or the chat transcript.
- Write the token only into `.env` (mode `600`). Confirm success with a quiz count, not the key.
- A login token from a non-staff user fails authoring calls with `403 PERMISSION_DENIED`.
- If the repo directory was moved and `run-stdio.sh` dies with `cannot execute: required file not found`, recreate `.venv`. The shebang still points at the old path.

## Steps

1. Confirm Python 3.12+ (`python3 --version`).
2. Confirm Quiz-App is up: `GET {QUIZ_APP_URL}/api/v1/tests/` returns 200. Do not guess the URL. This homelab publishes the app at `http://127.0.0.1:8050`.
3. From the repo root:

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -e ".[dev]"
   test -f .env || cp .env.example .env
   chmod +x run-stdio.sh
   ```

4. Set `QUIZ_APP_URL` and `QUIZ_APP_TOKEN` in `.env`. Ask for the token. Create one only if they say you may, inside Quiz-App (or `docker exec` into the web container, `django_web` in the homelab compose file):

   ```bash
   python manage.py shell -c "
   from django.contrib.auth import get_user_model
   from rest_framework.authtoken.models import Token
   user = get_user_model().objects.get(username='<staff-username>')
   assert user.is_staff
   token, _ = Token.objects.get_or_create(user=user)
   print(token.key)
   "
   ```

5. Register stdio with the absolute path to `run-stdio.sh` and no token in the client env. For Grok, edit `~/.grok/config.toml`:

   ```toml
   [mcp_servers.quiz-authoring]
   command = "/absolute/path/to/Quiz-App-MCP/run-stdio.sh"
   args = []
   enabled = true
   ```

6. Prove it. `grok mcp doctor quiz-authoring` should show a handshake and the tool list. Or, with `.env` loaded by the script, import `handle_list_quizzes` and report how many quizzes came back. A new Grok session picks up a server that failed at the start of the current one.

## Triage a reported issue

Use the host model. Do not call another LLM from the MCP.

1. `list_reports` for status `NEW`.
2. `get_report` for one id. Read the question, the learner's answer, and the description.
3. If the question is wrong, `update_question` or `retire_question` on that `test_id` and `question_id`.
4. `set_report_status` to `RESOLVED` or `REJECTED` with a short `resolution_note`. `IN_PROGRESS` is for a fix you have not finished.

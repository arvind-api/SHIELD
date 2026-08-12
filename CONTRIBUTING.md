# Contributing to SHIELD

## Scope

SHIELD has exactly two user-facing features: the **Email Analyzer** and the **Guardian Scam Scanner**. It is explicitly not a general-purpose AI chat app and not a resume analyzer — PRs adding either will be declined. See `CLAUDE.md` for full project scope and conventions.

## Getting set up

See the "Local development" and "With Docker Compose" sections in `README.md` to get the backend and frontend running.

## Making changes

- Python: snake_case for modules, functions, variables.
- React/TS: PascalCase for components, camelCase for functions/variables.
- Routes: kebab-case for both REST paths (e.g. `/email-analyzer/analyze`) and Next.js route segments.
- Keep Pydantic schemas (`backend/app/schemas/`) separate from SQLAlchemy models (`backend/app/models/`) — never reuse one for the other.
- One FastAPI router file per feature under `backend/app/api/routes/`, registered in `backend/app/main.py`.
- Feature logic belongs in `backend/app/services/`, not in route handlers — routes stay thin (validate → call service → return).
- All AI calls go through `backend/app/core/ai/client.py`; nothing else should import the Anthropic SDK directly.

## Before opening a PR

- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm run lint && npm run build`

Both run in CI on every push and PR to `master` — a PR won't be merged with a failing check.

## Commit messages

Keep them short and focused on why the change was made, not just what changed.

## Reporting issues

Open a GitHub issue with steps to reproduce, expected vs. actual behavior, and relevant logs if applicable.

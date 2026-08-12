# SHIELD

**S**cam & **H**armful **I**ntent **E**mail **L**ogic **D**etector — a focused cybersecurity web app.

## Purpose

SHIELD has exactly two user-facing features:

1. **Email Analyzer** — paste or upload an email, get back tone/intent analysis, spam/phishing signals, and a reply suggestion.
2. **Guardian Scam Scanner** — paste any text (message, link, offer, etc.) and get a scam/phishing/social-engineering risk assessment with reasoning.

## Explicitly out of scope

- **No AI chat module.** SHIELD is not a general-purpose assistant. Don't add a chat interface, chat route, or chat model — even if a request seems to imply one.
- **No resume analyzer.** Do not scaffold or build resume/CV analysis features.

If a future request resembles either of these, flag it rather than building it silently.

## Tech stack

**Backend** — FastAPI, SQLAlchemy, SQLite for now. The database layer is structured so Postgres is a drop-in swap later: the connection string lives in `DATABASE_URL` (config/env), never hardcoded, and models avoid SQLite-only types. Auth is JWT via `python-jose` + `passlib` (bcrypt).

**Frontend** — Next.js 14 (App Router), TypeScript, Tailwind CSS.

**AI** — Anthropic Claude API for real analysis, with a rule-based mock mode fallback so the app works without an API key. Mock/real switching is isolated behind `app/core/ai/client.py` — route handlers and services never call the Anthropic SDK or mock logic directly, only the client wrapper.

**Infra** — Docker Compose runs backend + frontend together for local dev.

## Conventions

- Python: snake_case for modules, functions, variables.
- React/TS: PascalCase for components, camelCase for functions/variables.
- Routes: kebab-case for both REST paths (`/email-analyzer/analyze`) and Next.js route segments (`/email-analyzer`).
- Pydantic schemas (`app/schemas/`) are kept separate from SQLAlchemy ORM models (`app/models/`) — never reuse one for the other.
- One FastAPI router file per feature under `app/api/routes/`, registered in `app/main.py`.
- Feature business logic lives in `app/services/`, not in route handlers — routes stay thin (validate → call service → return).
- All AI calls go through `app/core/ai/client.py`; nothing else imports the Anthropic SDK.

## Current state

Skeleton only. Auth (register/login/JWT), the two feature routes, DB models, and matching frontend pages exist as stubs/placeholders with no real analysis logic yet. Real logic will be built module by module in later sessions. UI/UX polish is a separate, later pass — don't polish styling while stubbing out features.

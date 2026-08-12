# SHIELD

Scam & Harmful Intent Email Logic Detector. See `CLAUDE.md` for project scope and conventions.

## Local development (without Docker)

**Backend**

```
cd backend
python -m venv .venv && source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp ../.env.example ../.env   # then edit as needed
uvicorn app.main:app --reload
```

API docs at http://localhost:8000/docs

**Frontend**

```
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

App at http://localhost:3000

## With Docker Compose

```
cp .env.example .env   # then edit as needed
docker compose up --build
```

## Status

Skeleton only — auth, DB models, and both feature routes/pages exist as stubs. No AI analysis logic yet.

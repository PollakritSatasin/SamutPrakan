# SamutPrakan

AI Simulated Patient (SP) training platform for medical students to practice history taking and physical examination through natural dialogue.

## Repository layout

```
backend/                 FastAPI service
  app/api/              HTTP routers
  app/core/             Settings
  app/models/           SQLAlchemy models
  app/schemas/          Pydantic v2 case schemas
  app/services/         Case loading and domain logic
  data/seed_cases/      Sample clinical cases (JSON)
  tests/                Pytest schema/loader tests
```

## Backend (current)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
pytest
```

See [backend/README.md](backend/README.md) for Docker and API details.

## Frontend

Next.js 14+ (App Router) client is planned next: TypeScript, Tailwind CSS, and Web Audio streaming.

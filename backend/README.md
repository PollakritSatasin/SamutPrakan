# SamutPrakan Backend

FastAPI service for the AI Simulated Patient (SP) training platform. Case definitions are validated with Pydantic v2 and loaded from JSON seed files.

## Requirements

- Python 3.11+

## Local setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Health: `GET /health`
- List cases: `GET /api/v1/cases`
- Case overview (no hidden diagnosis): `GET /api/v1/cases/{case_id}`
- Start session: `POST /api/v1/sessions` with `{"case_id": "..."}`
- Complete session: `POST /api/v1/sessions/{session_id}/complete`
- Faculty/full case (hidden diagnosis included): `GET /api/v1/cases/{case_id}/faculty`
- OpenAPI docs: `/docs`

## Tests

```bash
pytest
```

## Docker

```bash
docker build -t samutprakan-backend .
docker run --rm -p 8000:8000 samutprakan-backend
```

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
- Student case cards (title, chief complaint, setting only): `GET /api/v1/cases`
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

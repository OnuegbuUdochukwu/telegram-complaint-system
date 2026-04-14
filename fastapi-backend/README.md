# FastAPI Backend

Backend service for complaint submission, dashboard APIs, authentication/RBAC, realtime updates, and media handling.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Set at least these variables in `.env`:

- `DATABASE_URL`
- `JWT_SECRET` / `SECRET_KEY`
- `BACKEND_SERVICE_TOKEN`
- storage variables (`STORAGE_PROVIDER`, `S3_BUCKET`, etc.) when testing uploads

## Run

```bash
uvicorn app.main:app --reload --port 8000
```

Useful endpoints:

- `GET /health`
- `GET /metrics`
- `POST /auth/login`
- `GET /api/v1/complaints`

## Tests

```bash
pytest
ruff check app scripts
```

## Dependency Layout

- `requirements.txt`: runtime dependencies used by API/worker.
- `requirements-dev.txt`: development, lint, and test extras.

# Telegram Complaint System

Complaint lifecycle platform composed of a Telegram reporter bot, FastAPI backend, static admin dashboard, and supporting infrastructure.

## Repository Structure

- `src/bot/`: Telegram bot source code (`main.py`, `client.py`, `merged_constants.py`).
- `fastapi-backend/`: API, auth/RBAC, realtime updates, media/upload pipeline, migrations.
- `dashboard/`: static admin UI (`login.html`, `index.html`, JS utilities).
- `scripts/`: operational and smoke-test scripts.
- `tests/`: integration/E2E-style tests against a running backend.
- `docs/`: architecture, deployment, storage, and implementation notes.
- `infra/`: Terraform + IAM templates for cloud deployment.
- `archive/`: historical/legacy materials retained for traceability.

## Current Implementation State

- Completed: bot reporting/status flows, backend CRUD/auth/RBAC, dashboard complaint management, websocket refresh, S3/MinIO media support, observability, Alembic migrations.
- Partially complete: checklist/doc alignment, some production hardening and UAT process artifacts.
- Planned next work is tracked in `docs/ROADMAP.md`.

## Local Development

### Option A: Full stack with Docker Compose

```bash
cp fastapi-backend/.env.example fastapi-backend/.env
docker compose -f docker-compose.dev.yml up --build
```

Services:

| Service | Port | URL |
| --- | --- | --- |
| Backend API | 8001 | http://localhost:8001 |
| Dashboard (served by backend) | 8001 | http://localhost:8001/dashboard/login.html |
| MinIO API | 9000 | http://localhost:9000 |
| MinIO Console | 9001 | http://localhost:9001 |
| PostgreSQL | 5434 | localhost:5434 |
| Redis | 6379 | localhost:6379 |

### Option B: Backend only

```bash
cd fastapi-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Dashboard URL in this mode: `http://localhost:8000/dashboard/login.html`.

## Tests and Quality Checks

```bash
cd fastapi-backend
source .venv/bin/activate
pytest
ruff check app scripts
```

Optional root-level integration tests expect a running backend and can be executed with `pytest tests`.

## Production Notes

- Copy `.env.production.example` to `.env.production` and set real secrets.
- Use `docker compose -f docker-compose.prod.yml up -d` for production-like compose deployment.
- Follow `docs/DEPLOYMENT_GUIDE.md` and `infra/terraform/` for managed cloud environments.


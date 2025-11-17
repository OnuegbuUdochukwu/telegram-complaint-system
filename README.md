# Telegram Complaint System

Production-ready implementation of the Covenant University complaint workflow spanning:

- Telegram bot for students (`main.py`)
- FastAPI backend (`fastapi-backend/`)
- Static admin dashboard (`dashboard/`)
- S3-backed media uploads with Celery workers, Redis, and PostgreSQL
- Terraform IaC + operations docs under `infra/` and `docs/`

## Quick Start

```bash
cp fastapi-backend/.env.example fastapi-backend/.env   # edit secrets
docker compose -f docker-compose.dev.yml up --build
```

Services exposed locally:

| Service | Port | Notes |
| ------- | ---- | ----- |
| FastAPI API | 8001 | http://localhost:8001 |
| MinIO API / Console | 9000 / 9001 | mirrors S3 |
| Postgres | 5434 | `cms_user/cms_password` |
| Redis | 6379 | Celery broker |

## Running Tests

```bash
cd fastapi-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Unit tests (`fastapi-backend/tests`) mock S3 via `moto`. Integration tests inside `tests/` expect a running backend (`TEST_BACKEND_URL` configurable).

## CI/CD Snapshot

1. `pytest` (backend + bot).
2. `docker build` for backend + worker + bot images.
3. `terraform plan` against staging workspace.
4. Push images and deploy via ECS/Kubernetes GitOps.
5. Smoke test `/health`, run bot `/report` happy-path script (`scripts/e2e_run.py`).

## Deployment Summary

- Provision infrastructure with Terraform (`infra/terraform`).
- Publish container images for backend + worker (Dockerfile included).
- Configure Secrets Manager parameters (DB URL, Redis, service token, etc.).
- Deploy bot (python-telegram-bot) with `BACKEND_SERVICE_TOKEN` + `BACKEND_URL`.
- Follow the comprehensive `docs/DEPLOYMENT_GUIDE.md` for end-to-end steps.


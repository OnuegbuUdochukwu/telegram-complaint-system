# Phase 3 Development Checklist

This file is a reformatted, progress-trackable checklist derived from the Phase 3 task breakdown. Each major section includes tasks with nested subtasks and supporting context (Purpose, Tools/Technologies, Expected Output). After each section there's a short progress summary.

---

## 🔐 Backend — Security & Auth

-   [x] 3.1 Implement JWT-based authentication for backend

-   Purpose: Secure admin and write endpoints by issuing and validating time-limited JWTs. Provide a login flow for porters/admins.
-   Tools/Technologies: FastAPI, python-jose, Passlib (bcrypt), SQLModel, PostgreSQL
-   Expected Output: POST /auth/login issues access tokens; protected endpoints reject unauthorized/expired tokens.

-   [ ] 3.2 Harden admin endpoints and add RBAC (reporter, porter, admin)

    -   Purpose: Enforce least-privilege access across dashboard and write APIs.
    -   Tools/Technologies: FastAPI dependency injection, SQLModel, DB role column or mapping
    -   Expected Output: Admin/porter roles enforced; 401/403 returned on invalid/insufficient access.

-   [ ] 3.3 Secrets & config management
    -   Purpose: Move secrets out of repo and document secure local setup.
    -   Tools/Technologies: dotenv, Vault/Secrets Manager (optional), .env.example
    -   Expected Output: No creds in repo; README docs for local dev using secrets.

**Progress:** 1/3 tasks completed (33%)

---

## 🖥️ Admin Dashboard & API

-   [ ] 3.4 Build Admin Dashboard (MVP)

    -   Purpose: Provide a UI for admins/porters to list, filter, view, assign, and update complaints.
    -   Tools/Technologies: React (or Svelte), fetch/httpx, JWT for auth, frontend routing
    -   Expected Output: Minimal SPA with list view, detail modal/page, and assignment/status controls.

-   [ ] 3.5 API: paginated list + update endpoints for dashboard
    -   Purpose: Support dashboard with server-side pagination, filters, and PATCH updates to complaints.
    -   Tools/Technologies: FastAPI, SQLModel, PostgreSQL, Pydantic request/response models
    -   Expected Output: GET /api/v1/complaints?page=&page_size=&status=&hostel= ; PATCH /api/v1/complaints/{id} to change status/assignment.

**Progress:** 0/2 tasks completed (0%)

---

## ⚡ Real-time & Notifications

-   [ ] 3.6 WebSocket or Server-Sent Events (SSE) for real-time updates

    -   Purpose: Deliver new complaint and status-change events to connected dashboards in near real-time.
    -   Tools/Technologies: FastAPI WebSockets or SSE, Redis (pub/sub) optional, frontend WS client
    -   Expected Output: Authenticated WS/SSE endpoint and client displays new events within ~1s.

-   [ ] 3.7 Push notifications / Telegram admin alerts (optional)
    -   Purpose: Notify on high-priority complaints via Telegram or push channels.
    -   Tools/Technologies: python-telegram-bot for sending messages, push providers (FCM/APNs) optional
    -   Expected Output: Configurable alerting pipeline (hostel-level) that is rate-limited and opt-in.

**Progress:** 0/2 tasks completed (0%)

---

## 🖼️ Media handling (photos & attachments)

-   [ ] 3.8 Photo uploads and storage

    -   Purpose: Allow reporters to attach images; store them securely and serve thumbnails/links to dashboard.
    -   Tools/Technologies: S3-compatible storage (MinIO/AWS S3), signed URLs, FastAPI upload endpoint
    -   Expected Output: Upload endpoint returning signed URLs; access restricted to authenticated users.

-   [ ] 3.9 Thumbnailing & size limits
    -   Purpose: Reduce bandwidth and display-friendly thumbnails; enforce size/type limits.
    -   Tools/Technologies: Pillow or libvips, background worker (Celery/RQ) optional
    -   Expected Output: Thumbnails produced and available via authenticated endpoints; upload size/type limited.

**Progress:** 0/2 tasks completed (0%)

---

## 🛠️ CI/CD, Infra & Production Readiness

-   [ ] 3.10 CI: GitHub Actions workflow

    -   Purpose: Run tests and lint on PRs and prevent regressions before merges.
    -   Tools/Technologies: GitHub Actions, PostgreSQL service in CI, Python matrix
    -   Expected Output: Workflow that runs unit and integration tests; PRs block on failing tests.

-   [ ] 3.11 Dockerize backend and optional worker

    -   Purpose: Standardize dev and production builds; enable local reproducible environments.
    -   Tools/Technologies: Dockerfile, docker-compose, optional Redis/Postgres services
    -   Expected Output: docker-compose up for local dev; reproducible CI builds.

-   [ ] 3.12 Observability: logging, metrics, error tracking
    -   Purpose: Make system observable and trace errors in staging/production.
    -   Tools/Technologies: structured JSON logging, Prometheus client, Sentry integration
    -   Expected Output: /metrics endpoint and Sentry configured for error reporting.

**Progress:** 0/3 tasks completed (0%)

---

## 🧭 Operational & Misc

-   [ ] 3.13 Migration tooling (Alembic)

    -   Purpose: Manage schema changes safely and reproducibly across environments.
    -   Tools/Technologies: Alembic, SQLAlchemy/SQLModel integration
    -   Expected Output: Alembic configured and baseline revision created from current schema.

-   [ ] 3.14 Data privacy & retention policy

    -   Purpose: Define retention for complaints and media and add tools to purge old data.
    -   Tools/Technologies: DB scheduled jobs or background workers, policy docs
    -   Expected Output: In-repo retention policy and admin purge endpoint or cron job.

-   [ ] 3.15 Load testing & capacity planning
    -   Purpose: Validate system performance and estimate scaling requirements.
    -   Tools/Technologies: k6, Locust, or similar load testers
    -   Expected Output: Load test scripts and a report with recommended scaling limits.

**Progress:** 0/3 tasks completed (0%)

---

## 🚀 Quick first sprint (2 weeks) — recommended scope (MVP)

-   [ ] Implement JWT auth + RBAC (3.1 + 3.2)

    -   Purpose: Secure backend so dashboard and write flows can be developed safely.
    -   Tools/Technologies: FastAPI, python-jose, SQLModel
    -   Expected Output: Working /auth/login and protected endpoints; basic role enforcement.

-   [ ] Add GET /api/v1/complaints pagination + PATCH for status changes (3.5)

    -   Purpose: Provide stable API endpoints for dashboard list and status updates.
    -   Tools/Technologies: FastAPI, SQLModel, Pydantic
    -   Expected Output: Paginated list and PATCH endpoint with RBAC checks.

-   [ ] Create minimal React dashboard to list complaints and view detail (3.4, MVP subset)

    -   Purpose: Provide an early UI for admins and porters to manage complaints.
    -   Tools/Technologies: React, fetch/httpx, JWT auth
    -   Expected Output: SPA listing complaints, detail modal and status/assignment controls.

-   [ ] Add GitHub Actions CI for tests and linting (3.10)
    -   Purpose: Prevent regressions and automate tests on PRs.
    -   Tools/Technologies: GitHub Actions, pytest, flake8/ruff (optional)
    -   Expected Output: CI workflow that runs tests and lints on PRs.

**Sprint Progress:** 1/4 tasks completed (25%)

---

## 📈 Overall Progress

**Total Tasks:** 15
**Completed:** 1
**Overall Progress:** 7%

---

## Next steps

1. Create issues for each top-level task and assign owners & estimates in your issue tracker.
2. Convert the sprint items into smaller tickets and start with authentication + CI.
3. Add migrations (Alembic) before making schema changes (e.g., adding Porter.role/password_hash).

Document version: 2025-10-19

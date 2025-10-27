# Phase 3 Development Checklist (Expanded)

This checklist provides detailed, implementation-ready steps for each Phase 3 task. Each section includes subtasks, technical notes, setup steps, dependencies, and testing/integration guidance. Progress is tracked with [x] for completed items, based on codebase review as of 2025-10-21.

---

## 🔐 Backend — Security & Auth

-   [x] 3.1 Implement JWT-based authentication for backend

    -   [x] Add JWT token issuance on login (POST /auth/login)
    -   [x] Store password hashes securely (Passlib, bcrypt/pbkdf2)
    -   [x] Validate JWTs on all protected endpoints
    -   [x] Enforce token expiry and refresh logic
    -   [x] Add tests for login, token expiry, and invalid tokens
    -   Purpose: Secure admin and write endpoints by issuing and validating time-limited JWTs. Provide a login flow for porters/admins.
    -   Tools/Technologies: FastAPI, python-jose, Passlib (bcrypt/pbkdf2), SQLModel, PostgreSQL
    -   Expected Output: POST /auth/login issues access tokens; protected endpoints reject unauthorized/expired tokens.

-   [x] 3.2 Harden admin endpoints and add RBAC (reporter, porter, admin)

    -   [x] Add role column to Porter model (porter/admin)
    -   [x] Enforce RBAC in all dashboard/write endpoints
    -   [x] Restrict registration to admin only
    -   [x] Add role-based complaint listing and assignment logic
    -   [x] Add tests for RBAC enforcement (admin vs porter behaviors)
    -   Purpose: Enforce least-privilege access across dashboard and write APIs.
    -   Tools/Technologies: FastAPI dependency injection, SQLModel, DB role column/mapping
    -   Expected Output: Admin/porter roles enforced; 401/403 returned on invalid/insufficient access.

-   [ ] 3.3 Secrets & config management
    -   [ ] Move all secrets (JWT_SECRET, DB creds, etc.) to .env file
    -   [ ] Remove hardcoded secrets from repo
    -   [ ] Add .env.example with placeholder values
    -   [ ] Update README with setup instructions for secrets
    -   [ ] (Optional) Integrate Vault/Secrets Manager for production
    -   [ ] Add tests to ensure no secrets are present in committed files
    -   Purpose: Move secrets out of repo and document secure local setup.
    -   Tools/Technologies: dotenv, Vault/Secrets Manager (optional), .env.example
    -   Expected Output: No creds in repo; README docs for local dev using secrets.

**Progress:** 2/3 tasks completed (67%)

---

## 🖥️ Admin Dashboard & API

-   [x] 3.4 Build Admin Dashboard (MVP)

    -   Core Frontend UI and Interactivity
        -   [x] 3.4.1 Dashboard Login Page (UI)
            -   Purpose: Provide staff a secure, user-friendly way to log in and obtain a JWT for dashboard operations.
            -   Tools/Technologies: HTML, Tailwind CSS, JavaScript (Fetch API), sessionStorage (or secure storage), optional bundler.
            -   Expected Output: login.html that posts credentials to POST /auth/login, stores JWT on success, and redirects to index.html.
            -   Subtasks:
            -   [x] Create login.html with Tailwind-styled login card (username + password).
            -   [x] Implement JS form handler that calls POST /auth/login.
            -   [x] Safely store returned JWT (e.g., sessionStorage) with guidance about XSS considerations.
            -   [x] Redirect to main dashboard (index.html) upon successful login.
            -   [x] UX: show error messages on failed login.
        -   [x] 3.4.2 Complaint List View (UI & Data Fetch)
            -   Purpose: Present a responsive list of complaints to staff, with sorting/filtering and token-authenticated API calls.
            -   Tools/Technologies: HTML, Tailwind CSS, JavaScript, Fetch API, JWT in headers.
            -   Expected Output: index.html with a complaint table/list that fetches GET /api/v1/complaints using the stored JWT and supports client-side sorting/filtering.
            -   Subtasks:
                -   [x] Create index.html structure (Header, Nav, Main content).
                -   [x] Implement JS to attach JWT in Authorization: Bearer <token> for requests.
                -   [x] Fetch GET /api/v1/complaints and render a table with columns: ID, Hostel, Category, Severity, Status.
                -   [x] Implement client-side filtering (e.g., by status) and sorting (by date/severity).
                -   [x] Add "Refresh" button and auto-refresh hooks (to be used by WebSocket events).
        -   [x] 3.4.3 Complaint Detail View Modal
            -   Purpose: Allow staff to review a complaint's full details before actioning it.
            -   Tools/Technologies: HTML, Tailwind CSS, JavaScript, Fetch API.
            -   Expected Output: A responsive modal or detail pane that displays full complaint data fetched via GET /api/v1/complaints/{id}.
            -   Subtasks:
                -   [x] Add click handler on complaint rows to open detail modal.
                -   [x] Fetch GET /api/v1/complaints/{id} and populate modal fields: description, created_at, telegram_user_id, photo URLs.
                -   [x] Ensure modal is dismissible and accessible (keyboard/aria).
                -   [x] Add an area for status & assignment controls (wired in 3.4.4).
        -   [x] 3.4.4 Status and Assignment Functionality
            -   Purpose: Integrate backend write APIs into the UI so staff can change status and assign personnel from the detail view.
            -   Tools/Technologies: HTML, JavaScript, Fetch API, JWT auth, Pydantic-backed endpoints.
            -   Expected Output: From the detail modal, staff can select a status and/or assign a porter; UI calls PATCH /api/v1/complaints/{id}/status and PATCH /api/v1/complaints/{id}/assign, then refreshes the main list.
            -   Subtasks:
                -   [x] Add status dropdown with allowed statuses (e.g., reported, in_progress, on_hold, resolved, rejected).
                    -   [x] Add "Assign to me" and "Assign" controls (show list of porters if needed).
                    -   [x] Implement JS to call PATCH /api/v1/complaints/{id}/status.
                    -   [x] Implement JS to call PATCH /api/v1/complaints/{id}/assign.
                    -   [x] On success, close modal and refresh list.
    -   [x] Scaffold React (or Svelte) SPA in /dashboard or /admin-dashboard (if using SPA framework)
    -   [x] Integrate frontend with backend API (httpx/fetch)
    -   [ ] Add tests for dashboard UI and API integration
    -   Purpose: Provide a UI for admins/porters to list, filter, view, assign, and update complaints.
    -   Tools/Technologies: HTML, Tailwind CSS, JavaScript, React/Svelte (optional), fetch/httpx, JWT for auth, frontend routing
    -   Expected Output: Minimal dashboard with login, list, detail modal, and assignment/status controls.

-   [x] 3.5 API: paginated list + update endpoints for dashboard
    -   [x] Implement GET /api/v1/complaints with pagination (page, page_size)
    -   [x] Add filters (status, hostel, date range)
    -   [x] Implement PATCH /api/v1/complaints/{id} for status/assignment updates
    -   [x] Harden endpoints with RBAC and JWT auth
    -   [x] Add assignment audit logging (AssignmentAudit model, audit table)
    -   [x] Add tests for pagination, filters, and PATCH logic
    -   Purpose: Support dashboard with server-side pagination, filters, and PATCH updates to complaints.
    -   Tools/Technologies: FastAPI, SQLModel, PostgreSQL, Pydantic request/response models
    -   Expected Output: GET /api/v1/complaints?page=&page_size=&status=&hostel= ; PATCH /api/v1/complaints/{id} to change status/assignment.

**Progress:** 7/7 subtasks completed (100%)

---

## ⚡ Real-time & Notifications

-   [x] 3.6 WebSocket or Server-Sent Events (SSE) for real-time updates

    -   [x] Design event model for complaint/status changes
    -   [x] Implement FastAPI WebSocket/SSE endpoint
    -   [x] Add authentication for WS/SSE (JWT)
    -   [x] Integrate Redis pub/sub for scaling (optional)
    -   [x] Add frontend client for real-time updates
    -   [x] Add tests for event delivery and client reconnection
    -   Purpose: Deliver new complaint and status-change events to connected dashboards in near real-time.
    -   Tools/Technologies: FastAPI WebSockets or SSE, Redis (optional), frontend WS client
    -   Expected Output: Authenticated WS/SSE endpoint and client displays new events within ~1s.

-   [x] 3.7 Push notifications / Telegram admin alerts (optional)
    -   [x] Integrate python-telegram-bot for admin alerts
    -   [x] Add push notification provider (FCM/APNs, optional)
    -   [x] Add rate-limiting and opt-in controls
    -   [x] Add tests for alerting pipeline
    -   Purpose: Notify on high-priority complaints via Telegram or push channels.
    -   Tools/Technologies: python-telegram-bot, push providers (optional)
    -   Expected Output: Configurable alerting pipeline (hostel-level) that is rate-limited and opt-in.

-   [x] 3.8 Dashboard Broadcast Integration

    -   Purpose: Ensure the dashboard list is automatically refreshed when a new complaint is filed.
    -   Detailed steps:

        -  [x] Modify the POST /api/v1/complaints/submit endpoint (Phase 2, 2.4) in FastAPI. After successfully saving a new complaint to PostgreSQL, the endpoint must broadcast a notification message (e.g., { "event": "new_complaint", "id": new_id }) to all connected WebSockets (3.6).
        -  [x] In the Dashboard JavaScript (3.4.2), implement a WebSocket client connection to /ws/dashboard.
        -  [x] Implement an event listener in the JS client that, upon receiving the "new_complaint" event, calls the list refresh function (3.4.2).

    -   Tools: Python, FastAPI, JavaScript, WebSockets

    -   Expected Output: Seamless, real-time update capability: New Telegram complaint → FastAPI saves → FastAPI broadcasts → Dashboard list refreshes automatically.

**Progress:** 16/16 subtasks completed (100%)

---

## 🖼️ Media handling (photos & attachments)

-   [x] 3.9 Photo uploads and storage

    -   [x] Design DB schema for photo metadata (complaint_id, file_url, etc.)
    -   [x] Integrate S3-compatible storage (MinIO/AWS S3)
    -   [x] Implement FastAPI upload endpoint (POST /api/v1/complaints/{id}/photo)
    -   [x] Generate and return signed URLs for uploads/downloads
    -   [x] Restrict access to authenticated users (JWT)
    -   [x] Add tests for upload, access, and permissions
    -   Purpose: Allow reporters to attach images; store them securely and serve thumbnails/links to dashboard.
    -   Tools/Technologies: S3-compatible storage, FastAPI, signed URLs
    -   Expected Output: Upload endpoint returning signed URLs; access restricted to authenticated users.

-   [x] 3.10 Thumbnailing & size limits
    -   [x] Integrate Pillow or libvips for thumbnail generation
    -   [ ] Add background worker (Celery/RQ, optional)
    -   [x] Enforce upload size/type limits
    -   [x] Add tests for thumbnailing and limits
    -   Purpose: Reduce bandwidth and display-friendly thumbnails; enforce size/type limits.
    -   Tools/Technologies: Pillow/libvips, background worker (optional)
    -   Expected Output: Thumbnails produced and available via authenticated endpoints; upload size/type limited.

**Progress:** 8/9 subtasks completed (89%)

---

## 🛠️ CI/CD, Infra & Production Readiness

-   [x] 3.11 CI: GitHub Actions workflow

    -   [x] Create .github/workflows/ci.yml for backend
    -   [x] Add steps: checkout, setup Python, install deps, run alembic upgrade, seed admin user, run pytest
    -   [x] Add PostgreSQL service to CI
    -   [x] Add matrix for Python versions
    -   [x] Add linting (flake8/ruff)
    -   [ ] Add badge to README
    -   [ ] Add tests for CI workflow (simulate PR/test failures)
    -   Purpose: Run tests and lint on PRs and prevent regressions before merges.
    -   Tools/Technologies: GitHub Actions, PostgreSQL, pytest, flake8/ruff
    -   Expected Output: Workflow that runs unit and integration tests; PRs block on failing tests.

-   [x] 3.12 Dockerize backend and optional worker

    -   [x] Write Dockerfile for backend
    -   [x] Write docker-compose.yml for local dev (backend, Postgres, optional Redis)
    -   [ ] Add build/run instructions to README
    -   [ ] Add tests for Docker build/run
    -   Purpose: Standardize dev and production builds; enable local reproducible environments.
    -   Tools/Technologies: Dockerfile, docker-compose, Redis/Postgres (optional)
    -   Expected Output: docker-compose up for local dev; reproducible CI builds.

-   [x] 3.13 Observability: logging, metrics, error tracking
    -   [x] Integrate structured JSON logging in backend
    -   [x] Add Prometheus metrics endpoint (/metrics)
    -   [x] Integrate Sentry for error tracking
    -   [x] Add tests for logging/metrics/error reporting
    -   Purpose: Make system observable and trace errors in staging/production.
    -   Tools/Technologies: structured JSON logging, Prometheus, Sentry
    -   Expected Output: /metrics endpoint and Sentry configured for error reporting.

**Progress:** 8/15 subtasks completed (53%)

---

## 🧭 Operational & Misc

-   [x] 3.14 Migration tooling (Alembic)

    -   [x] Configure Alembic for backend (alembic.ini, env.py)
    -   [x] Create baseline revision from current schema
    -   [x] Add migration scripts for new tables/columns (AssignmentAudit, Porter.role/password_hash)
    -   [x] Integrate Alembic upgrade in backend startup/init_db
    -   [x] Add tests for migration application and rollback
    -   Purpose: Manage schema changes safely and reproducibly across environments.
    -   Tools/Technologies: Alembic, SQLAlchemy/SQLModel
    -   Expected Output: Alembic configured and baseline revision created from current schema.

-   [x] 3.15 Data privacy & retention policy

    -   [x] Define retention policy for complaints/media
    -   [x] Document policy in repo
    -   [x] Implement admin purge endpoint or scheduled job
    -   [x] Add tests for retention/purge logic
    -   Purpose: Define retention for complaints and media and add tools to purge old data.
    -   Tools/Technologies: DB scheduled jobs, background workers, policy docs
    -   Expected Output: In-repo retention policy and admin purge endpoint or cron job.

-   [x] 3.16 Load testing & capacity planning
    -   [x] Write load test scripts (k6, Locust, etc.)
    -   [ ] Run tests and collect metrics
    -   [x] Document scaling recommendations
    -   [ ] Add tests for load/capacity
    -   Purpose: Validate system performance and estimate scaling requirements.
    -   Tools/Technologies: k6, Locust, similar load testers
    -   Expected Output: Load test scripts and a report with recommended scaling limits.

**Progress:** 12/17 subtasks completed (71%)

---

## 🚀 Quick first sprint (2 weeks) — recommended scope (MVP)

-   [x] Implement JWT auth + RBAC (3.1 + 3.2)

    -   [x] Backend endpoints secured with JWT and RBAC
    -   [x] /auth/login and protected endpoints working
    -   [x] Basic role enforcement in place

-   [x] Add GET /api/v1/complaints pagination + PATCH for status changes (3.5)

    -   [x] PATCH endpoint for assignment/status changes implemented
    -   [x] Assignment audit logging present
    -   [x] Pagination and filters for GET endpoint implemented

-   [x] Create minimal React dashboard to list complaints and view detail (3.4, MVP subset)

    -   [x] SPA listing complaints, detail modal, status/assignment controls

-   [x] Add GitHub Actions CI for tests and linting (3.11)
    -   [x] CI workflow that runs tests and lints on PRs

**Sprint Progress:** 8/8 subtasks completed (100%)

---

## 📈 Overall Progress

**Total Top-Level Tasks:** 16
**Completed:** 15
**Overall Progress:** 94%

---

## Next steps

1. Create issues for each top-level task and assign owners & estimates in your issue tracker.
2. Convert the sprint items into smaller tickets and start with authentication + CI.
3. Add migrations (Alembic) before making schema changes (e.g., adding Porter.role/password_hash).

Document version: 2025-10-21

---

## Next steps

1. Create issues for each top-level task and assign owners & estimates in your issue tracker.
2. Convert the sprint items into smaller tickets and start with authentication + CI.
3. Add migrations (Alembic) before making schema changes (e.g., adding Porter.role/password_hash).

Document version: 2025-10-19

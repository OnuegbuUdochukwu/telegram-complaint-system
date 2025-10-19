# Phase 3 Checklist — Telegram Complaint System

This checklist contains prioritized work for Phase 3: security, admin UX, real-time updates, media handling, CI, and production readiness. Each item includes a short description, acceptance criteria, rough estimate, and suggested owner (if known). Use this as a living document while implementing Phase 3.

---

## How to use this file

-   Mark each item as TODO / IN-PROGRESS / DONE.
-   Add a short status line and a GitHub issue/PR link when you start work.
-   Estimates are rough; refine during sprint planning.

---

## Priority 1 — Security & Auth (must-have)

-   [ ] 3.1 Implement JWT-based authentication for backend

    -   Description: Add login endpoint, issue JWT access tokens (and refresh tokens optionally). Secure write endpoints (submit, update status, assign porter) and admin endpoints with role-based checks.
    -   Acceptance criteria:
        -   POST /auth/login returns access token for valid credentials
        -   Protected endpoints return 401 without token and 403 for insufficient role
        -   Tokens expire; refresh flow implemented or documented
    -   Rough estimate: 8–16 hours
    -   Owner: backend

-   [ ] 3.2 Harden admin endpoints and add RBAC

    -   Description: Implement roles (reporter, admin, porter). Ensure list, update, and assignment endpoints require admin or porter roles.
    -   Acceptance criteria:
        -   Admin can list and filter complaints, assign porter, change status
        -   Porter can see assigned complaints and change status to in-progress/resolved
    -   Rough estimate: 4–8 hours
    -   Owner: backend

-   [ ] 3.3 Secrets & config management
    -   Description: Move secrets out of .env into platform-appropriate secret store (or document vault usage). Add sample env and .env.example.
    -   Acceptance criteria:
        -   No credentials in repo
        -   README documents how to configure secrets locally
    -   Rough estimate: 2–4 hours
    -   Owner: devops/backend

---

## Priority 2 — Admin Dashboard (UX)

-   [ ] 3.4 Build Admin Dashboard (React or Svelte)

    -   Description: Create a single-page admin UI to list complaints with filters (status, hostel, date), view details, assign porter, change status, and upload notes/media (if implemented).
    -   Acceptance criteria:
        -   Dashboard authenticates via JWT
        -   Lists complaints with server-side pagination and filters
        -   Complaint detail view allows status/assignment changes
    -   Rough estimate: 40–80 hours (MVP)
    -   Owner: frontend

-   [ ] 3.5 API: list + update endpoints for dashboard
    -   Description: Implement paginated GET /api/v1/complaints with query params (status, hostel, assigned_to, page, page_size) and PATCH /api/v1/complaints/{id} for updates.
    -   Acceptance criteria:
        -   Endpoints respect RBAC and pagination
        -   PATCH validates allowed transitions (e.g., can't move from resolved to new without audit)
    -   Rough estimate: 8–16 hours
    -   Owner: backend

---

## Priority 3 — Real-time & Notifications

-   [ ] 3.6 WebSocket or server-sent events for real-time updates

    -   Description: Add a WebSocket endpoint that broadcasts new complaints and status updates to connected dashboard clients.
    -   Acceptance criteria:
        -   Dashboard receives new complaint events in <1s
        -   Authenticated connections only
    -   Rough estimate: 8–16 hours
    -   Owner: backend/frontend

-   [ ] 3.7 Push notifications / Telegram admin alerts (optional)
    -   Description: Send optional Telegram messages to admin chat or push notifications to mobile web when new high-priority complaints appear.
    -   Acceptance criteria:
        -   Configurable per-hostel or global
        -   Rate-limited and opt-in
    -   Rough estimate: 6–12 hours
    -   Owner: backend

---

## Priority 4 — Media handling (photos / attachments)

-   [ ] 3.8 Photo uploads and storage

    -   Description: Allow reporters to attach photos from Telegram. Decide on storage backend: S3-compatible (recommended), local disk (dev), or DB (not recommended).
    -   Acceptance criteria:
        -   Upload endpoint returns secure URL or signed URL
        -   Uploaded media accessible only to authenticated dashboard/admin clients
    -   Rough estimate: 8–20 hours (including storage & signed URLs)
    -   Owner: backend/devops

-   [ ] 3.9 Thumbnailing & size limits
    -   Description: Generate thumbnails on upload (or on-demand). Enforce size limits and file type checks.
    -   Acceptance criteria:
        -   Images larger than configured size are rejected or downscaled
        -   Thumbnails available via authenticated endpoint
    -   Rough estimate: 4–8 hours
    -   Owner: backend

---

## Priority 5 — CI/CD, infra, and production hardening

-   [ ] 3.10 CI: GitHub Actions workflow

    -   Description: Add CI to run lint, unit tests, and integration tests against a test PostgreSQL service on PRs.
    -   Acceptance criteria:
        -   PRs run tests and fail on regression
        -   Builds run in matrix (python versions optionally)
    -   Rough estimate: 6–12 hours
    -   Owner: devops

-   [ ] 3.11 Dockerize backend and optional worker

    -   Description: Add Dockerfile(s) for backend and a docker-compose for local dev (Postgres, backend, redis if needed). Add production-ready Dockerfile with environment variable configuration.
    -   Acceptance criteria:
        -   docker-compose up boots a working dev environment
        -   Images can be built reproducibly in CI
    -   Rough estimate: 6–12 hours
    -   Owner: devops

-   [ ] 3.12 Observability: logging, metrics, error tracking
    -   Description: Add structured logging, health checks, Prometheus metrics endpoint (or use FastAPI middleware integrations), and Sentry (optional) for exceptions.
    -   Acceptance criteria:
        -   Metrics endpoint available and basic dashboards documented
        -   Errors captured in Sentry in staging (optional)
    -   Rough estimate: 6–12 hours
    -   Owner: backend/devops

---

## Priority 6 — Operational & Misc

-   [ ] 3.13 Migration tooling (Alembic)

    -   Description: Integrate Alembic or a migration runner and convert existing SQL files into versioned migrations.
    -   Acceptance criteria:
        -   Alembic configured
        -   Existing schema represented as baseline revision
    -   Rough estimate: 4–8 hours
    -   Owner: backend

-   [ ] 3.14 Data privacy & retention policy

    -   Description: Document how long complaints and media are retained and add tools to purge old data.
    -   Acceptance criteria:
        -   Written policy in repo
        -   Admin endpoint to run purge job (or scheduled job)
    -   Rough estimate: 2–4 hours
    -   Owner: product/security

-   [ ] 3.15 Load testing & capacity planning
    -   Description: Run lightweight load tests (k6 or Locust) to validate system under expected traffic and estimate scaling needs.
    -   Acceptance criteria:
        -   Load test scripts checked in
        -   Test report with recommendations
    -   Rough estimate: 8–16 hours
    -   Owner: devops

---

## Quick first sprint (2 weeks) — recommended scope

Pick a subset to land a secure MVP for admins to manage complaints.

Sprint goal: Secure the backend, add RBAC and basic dashboard list/detail features, and run CI.

-   [ ] Implement JWT auth + RBAC (3.1 + 3.2)
-   [ ] Add GET /api/v1/complaints pagination + PATCH for status changes (3.5)
-   [ ] Create minimal React dashboard to list complaints and view detail (3.4, MVP subset)
-   [ ] Add GitHub Actions CI for tests and linting (3.10)

---

## Next steps (after creating this file)

1. Create issues and assign owners for each checked item above.
2. Break sprint goals into smaller tasks and estimate in story points.
3. Start with authentication and CI; they unblock safe development for the rest of Phase 3.

---

Document version: 2025-10-19

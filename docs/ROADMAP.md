# Roadmap

## Current Project State

The project is in a late implementation stage with core product workflows working:

- Telegram bot complaint submission and status tracking are implemented.
- FastAPI backend supports auth, RBAC, complaint management, assignment, realtime websocket updates, media upload flow, and metrics.
- Dashboard provides login, filtering, detail inspection, and update actions.
- Infrastructure and deployment assets exist (`docker-compose`, Terraform, IAM docs, migration tooling).

## Feature Completion Matrix

### Completed

- Complaint capture flow from Telegram bot to backend.
- Backend CRUD and dashboard APIs.
- JWT auth + role checks for protected actions.
- Complaint assignment and audit trails.
- Realtime dashboard updates.
- Media storage pipeline with S3-compatible support.
- Basic observability (`/health`, `/metrics`, structured logs, Sentry hooks).

### Partially Implemented / Inconsistent

- Cross-layer enum alignment (status/severity options not perfectly unified across docs/UI/backend history).
- Some checklist documents are stale relative to actual implementation.
- Production hardening tasks (secrets validation, CI coverage breadth, runbook completion) are incomplete.

### Missing / Remaining

- Formal UAT execution and documentation closure.
- Additional integration tests for full dashboard/API workflows.
- Consolidated security hardening and operational playbooks.

## Prioritized Milestones

### Phase 1: Stabilization and Consistency

1. Unify status/severity/category constants across bot, backend, and dashboard.
2. Remove remaining dead scripts/docs and centralize operational scripts under `scripts/`.
3. Consolidate environment documentation and eliminate conflicting startup instructions.

### Phase 2: Quality and Verification

1. Expand automated integration tests for dashboard + API + websocket flows.
2. Add smoke tests for compose startup and production config linting.
3. Split CI pipelines into fast checks (lint/unit) and slower integration suites.

### Phase 3: Security and Operations

1. Finalize secrets management policy and enforce non-secret examples only.
2. Add security-focused tests for auth edge cases and rate limiting.
3. Complete production runbook (incident response, key/token rotation, recovery).

### Phase 4: Release Readiness

1. Execute UAT with a defined pilot checklist and capture outcomes.
2. Resolve UAT findings and re-run regression tests.
3. Tag a release candidate with deployment checklist sign-off.

## Technical Debt and Refactoring Backlog

- Break down large backend modules (`fastapi-backend/app/main.py`) into smaller domain routers/services.
- Remove historical/duplicated phase-planning content from active docs path.
- Standardize script naming and ownership (`scripts/` conventions + usage docs).
- Keep runtime artifacts out of git permanently (logs, local DBs, generated storage content).

## Execution Notes

- Preserve existing behavior while refactoring; prefer additive migrations and compatibility wrappers.
- Run tests after each major cleanup batch.
- Track each milestone as small, independently shippable PRs.

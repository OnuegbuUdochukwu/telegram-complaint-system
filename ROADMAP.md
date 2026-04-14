# Project Roadmap

## Current State

The project is in an advanced implementation stage with core functionality already delivered:

- Telegram bot complaint intake flow is implemented and connected to backend APIs.
- FastAPI backend provides authentication, RBAC, complaint lifecycle endpoints, realtime updates, media support, and observability basics.
- Dashboard supports login, complaint listing/filtering, detail views, and update actions.
- Infrastructure assets exist for local compose and cloud provisioning (`infra/`).
- Repository structure has been cleaned and reorganized (`src/`, `docs/`, `archive/`, `scripts/`).

## What Remains for Full Completion

### Product/Feature Completion

- Close remaining user acceptance and release-readiness gaps.
- Harden and validate full end-to-end flows under production-like conditions.
- Finalize documentation consistency and operational runbooks.

### Engineering/Quality Completion

- Expand integration and regression test coverage.
- Complete security hardening tasks and verification checks.
- Reduce backend module complexity (especially large monolithic files).

## Prioritized Implementation Order

1. **Stability and correctness first** (alignment, test reliability, regressions).
2. **Security and operations hardening** (secrets, abuse protection, runbooks).
3. **Refactoring and maintainability** (module decomposition, naming consistency).
4. **Release preparation and UAT closure** (pilot validation, go-live checklist).

## Technical Debt and Refactoring Backlog

- Decompose `fastapi-backend/app/main.py` into domain routers/services.
- Standardize enums/constants across bot, backend, and dashboard (status/severity/category alignment).
- Continue documentation normalization (naming, cross-links, stale references).
- Keep runtime artifacts permanently out of version control and enforce via CI checks.
- Separate and validate runtime vs dev/test dependency boundaries.

## Milestone Plan (Actionable Phases)

## Phase 1: Stabilization and Consistency

### Goals
- Ensure all layers agree on data contracts and core workflows remain stable.

### Tasks
- Audit and align shared enums/constants across bot/backend/dashboard.
- Run full regression pass for complaint submission, status updates, assignment, and photo flows.
- Resolve doc-command mismatches and outdated references.
- Add quick CI checks for broken links and import/path regressions.

### Exit Criteria
- No enum mismatch between API and UI/bot.
- Core happy-path and edge-path flows pass locally and in CI.

## Phase 2: Testing and Quality Hardening

### Goals
- Raise confidence with broader automated coverage.

### Tasks
- Add integration tests for dashboard-authenticated API flows.
- Add websocket/realtime reliability tests (disconnect/reconnect/replay scenarios).
- Add smoke tests for compose stack startup and health endpoints.
- Track and reduce flaky tests.

### Exit Criteria
- Stable CI with reliable test suites and clear failure diagnostics.

## Phase 3: Security and Operational Readiness

### Goals
- Prepare for production-grade reliability and incident response.

### Tasks
- Finalize secrets policy (local `.env` vs production secrets manager).
- Validate rate limiting, auth edge cases, and role boundary protections.
- Complete operational runbook (on-call checks, rollback, token/key rotation).
- Add alerts/monitoring expectations to docs.

### Exit Criteria
- Security checklist completed and reproducible operational procedures documented.

## Phase 4: Refactoring and Maintainability

### Goals
- Reduce maintenance cost and improve developer velocity.

### Tasks
- Split backend monolith into routers/services/modules by domain.
- Refactor duplicated logic in bot and backend helpers.
- Keep docs segmented into active vs archive with stable index pages.
- Enforce naming conventions for new files and scripts.

### Exit Criteria
- Cleaner module boundaries and reduced cognitive load for contributors.

## Phase 5: UAT and Release Completion

### Goals
- Validate with real user workflows and prepare final rollout.

### Tasks
- Execute UAT scenarios using a structured checklist.
- Triage and resolve pilot feedback by severity.
- Run final regression suite after fixes.
- Publish release candidate notes and deployment checklist.

### Exit Criteria
- UAT sign-off, regression pass, and release checklist complete.

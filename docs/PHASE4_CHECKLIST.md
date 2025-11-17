# Phase 4 Development Checklist

This checklist converts the Phase 4 plan (Testing, Refinement, UAT) into a structured, progress-trackable Markdown file. Use this to track status, responsibilities, and outcomes for Phase 4 work.

---

## ⚙️ Task Set 1 — Automated Testing and Code Coverage (4.1)

Purpose: Establish automated tests and coverage for the backend to ensure logic correctness and data integrity.

### 4.1.1 — Pytest Setup and Test Database Configuration

[ ] Install Pytest and plugins (pytest, pytest-asyncio)

-   Purpose: Provide the test runner and async support for tests
-   Tools/Technologies: Python, pytest, pytest-asyncio, pip
-   Expected Output: Packages installed and available in project virtualenv

[ ] Configure dedicated test database URL (separate Postgres schema or in-memory SQLite)

-   Purpose: Run tests against an isolated DB so production/dev DBs are not affected
-   Tools/Technologies: PostgreSQL or SQLite, environment variables
-   Expected Output: `DATABASE_URL_TEST` (or similar) defined and usable by tests

[ ] Write core fixtures in `conftest.py` for session setup/teardown

-   Purpose: Ensure each test runs with a clean DB state and deterministic transactions
-   Tools/Technologies: pytest, sqlmodel/SQLAlchemy, FastAPI test utilities
-   Expected Output: `conftest.py` with fixtures that create/drop or roll back DB state for each test

Progress: 0/3 tasks completed (0%)

### 4.1.2 — Unit Tests: ORM/Model Logic (CRUD & Validation)

[ ] Create tests for create/read/update/delete across Complaint, Porter, Hostel models

-   Purpose: Validate ORM mappings and CRUD behavior
-   Tools/Technologies: Pytest, SQLModel, test DB fixture from 4.1.1
-   Expected Output: `tests/test_models.py` with CRUD tests

[ ] Test constraints and validation (required fields, enums, value ranges)

-   Purpose: Ensure the data layer enforces schema constraints and validation rules
-   Tools/Technologies: Pytest, SQLModel, Pydantic validation
-   Expected Output: Tests that assert correct exceptions / DB errors for invalid input

[ ] Test Pydantic schema validation on model instantiation (types and required fields)

-   Purpose: Prevent invalid data from being constructed and persisted
-   Tools/Technologies: Pydantic/SQLModel, pytest
-   Expected Output: Tests asserting `ValidationError` or similar for bad payloads

Progress: 0/3 tasks completed (0%)

### 4.1.3 — Unit Tests: API Endpoints (Core Functionality)

[ ] Test successful complaint submission (POST /api/v1/complaints/submit)

-   Purpose: Confirm API request/response contract and status codes (201)
-   Tools/Technologies: FastAPI TestClient, pytest, fixtures
-   Expected Output: `tests/test_api_submit.py` with assertions for 201 + payload structure

[ ] Test authentication failures and protected endpoints (e.g., PATCH /status requires JWT)

-   Purpose: Ensure RBAC/auth behavior is enforced at API layer
-   Tools/Technologies: TestClient, JWT token helpers, pytest
-   Expected Output: Tests asserting 401/403 responses for unauthorized access

[ ] Test input validation and 422 responses for malformed requests

-   Purpose: Ensure FastAPI input validation rejects bad input early
-   Tools/Technologies: TestClient, pytest
-   Expected Output: Tests asserting 422 status codes for invalid schemas

Progress: 0/3 tasks completed (0%)

---

## 🔗 Task Set 2 — Integration, Security, and E2E Testing (4.2)

Purpose: Test integrated system flows, security posture, and resilience to abuse.

### 4.2.1 — End-to-End (E2E) Test Case Documentation

[ ] Document the "Happy Path" and main E2E flows in a canonical format

-   Purpose: Provide repeatable end-to-end scenarios for manual or automated testing
-   Tools/Technologies: Markdown, test case templates
-   Expected Output: `docs/E2E_TESTS.md` with step-by-step scenarios (Happy Path)

[ ] Document edge cases and failure modes (timeouts, invalid inputs, concurrency)

-   Purpose: Ensure testers exercise negative and concurrent behaviors
-   Tools/Technologies: Markdown
-   Expected Output: Edge-case checklist appended to E2E document

[ ] Create a standardized tester checklist for each scenario

-   Purpose: Make test execution consistent across testers
-   Tools/Technologies: Markdown table or checklist
-   Expected Output: Checklist items for manual UAT runs

Progress: 0/3 tasks completed (0%)

### 4.2.2 — Security Audit: Authentication & Authorization

[ ] Test write endpoints with No token, Expired token, Valid token (correct role)

-   Purpose: Verify RBAC enforcement for all sensitive APIs
-   Tools/Technologies: Postman/Insomnia or automated pytest tests, JWT tooling
-   Expected Output: Test matrix and results showing 401/403 behavior where appropriate

[ ] Attempt cross-role access (Porter token calling Admin-only endpoints and vice versa)

-   Purpose: Ensure roles are enforced and cannot be escalated via API calls
-   Tools/Technologies: Test tooling, JWT helpers
-   Expected Output: Test failures for unauthorized role actions (403)

[ ] Verify token revocation and expiration handling

-   Purpose: Ensure expired or revoked tokens no longer provide access
-   Tools/Technologies: JWT expiry tests, token revocation workflow
-   Expected Output: Tests showing expired/revoked tokens produce 401 responses

Progress: 0/3 tasks completed (0%)

### 4.2.3 — Security Audit: Input Sanitization and Rate Limiting

[ ] Input sanitization checks (test XSS payloads via bot & API free-text fields)

-   Purpose: Confirm the system stores data safely and does not execute HTML/JS when rendered
-   Tools/Technologies: Browser DevTools, manual bot testing, pytest (optional)
-   Expected Output: Evidence that injected HTML/JS is rendered as plain text or safely escaped

[ ] Rate limiting / abuse testing for login and submit endpoints

-   Purpose: Confirm backend rejects excessive requests and prevents brute force/DoS
-   Tools/Technologies: Simple Python scripts, siege/locust, or shell loops
-   Expected Output: Observed 429 or deliberate throttling behavior once threshold is crossed

[ ] Create remediation notes for any sanitization or rate-limit gaps discovered

-   Purpose: Provide actionable fixes and prioritization for security issues
-   Tools/Technologies: Markdown, internal bug tracker
-   Expected Output: Security report with reproducible steps and suggested fixes

Progress: 0/3 tasks completed (0%)

---

## 🧪 Task Set 3 — User Acceptance and Refinement (4.3 / 4.4 / 4.5)

Purpose: Stage a UAT environment, gather pilot feedback, triage and implement refinements.

### 4.3.1 — UAT Staging Environment Setup

[ ] Provision a staging server or environment (cloud or dedicated host)

-   Purpose: Provide an isolated, production-like environment for pilot tests
-   Tools/Technologies: Docker, Nginx, cloud provider (DigitalOcean/AWS/GCP), CI/CD
-   Expected Output: Staging URL and credentials for pilot users

[ ] Deploy the full stack to staging (Telegram Bot, FastAPI, PostgreSQL, UI)

-   Purpose: Ensure the whole system can be deployed and exercised end-to-end
-   Tools/Technologies: Docker Compose or Kubernetes manifests, environment config
-   Expected Output: Deployed stack reachable at staging URL

[ ] Onboard pilot users with basic usage guide and credentials

-   Purpose: Ensure testers can access the system and run scenarios reliably
-   Tools/Technologies: Email/Docs, short usage guide (Markdown)
-   Expected Output: Pilot cohort onboarded and ready to test

Progress: 0/3 tasks completed (0%)

### 4.3.2 — UAT Execution and Feedback Logging

[ ] Execute E2E scenarios (from 4.2.1) with pilot users

-   Purpose: Validate real-world usage and collect usability/performance issues
-   Tools/Technologies: Pilot users, E2E checklist, logging
-   Expected Output: Logged test runs and issue reports

[ ] Provide a structured feedback form and issue categorization by severity

-   Purpose: Capture consistent feedback and prioritize fixes
-   Tools/Technologies: Google Forms, Markdown table, or internal tracker
-   Expected Output: Consolidated feedback report categorized by severity

[ ] Aggregate telemetry and performance metrics from the staging environment

-   Purpose: Quantify errors, latencies and resource usage during pilots
-   Tools/Technologies: Application logs, Prometheus/Grafana (optional), simple scripts
-   Expected Output: Telemetry summary and notable performance observations

Progress: 0/3 tasks completed (0%)

### 4.3.3 — Bug Prioritization and Resolution

[ ] Triage feedback and test failures; classify by severity (Critical/Major/Minor)

-   Purpose: Focus development on stability and security first
-   Tools/Technologies: Issue tracker, triage meeting notes
-   Expected Output: Prioritized bug list

[ ] Fix critical and major bugs, run unit/integration tests to validate fixes

-   Purpose: Ensure high-impact issues are resolved before wider rollout
-   Tools/Technologies: VS Code, Git, pytest, CI
-   Expected Output: Merged fixes and passing tests for critical items

[ ] Communicate fixes and retest with pilot users for verification

-   Purpose: Close the feedback loop and validate the fixes in staging
-   Tools/Technologies: Release notes, test reports
-   Expected Output: Verified fixes and updated feedback tracker

Progress: 0/3 tasks completed (0%)

### 4.3.4 — Feature Refinement Implementation (Usability)

[ ] Implement minor usability improvements from UAT feedback (clearer bot messages, dashboard defaults)

-   Purpose: Increase adoption and reduce user friction
-   Tools/Technologies: Python, FastAPI, HTML/JS, Tailwind CSS
-   Expected Output: UX improvements merged and deployed to staging

[ ] Rerun automated tests to ensure no regressions

-   Purpose: Prevent regressions as UI/UX changes are applied
-   Tools/Technologies: pytest, TestClient, CI
-   Expected Output: Green test runs after refinements

[ ] Prepare a short release note summarizing refinements for pilot users

-   Purpose: Inform pilot users of improvements and what changed
-   Tools/Technologies: Markdown, email/Slack
-   Expected Output: Release note posted to pilot channel

Progress: 0/3 tasks completed (0%)

---

## 📊 Overall Phase 4 Progress

-   Total Major Tasks: 10
    -   Task Set 1 (4.1): 3
    -   Task Set 2 (4.2): 3
    -   Task Set 3 (4.3): 4
-   Completed: 0
-   Overall Progress: 0/10 tasks completed (0%)

---

## 📌 Notes & Next Steps

-   Keep `.env` and secrets out of git; use CI/CD secrets or a secrets manager for staging/production.
-   Prioritize automated tests that cover security-sensitive code paths (auth, assignment, status transitions).
-   Consider adding lightweight integration tests that exercise the WebSocket manager and Telegram notifier in a mocked environment.

---

_File generated from the Phase 4 task breakdown provided by the project planning document._

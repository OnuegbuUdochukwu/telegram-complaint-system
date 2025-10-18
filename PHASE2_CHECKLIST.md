# Phase 2 Development Checklist

## 🗄️ Task Set 1: Data Persistence Layer (PostgreSQL)

-   [ ] 2.1.1 PostgreSQL Instance and Database Creation

    -   [ ] Install PostgreSQL server locally (or set up a Docker container).
    -   [ ] Create a dedicated superuser role for the application.
    -   [ ] Create the primary application database named `cms_db` (Complaint Management System Database).
    -   [ ] Verify connectivity using a database client (e.g., pgAdmin or `psql`).
    -   Purpose: Establish the relational database server instance required to store all application data persistently.
    -   Tools/Technologies: PostgreSQL, Docker (optional), `psql` command-line utility, pgAdmin.
    -   Expected Output: A running PostgreSQL instance with a verified `cms_db` available for connection.

-   [ ] 2.1.2 Initial Database Schema (DDL) Scripting
    -   [ ] Write DDL script for `hostels` table.
    -   [ ] Write DDL script for `porters` table (for future dashboard/auth).
    -   [ ] Write DDL script for `users` table (Telegram ID → internal ID mapping).
    -   [ ] Write DDL script for core `complaints` table (id PK, fields, NOT NULLs, constraints, enums).
    -   [ ] Execute all DDL scripts against `cms_db` and verify tables created.
    -   Purpose: Translate the Phase 1 Complaint Data Schema into executable PostgreSQL DDL to create required tables.
    -   Tools/Technologies: SQL, PostgreSQL, VS Code (or preferred editor), `psql`.
    -   Expected Output: Four fully structured tables (`hostels`, `porters`, `users`, `complaints`) created in `cms_db`.

**Progress:** 0/2 tasks completed (0%)

---

## 🚀 Task Set 2: Core FastAPI Backend Development

-   [ ] 2.2.1 FastAPI Project Initialization & Environment

    -   [ ] Create backend directory (e.g., `fastapi-backend`).
    -   [ ] Initialize Python virtual environment inside backend.
    -   [ ] Install core dependencies: `fastapi`, `uvicorn`, `python-dotenv[cli]`.
    -   [ ] Install DB dependencies: `sqlmodel`, `psycopg2-binary`.
    -   [ ] Create initial `app/main.py` and `.env` for database credentials.
    -   Purpose: Set up the backend service scaffold and required environment so the API can be developed and run.
    -   Tools/Technologies: Python, venv, pip, FastAPI, Uvicorn, python-dotenv, VS Code.
    -   Expected Output: A runnable FastAPI application scaffold that starts with Uvicorn (e.g., "Application startup complete").

-   [ ] 2.2.2 ORM / SQLModel Configuration and Models

    -   [ ] Define the PostgreSQL connection string in `.env` (e.g., `DATABASE_URL`).
    -   [ ] Implement `get_session()` using `sqlmodel` (session generator dependency that closes sessions).
    -   [ ] Define SQLModel classes for `complaints`, `hostels`, and `porters` with Pydantic validation.
    -   [ ] Add an initialization script that calls `SQLModel.metadata.create_all()` to create tables.
    -   Purpose: Provide ORM models and session management to interact safely with PostgreSQL.
    -   Tools/Technologies: FastAPI, SQLModel, Pydantic, PostgreSQL.
    -   Expected Output: `database.py` (or similar) with functional SQLModel definitions and a working `get_session` dependency.

-   [ ] 2.2.3 Complaint Submission API Endpoint

    -   [ ] Define input Pydantic schema `ComplaintCreate` matching the bot payload.
    -   [ ] Implement `POST /api/v1/complaints/submit` endpoint.
    -   [ ] Inside the endpoint: validate incoming data, set defaults (e.g., `status="reported"`, `created_at`), save the record, commit transaction.
    -   [ ] Return JSON containing the new complaint ID and HTTP status `201`.
    -   Purpose: Create the secure, internal endpoint for the Telegram bot to submit new complaint data.
    -   Tools/Technologies: FastAPI, SQLModel, Pydantic, PostgreSQL, Swagger UI for testing.
    -   Expected Output: Verified endpoint that accepts JSON, persists a complaint in PostgreSQL, and returns the new record ID.

-   [ ] 2.2.4 Dashboard Read API Endpoints
    -   [ ] Define output Pydantic schema `ComplaintRead` (ID, status, timestamps, non-sensitive fields).
    -   [ ] Implement `GET /api/v1/complaints` to fetch a list of complaints (support filtering e.g., unresolved).
    -   [ ] Implement `GET /api/v1/complaints/{id}` to fetch complaint details by ID.
    -   [ ] Add a placeholder/basic authentication guard (dependency) for these read endpoints (to be hardened in Phase 3).
    -   Purpose: Provide endpoints for administrative dashboard to fetch and display complaint data.
    -   Tools/Technologies: FastAPI, SQLModel, Pydantic.
    -   Expected Output: Two read endpoints tested and verified to return complaint data from the database.

**Progress:** 0/4 tasks completed (0%)

---

## 🤖 Task Set 3: Bot-to-API Integration

-   [ ] 2.3.1 Update Bot's API Client and Dependencies
    -   [ ] Install an asynchronous HTTP client in the bot environment: `httpx`.
    -   [ ] Replace `client.py` mock `submit_complaint(data)` with an actual `httpx.post()` to `POST /api/v1/complaints/submit`.
    -   [ ] Implement robust error handling: catch connection errors, handle 4xx/5xx responses.
    -   [ ] Add a retry mechanism with exponential backoff (e.g., up to 3 attempts) for transient failures.
    -   [ ] Update `get_complaint_status(id)` to call the FastAPI read endpoint via `httpx.get()`.
    -   Purpose: Replace mock I/O logic with real network calls so the bot stores complaints persistently via the backend.
    -   Tools/Technologies: Python, `httpx`, python-telegram-bot, FastAPI.
    -   Expected Output: Telegram bot successfully submits a complaint via HTTP to the FastAPI server, which saves it to PostgreSQL, and the bot confirms the real ID to the user.

**Progress:** 0/1 tasks completed (0%)

---

## 📊 Overall Progress Summary

**Total top-level tasks:** 7  
**Completed:** 0  
**Overall Progress:** 0%

If you'd like, I can:

-   Turn this Markdown into `PHASE2_CHECKLIST.md` in the repo and commit it.
-   Create starter files for the FastAPI project (`fastapi-backend/` scaffold) and sample SQL DDL files (templates) so you can begin Phase 2 quickly.
-   Make the tasks in this document linkable to issues or git branches for tracked progress.

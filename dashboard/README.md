# Admin Dashboard

Static admin dashboard for complaint triage and assignment.

## Main Files

- `login.html`: auth screen.
- `index.html`: complaints table, detail modal, status/assignment updates.
- `js/auth.js`: token/session helpers and authenticated fetch wrappers.
- `js/config.js`: API base URL config.

## Features

- JWT login flow and protected access.
- Complaint listing with filtering and pagination.
- Detail modal with update actions.
- Realtime refresh through websocket (`ws`/`wss` auto-selected).

## Access

- Backend-only mode (`uvicorn` on 8000):
  - `http://localhost:8000/dashboard/login.html`
- Root dev compose mode (backend mapped to 8001):
  - `http://localhost:8001/dashboard/login.html`

FastAPI backend scaffold for the Complaint Management System

Files created:

-   `app/main.py` - FastAPI application and minimal endpoints
-   `app/database.py` - SQLModel engine and session helper
-   `app/models.py` - SQLModel models for complaints, hostels, porters, users
-   `.env.example` - example environment variables

Run locally (from `fastapi-backend/`):

```bash
# create venv
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# copy .env.example -> .env and set DATABASE_URL
cp .env.example .env

# start server
uvicorn app.main:app --reload --port 8000
```

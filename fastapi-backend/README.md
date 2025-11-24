FastAPI backend scaffold for the Complaint Management System

Files created:

-   `app/main.py` - FastAPI application and minimal endpoints
-   `app/database.py` - SQLModel## 🔐 Environment Configuration

This application requires several environment variables to run securely.

1.  **Copy the example configuration:**
    ```bash
    cp env.example .env
    ```
2.  **Edit `.env` and set secure values:**
    *   `JWT_SECRET`: **CRITICAL**. Set this to a long, random string.
    *   `DATABASE_URL`: Your PostgreSQL connection string.
    *   `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather.

> [!IMPORTANT]
> The application will fail to start if `JWT_SECRET` is not set. Do not use default values in production.

## 🚀 Getting Started session helper
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

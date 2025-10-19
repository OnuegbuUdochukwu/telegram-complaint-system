from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials, OAuth2PasswordRequestForm
from fastapi import Body
from . import auth
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timezone
from sqlmodel import select


from .database import init_db, get_session
from .models import Complaint, Porter

app = FastAPI(title="Complaint Management API")

security = HTTPBasic()


@app.post("/auth/login", response_model=dict)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session=Depends(get_session)):
    # Validate credentials against porters table (email or phone as username)
    porter = auth.authenticate_porter(form_data.username, form_data.password, session)
    if not porter:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = auth.create_access_token(subject=porter.id, role="admin" if (porter.email and porter.email.endswith("@admin.local")) else "porter")
    return {"access_token": token, "token_type": "bearer"}


@app.post("/auth/register", response_model=dict)
def register_porter(full_name: str = Body(...), email: Optional[str] = Body(None), phone: Optional[str] = Body(None), password: str = Body(...), session=Depends(get_session)):
    # Dev-only helper: create a porter with hashed password
    from .auth import get_password_hash
    new = {
        "full_name": full_name,
        "email": email,
        "phone": phone,
        "password_hash": get_password_hash(password),
    }
    porter = Porter(**{k: v for k, v in new.items() if v is not None})
    session.add(porter)
    session.commit()
    session.refresh(porter)
    return {"id": porter.id, "email": porter.email, "phone": porter.phone}

app = FastAPI(title="Complaint Management API")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/complaints/submit", status_code=201)
def submit_complaint(payload: Complaint, session=Depends(get_session)):
    # Basic validation handled by SQLModel/Pydantic; store record
    session.add(payload)
    session.commit()
    session.refresh(payload)
    return {"complaint_id": payload.id}


@app.get("/api/v1/complaints/{complaint_id}")
def get_complaint(complaint_id: str, session=Depends(get_session)):
    # Complaint.id is stored as UUID in the DB. Guard against invalid
    # UUID text being used in the query which causes a DB-level DataError.
    import re

    uuid_like = re.compile(r'^[0-9a-fA-F-]{1,36}$')
    if not uuid_like.match(complaint_id):
        # Treat clearly invalid IDs as not found to avoid 500 internal errors.
        raise HTTPException(status_code=404, detail="Not found")

    statement = select(Complaint).where(Complaint.id == complaint_id)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result


@app.get("/api/v1/complaints", response_model=List[Complaint])
def list_complaints(status: Optional[str] = None, admin_user: Porter = Depends(auth.require_role("admin")), session=Depends(get_session)):
    # Optional filter by status (e.g., reported, in_progress, resolved)
    statement = select(Complaint)
    if status:
        statement = statement.where(Complaint.status == status)
    results = session.exec(statement).all()
    return results


class StatusUpdateSchema(BaseModel):
    status: str


@app.patch("/api/v1/complaints/{complaint_id}/status", response_model=Complaint)
def update_complaint_status(
    complaint_id: str,
    body: StatusUpdateSchema,
    user: Porter = Depends(auth.get_current_user),
    session=Depends(get_session),
):
    """Secure endpoint to update a complaint's status.

    Requires authentication (porter or admin). Validates the status value,
    updates `status` and `updated_at` (timezone-aware), then returns the record.
    """
    # Guard against invalid-looking IDs (avoid DB DataError)
    import re

    uuid_like = re.compile(r'^[0-9a-fA-F-]{1,36}$')
    if not uuid_like.match(complaint_id):
        raise HTTPException(status_code=404, detail="Not found")

    # Fetch complaint
    statement = select(Complaint).where(Complaint.id == complaint_id)
    complaint = session.exec(statement).first()
    if not complaint:
        raise HTTPException(status_code=404, detail="Not found")

    # Validate status value
    allowed_statuses = {"reported", "in_progress", "resolved", "closed"}
    if body.status not in allowed_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Allowed: {', '.join(sorted(allowed_statuses))}")

    # Authorization: allow porter or admin (auth.get_current_user already ensures valid token)
    # If role-level checks are needed (e.g., only admin can set 'closed'), enforce here.

    complaint.status = body.status
    complaint.updated_at = datetime.now(timezone.utc)
    session.add(complaint)
    session.commit()
    session.refresh(complaint)
    return complaint

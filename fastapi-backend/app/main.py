from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List, Optional
from sqlmodel import select

from .database import init_db, get_session
from .models import Complaint

security = HTTPBasic()

def get_admin_user(credentials: HTTPBasicCredentials = Depends(security)) -> bool:
    # Placeholder admin guard: accepts any credentials for now. Replace with real check in Phase 3.
    return True

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
def list_complaints(status: Optional[str] = None, admin: bool = Depends(get_admin_user), session=Depends(get_session)):
    # Optional filter by status (e.g., reported, in_progress, resolved)
    statement = select(Complaint)
    if status:
        statement = statement.where(Complaint.status == status)
    results = session.exec(statement).all()
    return results

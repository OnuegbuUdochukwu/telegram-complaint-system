from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlmodel import select

from .database import init_db, get_session
from .models import Complaint

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
    statement = select(Complaint).where(Complaint.id == complaint_id)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result

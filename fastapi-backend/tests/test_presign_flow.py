import os
import uuid

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlmodel import Session

os.environ.setdefault("ALLOW_DEV_REGISTER", "1")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("BACKEND_SERVICE_TOKEN", "test-service-token")
os.environ.setdefault("STORAGE_PROVIDER", "s3")
os.environ.setdefault("S3_BUCKET", "test-complaint-bucket")
os.environ.setdefault("S3_REGION", "us-east-1")
os.environ.setdefault("S3_ACCESS_KEY_ID", "testing")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "testing")

from app.main import app, init_db  # noqa: E402
from app.database import engine  # noqa: E402
from app.models import Complaint  # noqa: E402
from app.routes import photos as photos_router  # noqa: E402


@pytest.fixture(scope="function")
def test_client(tmp_path, monkeypatch):
    db_url = f"sqlite:///{tmp_path/'test.db'}"
    monkeypatch.setenv("DATABASE_URL", db_url)
    init_db()
    photos_router.enqueue_thumbnail_job = lambda *a, **k: None
    return TestClient(app)


def _create_complaint() -> str:
    with Session(engine) as session:
        complaint = Complaint(
            telegram_user_id="tester",
            hostel="John",
            room_number="A101",
            category="plumbing",
            description="Leak",
            severity="low",
        )
        session.add(complaint)
        session.commit()
        session.refresh(complaint)
        return complaint.id


@mock_aws
def test_presign_and_confirm_flow(test_client):
    s3 = boto3.client(
        "s3",
        region_name=os.environ["S3_REGION"],
        aws_access_key_id=os.environ["S3_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["S3_SECRET_ACCESS_KEY"],
    )
    s3.create_bucket(Bucket=os.environ["S3_BUCKET"])

    complaint_id = _create_complaint()
    headers = {"Authorization": "Bearer test-service-token"}

    presign_resp = test_client.post(
        f"/api/v1/complaints/{complaint_id}/photos/presign",
        json={
            "filename": "test.jpg",
            "content_type": "image/jpeg",
            "content_length": 1024,
        },
        headers=headers,
    )
    assert presign_resp.status_code == 201
    body = presign_resp.json()
    assert body["photo_id"]
    key = body["s3_key"]

    # Simulate upload by writing directly via boto3
    s3.put_object(Bucket=os.environ["S3_BUCKET"], Key=key, Body=b"\xff\xd8\xff", ContentType="image/jpeg")

    confirm_resp = test_client.post(
        f"/api/v1/complaints/{complaint_id}/photos/confirm",
        json={
            "photo_id": body["photo_id"],
            "s3_key": key,
            "file_size": 3,
            "content_type": "image/jpeg",
        },
        headers=headers,
    )
    assert confirm_resp.status_code == 200
    payload = confirm_resp.json()
    assert payload["complaint_id"] == complaint_id
    assert payload["file_name"] == "test.jpg"


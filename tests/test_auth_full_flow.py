import os
import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock, MagicMock
from sqlmodel import SQLModel
from sqlalchemy import text as sa_text

# Import app modules.
# Note: conftest.py sets up DATABASE_URL to use shared test.db and creates tables.
# We should rely on that.

from app.main import app
from app.database import engine
from app import auth
from app.models import Porter, AdminInvitation, OTPToken


@pytest.fixture(name="client")
async def client_fixture():
    # Helper to clear data relevant to this test suite
    async with engine.begin() as conn:
        # Clear specific tables to ensure clean state without dropping tables
        await conn.execute(sa_text("DELETE FROM otp_tokens"))
        await conn.execute(sa_text("DELETE FROM admin_invitations"))
        # Be careful deleting porters as other tests might need them (e.g. seed users)
        # But this test creates its own superadmin.
        # Let's verify if seed users are needed.
        pass

    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c

    # Cleanup data specific to this test
    async with engine.begin() as conn:
        await conn.execute(sa_text("DELETE FROM otp_tokens"))
        await conn.execute(sa_text("DELETE FROM admin_invitations"))
        # We can try to delete the users we created if we track them,
        # or just leave them if they don't conflict.


@pytest.mark.asyncio
async def test_admin_invite_flow(client):
    # 1. Seed strict Admin using dependency override or creating directly
    # We'll creating directly via auth.create_porter using a new session
    from app.database import get_session

    # We need a session, let's create one manually using engine
    from sqlalchemy.orm import sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    admin_email = "superadmin@example.com"
    admin_password = "SuperPassword123!"

    async with async_session() as session:
        admin_user = await auth.create_porter(
            session,
            full_name="Super Admin",
            email=admin_email,
            password=admin_password,
            role="admin",
        )
        assert admin_user.id is not None

    # Login as Admin
    resp = await client.post(
        "/auth/login", data={"username": admin_email, "password": admin_password}
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    auth_header = {"Authorization": f"Bearer {token}"}

    # 2. Invite new admin
    new_admin_email = "newadmin@example.com"

    # Mock email service and email validator
    mock_valid = MagicMock()
    mock_valid.email = new_admin_email

    with patch(
        "app.main.send_invitation_email", new_callable=AsyncMock
    ) as mock_email, patch("app.main.validate_email", return_value=mock_valid):

        mock_email.return_value = True

        resp = await client.post(
            "/auth/admin/invite", json={"email": new_admin_email}, headers=auth_header
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["message"] == "Invitation sent successfully"
        mock_email.assert_called_once()

        # In a real app we'd get the token from the email.
        # In this test, we have to query the DB to mock the user clicking the link.
        async with async_session() as session:
            # We can't query directly if we don't import models, but they are imported in main
            from app.models import AdminInvitation
            from sqlmodel import select

            res = await session.exec(
                select(AdminInvitation).where(AdminInvitation.email == new_admin_email)
            )
            invitation = res.first()
            invitation_token = invitation.token

    # 3. Validate Token
    resp = await client.get(f"/auth/invitation/{invitation_token}")
    assert resp.status_code == 200
    assert resp.json()["email"] == new_admin_email

    # 4. Request OTP for Signup
    # "The frontend should handle the two-step flow: verify OTP first, then call signup." -> Wait, logic check:
    # /auth/send-otp for 'signup' requires invitation context.

    with patch(
        "app.main.send_otp_email", new_callable=AsyncMock
    ) as mock_otp_email, patch("app.main.validate_email", return_value=mock_valid):

        mock_otp_email.return_value = True

        resp = await client.post(
            "/auth/send-otp", json={"email": new_admin_email, "purpose": "signup"}
        )
        assert resp.status_code == 200
        mock_otp_email.assert_called_once()

        # Fetch OTP code from DB
        async with async_session() as session:
            from app.models import OTPToken

            pass

    # Actually, hijacking `generate_otp_code` is easier.
    fixed_otp = "123456"
    with patch("app.otp_utils.generate_otp_code", return_value=fixed_otp), patch(
        "app.main.validate_email", return_value=mock_valid
    ):

        # Retry send-otp so we know the code
        with patch("app.main.send_otp_email", new_callable=AsyncMock):
            resp = await client.post(
                "/auth/send-otp", json={"email": new_admin_email, "purpose": "signup"}
            )
            assert resp.status_code == 200

        # 5. Verify OTP
        resp = await client.post(
            "/auth/verify-otp",
            json={"email": new_admin_email, "otp_code": fixed_otp, "purpose": "signup"},
        )
        assert resp.status_code == 200
        assert resp.json()["verified"] is True

        # 6. Complete Signup
        new_password = "NewStrongPassword1!"
        resp = await client.post(
            "/auth/signup",
            json={
                "invitation_token": invitation_token,
                "full_name": "New Admin User",
                "password": new_password,
            },
        )
        assert resp.status_code == 200
        new_user_id = resp.json()["id"]

    # 7. Login as new admin
    resp = await client.post(
        "/auth/login", data={"username": new_admin_email, "password": new_password}
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == new_user_id


@pytest.mark.asyncio
async def test_rbac_porter_cannot_invite(client):
    # Create Porter
    from sqlalchemy.orm import sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    email = "porter@example.com"
    pwd = "PorterPassword1!"
    async with async_session() as session:
        await auth.create_porter(
            session, "Porter John", email=email, password=pwd, role="porter"
        )

    # Login
    resp = await client.post("/auth/login", data={"username": email, "password": pwd})
    token = resp.json()["access_token"]

    # Try to invite
    resp = await client.post(
        "/auth/admin/invite",
        json={"email": "victim@example.com"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_service_token_auth(client):
    # Try accessing a protected endpoint that allows service tokens (e.g. upload or similar - wait, dependencies.py says UPLOAD allows it)
    # But does main.py expose an endpoint that uses `get_authenticated_user_or_service`?
    # /api/v1/complaints/{id}/photos POST uses `get_authenticated_user_or_service`
    # Let's try that.

    # Setup data
    from sqlalchemy.orm import sessionmaker
    from sqlmodel.ext.asyncio.session import AsyncSession
    from app.models import Complaint

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    complaint_eval_id = "test-complaint-id"
    # Note: If we use SQLite, ID is string uuid.
    import uuid

    complaint_eval_id = str(uuid.uuid4())

    async with async_session() as session:
        c = Complaint(
            id=complaint_eval_id,
            telegram_user_id="123",
            hostel="H1",
            room_number="A101",
            category="plumbing",
            description="desc",
            severity="low",
        )
        session.add(c)
        await session.commit()

    # Request
    headers = {"Authorization": "Bearer test-service-token"}
    # We need a file
    files = {"file": ("test.jpg", b"fake-image-content", "image/jpeg")}

    # We need to mock validity checks inside upload_photo_to_complaint
    with patch("app.main.validate_image", return_value=(True, "")) as m_val, patch(
        "app.main.process_image",
        return_value=(b"opt", b"thumb", 100, 100, "image/jpeg"),
    ) as m_proc, patch(
        "app.main.upload_photo",
        return_value=("http://s3/file.jpg", "http://s3/thumb.jpg"),
    ) as m_up:

        resp = await client.post(
            f"/api/v1/complaints/{complaint_eval_id}/photos",
            headers=headers,
            files=files,
        )
        # Should be 200 OK because service token is accepted
        assert resp.status_code == 200
        assert resp.json()["file_url"] == "http://s3/file.jpg"

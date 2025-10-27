"""E2E helper: submit complaint, upload image, and verify via backend API.
Run this from the repo root with the project venv active or by invoking the venv python.
"""
import os
import io
import sys
import json

# ensure app package on path
sys.path.insert(0, os.path.join(os.getcwd(), "fastapi-backend"))

import client
import httpx
from PIL import Image
from app.database import engine
from sqlmodel import Session, select
from app.models import Porter
from app import auth

# Create service token
with Session(engine) as session:
    stmt = select(Porter).where(Porter.email == 'bot@example.com')
    p = session.exec(stmt).first()
    if not p:
        print('No porter found; aborting')
        raise SystemExit(1)
    token = auth.create_access_token(subject=p.id, role=p.role)
    os.environ['BACKEND_SERVICE_TOKEN'] = token
    print('Service token ready for:', p.email, p.id)

# Submit complaint
print('Submitting complaint...')
data = {
    'telegram_user_id': 'e2e-test-telegram',
    'hostel': 'A',
    'room_number': 'A101',
    'category': 'plumbing',
    'description': 'E2E test complaint created by automated script',
    'severity': 'low'
}
res = client.submit_complaint(data)
print(json.dumps(res, indent=2))
complaint_id = res.get('complaint_id') or res.get('id')
if not complaint_id:
    print('Failed to get complaint_id; aborting')
    raise SystemExit(1)

# Generate JPEG
img = Image.new('RGB', (200,200), (0,128,255))
buf = io.BytesIO()
img.save(buf, format='JPEG')
bytes_img = buf.getvalue()
print(f'Uploading image ({len(bytes_img)} bytes) to complaint {complaint_id}')
photo_resp = client.upload_photo(complaint_id, bytes_img, 'e2e_test.jpg', 'image/jpeg')
print(json.dumps(photo_resp, indent=2))

# Verify GET complaint
print('Verifying via HTTP GETs...')
base = os.environ.get('BACKEND_URL') or 'http://127.0.0.1:8001'
r = httpx.get(base.rstrip('/') + f"/api/v1/complaints/{complaint_id}")
print('GET complaint status', r.status_code)
print(json.dumps(r.json(), indent=2))
# GET photos (needs auth)
headers = {'Authorization': f"Bearer {os.environ.get('BACKEND_SERVICE_TOKEN')}"}
r2 = httpx.get(base.rstrip('/') + f"/api/v1/complaints/{complaint_id}/photos", headers=headers)
print('GET photos status', r2.status_code)
print(json.dumps(r2.json(), indent=2))

print('E2E script completed')

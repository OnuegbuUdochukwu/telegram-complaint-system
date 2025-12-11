import os
import pytest
from client import upload_photo


@pytest.mark.asyncio
async def test_client_upload_photo_mock():
    """When BACKEND_URL is not set, upload_photo should return a mock response
    with a storage path under /storage and echo the complaint id and filename.
    """
    # Ensure BACKEND_URL is not set for this unit test to exercise mock fallback
    os.environ.pop("BACKEND_URL", None)
    import client

    old_url = client.BACKEND_URL
    client.BACKEND_URL = None
    print(f"DEBUG: client.BACKEND_URL set to {client.BACKEND_URL}")
    try:
        complaint_id = "TEST-CID-123"
        data = b"fake-image-bytes"
        filename = "test.jpg"

        resp = await upload_photo(complaint_id, data, filename)

        assert isinstance(resp, dict)
        assert resp.get("complaint_id") == complaint_id
        assert resp.get("file_name") == filename
        assert resp.get("file_size") == len(data)
        assert resp.get("file_url") is not None
        assert resp.get("file_url").startswith(
            "/storage/"
        ), "Mock file_url should point to /storage/ path"

    finally:
        client.BACKEND_URL = old_url

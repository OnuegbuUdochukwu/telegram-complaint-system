# Photo Upload and Storage Implementation

## Overview

This document describes the implementation of photo upload and storage functionality (Phase 3, items 3.9 and 3.10) for the Telegram Complaint System.

## What Was Implemented

### 1. Database Schema (models.py)

Added a new `Photo` model to store photo metadata:
- `id`: UUID primary key
- `complaint_id`: Foreign key to complaints table
- `file_url`: URL/path to the original photo
- `thumbnail_url`: URL/path to the thumbnail version
- `file_name`: Original filename
- `file_size`: File size in bytes
- `mime_type`: MIME type (e.g., "image/jpeg")
- `width`: Image width in pixels
- `height`: Image height in pixels
- `created_at`: Timestamp when photo was uploaded

### 2. Alembic Migration

Created migration file `20251021_create_photos_table.py`:
- Creates `photos` table in PostgreSQL
- Adds foreign key constraint to `complaints` table
- Adds index on `complaint_id` for efficient queries
- Includes CASCADE delete to remove photos when complaint is deleted

### 3. Storage Service (storage.py)

Implemented a flexible storage service that supports:
- **S3-compatible storage** (AWS S3, MinIO)
  - Configurable via environment variables
  - Automatic bucket creation
  - Signed URL generation for secure access
- **Local filesystem fallback**
  - Stores files in `storage/` directory
  - Organized by complaint_id
  - Useful for development and testing

Environment variables for S3 configuration:
- `S3_ENDPOINT_URL`: S3 endpoint URL (for MinIO)
- `S3_ACCESS_KEY`: AWS access key
- `S3_SECRET_KEY`: AWS secret key
- `S3_BUCKET_NAME`: Bucket name (defaults to "complaint-photos")
- `S3_REGION`: AWS region (defaults to "us-east-1")

### 4. Photo Processing (photo_utils.py)

Image processing utilities using Pillow:
- **Validation**:
  - File size limit: 10 MB maximum
  - File type restriction: Only images (JPEG, PNG, GIF, WebP)
  - Dimension validation: Maximum 4000x4000 pixels
- **Processing**:
  - Automatic image optimization
  - Thumbnail generation (256x256 pixels)
  - Format conversion to JPEG for consistency
  - Transparency handling (RGB conversion with white background)

### 5. API Endpoints (main.py)

Three new endpoints were added:

#### POST `/api/v1/complaints/{complaint_id}/photos`
- Upload a photo to a complaint
- Requires JWT authentication
- Accepts multipart/form-data file upload
- Validates file size, type, and dimensions
- Processes image and generates thumbnail
- Stores both original and thumbnail
- Returns photo metadata

#### GET `/api/v1/complaints/{complaint_id}/photos`
- List all photos for a complaint
- Requires JWT authentication
- Returns array of photo metadata objects

#### DELETE `/api/v1/complaints/{complaint_id}/photos/{photo_id}`
- Delete a photo from a complaint
- Requires JWT authentication
- Removes photo from storage and database

### 6. Dependencies (requirements.txt)

Added new dependencies:
- `boto3==1.34.0`: AWS SDK for S3 integration
- `Pillow==10.1.0`: Image processing library

### 7. Tests (test_photo_uploads.py)

Created comprehensive test suite:
- `test_upload_photo_requires_auth`: Verifies authentication is required
- `test_upload_and_list_photos`: End-to-end upload and listing test
- `test_photo_validation`: Tests file size and type validation
- `test_list_photos_for_nonexistent_complaint`: Tests error handling

## Configuration

### Environment Variables

Add to `.env` file for S3 storage:

```env
S3_ENDPOINT_URL=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=complaint-photos
S3_REGION=us-east-1
```

For local development, these are optional - the system will fall back to local filesystem storage.

### Database Migration

Run the migration to create the photos table:

```bash
cd fastapi-backend
alembic upgrade head
```

## Usage Examples

### Upload a Photo

```python
import httpx

# Upload photo with authentication
with open("photo.jpg", "rb") as f:
    files = {"file": ("photo.jpg", f, "image/jpeg")}
    response = httpx.post(
        "http://localhost:8001/api/v1/complaints/{complaint_id}/photos",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )
```

### List Photos for a Complaint

```python
response = httpx.get(
    "http://localhost:8001/api/v1/complaints/{complaint_id}/photos",
    headers={"Authorization": f"Bearer {token}"}
)
photos = response.json()
```

### Delete a Photo

```python
response = httpx.delete(
    "http://localhost:8001/api/v1/complaints/{complaint_id}/photos/{photo_id}",
    headers={"Authorization": f"Bearer {token}"}
)
```

## Features

### Security
- ✅ JWT authentication required for all photo operations
- ✅ File type validation (images only)
- ✅ File size limits (10 MB max)
- ✅ Signed URLs for S3 access (7-day expiry)

### Image Processing
- ✅ Automatic image optimization
- ✅ Thumbnail generation (256x256)
- ✅ Format conversion to JPEG for consistency
- ✅ Dimension resizing for large images (max 2048px)

### Storage
- ✅ S3-compatible storage (AWS S3, MinIO)
- ✅ Local filesystem fallback
- ✅ Organized storage by complaint_id
- ✅ Automatic thumbnail storage

### API Design
- ✅ RESTful endpoints
- ✅ Proper HTTP status codes
- ✅ Detailed error messages
- ✅ Comprehensive response data

## Testing

Run the photo upload tests:

```bash
pytest tests/test_photo_uploads.py -v
```

## Next Steps (Optional)

For production deployment, consider adding:
1. Background worker (Celery/RQ) for async thumbnail generation
2. CDN integration for photo delivery
3. Image optimization with multiple sizes (thumb, medium, large)
4. Rate limiting on uploads
5. Virus scanning for uploaded files
6. Automatic cleanup of orphaned files

## Files Created/Modified

### New Files
- `fastapi-backend/app/storage.py`: Storage service
- `fastapi-backend/app/photo_utils.py`: Image processing utilities
- `fastapi-backend/alembic/versions/20251021_create_photos_table.py`: Database migration
- `tests/test_photo_uploads.py`: Test suite

### Modified Files
- `fastapi-backend/app/models.py`: Added Photo model
- `fastapi-backend/app/main.py`: Added photo endpoints
- `fastapi-backend/requirements.txt`: Added boto3 and Pillow
- `PHASE3_CHECKLIST.md`: Marked items 3.9 and 3.10 as complete

## Progress Update

**Phase 3 Media Handling:**
- ✅ 3.9 Photo uploads and storage (6/6 subtasks complete)
- ✅ 3.10 Thumbnailing & size limits (3/4 subtasks complete, background worker optional)
- **Overall: 8/9 subtasks (89%)**

**Overall Phase 3 Progress:** 11/16 top-level tasks completed (69%)


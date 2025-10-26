"""
Storage service for photo uploads and management.

Supports S3-compatible storage (AWS S3, MinIO) with local fallback.
"""

import boto3
from botocore.exceptions import ClientError
from botocore.config import Config
from pathlib import Path
import os
from typing import Optional, BinaryIO, Tuple
import logging
from dotenv import dotenv_values

logger = logging.getLogger("app.storage")
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    logger.addHandler(handler)

_env_path = Path(__file__).resolve().parents[2] / ".env"
config = dotenv_values(str(_env_path))

# Configuration with environment variable overrides
S3_ENDPOINT_URL = os.environ.get("S3_ENDPOINT_URL") or config.get("S3_ENDPOINT_URL")
S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY") or config.get("S3_ACCESS_KEY")
S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY") or config.get("S3_SECRET_KEY")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME") or config.get("S3_BUCKET_NAME") or "complaint-photos"
S3_REGION = os.environ.get("S3_REGION") or config.get("S3_REGION") or "us-east-1"

# Local storage fallback
LOCAL_STORAGE_PATH = Path(__file__).resolve().parents[2] / "storage"
LOCAL_STORAGE_PATH.mkdir(exist_ok=True)

# Initialize S3 client if credentials are available
_s3_client = None
if S3_ACCESS_KEY and S3_SECRET_KEY:
    try:
        # Use minio-compatible settings if endpoint is provided
        s3_config = Config(
            signature_version='s3v4',
            retries={'max_attempts': 3}
        )
        
        _s3_client = boto3.client(
            's3',
            endpoint_url=S3_ENDPOINT_URL,
            aws_access_key_id=S3_ACCESS_KEY,
            aws_secret_access_key=S3_SECRET_KEY,
            region_name=S3_REGION,
            config=s3_config
        )
        
        # Create bucket if it doesn't exist (for S3-compatible services)
        try:
            _s3_client.head_bucket(Bucket=S3_BUCKET_NAME)
            logger.info(f"S3 bucket '{S3_BUCKET_NAME}' exists and is accessible")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                # Bucket doesn't exist, create it
                if S3_ENDPOINT_URL:
                    # MinIO-style
                    _s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
                else:
                    # AWS S3
                    _s3_client.create_bucket(
                        Bucket=S3_BUCKET_NAME,
                        CreateBucketConfiguration={'LocationConstraint': S3_REGION}
                    )
                logger.info(f"Created S3 bucket '{S3_BUCKET_NAME}'")
            else:
                logger.error(f"Error accessing S3 bucket: {e}")
                _s3_client = None
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        _s3_client = None

logger.info(f"Storage initialized: S3={_s3_client is not None}, Local fallback={LOCAL_STORAGE_PATH}")


def get_s3_key(complaint_id: str, photo_id: str, is_thumbnail: bool = False) -> str:
    """Generate S3 key for a photo."""
    suffix = "_thumb.jpg" if is_thumbnail else ".jpg"
    return f"complaints/{complaint_id}/{photo_id}{suffix}"


def upload_photo(file_data: bytes, complaint_id: str, photo_id: str, 
                 content_type: str = "image/jpeg") -> Tuple[str, Optional[str]]:
    """
    Upload a photo to storage.
    
    Returns:
        Tuple of (file_url, thumbnail_url)
    """
    # Generate storage paths
    s3_key = get_s3_key(complaint_id, photo_id, is_thumbnail=False)
    thumbnail_key = get_s3_key(complaint_id, photo_id, is_thumbnail=True)
    
    if _s3_client:
        # Upload to S3
        try:
            # Upload original photo
            _s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    'complaint_id': complaint_id,
                    'photo_id': photo_id
                }
            )
            
            file_url = f"s3://{S3_BUCKET_NAME}/{s3_key}"
            
            # Generate signed URL for access (valid for 7 days)
            # TODO: Store thumbnail_key when thumbnail is uploaded
            thumbnail_url = None
            
            logger.info(f"Uploaded photo to S3: {file_url}")
            return file_url, thumbnail_url
            
        except Exception as e:
            logger.error(f"Failed to upload photo to S3: {e}")
            # Fall through to local storage
    
    # Local storage fallback
    local_dir = LOCAL_STORAGE_PATH / complaint_id
    local_dir.mkdir(parents=True, exist_ok=True)
    
    photo_path = local_dir / f"{photo_id}.jpg"
    photo_path.write_bytes(file_data)
    
    file_url = f"/storage/{complaint_id}/{photo_id}.jpg"
    thumbnail_url = None
    
    logger.info(f"Stored photo locally: {photo_path}")
    return file_url, thumbnail_url


def upload_thumbnail(thumbnail_data: bytes, complaint_id: str, photo_id: str) -> Optional[str]:
    """Upload a thumbnail version of a photo."""
    s3_key = get_s3_key(complaint_id, photo_id, is_thumbnail=True)
    
    if _s3_client:
        try:
            _s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=thumbnail_data,
                ContentType="image/jpeg",
                Metadata={
                    'complaint_id': complaint_id,
                    'photo_id': photo_id,
                    'type': 'thumbnail'
                }
            )
            
            return f"s3://{S3_BUCKET_NAME}/{s3_key}"
        except Exception as e:
            logger.error(f"Failed to upload thumbnail to S3: {e}")
            # Fall through to local storage
    
    # Local storage fallback
    local_dir = LOCAL_STORAGE_PATH / complaint_id
    local_dir.mkdir(parents=True, exist_ok=True)
    
    thumbnail_path = local_dir / f"{photo_id}_thumb.jpg"
    thumbnail_path.write_bytes(thumbnail_data)
    
    logger.info(f"Stored thumbnail locally: {thumbnail_path}")
    return f"/storage/{complaint_id}/{photo_id}_thumb.jpg"


def get_photo_url(complaint_id: str, photo_id: str, is_thumbnail: bool = False) -> str:
    """
    Generate a URL for accessing a photo.
    
    For S3, this returns a signed URL valid for 7 days.
    For local storage, returns a path-relative URL.
    """
    s3_key = get_s3_key(complaint_id, photo_id, is_thumbnail)
    
    if _s3_client:
        try:
            # Generate signed URL (valid for 7 days = 604800 seconds)
            url = _s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': S3_BUCKET_NAME, 'Key': s3_key},
                ExpiresIn=604800
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL: {e}")
            return f"/api/v1/storage/{complaint_id}/{photo_id}"
    
    # Local storage
    suffix = "_thumb.jpg" if is_thumbnail else ".jpg"
    return f"/storage/{complaint_id}/{photo_id}{suffix}"


def delete_photo(complaint_id: str, photo_id: str) -> bool:
    """Delete a photo from storage."""
    s3_key = get_s3_key(complaint_id, photo_id, is_thumbnail=False)
    thumbnail_key = get_s3_key(complaint_id, photo_id, is_thumbnail=True)
    
    deleted = False
    
    if _s3_client:
        try:
            # Delete photo and thumbnail
            _s3_client.delete_objects(
                Bucket=S3_BUCKET_NAME,
                Delete={
                    'Objects': [
                        {'Key': s3_key},
                        {'Key': thumbnail_key}
                    ]
                }
            )
            deleted = True
            logger.info(f"Deleted photo from S3: {s3_key}")
        except Exception as e:
            logger.error(f"Failed to delete photo from S3: {e}")
    
    # Also try to delete from local storage
    local_dir = LOCAL_STORAGE_PATH / complaint_id
    if local_dir.exists():
        photo_path = local_dir / f"{photo_id}.jpg"
        thumbnail_path = local_dir / f"{photo_id}_thumb.jpg"
        
        if photo_path.exists():
            photo_path.unlink()
            deleted = True
        if thumbnail_path.exists():
            thumbnail_path.unlink()
            deleted = True
    
    return deleted


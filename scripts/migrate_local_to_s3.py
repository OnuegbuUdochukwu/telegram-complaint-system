#!/usr/bin/env python
"""
Migration helper that copies legacy filesystem photos into S3 and updates DB rows.

Usage:
    python scripts/migrate_local_to_s3.py --storage-dir ./storage --bucket complaint-photos
"""

from __future__ import annotations

import argparse
from pathlib import Path
import logging
import os

from sqlmodel import Session, select

REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PATH = REPO_ROOT / "fastapi-backend"
import sys

if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

from app.database import engine
from app.models import Photo
from app.storage_s3 import S3Storage, guess_extension
from app.config import get_settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("migrate-local-to-s3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Migrate local files to S3")
    parser.add_argument(
        "--storage-dir",
        default="storage",
        help="Directory containing legacy photo files",
    )
    parser.add_argument(
        "--bucket",
        default=None,
        help="Override bucket name (defaults to env S3_BUCKET)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Only log actions without uploading"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    settings = get_settings()
    bucket = args.bucket or settings.s3_bucket

    storage_path = Path(args.storage_dir)
    if not storage_path.exists():
        raise SystemExit(f"Storage directory {storage_path} not found")

    s3 = S3Storage()
    s3.ensure_bucket()

    with Session(engine) as session:
        photos = session.exec(select(Photo)).all()
        for photo in photos:
            if photo.s3_key:
                continue  # already migrated
            disk_path = storage_path / photo.complaint_id / f"{photo.id}.jpg"
            if not disk_path.exists():
                logger.warning("Missing file for photo %s at %s", photo.id, disk_path)
                continue

            data = disk_path.read_bytes()
            ext = guess_extension(photo.mime_type or "image/jpeg")
            key = f"complaints/{photo.complaint_id}/originals/{photo.id}.{ext}"
            logger.info("Uploading %s to s3://%s/%s", disk_path, bucket, key)
            if not args.dry_run:
                s3.put_object(key, data, photo.mime_type or "image/jpeg")
                photo.s3_key = key
                photo.file_url = f"s3://{bucket}/{key}"
                photo.storage_provider = "s3"
                session.add(photo)

        if not args.dry_run:
            session.commit()


if __name__ == "__main__":
    main()

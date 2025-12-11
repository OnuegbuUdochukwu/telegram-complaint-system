"""
High-level helpers for interacting with AWS S3 (or compatible services like MinIO).

This module encapsulates presigned URL generation, object management, and
secure defaults (SSE, explicit content-type bindings, CloudFront integration).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Dict, Any
import logging
import mimetypes

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from .config import get_settings

logger = logging.getLogger("app.storage_s3")


class StorageError(RuntimeError):
    """Raised when storage operations fail."""


@dataclass
class PresignedUpload:
    upload_id: str
    photo_id: str
    method: str
    url: str
    fields: Optional[Dict[str, Any]]
    expires_in: int
    s3_key: str


class S3Storage:
    """Wrapper over boto3 with sane defaults for presigned flows."""

    def __init__(self) -> None:
        settings = get_settings()
        session_kwargs = {}

        if settings.s3_access_key_id and settings.s3_secret_access_key:
            session_kwargs.update(
                aws_access_key_id=settings.s3_access_key_id,
                aws_secret_access_key=settings.s3_secret_access_key,
            )

        session = (
            boto3.session.Session(**session_kwargs)
            if session_kwargs
            else boto3.session.Session()
        )

        # Internal client for actual S3 operations (uses Docker-internal endpoint)
        client_kwargs = {
            "service_name": "s3",
            "region_name": settings.s3_region,
            "config": Config(signature_version="s3v4"),
        }
        if settings.s3_endpoint:
            client_kwargs["endpoint_url"] = settings.s3_endpoint
        if settings.s3_use_ssl is False:
            client_kwargs["use_ssl"] = False

        self._client = session.client(**client_kwargs)

        # Separate client for presigned URL generation using public endpoint
        # This ensures the signature matches the host that external clients will use
        if (
            settings.s3_endpoint_public
            and settings.s3_endpoint_public != settings.s3_endpoint
        ):
            presign_kwargs = client_kwargs.copy()
            presign_kwargs["endpoint_url"] = settings.s3_endpoint_public
            self._presign_client = session.client(**presign_kwargs)
        else:
            self._presign_client = self._client

        self._bucket = settings.s3_bucket
        self._kms_key_id = settings.kms_key_id
        self._upload_expiry = settings.s3_presign_expiry_upload
        self._download_expiry = settings.s3_presign_expiry_get
        self._cloudfront_domain = settings.cloudfront_domain

    # ---------- helpers ----------
    @staticmethod
    def build_s3_key(
        complaint_id: str,
        photo_id: str,
        variant: str = "original",
        extension: str = "jpg",
    ) -> str:
        prefix = "originals" if variant == "original" else "thumbnails"
        return f"complaints/{complaint_id}/{prefix}/{photo_id}.{extension}"

    def _apply_object_defaults(
        self, extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if self._kms_key_id:
            params["ServerSideEncryption"] = "aws:kms"
            params["SSEKMSKeyId"] = self._kms_key_id
        if extra:
            params.update(extra)
        return params

    # ---------- presign ----------
    def generate_presigned_put(
        self, key: str, content_type: str, content_length: Optional[int]
    ) -> PresignedUpload:
        conditions = [
            {"bucket": self._bucket},
            {"key": key},
            {"Content-Type": content_type},
        ]
        if content_length:
            conditions.append(["content-length-range", 1, content_length])

        try:
            # Use presign_client (which uses public endpoint) for external clients
            url = self._presign_client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": key,
                    "ContentType": content_type,
                    **self._apply_object_defaults(
                        {"Metadata": {"managed-by": "complaint-backend"}}
                    ),
                },
                ExpiresIn=self._upload_expiry,
                HttpMethod="PUT",
            )
        except ClientError as exc:
            raise StorageError(f"Failed to generate presigned PUT URL: {exc}") from exc

        return PresignedUpload(
            upload_id=key,
            photo_id=key.split("/")[-1].split(".")[0],
            method="PUT",
            url=url,
            fields=None,
            expires_in=self._upload_expiry,
            s3_key=key,
        )

    def generate_presigned_get(self, key: str) -> str:
        if self._cloudfront_domain:
            return f"https://{self._cloudfront_domain}/{key}"

        try:
            return self._client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self._bucket, "Key": key},
                ExpiresIn=self._download_expiry,
            )
        except ClientError as exc:
            raise StorageError(f"Failed to generate presigned GET URL: {exc}") from exc

    # ---------- object helpers ----------
    def head_object(self, key: str) -> Dict[str, Any]:
        try:
            return self._client.head_object(Bucket=self._bucket, Key=key)
        except ClientError as exc:
            raise StorageError(f"head_object failed for {key}: {exc}") from exc

    def delete_object_tree(self, complaint_id: str, photo_id: str) -> None:
        objects = [
            {"Key": self.build_s3_key(complaint_id, photo_id, "original")},
            {"Key": self.build_s3_key(complaint_id, photo_id, "thumbnail")},
        ]
        try:
            self._client.delete_objects(
                Bucket=self._bucket, Delete={"Objects": objects, "Quiet": True}
            )
        except ClientError as exc:
            raise StorageError(
                f"Failed to delete objects for photo {photo_id}: {exc}"
            ) from exc

    def copy_object(
        self, source_key: str, dest_key: str, content_type: Optional[str] = None
    ) -> None:
        extra = {}
        if content_type:
            extra["ContentType"] = content_type
            extra["MetadataDirective"] = "REPLACE"
        try:
            self._client.copy(
                {"Bucket": self._bucket, "Key": source_key},
                self._bucket,
                dest_key,
                ExtraArgs=self._apply_object_defaults(extra),
            )
        except ClientError as exc:
            raise StorageError(
                f"copy_object failed from {source_key} to {dest_key}: {exc}"
            ) from exc

    def put_object(
        self, key: str, data: bytes, content_type: Optional[str] = None
    ) -> None:
        extra = {}
        if content_type:
            extra["ContentType"] = content_type
        try:
            self._client.put_object(
                Bucket=self._bucket,
                Key=key,
                Body=data,
                **self._apply_object_defaults(extra),
            )
        except ClientError as exc:
            raise StorageError(f"put_object failed for {key}: {exc}") from exc

    def get_object_bytes(self, key: str) -> bytes:
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            body = response["Body"].read()
            return body
        except ClientError as exc:
            raise StorageError(f"Failed to download {key}: {exc}") from exc

    def ensure_bucket(self) -> None:
        """Best-effort check that bucket exists (useful for local MinIO)."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            error_code = exc.response.get("Error", {}).get("Code")
            if error_code in {"404", "NoSuchBucket"}:
                logger.info(
                    "Bucket %s missing; attempting to create for dev/local use",
                    self._bucket,
                )
                params = {"Bucket": self._bucket}
                region = get_settings().s3_region
                if region and region != "us-east-1":
                    params["CreateBucketConfiguration"] = {"LocationConstraint": region}
                self._client.create_bucket(**params)
            else:
                raise


def guess_extension(content_type: str) -> str:
    mapped = mimetypes.guess_extension(content_type) or ".jpg"
    return mapped.lstrip(".")


__all__ = ["S3Storage", "StorageError", "PresignedUpload", "guess_extension"]

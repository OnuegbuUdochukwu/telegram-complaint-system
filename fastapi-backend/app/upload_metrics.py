"""Prometheus metrics shared by upload-related modules."""

from prometheus_client import Counter


UPLOAD_ATTEMPTS = Counter(
    "upload_photo_attempts_total",
    "Total number of photo upload attempts (legacy direct uploads + presign confirms)",
)
UPLOAD_SUCCESSES = Counter(
    "upload_photo_success_total",
    "Total number of successful photo uploads",
)
UPLOAD_FAILURES = Counter(
    "upload_photo_failure_total",
    "Total number of failed photo uploads",
)
UPLOAD_AUTH_FAILURES = Counter(
    "upload_photo_auth_failures_total",
    "Total number of upload attempts that failed authentication",
)


Task: Implement production-ready S3-backed media uploads for the Telegram complaint bot

Overview

Goal: Replace or augment local file storage with a secure, scalable AWS S3-based pipeline that supports:

Presigned uploads (backend issues presigned upload URLs; bot uploads directly to S3)

Background processing (thumbnailing, resizing, virus scan, metadata extraction)

Secure serving (CloudFront or presigned GET URLs)

Minimal exposure of secrets, least-privilege IAM, and production-grade infra (IaC)

Deliverables (final artifacts Agent B must produce):

Architecture diagram(s) (Mermaid + PNG/SVG) and a short textual flow description.

Backend code (Python/FastAPI preferred) implementing presigned-upload endpoints, metadata callbacks, and S3 helpers.

Worker code (Celery + Redis or AWS Lambda) that consumes S3 events to process images and create thumbnails.

DB schema changes or migration scripts to store S3 object keys/metadata.

Example IAM policies (minimal least-privilege) for backend, workers, and any Lambda functions.

Infrastructure-as-Code (Terraform or CloudFormation) to create:

S3 bucket(s) with encryption, lifecycle rules, and logging

CloudFront distribution (recommended)

KMS key (if using SSE-KMS)

IAM roles/policies

Optional: SNS/SQS/Lambda triggers & IAM bindings

CI/CD instructions and deployment steps, including how to provision secrets (AWS Secrets Manager / Parameter Store recommended) vs .env.

Local dev & test setup (MinIO or moto), unit & integration tests (pytest), and an E2E test harness.

Migration plan and script to move existing local files to S3 (if needed).

README with setup, commands, and acceptance criteria.

Cost and operations notes (estimates, lifecycle policy recommendations, backup/retention).

Constraints & assumptions

Primary cloud: AWS (S3 + CloudFront). Alternatives are acceptable (DigitalOcean Spaces, Supabase Storage, MinIO) but the primary deliverable must target AWS S3.

Language/stack: Prefer Python 3.10+ with FastAPI (backend), boto3 (S3), Celery + Redis for workers. If Agent B chooses Node.js or another stack, they must clearly document that choice and provide equivalent code and IaC.

Secrets: In production, store secrets in secrets manager; .env is only allowed for local dev. The repository .env (attached) shows example keys; do not commit real secrets.

Service token model: Use the existing BACKEND_SERVICE_TOKEN mechanism for bot→backend authentication (opaque token), and ensure token usage for presigned URL issuance and any metadata callback is secure.

Detailed specification — API & behavior

1. API endpoints (specify exact HTTP contracts)

A. Request presigned upload URL (backend)

Endpoint: POST /api/v1/complaints/{complaint_id}/photos/presign

Auth: Bearer service token (BACKEND_SERVICE_TOKEN) or a valid JWT for authenticated users.

Request body (JSON):

{
"filename": "IMG_001.jpg",
"content_type": "image/jpeg",
"content_length": 234567 // optional, for size enforcement
}

Response (201):

{
"upload_id": "<uuid>", // internal id for the upload attempt (idempotency)
"s3_key": "complaints/{complaint_id}/{photo_id}.jpg",
"method": "PUT" | "POST", // prefer PUT for bot uploads
"url": "<presigned_put_url>",
"fields": null | { ... }, // only for POST form-based presign
"expires_in": 300 // seconds
}

Behavior:

Validate complaint existence and caller authorization.

Enforce max file size and allowed content types; reject if above threshold.

Generate a server-side photo_id (UUID) and S3 key pattern: complaints/{complaint_id}/{photo_id}.jpg.

Generate an S3 presigned PUT URL (prefer PUT) and return it along with s3_key and upload_id.

Optionally store a DB record for the in-progress upload (idempotency).

TTL: short-lived (recommend 5 minutes).

B. Confirm upload / metadata callback

Option 1 (recommended): Bot calls backend after successful PUT to confirm and provide metadata.

Endpoint: POST /api/v1/complaints/{complaint_id}/photos/confirm

Auth: service token

Request body:

{
"photo_id": "<uuid>",
"s3_key": "complaints/..",
"file_size": 234567,
"content_type": "image/jpeg",
"checksum": "<optional sha256>"
}

Response: 200 with stored photo metadata / DB record

Option 2: Rely on S3 event notification + worker to discover new object and update DB (also required for processing if bot doesn't call confirm).

Both approaches can co-exist.

C. List photos, get photo metadata, delete photo endpoints

Keep or extend existing endpoints:

GET /api/v1/complaints/{complaint_id}/photos → list stored photo metadata

GET /api/v1/complaints/{complaint_id}/photos/{photo_id} → metadata + signed GET URL (or CloudFront URL)

DELETE /... → delete object (remove S3 object and DB record)

For GET photo content: prefer returning a presigned GET URL (short TTL) or a CloudFront signed URL.

D. Health & admin endpoints

Ensure ability to check S3 connectivity and IAM permissions (e.g., /admin/storage-health returns bucket reachable + IAM policy effectiveness).

2. S3 design & policies

Bucket(s):

One bucket named by env: S3_BUCKET (example: complaint-photos).

Private by default (Block Public Access).

Use prefixes: complaints/{complaint_id}/originals/ and complaints/{complaint_id}/thumbnails/.

Object naming: deterministic keys with photo_id UUIDs: e.g. complaints/{complaint_id}/{photo_id}.jpg and complaints/{complaint_id}/{photo_id}\_thumb.jpg.

Server-side encryption:

Use SSE-KMS for sensitive data (recommended) or SSE-S3 as minimal.

Provide KMS key creation sample in IaC.

Lifecycle/retention:

Move to Infrequent Access after 30 days, Glacier after 365 days (configurable).

Optional TTL purge for attachments older than retention policy (admin endpoint / purge).

Bucket logging & audit:

Enable S3 server access logging or S3 access logs to a dedicated logging bucket.

CORS:

If presigned POSTs are used from browsers, provide minimal CORS rules.

CloudFront:

Use CloudFront with an Origin Access Control (OAC) or Origin Access Identity (OAI) so CloudFront can fetch private S3 objects.

Use signed URLs or signed cookies to protect private content if necessary.

Configure caching and TTLs; set Cache-Control headers when writing objects.

3. IAM (least privilege)

Backend role/policy (able to presign and read/write for upload operations):

Allowed actions (limited scope):

s3:PutObject (for presigned PUT generation)

s3:GetObject (to validate/verify or for server-side operations)

s3:DeleteObject (for delete ops)

s3:ListBucket (if needed limited to complaint prefixes)

kms:Encrypt/Decrypt/GenerateDataKey if using SSE-KMS on given KMS key ARN

Restrict resources to the bucket ARN and optionally to arn:aws:s3:::complaint-photos/complaints/\*

Worker role (thumbnailer):

s3:GetObject, s3:PutObject (for thumbnails prefix), kms actions

Bot does not need AWS credentials; it uses presigned URLs.

# Task: Implement production-ready S3-backed media uploads for the Telegram complaint bot

## Overview

**Goal:** Replace or augment local file storage with a secure, scalable AWS S3-based pipeline that supports:

-   Presigned uploads (backend issues presigned upload URLs; bot uploads directly to S3)
-   Background processing (thumbnailing, resizing, virus scan, metadata extraction)
-   Secure serving (CloudFront or presigned GET URLs)
-   Minimal exposure of secrets, least-privilege IAM, and production-grade infra (IaC)

---

## Deliverables (final artifacts Agent B must produce)

-   Architecture diagram(s) (Mermaid + PNG/SVG) and a short textual flow description.
-   Backend code (Python/FastAPI preferred) implementing presigned-upload endpoints, metadata callbacks, and S3 helpers.
-   Worker code (Celery + Redis or AWS Lambda) that consumes S3 events to process images and create thumbnails.
-   DB schema changes or migration scripts to store S3 object keys/metadata.
-   Example IAM policies (minimal least-privilege) for backend, workers, and any Lambda functions.
-   Infrastructure-as-Code (Terraform or CloudFormation) to create:
    -   S3 bucket(s) with encryption, lifecycle rules, and logging
    -   CloudFront distribution (recommended)
    -   KMS key (if using SSE-KMS)
    -   IAM roles/policies
    -   Optional: SNS/SQS/Lambda triggers & IAM bindings
-   CI/CD instructions and deployment steps, including how to provision secrets (AWS Secrets Manager / Parameter Store recommended) vs `.env`.
-   Local dev & test setup (MinIO or moto), unit & integration tests (pytest), and an E2E test harness.
-   Migration plan and script to move existing local files to S3 (if needed).
-   README with setup, commands, and acceptance criteria.
-   Cost and operations notes (estimates, lifecycle policy recommendations, backup/retention).

---

## Constraints & assumptions

-   **Primary cloud:** AWS (S3 + CloudFront). Alternatives (DigitalOcean Spaces, Supabase Storage, MinIO) are acceptable for dev/test, but primary deliverables must target AWS S3.
-   **Language/stack:** Prefer Python 3.10+ with FastAPI (backend), `boto3` (S3), Celery + Redis for workers. If another stack (Node.js, etc.) is chosen, document the choice and provide equivalent code and IaC.
-   **Secrets:** In production, store secrets in a secrets manager; `.env` is only allowed for local dev. Do not commit real secrets.
-   **Service token model:** Use the existing `BACKEND_SERVICE_TOKEN` mechanism for bot→backend authentication (opaque token), and ensure token usage for presigned URL issuance and any metadata callback is secure.

---

## Detailed specification — API & behavior

### 1) API endpoints (specify exact HTTP contracts)

#### A. Request presigned upload URL (backend)

-   **Endpoint:** `POST /api/v1/complaints/{complaint_id}/photos/presign`
-   **Auth:** Bearer service token (`BACKEND_SERVICE_TOKEN`) or a valid JWT for authenticated users.
-   **Request body (JSON):**

```json
{
    "filename": "IMG_001.jpg",
    "content_type": "image/jpeg",
    "content_length": 234567 // optional, for size enforcement
}
```

-   **Response (201):**

```json
{
    "upload_id": "<uuid>",
    "s3_key": "complaints/{complaint_id}/{photo_id}.jpg",
    "method": "PUT", // prefer PUT for bot uploads
    "url": "<presigned_put_url>",
    "fields": null, // only for POST form-based presign
    "expires_in": 300
}
```

**Behavior:**

-   Validate complaint existence and caller authorization.
-   Enforce max file size and allowed content types; reject if above threshold.
-   Generate a server-side `photo_id` (UUID) and S3 key pattern: `complaints/{complaint_id}/{photo_id}.jpg`.
-   Generate an S3 presigned PUT URL (prefer PUT) and return it along with `s3_key` and `upload_id`.
-   Optionally store a DB record for the in-progress upload (idempotency).
-   TTL: short-lived (recommend 5 minutes).

#### B. Confirm upload / metadata callback

Option 1 (recommended): Bot calls backend after successful PUT to confirm and provide metadata.

-   **Endpoint:** `POST /api/v1/complaints/{complaint_id}/photos/confirm`
-   **Auth:** service token
-   **Request body:**

```json
{
    "photo_id": "<uuid>",
    "s3_key": "complaints/...",
    "file_size": 234567,
    "content_type": "image/jpeg",
    "checksum": "<optional sha256>"
}
```

-   **Response:** `200` with stored photo metadata / DB record

Option 2: Rely on S3 event notification + worker to discover the new object and update DB (also required for processing if bot doesn't call confirm).

Both approaches can co-exist.

#### C. List photos, get photo metadata, delete photo endpoints

Keep or extend existing endpoints:

-   `GET /api/v1/complaints/{complaint_id}/photos` → list stored photo metadata
-   `GET /api/v1/complaints/{complaint_id}/photos/{photo_id}` → metadata + signed GET URL (or CloudFront URL)
-   `DELETE /api/v1/complaints/{complaint_id}/photos/{photo_id}` → delete object (remove S3 object and DB record)

For GET photo content: prefer returning a presigned GET URL (short TTL) or a CloudFront signed URL.

#### D. Health & admin endpoints

Ensure ability to check S3 connectivity and IAM permissions (e.g., `/admin/storage-health` returns bucket reachable + IAM policy effectiveness).

---

### 2) S3 design & policies

**Bucket(s):**

-   One bucket named by env: `S3_BUCKET` (example: `complaint-photos`).
-   Private by default (Block Public Access).
-   Use prefixes: `complaints/{complaint_id}/originals/` and `complaints/{complaint_id}/thumbnails/`.
-   Object naming: deterministic keys with `photo_id` UUIDs, e.g.:

    -   `complaints/{complaint_id}/{photo_id}.jpg`
    -   `complaints/{complaint_id}/{photo_id}_thumb.jpg`

**Server-side encryption:**

-   Use SSE-KMS for sensitive data (recommended) or SSE-S3 as minimal.
-   Provide KMS key creation sample in IaC.

**Lifecycle/retention:**

-   Move to Infrequent Access after 30 days, Glacier after 365 days (configurable).
-   Optional TTL purge for attachments older than retention policy (admin endpoint `/purge`).

**Bucket logging & audit:**

-   Enable S3 server access logging or S3 access logs to a dedicated logging bucket.

**CORS:**

-   If presigned POSTs are used from browsers, provide minimal CORS rules.

**CloudFront:**

-   Use CloudFront with an Origin Access Control (OAC) or Origin Access Identity (OAI) so CloudFront can fetch private S3 objects.
-   Use signed URLs or signed cookies to protect private content if necessary.
-   Configure caching and TTLs; set `Cache-Control` headers when writing objects.

---

### 3) IAM (least privilege)

**Backend role/policy** (able to presign and read/write for upload operations):

**Allowed actions (limited scope):**

-   `s3:PutObject` (for presigned PUT generation)
-   `s3:GetObject` (to validate/verify or for server-side operations)
-   `s3:DeleteObject` (for delete ops)
-   `s3:ListBucket` (if needed, limited to complaint prefixes)
-   `kms:Encrypt/Decrypt/GenerateDataKey` if using SSE-KMS on given KMS key ARN

Restrict resources to the bucket ARN and optionally to `arn:aws:s3:::complaint-photos/complaints/*`.

**Worker role (thumbnailer):**

-   `s3:GetObject`, `s3:PutObject` (for thumbnails prefix), and `kms` actions (if needed)

**Bot:**

-   Bot does not need AWS credentials; it uses presigned URLs.

Provide JSON examples of IAM policies for each role in the deliverables.

---

### 4) Processing architecture (workers)

**Trigger:**

-   Preferred: S3 event (PUT object created) → SNS or SQS (recommended: SQS queue) → worker (Celery or Lambda) polls queue
-   Alternative: Backend confirm endpoint triggers a background job queue (Celery) to process object.

**Worker responsibilities:**

-   Download object from S3 (use presigned GET or SDK with IAM role)
-   Validate image again (content-type/size/dimensions, virus scan)
-   Generate thumbnail(s) at configured sizes (e.g., 256px, 1024px)
-   Compress/optimize and write thumbnails to S3 `thumbnails/` prefix
-   Update DB record with thumbnail S3 keys and final metadata (width, height, final size)
-   Emit metrics and logs, and optionally send notification to WebSocket manager or webhook to the dashboard

**Implementation details:**

-   Use Pillow for image processing.
-   Use a lightweight virus scanning approach (ClamAV) if required; otherwise document limitations.
-   Ensure idempotency: worker must detect if thumbnail already exists (e.g., by DB row or S3 metadata).
-   Use retries, DLQ (dead-letter queue) for failures.

---

### 5) Database changes

Add or update `photos` table / SQLModel model to store:

-   `id` (UUID) — `photo_id`
-   `complaint_id` (FK)
-   `s3_key` (original)
-   `s3_thumbnail_key`
-   `file_name`
-   `mime_type`
-   `file_size` (original)
-   `width`, `height`
-   `storage_provider` (e.g., `s3`)
-   `created_at`, `processed_at`

Migration: create Alembic revision to add columns or table.

When migrating from local storage, supply a script to map existing local paths to S3 uploads (copy + DB update).

---

### 6) Security design & best practices

-   **Secrets:** Use AWS Secrets Manager / Parameter Store for production (do not store AWS keys in repo). Accept `.env` for local dev only.
-   Rotate service token and AWS keys regularly; use IAM roles for compute (no long-lived keys on hosts).
-   Use SSE-KMS for server-side encryption of objects.
-   Use HTTPS for all presigned URLs and enforce TLS.

**Presigned URLs must:**

-   Be short-lived (5 minutes for PUT upload; 1 hour or less for GET)
-   Bind to the intended `Content-Type` and `Content-Length` (generate presigned PUT with `Content-Type` constraint for added safety)

**Logging & monitoring:**

-   CloudWatch metrics and logs for Lambdas and workers
-   S3 access logs to track abnormal activity
-   Alarms on error rates and backpressure on queue

**Network:**

-   Use VPC endpoints (Gateway endpoint for S3) so traffic to S3 stays inside AWS network
-   Place workers/backends in private subnets; NAT for egress if needed

---

### 7) Local dev & testing strategy

-   Use MinIO for local S3-compatible testing and `moto` for unit tests that mock `boto3`.
-   Provide a `docker-compose` dev stack:
    -   Local FastAPI backend
    -   Redis (Celery)
    -   Celery worker
    -   MinIO server with matching bucket + credentials
    -   Optional: Localstack for broader AWS emulation

**Tests:**

-   Unit tests for presign endpoint (mock boto3)
-   Integration tests that use MinIO to verify presigned PUT flows

**E2E test that:**

1. Submits a complaint
2. Requests presigned URL
3. Uploads file to presigned URL
4. Confirms upload or waits for worker processing
5. Verifies database record and thumbnail presence

---

### 8) Infrastructure-as-Code (IaC)

Provide Terraform or CloudFormation templates to create:

-   S3 bucket with required policies, Block Public Access ON, lifecycle rules
-   CloudFront distribution with OAC/OAI, origins pointing to S3
-   KMS key (if SSE-KMS)
-   IAM roles & policies for backend, worker, Lambda
-   SQS queue & SNS topic for S3 event notifications
-   Optional: Lambda to process S3 events (if using serverless)

Include outputs that are easy to plug into backend config (bucket name, region, KMS key ARN, CloudFront domain).

---

### 9) CloudFront & serving strategy

-   For public content: allow CloudFront to cache and set TTLs; origin access via IAM.
-   For private content: use CloudFront signed URLs or signed cookies (CloudFront) or presigned S3 GET URLs.
-   If you use CloudFront, create Origin Access Control and restrict direct bucket access.

---

### 10) Migration plan from local file storage

Script to:

1. Read DB rows with local file paths (existing `file_url` values)
2. Upload each file to S3 at new key
3. Update DB `file_url` → `s3://bucket/key` (or canonical HTTP URL)
4. Mark as processed to trigger worker if thumbnails missing

Run migration in batches with retries and verification checksums.

---

### 11) Observability & SLOs

**Track:**

-   Upload successes/failures (backend metrics)
-   S3 `PutObject`/`DeleteObject` error counts
-   Worker processing duration
-   Thumbnail generation failures

**Define SLOs:** e.g., 99.9% upload success within 5 minutes, 95% processing within 2 minutes.

Alerts to Slack/email on repeated failures or DLQ items.

---

### 12) Cost & ops

-   Provide a rough cost model example (per GB/month, presigned PUT/GET request costs negligible but measure request count).
-   Recommend lifecycle rules to reduce cost (transition after 30/90/365 days).
-   Provide retention policies and an admin way to purge old files.

---

### 13) Acceptance criteria and testing checklist

-   Unit tests cover presign logic and input validation.
-   Integration test (MinIO) proves a full presigned PUT flow with confirm.
-   Worker test verifies thumbnail written to S3 and DB updated.
-   Security check: verify presigned URL cannot be used to overwrite other prefixes; IAM policy restricts writes to allowed prefixes.
-   Load test: simulate scaled uploads to prove backend is not proxying payloads (i.e., test many concurrent presign requests and many direct S3 PUTs).
-   Documentation: README with steps to provision infra, run locally, run tests, and deploy to staging.

---

### 14) Operational runbook

-   How to rotate keys, how to revoke a compromised S3 key, how to reissue service token, how to list/delete objects, how to run migration rollback.

**Implementation guidance & code-level detail (FastAPI + boto3 example instructions)**

Add new env variables (example names — ensure these are captured from the `.env` or secrets manager):

```text
STORAGE_PROVIDER=s3
S3_BUCKET
S3_REGION
S3_ENDPOINT (optional for non-AWS)
S3_USE_SSL=true
S3_ACCESS_KEY_ID / S3_SECRET_ACCESS_KEY (local dev only; in prod use IAM role)
S3_PRESIGN_EXPIRY_SECONDS_UPLOAD=300
S3_PRESIGN_EXPIRY_SECONDS_GET=3600
KMS_KEY_ID (optional)
```

**Backend presign implementation (outline):**

-   Use `boto3.client('s3')` and call `generate_presigned_url('put_object', Params={'Bucket':..., 'Key':..., 'ContentType': ...}, ExpiresIn=expiry)`
-   Or use `generate_presigned_post` for form-based uploads.
-   For additional security, set Conditions for Content-Length or enforce with Content-Type.

**Worker:**

-   Use Celery tasks triggered by either SQS/SNS push or backend enqueuing upon confirm endpoint.
-   Implement idempotent processing and atomic DB updates.

**DB:**

-   Add migration to create/alter `photos` table (SQLModel/Alembic).

---

### Deliverable format & repo layout

Agent B should produce a repo branch `feature/s3-uploads` containing:

-   `fastapi-backend/app/storage_s3.py` — S3 helper functions (presign, put/get, delete)
-   `fastapi-backend/app/photo_processing.py` — worker processing tasks
-   `fastapi-backend/app/routes/photos.py` — presign and confirm endpoints
-   `versions` — migration file(s)
-   `infra/terraform/` or `infra/cloudformation/` — IaC templates
-   `docker-compose.dev.yml` — MinIO, Redis, backend, worker, db, and test harness
-   `tests` — unit and integration tests
-   `docs/storage.md` — architecture doc + runbook
-   `README.md` — concise instructions for provisioning and running locally

Every code file should contain type hints, docstrings, and unit tests.

---

### Diagrams & flow

Agent B must include a Mermaid diagram showing:

```
Bot -> Backend presign -> S3 (PutObject via presigned URL) -> S3 Event -> SQS -> Worker -> S3 Thumbnails -> DB update -> Dashboard requests signed GET / CloudFront
```

Also include a sequence diagram showing exact HTTP calls and which service authenticates how.

---

### Security checklist (deliverable)

Validate and include:

-   Bucket policies JSON
-   IAM role JSON for backend, worker, and Lambda
-   KMS key policy (if used)
-   Example CloudFront OAC/OAI config and signed URL approach
-   Recommended rotation and secrets storage approach (AWS Secrets Manager or Parameter Store)

**Acceptance test to run locally (must be runnable by me)**

1. Start `docker-compose` dev (MinIO, Redis, DB, backend, worker).
2. Create a complaint via API.
3. Request presigned URL for that complaint.
4. Upload file to presigned URL using `curl --upload-file` or `httpie`.
5. Call confirm endpoint (or wait for worker) and assert the DB row is updated and thumbnail exists in MinIO.
6. Request GET photo metadata endpoint and receive a presigned GET URL that returns the image.

---

### Project timeline & staged milestones (high-level)

-   **Phase 1 (3–5 days):** Presign endpoint + basic S3 helper + DB migration + local MinIO dev stack + tests.
-   **Phase 2 (2–3 days):** Worker (Celery) + S3 event wiring + thumbnail generation + processing tests.
-   **Phase 3 (2 days):** IaC for S3, IAM, KMS, CloudFront + security review and policies.
-   **Phase 4 (1–2 days):** Migration script + load tests + runbook and docs.

Provide time estimates with assumptions: availability of AWS account, review cycles, and approvals.

---

### Extra instructions for Agent B

-   Use typed, well-documented code. Provide unit tests and integration tests.
-   Keep secrets out of repo; provide sample `.env.example` and instruct use of Secrets Manager for prod.
-   Provide a "how to deploy to staging" step list and a checklist for going to production (bucket policy review, key rotation, CloudFront TTLs, cost estimates).
-   If choosing serverless (Lambda) for processing, provide cost and scaling explanation vs Celery.
-   Provide migration script that runs safely and marks progress (idempotent, resume support).
-   Provide a final operations checklist (runbook) for on-call engineers.

---

### Acceptance & hand-off

Agent B must produce a pull request with:

-   All code and IaC templates
-   Tests passing locally (instructions to run)
-   Architecture doc + diagrams
-   A short video or step-by-step screenshots demonstrating a successful local E2E run (optional but preferred)

Supply a short handover note listing any manual steps required (e.g., create KMS key, run `terraform apply`, set service token in secrets manager, configure CloudFront).

---

### Example `.env.example`

```text
TELEGRAM_BOT_TOKEN="<redacted>"
DATABASE_URL="postgresql+psycopg2://cms_user:cms_user_password@localhost:5432/cms_db"
BACKEND_URL="http://localhost:8000"
BACKEND_SERVICE_TOKEN="<opaque-service-token>"
STORAGE_PROVIDER="s3"
S3_BUCKET="complaint-photos"
S3_REGION="us-east-1"
S3_ENDPOINT="https://s3.us-east-1.amazonaws.com"  # optional
S3_PRESIGN_EXPIRY_SECONDS_UPLOAD=300
S3_PRESIGN_EXPIRY_SECONDS_GET=3600
KMS_KEY_ID="<optional-kms-key-id>"
```

**Security note:** NEVER commit real S3 credentials or KMS keys to the repository. Use environment injection or secrets manager.

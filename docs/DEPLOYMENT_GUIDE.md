# Production Deployment Guide

This guide walks through deploying every component of the Telegram Complaint System (bot, backend, worker, dashboard, PostgreSQL, and S3/CloudFront) from scratch. Follow the sections in order; each step is self-contained so another engineer can reproduce the environment without additional clarifications.

---

## 1. Prerequisites

- AWS account with permissions to create S3, CloudFront, IAM, KMS, SQS, and Secrets Manager resources.
- Docker + Docker Compose v2 (for local validation).
- Terraform ≥ 1.6.
- Python 3.11 runtime (for bot + backend container build).
- Domain / SSL if you plan to expose the backend publicly (optional; can remain internal).
- Telegram Bot Token (via @BotFather).

---

## 2. Provision Cloud Infrastructure (Terraform)

1. Navigate to `infra/terraform`.
2. Create `terraform.tfvars` (replace values as needed):
   ```hcl
   environment    = "production"
   aws_region     = "us-east-1"
   s3_bucket_name = "prod-complaint-photos"
   ```
3. Initialize + apply:
   ```bash
   terraform init
   terraform apply
   ```
4. Record the outputs:
   - `s3_bucket_name`
   - `cloudfront_domain`
   - `kms_key_arn`
   - `sqs_queue_arn`

These values feed into backend/worker environment variables and IAM policies.

---

## 3. Configure Secrets

Use AWS Secrets Manager (or Parameter Store) for all sensitive values. Recommended secrets:

| Secret Name | Example Value |
| ----------- | ------------- |
| `/complaint/db_url` | `postgresql+psycopg2://cms_user:password@db-host:5432/cms_db` |
| `/complaint/redis_url` | `redis://cache-host:6379/0` |
| `/complaint/backend_service_token` | random 32+ byte string |
| `/complaint/telegram_bot_token` | from BotFather |

Grant ECS/EC2 roles access to these secrets only.

---

## 4. PostgreSQL Setup

1. Provision an RDS PostgreSQL instance (or Aurora compatible).
2. Create database `cms_db` and user `cms_user` with strong password.
3. Enable automated backups and Multi-AZ for production.
4. Allow inbound traffic only from application subnets/security groups.
5. Run migrations once containers are deployed (the backend container executes `alembic upgrade head` on start; ensure the DB is reachable).

---

## 5. Redis / Celery Broker

1. Deploy Amazon ElastiCache for Redis (cluster mode disabled is fine).
2. Restrict network access to your application subnets only.
3. Store the connection string (e.g., `redis://cache:6379/0`) in Secrets Manager.

---

## 6. Build & Publish Containers

From the project root:

```bash
docker build -t complaint-backend ./fastapi-backend
docker build -t complaint-worker ./fastapi-backend
```

Push to your registry of choice (ECR, Docker Hub, etc.). Tag images with version numbers (e.g., `complaint-backend:v1.0.0`).

---

## 7. Deploy Backend API (FastAPI)

1. Choose a runtime (ECS on Fargate, EC2 autoscaling group, or Kubernetes). Example ECS task definition environment variables:
   ```bash
   DATABASE_URL=secrets:/complaint/db_url
   REDIS_URL=secrets:/complaint/redis_url
   CELERY_BROKER_URL=secrets:/complaint/redis_url
   CELERY_RESULT_BACKEND=secrets:/complaint/redis_url
   STORAGE_PROVIDER=s3
   S3_BUCKET=<terraform output>
   S3_REGION=us-east-1
   KMS_KEY_ID=<kms arn>
   CLOUDFRONT_DOMAIN=<cloudfront domain>
   BACKEND_SERVICE_TOKEN=secrets:/complaint/backend_service_token
   APP_ENV=production
   ```
2. Point the service to your container image.
3. Expose port `8000` via an internal load balancer (public if necessary). Enforce HTTPS with ACM certificates.
4. Health checks: `/health` (GET) and `/metrics` for Prometheus scraping.

---

## 8. Deploy Celery Worker

Use the same container image but different command:

```
celery -A app.photo_processing.celery_app worker --loglevel=info
```

Environment variables mirror the backend (DB URL, Redis, S3 credentials). Ensure the worker IAM role includes SQS permissions if you later wire S3 events.

---

## 9. Static Dashboard Hosting

The HTML dashboard (`dashboard/`) can be hosted on:

- S3 static website behind CloudFront.
- Or served directly from the FastAPI backend (already mounted at `/dashboard`).

For standalone hosting:

1. Create a separate S3 bucket (public-read via CloudFront).
2. Upload `dashboard/*.html`, configure index/404 documents.
3. Deploy CloudFront distribution pointing to the bucket.

---

## 10. Telegram Bot Deployment

1. Provision a small VM or container (Docker recommended).
2. Install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
3. Define environment variables:
   ```bash
   TELEGRAM_BOT_TOKEN=secrets:/complaint/telegram_bot_token
   BACKEND_URL=https://api.example.com
   BACKEND_SERVICE_TOKEN=secrets:/complaint/backend_service_token
   ```
4. Run `python main.py`.
5. For production, use a process manager (systemd, supervisord) or container orchestrator (ECS/Kubernetes).

---

## 11. MinIO / Local Dev Setup

For local testing, `docker-compose.dev.yml` provisions MinIO, Postgres, Redis, backend, and worker. Ensure `.env` contains:

```
STORAGE_PROVIDER=s3
S3_BUCKET=complaint-photos
S3_REGION=us-east-1
S3_ENDPOINT=http://minio:9000
S3_USE_SSL=false
S3_ACCESS_KEY_ID=minioadmin
S3_SECRET_ACCESS_KEY=minioadmin
BACKEND_SERVICE_TOKEN=local-token
```

---

## 12. Environment Variable Reference

| Variable | Description |
| -------- | ----------- |
| `APP_ENV` | `production`, `staging`, etc. |
| `DATABASE_URL` | SQLAlchemy URL to PostgreSQL |
| `REDIS_URL` | Redis connection for Celery |
| `STORAGE_PROVIDER` | `s3` or `local` (dev fallback) |
| `S3_BUCKET`, `S3_REGION` | S3 settings |
| `S3_ENDPOINT`, `S3_USE_SSL` | Optional for MinIO/localstack |
| `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY` | Local credentials; use IAM roles in AWS |
| `S3_PRESIGN_EXPIRY_SECONDS_UPLOAD` | Default 300 seconds |
| `S3_PRESIGN_EXPIRY_SECONDS_GET` | Default 3600 seconds |
| `KMS_KEY_ID` | ARN of SSE-KMS key |
| `CLOUDFRONT_DOMAIN` | Domain for serving attachments |
| `BACKEND_SERVICE_TOKEN` | Shared secret for bot→backend auth |
| `TELEGRAM_BOT_TOKEN` | Bot token from BotFather |

---

## 13. Deployment Verification Checklist

1. `terraform apply` completed with no errors.
2. Backend `/health` returns `{"status":"healthy"}`.
3. `/api/v1/admin/storage-health` reports `status: ok`.
4. Celery worker logs show “ready” and can process dummy jobs.
5. Bot `/report` flow successfully uploads a photo, receives presigned URL, and metadata is stored (verify via `/api/v1/complaints/{id}`).
6. Dashboard displays thumbnails via CloudFront signed/presigned URLs.

---

## 14. Ongoing Operations

- **Monitoring**: scrape `/metrics` into Prometheus + configure alerts for high `upload_photo_failure_total`.
- **Logging**: send container logs to CloudWatch (ECS) or ELK.
- **Backups**: RDS automated backups + KMS key rotation.
- **Disaster Recovery**: restore DB snapshot, re-run `scripts/migrate_local_to_s3.py` only if legacy disk nodes were still in use.

---

## 15. Rollback Plan

1. Keep previous container images tagged (e.g., `v1.0.0`).
2. If S3/KMS changes caused issues, re-apply previous Terraform state (stored remotely).
3. Revert service token (Secrets Manager keeps versioned history).
4. Disable Celery worker if it misbehaves; uploads still work (thumbnails delayed).

---

With this guide, another engineer can provision infrastructure, deploy components, and validate end-to-end functionality without referencing additional documents.


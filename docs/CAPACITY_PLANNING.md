# Capacity Planning & Load Testing Report

**Date:** 2025-11-24
**Version:** 1.1

## 1. Load Test Results (Baseline)

### Test Configuration
- **Tool:** Locust
- **Users:** 10 concurrent users
- **Duration:** 10 seconds
- **Ramp-up:** 2 users/sec
- **Host:** Localhost (Development Environment)

### Performance Metrics
| Endpoint | Requests | Failure Rate | Avg Response Time (ms) | Min (ms) | Max (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `POST /auth/login` | 5 | 0% | ~2ms | 1ms | 4ms |
| `POST /auth/register` | 5 | 0% | ~16ms | 6ms | 60ms |
| `GET /api/v1/complaints` | 4 | 0% | ~2ms | 1ms | 2ms |
| `GET /metrics` | 3 | 0% | ~8ms | 2ms | 21ms |

### Observations
- **Stability:** The system handled 10 concurrent users with **0% failure rate**.
- **Latency:** Response times are extremely low (<20ms avg) for the local environment.
- **Throughput:** The system processed ~4 requests/second without saturation.

## 2. Scaling Recommendations

### Database (PostgreSQL)
- **Current:** Single instance (Local/Docker).
- **Recommendation:** For production with >500 students, use a managed PostgreSQL instance (AWS RDS / DigitalOcean Managed DB) with at least 2GB RAM and 1 vCPU. Connection pooling (PgBouncer) is recommended if concurrent connections exceed 100.

### Backend (FastAPI)
- **Current:** Single worker (Uvicorn).
- **Recommendation:** Run with `gunicorn -w 4 -k uvicorn.workers.UvicornWorker` to utilize multiple cores.
- **Horizontal Scaling:** The stateless nature of the API allows adding more container replicas behind a load balancer (Nginx/AWS ALB).

### Storage (S3)
- **Current:** Local/S3.
- **Recommendation:** Ensure S3 bucket is in the same region as the backend to minimize latency for photo uploads.

## 3. Future Load Testing Goals
- **Target:** Simulate 50-100 concurrent users (approx. 10% of hostel population active simultaneously).
- **Scenario:** Heavy photo upload traffic (mixed read/write).
- **Success Criteria:** 95th percentile response time < 500ms.

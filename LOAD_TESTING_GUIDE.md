# Load Testing Guide

## Overview
This document provides instructions for load testing the Complaint Management System and capacity planning recommendations.

## Load Testing Tools

### Locust (Recommended)
Locust is a Python-based load testing framework that allows you to define user behavior and simulate high traffic.

### Installation
```bash
pip install locust
```

### Running Load Tests

#### Basic Test
```bash
cd load_tests
locust -f test_complaints_load.py --host=http://localhost:8000
```

Then open `http://localhost:8089` in your browser to access the Locust web interface.

#### Headless Test (for CI)
```bash
locust -f test_complaints_load.py --host=http://localhost:8000 \
    --headless -u 100 -r 10 -t 60s --html=report.html
```

Where:
- `-u 100`: 100 concurrent users
- `-r 10`: Spawn rate of 10 users per second
- `-t 60s`: Run for 60 seconds
- `--html=report.html`: Generate HTML report

## Test Scenarios

### 1. Normal Load
- **Users**: 50 concurrent users
- **Scenario**: Mixed complaint operations (list, view, update)
- **Expected**: 200 OK responses, < 500ms latency

### 2. High Load
- **Users**: 200 concurrent users
- **Scenario**: Heavy complaint submission and listing
- **Expected**: 200 OK responses, < 1s latency

### 3. Stress Test
- **Users**: 500 concurrent users
- **Scenario**: Maximum load
- **Expected**: Some 429 (rate limit) responses acceptable, graceful degradation

## Performance Benchmarks

### Target Metrics (Single Instance)
- **Complaint Submission**: < 300ms
- **Complaint Listing (20 items)**: < 200ms
- **Photo Upload**: < 2s
- **Status Update**: < 150ms
- **WebSocket Connection**: < 100ms

### Capacity Estimates

#### Resource Requirements (Per Instance)
- **CPU**: 2 cores minimum, 4 cores recommended
- **RAM**: 4GB minimum, 8GB recommended
- **Database**: 50-100 connections maximum
- **WebSocket**: 500 concurrent connections maximum

#### Scaling Limits
- **Single Instance**: Up to 1000 requests/minute
- **Horizontal Scaling**: Add instances behind load balancer
- **Database Scaling**: Consider read replicas for high read traffic
- **Storage**: S3/MinIO scales horizontally

## Scaling Recommendations

### Vertical Scaling
Increase server resources:
- Add more CPU cores
- Increase RAM
- Use faster storage (SSD)

### Horizontal Scaling
Run multiple backend instances:
- Use load balancer (nginx, HAProxy)
- Database connection pooling
- Redis for shared session state
- WebSocket sticky sessions

### Database Optimization
- **Connection Pooling**: Set max_connections based on load
- **Read Replicas**: Offload read traffic
- **Indexing**: Ensure proper indexes on frequently queried columns
- **Query Optimization**: Monitor slow queries

### Caching Strategy
- **Redis Cache**: Cache frequently accessed complaints
- **CDN**: Serve static assets (dashboard HTML/CSS/JS)
- **Database Query Cache**: Cache repeated queries

## Monitoring During Load Tests

### Metrics to Monitor
1. **Response Times** (p50, p95, p99)
2. **Error Rates** (4xx, 5xx responses)
3. **Throughput** (requests per second)
4. **Database Connections** (active/idle)
5. **Memory Usage** (RSS, heap)
6. **CPU Usage** (per core)

### Prometheus Metrics
Access metrics endpoint:
```bash
curl http://localhost:8000/metrics
```

Key metrics:
- `http_requests_total`: Total HTTP requests
- `http_request_duration_seconds`: Request latency
- `active_complaints_total`: Active complaints by status
- `websocket_connections_active`: Active WebSocket connections

## Load Testing Checklist

- [ ] Run normal load test (50 users)
- [ ] Run high load test (200 users)
- [ ] Run stress test (500 users)
- [ ] Monitor database performance
- [ ] Monitor memory usage
- [ ] Monitor CPU usage
- [ ] Check for memory leaks
- [ ] Verify no data corruption
- [ ] Test with realistic data volumes
- [ ] Test recovery after high load

## Results Interpretation

### Healthy System
- Response times within target metrics
- Error rate < 1%
- No memory leaks observed
- Database performance stable
- No connection pool exhaustion

### System Under Stress
- Response times increase gradually
- Error rate 1-5% (acceptable)
- Memory usage stabilizes
- Graceful degradation

### System Overload
- Response times spike
- Error rate > 5%
- Memory exhaustion
- Database connection issues
- Timeouts and crashes

## Capacity Planning Recommendations

### Development Environment
- **Single instance**: Sufficient for local development and testing
- **Database**: SQLite or small Postgres instance

### Staging Environment
- **2 backend instances**: For redundancy
- **Postgres**: 50-100 max connections
- **Load balancer**: Simple nginx configuration

### Production Environment
- **3-5 backend instances**: Based on expected load
- **Postgres**: 200-500 max connections with connection pooling
- **Load balancer**: HA setup with health checks
- **Redis**: For caching and session management
- **Monitoring**: Prometheus + Grafana
- **Alerting**: Configure alerts for error rates and latency

### High-Traffic Production
- **10+ backend instances**: Auto-scaling based on CPU/memory
- **Postgres cluster**: Primary + read replicas
- **CDN**: For static assets
- **Edge caching**: Redis/CDN cache layer
- **Database sharding**: Consider if data volume exceeds capacity

## Continuous Load Testing

### CI/CD Integration
Add load tests to CI pipeline:
```yaml
- name: Run Load Tests
  run: |
    locust -f load_tests/test_complaints_load.py \
        --host=http://localhost:8000 \
        --headless -u 50 -r 5 -t 30s
```

### Scheduled Testing
Run load tests weekly:
- Verify performance hasn't degraded
- Check for regression
- Plan capacity expansion

## Notes
- Always run load tests against a staging environment
- Never run load tests against production during business hours
- Monitor closely for resource exhaustion
- Have rollback plan ready

Document version: 2025-10-21


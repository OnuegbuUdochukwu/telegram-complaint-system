# Capacity Planning Report

## System Overview
The Complaint Management System handles complaint submission, assignment, tracking, and resolution for hostel maintenance.

## Current Architecture
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL (or SQLite for development)
- **Storage**: S3/MinIO for photos
- **Real-time**: WebSocket connections
- **Authentication**: JWT-based
- **Monitoring**: Prometheus metrics

## Performance Characteristics

### Typical Workload
- **Complaint Submissions**: 10-50 per day
- **Active Complaints**: 50-200
- **Concurrent Users**: 5-20 staff members
- **Photo Uploads**: 20-100 per day
- **Real-time Updates**: 5-10 per minute

### Peak Workload
- **Complaint Submissions**: 100-200 per day
- **Active Complaints**: 500-1000
- **Concurrent Users**: 50-100 staff
- **Photo Uploads**: 200-500 per day
- **Real-time Updates**: 50-100 per minute

## Resource Requirements

### Development Environment
| Resource | Requirement | Notes |
|----------|------------|-------|
| CPU | 1 core | Sufficient for development |
| RAM | 2GB | With SQLite database |
| Storage | 10GB | Including test data and photos |
| Database | SQLite | For local development |

### Staging Environment
| Resource | Requirement | Notes |
|----------|------------|-------|
| CPU | 2 cores | Peak load handling |
| RAM | 4GB | With connection pooling |
| Storage | 50GB | Including photos and backups |
| Database | PostgreSQL 15 | 50-100 connections |
| Load Balancer | 1 instance | Simple nginx setup |

### Production Environment (Typical Load)
| Resource | Requirement | Notes |
|----------|------------|-------|
| CPU | 4 cores | Per backend instance |
| RAM | 8GB | Per backend instance |
| Storage | 200GB | Including photos and backups |
| Database | PostgreSQL 15 | 200-500 connections |
| Redis | 2GB RAM | For caching and sessions |
| Load Balancer | 2 instances (HA) | Redundant setup |

### Production Environment (High Load)
| Resource | Requirement | Notes |
|----------|------------|-------|
| CPU | 8 cores | Per backend instance |
| RAM | 16GB | Per backend instance |
| Storage | 500GB | With replication |
| Database | PostgreSQL cluster | Primary + 2 read replicas |
| Redis | 4GB RAM | Redis Cluster |
| Load Balancer | 2 instances (HA) | Auto-scaling enabled |
| CDN | Optional | For static assets |

## Scalability Limits

### Single Instance Limits
- **HTTP Requests**: ~1000 req/min
- **WebSocket Connections**: ~500 concurrent
- **Database Connections**: ~100 max
- **Photo Storage**: Depends on S3/MinIO capacity
- **Active Complaints**: ~10,000 (estimated)

### Bottlenecks
1. **Database Connections**: PostgreSQL connection pool
2. **WebSocket Connections**: Memory per connection
3. **Photo Upload**: S3 API rate limits
4. **CPU**: Image processing (thumbnailing)

## Scaling Strategies

### Vertical Scaling
**When to use**: Low to moderate load increase
- Increase CPU cores
- Increase RAM
- Use faster storage

**Limitations**: 
- Single point of failure
- Cost increases linearly
- Hardware limitations

### Horizontal Scaling
**When to use**: High load, redundancy required
- Add multiple backend instances
- Load balancer distribution
- Database read replicas

**Configuration**:
- Backend: 3-5 instances behind load balancer
- Database: Primary + 2 read replicas
- Redis: Cluster mode
- WebSocket: Sticky sessions required

## Capacity Estimates by User Volume

### Small Deployment (50-100 users)
- **Backend Instances**: 2
- **Database**: Single PostgreSQL instance
- **Storage**: 100GB
- **Estimated Cost**: $200-300/month

### Medium Deployment (200-500 users)
- **Backend Instances**: 3-5
- **Database**: Primary + 1 read replica
- **Storage**: 500GB
- **Estimated Cost**: $500-800/month

### Large Deployment (1000+ users)
- **Backend Instances**: 10+ (auto-scaling)
- **Database**: Primary + 2 read replicas
- **Storage**: 1TB+
- **Estimated Cost**: $1500-3000/month

## Monitoring and Alerting

### Key Metrics to Monitor
1. **Request Rate**: Requests per second
2. **Response Time**: P50, P95, P99 latencies
3. **Error Rate**: 4xx and 5xx responses
4. **Database**: Connection pool usage, slow queries
5. **Memory**: RAM usage, potential leaks
6. **CPU**: Peak usage patterns
7. **Storage**: Disk space, S3 bucket size
8. **WebSocket**: Active connections, message rate

### Alerting Thresholds
- **Response Time P95**: > 2 seconds
- **Error Rate**: > 1%
- **Database Connections**: > 80% pool used
- **Memory**: > 85% usage
- **Disk Space**: < 10% free

## Capacity Planning Recommendations

### Phase 1: MVP (Current)
- Single backend instance
- PostgreSQL database
- Local file storage or S3
- Suitable for: Development and initial production

### Phase 2: Production Ready
- 2-3 backend instances
- PostgreSQL with connection pooling
- S3 storage with backups
- Load balancer
- Monitoring setup
- Suitable for: 100-500 daily users

### Phase 3: Scale Out
- Auto-scaling backend (5-10 instances)
- PostgreSQL cluster (primary + replicas)
- Redis cache layer
- CDN for static assets
- Advanced monitoring
- Suitable for: 500+ daily users

### Phase 4: High Availability
- Multi-region deployment
- Database replication across regions
- Global CDN
- Auto-failover
- Disaster recovery
- Suitable for: Critical production, 1000+ users

## Cost Optimization

### Cost Drivers
1. **Compute**: Backend instances
2. **Database**: PostgreSQL licenses, storage
3. **Storage**: S3/object storage for photos
4. **Bandwidth**: Data transfer costs
5. **Monitoring**: Logging and metrics

### Optimization Strategies
1. **Right-size instances**: Don't over-provision
2. **Use autoscaling**: Scale down during off-hours
3. **Cache aggressively**: Reduce database load
4. **Compress photos**: Reduce storage and bandwidth
5. **Archive old data**: Move to cheaper storage tiers

## Testing Capacity

### Load Testing Results
- **Baseline**: 50 concurrent users
- **High Load**: 200 concurrent users
- **Stress Test**: 500 concurrent users

### Performance Targets
- Complaint submission: < 300ms
- Complaint listing: < 200ms
- Photo upload: < 2s
- Status update: < 150ms
- 99% uptime SLA

## Future Considerations

### Database Sharding
If complaint volume exceeds 100,000:
- Shard by hostel
- Shard by date range
- Consider NoSQL for certain data

### Microservices
If system needs to scale beyond monolith:
- Split photo service
- Split notification service
- Split analytics service

### Geographic Distribution
If users span multiple regions:
- Deploy in multiple regions
- Use CDN for low latency
- Sync critical data across regions

Document version: 2025-10-21


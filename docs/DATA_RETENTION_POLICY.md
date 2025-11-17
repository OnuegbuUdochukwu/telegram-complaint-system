# Data Retention Policy

## Overview
This document outlines the data retention policy for the Complaint Management System. This policy defines how long different types of data are retained and how old data is purged.

## Retention Periods

### Complaints
- **Active complaints (status: reported, in_progress)**: Retained indefinitely until resolved
- **Resolved complaints**: Retained for 90 days after resolution
- **Closed complaints**: Retained for 30 days after closure
- **Rejected complaints**: Retained for 7 days after rejection

### Photos and Media
- **Attached to resolved complaints**: Retained until complaint is purged
- **Attached to closed complaints**: Retained until complaint is purged
- **Orphaned photos**: Retained for 7 days (complaint deleted but photos remain)

### Audit Logs
- **Assignment audit logs**: Retained for 1 year after complaint resolution
- **User activity logs**: Retained for 90 days

### User Data
- **Reporter data (telegram_user_id)**: Retained as long as associated complaints exist
- **Porter data**: Retained while porter is active
- **Inactive porters**: Data retained for 1 year after deactivation

## Purge Procedure

The system provides an admin-only purge endpoint that automatically removes data older than the retention period.

### Manual Purge Endpoint
- **Endpoint**: `DELETE /api/v1/admin/purge`
- **Authorization**: Admin only
- **Query Parameters**:
  - `complaint_status`: Optional filter for specific status types
  - `days_old`: Optional override for retention period (defaults to policy)
  
### Automatic Purge (Future Implementation)
- Cron job to run daily purge
- Configurable via environment variables
- Logs all purged records for audit

## Privacy Considerations

1. **Data Minimization**: Only data necessary for complaint resolution is stored
2. **Right to Deletion**: Users can request data deletion via support channels
3. **Anonymization**: Consider anonymizing old complaint data instead of deletion
4. **Backup Retention**: Backup data follows same retention policy

## Compliance

This policy complies with:
- General Data Protection Regulation (GDPR) - Right to erasure (Article 17)
- Local data protection laws

## Documentation
Last updated: 2025-10-21


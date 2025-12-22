# ArcticCodex Audit and Compliance Guide

## Overview

This guide explains the audit system in ArcticCodex, including event types, hash-chain verification, compliance requirements, and analysis procedures.

## Audit Events

### Event Types

ArcticCodex records 10 types of audit events:

| Event Type | Description | Example | Logged When |
|-----------|-------------|---------|------------|
| **request** | Incoming API request | GET /api/audit/events | API handler starts |
| **response** | Outgoing API response | HTTP 200 with data | API handler completes |
| **error** | API error response | HTTP 500, 403, 400 | Error occurs in handler |
| **auth** | Authentication event | Login, logout, register | User authenticates |
| **unauthorized** | Permission denied | 403 Forbidden | User lacks permission |
| **tool** | Tool execution | Agent runs python tool | Tool is executed |
| **approval** | Policy approval | Admin approves tool | Approval workflow |
| **policy** | Configuration change | Create tool policy | Policy is modified |
| **phi** | PII/PHI detected | SSN in response | Sensitive data detected |
| **cost** | Cost tracking | Query costs $0.15 | Cost computed |

### Event Structure

Every audit event contains:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "org_id": "550e8400-e29b-41d4-a716-446655440001",
  "event_type": "request",
  "timestamp": "2024-01-15T10:30:45.123Z",
  "run_id": "550e8400-e29b-41d4-a716-446655440002",
  "actor": "user@example.com",
  "payload": {
    "method": "GET",
    "path": "/api/agent/run",
    "status": 200,
    "duration_ms": 1234,
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.1"
  },
  "event_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6...",
  "prev_hash": "0f1e2d3c4b5a6978e8d7c6b5a4938271..."
}
```

### Timestamp Format

All timestamps in UTC (ISO 8601):
```
2024-01-15T10:30:45.123Z
↑     ↑   ↑  ↑  ↑  ↑    ↑
Year  Mo Day Hr Min Sec  Milliseconds + Z (UTC)
```

## Audit Data Collection

### What Gets Logged

**Always Logged:**
- Every API request (method, path, status, duration)
- Authentication events (login, logout, register)
- Permission denied attempts
- Policy changes
- Tool executions
- Cost transactions

**Never Logged:**
- Request/response bodies (too large, contains sensitive data)
- API key values (only prefix)
- Password values
- JWT tokens

**Selectively Logged:**
- PHI events (only if configured, configurable via detection rules)
- Tool output (only errors)

### Data Retention

Default retention policy:
- **Retention Period**: 90 days (configurable via `AUDIT_RETENTION_DAYS`)
- **Archival**: Manual export to cold storage
- **Deletion**: Automatic after retention period (soft delete with is_archived flag)
- **Compliance**: For HIPAA, set to 2,190 days (6 years)

```env
# In .env
AUDIT_RETENTION_DAYS=90        # Standard: 90 days
# For healthcare: 2190 days
# For finance: 2555 days (7 years)
```

## Hash-Chain Verification

### Purpose

Hash-chain provides cryptographic proof that audit events have not been tampered with. Each event links to the previous event via SHA256 hash.

### Hash Computation

```python
import hashlib
import json

def compute_event_hash(event):
    """Compute SHA256 hash of audit event."""
    # Include all relevant fields
    data = {
        'event_type': event.event_type,
        'timestamp': event.timestamp.isoformat(),
        'actor': event.actor,
        'run_id': event.run_id,
        'payload': event.payload,
        'prev_hash': event.prev_hash  # Link to previous event
    }
    
    # Serialize to JSON (deterministic)
    json_str = json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    # Compute SHA256
    return hashlib.sha256(json_str.encode()).hexdigest()
```

### Chain Structure

**Genesis Event** (first event):
```
Event 1:
  event_hash = sha256(event1_data + "0" * 64)
  prev_hash = "0" * 64
```

**Linked Events:**
```
Event 2:
  event_hash = sha256(event2_data + event1.event_hash)
  prev_hash = event1.event_hash

Event 3:
  event_hash = sha256(event3_data + event2.event_hash)
  prev_hash = event2.event_hash
```

### Verification Algorithm

```python
def verify_audit_chain(events: List[AuditEvent]) -> bool:
    """Verify hash-chain integrity of events."""
    
    for i, event in enumerate(events):
        # Check prev_hash links to previous event
        if i == 0:
            expected_prev_hash = "0" * 64
        else:
            expected_prev_hash = events[i-1].event_hash
        
        if event.prev_hash != expected_prev_hash:
            print(f"Chain broken at event {i}")
            return False
        
        # Compute expected hash
        expected_hash = compute_event_hash(event)
        
        if event.event_hash != expected_hash:
            print(f"Hash mismatch at event {i}")
            print(f"  Expected: {expected_hash}")
            print(f"  Actual:   {event.event_hash}")
            return False
    
    return True
```

### Tampering Detection

If event is modified:
- Event's `event_hash` no longer matches computed hash
- Next event's `prev_hash` no longer matches modified event's hash
- Chain breaks, tampering is immediately detected

**Example:**
```
Original:
  Event 1 (hash=abc123) -> Event 2 (prev=abc123, hash=def456) -> Event 3 (prev=def456)

Tampered (Event 2 modified):
  Event 1 (hash=abc123) -> Event 2 (prev=abc123, hash=CHANGED) -> Event 3 (prev=def456)
  ❌ Event 2's hash no longer matches computed hash
  ❌ Event 3's prev_hash (def456) doesn't match Event 2's new hash
  ✓ Tampering detected!
```

## Querying Audit Events

### Via Studio UI

**Filter by Event Type:**
1. Go to **Audit** tab
2. Select **Event Type** dropdown
3. Choose: request, response, error, auth, unauthorized, tool, approval, policy, phi, cost
4. Click **Apply**

**Filter by Actor:**
1. Enter user email or API key prefix
2. View all events from that user/key
3. Useful for finding specific user's activities

**Filter by Date Range:**
1. Select **Start Date** and **End Date**
2. View events in time window
3. Useful for incident investigation

**Filter by Run ID:**
1. Enter specific run UUID
2. View all events related to single query
3. Trace complete execution path

### Via API

**Basic Query:**
```bash
curl "http://localhost:8000/api/audit/events" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "events": [
    {
      "id": "event-uuid",
      "event_type": "request",
      "timestamp": "2024-01-15T10:30:45Z",
      "actor": "user@example.com",
      "payload": {...}
    }
  ],
  "total": 1234,
  "page": 1,
  "limit": 100
}
```

**Filter by Event Type:**
```bash
curl "http://localhost:8000/api/audit/events?event_type=error" \
  -H "Authorization: Bearer $TOKEN"
```

**Filter by Actor:**
```bash
curl "http://localhost:8000/api/audit/events?actor=user@example.com" \
  -H "Authorization: Bearer $TOKEN"
```

**Filter by Date Range:**
```bash
curl "http://localhost:8000/api/audit/events?from=2024-01-01&to=2024-01-31" \
  -H "Authorization: Bearer $TOKEN"
```

**Filter by Run ID:**
```bash
curl "http://localhost:8000/api/audit/events?run_id=run-uuid" \
  -H "Authorization: Bearer $TOKEN"
```

**Pagination:**
```bash
curl "http://localhost:8000/api/audit/events?limit=50&offset=100" \
  -H "Authorization: Bearer $TOKEN"
```

### Via Direct SQL

Connect to database and query:

```sql
-- All error events
SELECT * FROM audit_events 
WHERE event_type = 'error' 
ORDER BY timestamp DESC LIMIT 100;

-- All events from user in last 24 hours
SELECT * FROM audit_events 
WHERE actor = 'user@example.com' 
  AND timestamp > now() - interval '24 hours'
ORDER BY timestamp DESC;

-- Count by event type
SELECT event_type, COUNT(*) 
FROM audit_events 
GROUP BY event_type 
ORDER BY COUNT DESC;

-- Failed auth attempts
SELECT actor, COUNT(*) as attempt_count 
FROM audit_events 
WHERE event_type = 'error' 
  AND payload->>'path' LIKE '/api/auth/login%'
  AND timestamp > now() - interval '1 hour'
GROUP BY actor 
HAVING COUNT(*) > 5;
```

## Compliance Reporting

### HIPAA Compliance

**HIPAA Requirements:**
- Access controls (RBAC) ✓
- Audit logging (100% events logged) ✓
- Integrity controls (hash-chain verification) ✓
- Encryption in transit (TLS/HTTPS) ⚠️ Must configure at load balancer
- Encryption at rest (pgcrypto) ⚠️ Must enable in Supabase
- Data retention (6 years for healthcare) ⚠️ Must set `AUDIT_RETENTION_DAYS=2190`

**HIPAA Audit Report:**

```bash
# Export audit for compliance review
curl "http://localhost:8000/api/audit/export?from=2024-01-01&to=2024-12-31" \
  -H "Authorization: Bearer $TOKEN" \
  --output hipaa_audit_2024.zip

# Verify hash-chain integrity
python verify_audit_chain.py hipaa_audit_2024.zip

# Output:
# ✓ Hash chain integrity verified
# ✓ 123,456 events verified
# ✓ No tampering detected
# ✓ Chain spans from 2024-01-01 to 2024-12-31
```

### SOC 2 Compliance

**SOC 2 Trust Service Criteria:**

| Criterion | Requirement | Evidence |
|-----------|-------------|----------|
| **CC6.1** | Access controls | RBAC, user:manage permission, org isolation |
| **CC7.2** | System monitoring | Audit events on all requests |
| **CC9.2** | Change management | Audit events on policy changes |
| **A1.2** | Availability | Uptime monitoring, incident response |

**SOC 2 Audit Trail:**

```bash
# Access control changes
curl "http://localhost:8000/api/audit/events?event_type=policy" \
  -H "Authorization: Bearer $TOKEN"

# User management changes
curl "http://localhost:8000/api/audit/events?actor=admin@example.com" \
  -H "Authorization: Bearer $TOKEN"

# Unauthorized access attempts
curl "http://localhost:8000/api/audit/events?event_type=unauthorized" \
  -H "Authorization: Bearer $TOKEN"
```

### PCI DSS Compliance

**PCI DSS Requirements:**
- Audit logging (requirement 10.2) ✓
- Audit log retention (requirement 10.7) ✓
- Log integrity protection (requirement 10.5) ✓

**PCI DSS Audit Report:**

```bash
# Export full audit trail
curl "http://localhost:8000/api/audit/export" \
  -H "Authorization: Bearer $TOKEN" \
  --output pci_audit.zip

# Verify integrity
python verify_audit_chain.py pci_audit.zip

# Generate compliance report
python generate_pci_report.py pci_audit.zip compliance_2024.pdf
```

## Analysis and Investigation

### Incident Investigation

**Find root cause of incident:**

```bash
# 1. Identify issue time window
# 2. Get events from that time window
curl "http://localhost:8000/api/audit/events?from=2024-01-15T10:00:00Z&to=2024-01-15T11:00:00Z" \
  -H "Authorization: Bearer $TOKEN"

# 3. Look for error events
curl "http://localhost:8000/api/audit/events?event_type=error&from=2024-01-15T10:00:00Z&to=2024-01-15T11:00:00Z" \
  -H "Authorization: Bearer $TOKEN"

# 4. Trace run execution
curl "http://localhost:8000/api/audit/events?run_id=problem-run-uuid" \
  -H "Authorization: Bearer $TOKEN"

# 5. Check user activity
curl "http://localhost:8000/api/audit/events?actor=user@example.com&from=2024-01-15T09:00:00Z&to=2024-01-15T12:00:00Z" \
  -H "Authorization: Bearer $TOKEN"
```

### Security Audit

**Find suspicious activity:**

```bash
# Failed login attempts
SELECT actor, COUNT(*) 
FROM audit_events 
WHERE event_type = 'error' 
  AND payload->>'path' LIKE '/api/auth/login%'
  AND timestamp > now() - interval '7 days'
GROUP BY actor 
HAVING COUNT(*) > 10;

# Unauthorized access attempts
SELECT actor, COUNT(*) 
FROM audit_events 
WHERE event_type = 'unauthorized'
  AND timestamp > now() - interval '7 days'
GROUP BY actor;

# Admin activities
SELECT timestamp, actor, payload 
FROM audit_events 
WHERE actor IN (SELECT email FROM users WHERE role = 'admin')
  AND event_type IN ('policy', 'auth')
  AND timestamp > now() - interval '30 days'
ORDER BY timestamp DESC;

# API key usage
SELECT actor, COUNT(*) 
FROM audit_events 
WHERE actor LIKE 'api_key_%'
  AND timestamp > now() - interval '7 days'
GROUP BY actor;
```

### Performance Analysis

**Find slow queries:**

```bash
# Average request duration by endpoint
SELECT 
  payload->>'path' as endpoint,
  COUNT(*) as request_count,
  AVG((payload->>'duration_ms')::int) as avg_duration_ms,
  MAX((payload->>'duration_ms')::int) as max_duration_ms
FROM audit_events
WHERE event_type = 'request'
  AND timestamp > now() - interval '7 days'
GROUP BY payload->>'path'
ORDER BY avg_duration_ms DESC;
```

### Cost Analysis

**Find expensive queries:**

```bash
-- Query cost by user
SELECT 
  actor,
  COUNT(*) as query_count,
  SUM((payload->>'cost')::float) as total_cost
FROM audit_events
WHERE event_type = 'cost'
  AND timestamp > now() - interval '30 days'
GROUP BY actor
ORDER BY total_cost DESC;

-- Cost by time of day
SELECT 
  DATE_TRUNC('hour', timestamp) as hour,
  SUM((payload->>'cost')::float) as hourly_cost
FROM audit_events
WHERE event_type = 'cost'
GROUP BY DATE_TRUNC('hour', timestamp)
ORDER BY hourly_cost DESC;
```

## Export Format

### Export Structure

```
audit_export.zip
├── metadata.json
├── request_events.csv
├── response_events.csv
├── error_events.csv
├── auth_events.csv
├── unauthorized_events.csv
├── tool_events.csv
├── approval_events.csv
├── policy_events.csv
├── phi_events.csv
├── cost_events.csv
└── hash_chain_verification.txt
```

### Metadata File

```json
{
  "export_date": "2024-01-31T15:30:00Z",
  "organization": "My Organization",
  "org_id": "org-uuid",
  "from_date": "2024-01-01",
  "to_date": "2024-01-31",
  "total_events": 12345,
  "events_by_type": {
    "request": 5000,
    "response": 4500,
    "error": 500,
    "auth": 200,
    "unauthorized": 100,
    "tool": 50,
    "approval": 10,
    "policy": 5,
    "phi": 20,
    "cost": 1060
  },
  "hash_chain_verified": true
}
```

### CSV Format

Each CSV contains relevant event data:

```csv
event_id,timestamp,actor,payload
550e8400-e29b-41d4-a716-446655440000,2024-01-15T10:30:45Z,user@example.com,"{""method"":""GET"",""path"":""/api/audit/events"",""status"":200}"
```

### Hash Chain Verification

```
ArcticCodex Audit Hash Chain Verification
==========================================

Organization: My Organization (org-uuid)
Export Date: 2024-01-31T15:30:00Z
Total Events: 12345

Hash Chain Status: ✓ VERIFIED
  ✓ All 12345 events verified
  ✓ No gaps in chain
  ✓ No tampering detected
  ✓ Genesis event found
  ✓ Chain integrity: INTACT

Verification Details:
  First event hash:  0f1e2d3c4b5a6978...
  Last event hash:   a1b2c3d4e5f6g7h8...
  Chain length:      12345 events
  Date range:        2024-01-01 to 2024-01-31
  
Conclusion: Audit trail is authentic and has not been tampered with.
```

## Best Practices

### Audit Review Cadence

- **Daily**: Check for errors and unauthorized access
- **Weekly**: Review admin activities and policy changes
- **Monthly**: Full audit trail export for compliance
- **Quarterly**: Security audit with hash-chain verification
- **Annually**: Third-party audit for compliance certifications

### Retention Strategy

**Development Environment:**
- Retention: 7 days
- Archive: No
- Purpose: Debugging

**Staging Environment:**
- Retention: 30 days
- Archive: Weekly to S3
- Purpose: Testing

**Production Environment:**
- Retention: 90 days (minimum)
- Archive: Monthly to long-term storage
- Purpose: Compliance and incident investigation

### Alerting

Set up alerts for:

```sql
-- Failed login attempts (>10 in 1 hour)
SELECT COUNT(*) as failed_logins
FROM audit_events
WHERE event_type = 'error'
  AND payload->>'path' LIKE '%/login%'
  AND timestamp > now() - interval '1 hour'
GROUP BY actor
HAVING COUNT(*) > 10;

-- Unauthorized access attempts (any)
SELECT COUNT(*) as unauthorized
FROM audit_events
WHERE event_type = 'unauthorized'
  AND timestamp > now() - interval '1 hour';

-- High cost queries (>$100)
SELECT SUM((payload->>'cost')::float) as total_cost
FROM audit_events
WHERE event_type = 'cost'
  AND timestamp > now() - interval '1 hour'
HAVING SUM((payload->>'cost')::float) > 100;
```

## Troubleshooting

### Hash Chain Verification Failed

**Cause**: Event was modified or deleted

**Steps**:
1. Export audit trail with date range before tampering
2. Verify integrity of that export
3. Identify first broken event
4. Review database backups
5. Restore from backup point before tampering

### Missing Events in Export

**Cause**: Events deleted, date range too narrow, or filters too restrictive

**Steps**:
1. Check export date range includes events
2. Remove filters and try again
3. Check that events weren't soft-deleted (check is_archived flag)
4. Verify user has audit:export permission

### Slow Audit Queries

**Cause**: Large table size, missing indexes

**Steps**:
1. Add index: `CREATE INDEX idx_audit_timestamp ON audit_events(timestamp)`
2. Archive old events: `UPDATE audit_events SET is_archived=true WHERE timestamp < now() - interval '90 days'`
3. Vacuum database: `VACUUM ANALYZE audit_events`

## Support

For audit-related questions:
- Check documentation: https://arcticcodex.com/docs/audit
- GitHub Issues: https://github.com/ArcticCodex/arcticcodex/issues
- Email: support@arcticcodex.com

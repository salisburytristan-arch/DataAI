# ArcticCodex Security Guide

## Overview

This document describes the security architecture of ArcticCodex, including authentication mechanisms, authorization controls, data protection, and threat mitigations.

## Authentication Model

### JWT Token-Based Authentication

ArcticCodex uses JWT (JSON Web Tokens) with HS256 (HMAC-SHA256) for stateless authentication.

**Token Structure:**
```json
{
  "sub": "user-id-uuid",
  "email": "user@example.com",
  "org_id": "org-id-uuid",
  "jti": "unique-session-id",
  "role": "admin|analyst|viewer|auditor",
  "exp": 1672531200,
  "iat": 1672444800
}
```

**Token Lifecycle:**
1. User submits email + password to `/auth/login`
2. Backend verifies password against bcrypt hash
3. Creates JWT with 24-hour expiration (configurable via `JWT_EXPIRATION`)
4. Token stored in browser localStorage (SameSite not applicable for SPA)
5. Token sent in `Authorization: Bearer <token>` header on all API requests
6. Token validation occurs on every request via RBAC middleware
7. Session revocation via `UserSession.revoked_at` timestamp

### Password Hashing

- **Algorithm**: bcrypt with 10 salt rounds
- **Cost**: ~100ms per hash operation (intentional slowness prevents brute force)
- **Never Stored**: Plaintext passwords deleted after hashing
- **Comparison**: bcrypt.checkpw() for constant-time verification

```python
password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(10))
is_valid = bcrypt.checkpw(password.encode(), password_hash)
```

### API Key Authentication

API keys are generated for programmatic access to agent APIs.

**API Key Storage:**
1. Full key generated as random 32-byte hex string
2. Only SHA256 hash stored in database (`api_keys.key_hash`)
3. First 8 characters stored as `key_prefix` for identification
4. Key displayed once to user after creation - never shown again
5. Key format: `ac_<prefix>_<suffix>` (e.g., `ac_abc12345_...`)

**API Key Revocation:**
1. Revoked keys have `revoked_at` timestamp set
2. Revocation checked on every request
3. Old keys cannot be reactivated

## Authorization Model (RBAC)

### Role Hierarchy

| Role | Permissions | Use Case |
|------|------------|----------|
| **admin** | All 8 permissions | Org admin, can configure everything |
| **analyst** | 4 permissions (ingest, run, execute, audit:view) | Data scientist, can run queries |
| **viewer** | 1 permission (audit:view) | Read-only audit access |
| **auditor** | 2 permissions (audit:view, audit:export) | Compliance officer, can export logs |

### Permission Matrix

```
Permission              | Admin | Analyst | Viewer | Auditor
-----------------------|-------|---------|--------|--------
data:ingest            |  ✓    |    ✓    |   ✗    |   ✗
agent:run              |  ✓    |    ✓    |   ✗    |   ✗
tool:execute           |  ✓    |    ✓    |   ✗    |   ✗
tool:approve           |  ✓    |    ✗    |   ✗    |   ✗
audit:view             |  ✓    |    ✓    |   ✓    |   ✓
audit:export           |  ✓    |    ✗    |   ✗    |   ✓
config:manage          |  ✓    |    ✗    |   ✗    |   ✗
user:manage            |  ✓    |    ✗    |   ✗    |   ✗
```

### Permission Enforcement

1. **Route-to-Permission Mapping**: Each API endpoint requires specific permission
2. **RBAC Middleware**: Intercepts all requests before route handler execution
3. **Fail-Closed**: Missing permission → 403 Forbidden (not 401)
4. **Audit Logging**: Every access attempt logged to `audit_events` table
5. **JWT Payload**: Role extracted from JWT claims, verified against ROUTE_PERMISSIONS

```python
# Example: Require admin to create policies
POST /api/tool-policies -> requires "config:manage" -> requires admin role
```

## Multi-Tenancy and Isolation

### Organization-Based Isolation

Every entity (user, session, key, policy, run, audit) includes `org_id` foreign key.

**Database-Level Enforcement via Row-Level Security (RLS):**

```sql
CREATE POLICY org_isolation_users ON users
USING (org_id = current_setting('app.current_org_id')::uuid);

CREATE POLICY org_isolation_api_keys ON api_keys
USING (org_id = current_setting('app.current_org_id')::uuid);
```

**Application-Level Enforcement:**

1. JWT includes `org_id` claim
2. RequestContext extracts `org_id` from JWT
3. All database queries filtered by `org_id = request.org_id`
4. Helper: `filter_by_org(query, org_id)` wraps filters

```python
# All queries scoped by org_id
runs = session.query(AgentRun).filter_by(org_id=request.org_id).all()
```

**Tenant Isolation Guarantees:**
- Organization A **cannot** see Organization B's:
  - Users, sessions, API keys
  - Agent runs, queries, responses
  - Audit events
  - Policies, configurations
  - Costs and usage metrics

### Data Access Controls

| Entity | Isolation | Visibility |
|--------|-----------|-----------|
| Users | Within org | Own profile, org members |
| Sessions | Within org | Own sessions |
| API Keys | Within org | Prefix masked, owned keys |
| Runs | Within org | Own org only |
| Audit Events | Within org | Query filtered by org |
| Policies | Within org | Org-wide |

## Threat Model and Mitigations

### Threat 1: Unauthorized API Access

**Threat**: Attacker uses stolen API key to call agent endpoints

**Mitigations**:
- API key stored as SHA256 hash (one-way, cannot reverse)
- Key prefix only (first 8 chars) visible to user for identification
- Full key shown only once after creation
- Revocation via `revoked_at` timestamp check
- Rate limiting: `API_RATE_LIMIT_RPM` (default 100/min)

### Threat 2: Privilege Escalation

**Threat**: Analyst tries to modify tool policies (requires admin)

**Mitigations**:
- RBAC middleware enforces role requirements before handler execution
- `require_role("admin")` decorator on sensitive endpoints
- Fail-closed: Missing permission = 403 Forbidden
- All privilege escalation attempts logged to audit_events
- Attempt detected via AuditEvent.event_type = EventType.UNAUTHORIZED

### Threat 3: Cross-Tenant Data Leakage

**Threat**: Organization A queries tables and retrieves Org B data

**Mitigations**:
- RLS policies at database level (Postgres enforces even with service role)
- All queries explicitly filtered by `org_id` in application
- Helper function `ensure_org_access(session, org_id)` validates ownership
- Unit tests verify tenant isolation with multiple organizations

### Threat 4: Session Hijacking

**Threat**: Attacker steals JWT token and impersonates user

**Mitigations**:
- JWT stored in browser localStorage (vulnerable to XSS, protected by CSP)
- 24-hour token expiration limits window
- Session revocation via `/auth/logout` sets `revoked_at` immediately
- IP address logged in UserSession for admin review
- User can revoke all sessions via `/auth/sessions` endpoint

**Recommendations for Production**:
- Use `Secure; HttpOnly; SameSite=Strict` cookies instead of localStorage
- Implement refresh tokens with short expiration (<15 min)
- Use Content Security Policy (CSP) to prevent XSS

### Threat 5: Brute Force Password Attack

**Threat**: Attacker tries 1000s of password combinations

**Mitigations**:
- bcrypt with 10 rounds: ~100ms per attempt (limits to ~600/hour per IP)
- Rate limiting at API gateway level (not yet implemented)
- Account lockout after N failed attempts (not yet implemented)

**Recommendations**:
- Implement `/auth/login` rate limiting (max 5 attempts/10min per IP)
- Add account lockout (lock after 5 failed attempts)
- Implement 2FA for admin accounts

### Threat 6: SQL Injection

**Threat**: Attacker injects SQL via query parameter

**Mitigations**:
- SQLAlchemy ORM with parameterized queries (not raw SQL)
- Pydantic validation on all request payloads
- No string concatenation in queries
- Type checking on all inputs

```python
# Safe (parameterized)
user = session.query(User).filter_by(email=email).first()

# Unsafe (not used)
user = session.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### Threat 7: Audit Log Tampering

**Threat**: Attacker modetes audit_events table to hide activity

**Mitigations**:
- Audit events immutable after creation (no UPDATE, DELETE in policies)
- Hash-chain: Each event includes `event_hash` and `prev_hash`
- Genesis event: First event has `prev_hash = '0' * 64`
- Verification: SHA256(event_type + actor + timestamp + prev_hash) = event_hash
- Cloud database: Supabase handles backups, point-in-time recovery

**Verification Code**:
```python
def verify_audit_chain(events: List[AuditEvent]) -> bool:
    for i, event in enumerate(events):
        if i == 0:
            expected_prev = '0' * 64
        else:
            expected_prev = events[i-1].event_hash
        
        if event.prev_hash != expected_prev:
            return False
        
        # Verify hash
        payload_str = json.dumps(event.payload, sort_keys=True)
        data = f"{event.event_type}{event.actor}{event.timestamp}{event.prev_hash}{payload_str}"
        computed = hashlib.sha256(data.encode()).hexdigest()
        if event.event_hash != computed:
            return False
    
    return True
```

## Key Rotation

### API Key Rotation

1. Admin creates new API key via `/api-keys` endpoint
2. Old key's `revoked_at` is set to current timestamp
3. New key is immediately active
4. Old key rejected on next request (revoked_at check)
5. No grace period - immediate cutover

### JWT Secret Rotation (Not Yet Implemented)

Recommended process:
1. Create new `JWT_SECRET_NEW` environment variable
2. Accept tokens signed with either secret for 24 hours
3. All new tokens signed with new secret only
4. After 24 hours, reject old-secret tokens
5. Remove old secret from environment

## Audit and Compliance

### Audit Event Types

Every action logged to `audit_events` table with:
- Timestamp (UTC)
- Actor (user email)
- Event type (one of 10 types)
- Payload (action details as JSON)
- Hash-chain (event_hash, prev_hash)

```python
class EventType(str, Enum):
    REQUEST = "request"          # Incoming API request
    RESPONSE = "response"        # Outgoing API response
    ERROR = "error"              # API error
    AUTH = "auth"                # Login/logout
    UNAUTHORIZED = "unauthorized"  # Permission denied
    TOOL = "tool"                # Tool execution
    APPROVAL = "approval"        # Policy approval
    POLICY = "policy"            # Policy change
    PHI = "phi"                  # PHI detected in response
    COST = "cost"                # Cost tracking
```

### Audit Retention

- Default retention: 90 days (configurable via `AUDIT_RETENTION_DAYS`)
- Older events can be archived via `DELETE` (separate process)
- Compliance: HIPAA requires 6 years for healthcare data

### Audit Export

Export via `POST /api/audit/export?from=DATE&to=DATE`
- Returns ZIP containing CSV files per event type
- Includes hash-chain verification data
- Timestamped and signed (optional, not implemented)

## Compliance Standards

### HIPAA (Healthcare)

| Requirement | Implementation | Status |
|-------------|----------------|--------|
| Access controls | RBAC + multi-tenancy | ✓ Complete |
| Audit logging | Hash-chain events | ✓ Complete |
| Encryption (transit) | TLS/HTTPS | ⚠ Requires Nginx reverse proxy |
| Encryption (rest) | Supabase pgcrypto | ⚠ Not enabled by default |
| Data integrity | Hash verification | ✓ Complete |
| Backup/recovery | Supabase automated | ✓ Complete |
| Incident response | Audit export | ✓ Complete |

### SOC 2

| Criterion | Implementation | Status |
|-----------|----------------|--------|
| Access control | RBAC, user:manage permission | ✓ Complete |
| Change management | Audit events on policy changes | ✓ Complete |
| Monitoring | Audit export, event filtering | ✓ Complete |
| Incident response | Audit trail, admin access logs | ✓ Complete |

## Configuration Security

### Environment Variables

**Critical variables** (must be set in production):
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Public API key
- `SUPABASE_SERVICE_KEY`: Service role key (never expose)
- `JWT_SECRET`: 32+ byte random hex (generate: `openssl rand -hex 32`)
- `DATABASE_URL`: PostgreSQL connection string

**Never committed to Git:**
- `.env` files (add to `.gitignore`)
- `SUPABASE_SERVICE_KEY`
- `JWT_SECRET`
- API keys (OpenAI, Anthropic)

**Secure .env Location:**
```bash
# Generate secure JWT secret
openssl rand -hex 32

# Example .env (never commit)
JWT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGc...
```

## Production Deployment Checklist

- [ ] All `.env` variables set (no defaults for sensitive values)
- [ ] `SUPABASE_SERVICE_KEY` stored in secure secret manager (not Docker env)
- [ ] TLS/HTTPS enabled at load balancer
- [ ] CORS configured to specific origin (not `*`)
- [ ] Rate limiting enabled for authentication endpoints
- [ ] Database backups tested and verified
- [ ] Audit log retention policy set
- [ ] Admin users created with strong passwords (min 16 chars)
- [ ] Monitoring enabled (logging, error tracking)
- [ ] Incident response plan documented
- [ ] Security audit conducted by third party
- [ ] DLP (Data Loss Prevention) tools configured

## Incident Response

### Security Breach Detected

1. **Immediate**: Revoke all active API keys (`POST /api-keys/{id}`)
2. **Within 1 hour**: Export audit events for analysis
3. **Within 24 hours**: Rotate `JWT_SECRET` and force re-login
4. **Notification**: Inform affected users
5. **Investigation**: Review audit logs, identify compromised accounts
6. **Follow-up**: Update passwords, enable 2FA, patch vulnerability

### Audit Events to Review

```sql
-- Unauthorized access attempts
SELECT * FROM audit_events 
WHERE event_type = 'unauthorized' 
  AND timestamp > now() - interval '24 hours'
ORDER BY timestamp DESC;

-- Privilege escalation attempts
SELECT * FROM audit_events 
WHERE event_type = 'unauthorized' 
  AND payload->>'permission' IN ('admin', 'config:manage')
ORDER BY timestamp DESC;

-- Admin activities
SELECT * FROM audit_events 
WHERE actor IN (SELECT email FROM users WHERE role = 'admin')
  AND timestamp > now() - interval '7 days'
ORDER BY timestamp DESC;
```

## Additional Security Resources

- [OWASP Top 10](https://owasp.org/Top10/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework/)
- [CWE/SANS Top 25](https://cwe.mitre.org/top25/)

## Support

For security questions or to report vulnerabilities:
- **Email**: security@arcticcodex.com (not implemented)
- **GitHub Security Advisory**: [Report here](https://github.com/ArcticCodex/arcticcodex/security/advisories)
- **Do not**: Create public GitHub issues for security vulnerabilities

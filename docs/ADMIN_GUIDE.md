# ArcticCodex Administrator Guide

## Overview

This guide covers operational procedures for administering ArcticCodex including user management, API key rotation, organization configuration, and troubleshooting.

## Initial Setup

### 1. Deployment

**Prerequisites:**
- Docker and Docker Compose installed
- Supabase account with PostgreSQL database created
- Environment variables configured in `.env`

**Setup Steps:**

```bash
# 1. Clone repository
git clone https://github.com/ArcticCodex/arcticcodex.git
cd arcticcodex

# 2. Copy and configure environment
cp .env.example .env
# Edit .env with your Supabase credentials and API keys

# 3. Start Docker containers
docker-compose -f docker-compose.production.yml up -d

# 4. Check service health
docker-compose logs -f backend
docker-compose logs frontend

# 5. Create initial organization
docker-compose exec backend python seed.py
# Follow prompts to create admin user and organization
```

**Verify Deployment:**
```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# View API documentation
open http://localhost:8000/docs
```

**Initial Setup Time:** ~5 minutes

### 2. Database Schema

The initial setup automatically creates the following tables:

```
organizations    - Organizations (org separation)
users           - User accounts with roles
user_sessions   - Active sessions and login history
api_keys        - API key credentials (hashed)
tool_policies   - Tool execution policies
tool_approvals  - Pending policy approvals
model_policies  - LLM model rate limits
audit_events    - Immutable audit trail
agent_runs      - Query execution history
```

View schema:
```bash
docker-compose exec backend psql $DATABASE_URL -c "\\dt"
```

## User Management

### Creating Users

**Via Studio UI (Recommended):**

1. Login as admin to http://localhost:3000
2. Navigate to **Users** tab
3. Click **+ Invite User**
4. Fill in form:
   - **Email**: user@example.com
   - **Full Name**: John Doe
   - **Password**: (generate strong password)
   - **Role**: Select from admin/analyst/viewer/auditor
5. Click **Send Invite**
6. Share credentials with user

**Via API:**

```bash
curl -X POST http://localhost:8000/api/orgs/{org_id}/invite \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "full_name": "John Doe",
    "password": "SecurePassword123",
    "role": "analyst"
  }'
```

### User Roles and Permissions

| Role | Permission Set | Typical Use |
|------|---|---|
| **admin** | All 8 permissions | Organization administrator |
| **analyst** | Run queries, execute tools | Data scientist, engineer |
| **viewer** | View audit only | Auditor, observer |
| **auditor** | View + export audit | Compliance officer |

**Permission Matrix:**

| Permission | Admin | Analyst | Viewer | Auditor |
|---|:---:|:---:|:---:|:---:|
| data:ingest | ✓ | ✓ | | |
| agent:run | ✓ | ✓ | | |
| tool:execute | ✓ | ✓ | | |
| tool:approve | ✓ | | | |
| audit:view | ✓ | ✓ | ✓ | ✓ |
| audit:export | ✓ | | | ✓ |
| config:manage | ✓ | | | |
| user:manage | ✓ | | | |

### Updating User Roles

**Via Studio UI:**

1. Go to **Users** tab
2. Find user in list
3. Click **Change Role** dropdown
4. Select new role from: admin, analyst, viewer, auditor
5. Click **Save**

**Via API:**

```bash
curl -X PATCH http://localhost:8000/api/orgs/{org_id}/members/{user_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "viewer"
  }'
```

### Removing Users

**Via Studio UI:**

1. Go to **Users** tab
2. Find user in list
3. Click **Remove** button
4. Confirm removal
5. User account is deactivated, sessions revoked

**Via API:**

```bash
curl -X DELETE http://localhost:8000/api/orgs/{org_id}/members/{user_id} \
  -H "Authorization: Bearer $TOKEN"
```

**Effect of Removal:**
- User's `is_active` set to false
- All active sessions revoked (`revoked_at` set)
- User cannot login
- Cannot access any organization resources
- Account not deleted (audit trail preserved)

### Session Management

View user sessions:

```bash
curl http://localhost:8000/api/auth/sessions \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "sessions": [
    {
      "id": "session-uuid",
      "user_id": "user-uuid",
      "created_at": "2024-01-15T10:30:00Z",
      "expires_at": "2024-01-16T10:30:00Z",
      "revoked_at": null,
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0..."
    }
  ]
}
```

Revoke specific session:

```bash
curl -X DELETE http://localhost:8000/api/auth/sessions/{session_id} \
  -H "Authorization: Bearer $TOKEN"
```

Force user logout (revoke all sessions):

```bash
# Requires admin or user:manage permission
curl -X DELETE http://localhost:8000/api/auth/sessions \
  -H "Authorization: Bearer $TOKEN"
```

## API Key Management

### Generating API Keys

**Via Studio UI (Recommended):**

1. Go to **API Keys** tab
2. Click **+ Generate Key**
3. Enter key name (e.g., "Production API", "CI/CD Integration")
4. Click **Generate**
5. **IMPORTANT**: Copy key immediately and store securely
6. Key shown only once - cannot be retrieved later

**Via API:**

```bash
curl -X POST http://localhost:8000/api/api-keys \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "production-key"
  }'

# Response (key shown only once):
{
  "id": "key-uuid",
  "key": "ac_abc12345_xyzAbCxyzAbCxyzAbCxyzAbC",
  "key_prefix": "abc12345",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### API Key Storage

**Recommended Storage:**

1. **Environment Variables** (development):
   ```bash
   export ARCTICCODEX_API_KEY="ac_abc12345_..."
   ```

2. **Secret Manager** (production):
   - AWS Secrets Manager
   - HashiCorp Vault
   - Google Cloud Secret Manager
   - Azure Key Vault

3. **CI/CD Secrets**:
   - GitHub Actions: Settings > Secrets and variables > Actions
   - GitLab CI: Settings > CI/CD > Variables
   - Jenkins: Credentials > System > Global credentials

**Never:**
- Commit API keys to Git
- Store in plaintext config files
- Share in chat/email
- Log to stdout

### API Key Usage

**Call Agent Endpoint:**

```bash
curl -X POST http://localhost:8000/api/agent/run \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the weather?",
    "tools": ["weather", "news"]
  }'
```

**In Application Code:**

```python
import requests
import os

api_key = os.environ['ARCTICCODEX_API_KEY']
headers = {'Authorization': f'Bearer {api_key}'}

response = requests.post(
    'http://localhost:8000/api/agent/run',
    headers=headers,
    json={'query': 'Find latest news', 'tools': ['news']}
)
```

### API Key Rotation

**Recommended Rotation Schedule:** Every 90 days

**Rotation Process:**

1. Create new API key with same name (e.g., "production-key-v2")
2. Copy new key and update all applications
3. Test new key in staging environment
4. Deploy applications with new key
5. Monitor for errors (should be none)
6. Revoke old key via Studio or API

**Revoke Key:**

```bash
curl -X DELETE http://localhost:8000/api/api-keys/{key_id} \
  -H "Authorization: Bearer $TOKEN"
```

**After Revocation:**
- Old key immediately rejected
- No grace period
- Any requests using old key return 401 Unauthorized

### Audit API Key Access

View which API keys have been used:

```bash
curl http://localhost:8000/api/api-keys \
  -H "Authorization: Bearer $TOKEN"

# Response includes:
{
  "id": "key-uuid",
  "key_prefix": "abc12345",
  "name": "production-key",
  "created_at": "2024-01-15T10:30:00Z",
  "is_active": true,
  "last_used_at": "2024-01-16T15:45:30Z"
}
```

Query audit events for key usage:

```bash
curl "http://localhost:8000/api/audit/events?actor=api_key_abc12345" \
  -H "Authorization: Bearer $TOKEN"
```

## Organization Configuration

### Change Organization Name

**Via Studio UI:**

1. Go to **Settings** tab
2. Edit "Organization Name"
3. Click **Save**

**Via API:**

```bash
curl -X PATCH http://localhost:8000/api/orgs/{org_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "New Org Name"
  }'
```

### Vault Configuration

Configure evidence storage and retrieval:

**Via Studio UI:**

1. Go to **Settings** tab
2. Under "Vault Configuration":
   - Set **Evidence Chunk Limit** (max characters per chunk)
   - Select **Retrieval Strategy**: semantic, keyword, or hybrid
3. Click **Save**

**Environment Variables:**

```env
VAULT_PATH=/app/vault
VAULT_EVIDENCE_LIMIT=5000
VAULT_RETRIEVAL_STRATEGY=semantic
```

### LLM Model Configuration

Configure which models are available and their rate limits:

**Via Studio UI:**

1. Go to **Settings** > **LLM Models**
2. Click **+ Add Model**
3. Configure:
   - **Provider**: OpenAI, Anthropic, or Local
   - **Model Name**: gpt-4, claude-3-sonnet, etc.
   - **Max Requests/Minute**: Rate limit
   - **Max Tokens/Minute**: Token limit
   - **Max Cost/Request**: Cost cap
   - **Max Daily Cost**: Daily budget
4. Click **Add**

**Model Policy Fields:**

```
provider            - openai, anthropic, local
model_name         - Model identifier (e.g., gpt-4-turbo)
max_rpm            - Max requests per minute
max_tpm            - Max tokens per minute  
max_cost_per_req   - Max USD per single request
max_daily_cost     - Max USD per organization per day
max_failures       - Max failures before cooldown
cooldown_seconds   - Seconds to wait after max_failures reached
```

### Tool Policy Configuration

Configure which tools can be executed and how:

**Via Studio UI:**

1. Go to **Policies** tab
2. Click **+ New Policy**
3. Configure:
   - **Tool Name**: tool identifier
   - **Execution Mode**: auto (always allowed), approve (requires approval), deny (blocked)
   - **Constraints**: Max file size, timeout, network access
4. Click **Create**

**Execution Modes:**

| Mode | Behavior | Use Case |
|------|----------|----------|
| **auto** | Always allowed | Safe tools (search, calculator) |
| **approve** | Requires admin approval | Sensitive tools (delete, modify) |
| **deny** | Blocked | Disabled tools, breaking changes |

## Audit and Monitoring

### View Audit Events

**Via Studio UI:**

1. Go to **Audit** tab
2. Filter by:
   - Event Type (request, response, error, auth, unauthorized, tool, etc.)
   - Actor (user email or API key)
   - Date Range
   - Run ID
3. Click **Apply Filters**
4. View event details in expandable cards

**Via API:**

```bash
curl "http://localhost:8000/api/audit/events?event_type=error&limit=100" \
  -H "Authorization: Bearer $TOKEN"
```

### Export Audit Logs

**Via Studio UI:**

1. Go to **Audit** tab
2. Apply filters as desired
3. Click **Export** button
4. Download ZIP containing CSV files

**Via API:**

```bash
curl "http://localhost:8000/api/audit/export?from=2024-01-01&to=2024-01-31" \
  -H "Authorization: Bearer $TOKEN" \
  --output audit_export.zip
```

**Export Contents:**

```
audit_export.zip
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

**CSV Format:**

```csv
event_id,timestamp,actor,event_type,payload,event_hash,prev_hash
abc-123,2024-01-15T10:30:00Z,user@example.com,request,"...json...",abc123,def456
```

### Verify Hash Chain Integrity

Each audit event is linked via hash-chain for immutability:

```python
# Verify using ArcticCodex CLI
arcticcodex audit verify --export audit_export.zip

# Output:
# ✓ Hash chain integrity verified
# ✓ 1,234 events verified
# ✓ No tampering detected
# ✓ Chain spans from 2024-01-01 to 2024-01-31
```

### Monitor Costs

**Via Studio UI:**

1. Go to **Costs** tab
2. View summary:
   - Total cost (last 30 days)
   - Average cost per run
   - Top provider
   - Budget status
3. View breakdown by:
   - Provider (OpenAI, Anthropic, Local)
   - User (top spenders)
   - Daily trend (chart)

**Cost Data Fields:**

```
total_cost          - Total USD spent in period
cost_per_run        - Average cost per query
top_provider        - Most-used provider
budget_remaining    - Budget cap - current spend
daily_breakdown     - Cost per day (array)
by_provider         - Cost breakdown by LLM provider
by_user             - Cost breakdown by user email
```

**Set Budget Alerts:**

```bash
curl -X PATCH http://localhost:8000/api/orgs/{org_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "settings": {
      "budget_daily_max": 100.00,
      "budget_monthly_max": 3000.00
    }
  }'
```

## Troubleshooting

### Service Health Checks

```bash
# Check backend service
docker-compose logs backend | tail -20

# Check frontend service
docker-compose logs frontend | tail -20

# Verify Supabase connectivity
curl $SUPABASE_URL/rest/v1/ \
  -H "apikey: $SUPABASE_KEY"
```

### Common Issues

**Issue: Login fails with "Invalid credentials"**
- Check email is correct
- Verify password is correct
- Check user is active (not removed)
- View audit events for auth failures

**Issue: API key rejected with 401**
- Verify key not revoked
- Check key prefix in audit logs
- Generate new key if lost

**Issue: User cannot create API key**
- Check user has admin role (api:manage permission)
- Verify organization is active

**Issue: Audit export empty**
- Check date range includes events
- Verify filters are not too restrictive
- Check user has audit:export permission

### Database Troubleshooting

**Connect to Database Directly:**

```bash
# Get connection string
echo $DATABASE_URL

# Connect with psql
psql $DATABASE_URL
```

**Check User Count:**
```sql
SELECT org_id, COUNT(*) FROM users GROUP BY org_id;
```

**Check API Key Status:**
```sql
SELECT name, is_active, revoked_at FROM api_keys;
```

**Check Audit Events:**
```sql
SELECT event_type, COUNT(*) FROM audit_events 
GROUP BY event_type ORDER BY COUNT DESC;
```

**Rebuild Indexes (if slow):**
```sql
REINDEX DATABASE arcticcodex;
```

### Log Analysis

**View Error Logs:**
```bash
docker-compose logs backend | grep ERROR
```

**View Auth Logs:**
```bash
docker-compose logs backend | grep auth
```

**View All Logs with Timestamps:**
```bash
docker-compose logs --timestamps backend
```

## Backup and Recovery

### Automated Backups

Supabase automatically backs up your database:
- Daily backups (7 days retention)
- Weekly backups (4 weeks retention)
- Monthly backups (1 year retention)

View backups in Supabase dashboard:
1. Go to https://app.supabase.com
2. Select your project
3. Navigate to Backups
4. View backup history

### Manual Backup

```bash
# Dump database to SQL file
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Compress backup
gzip backup_*.sql
```

### Recovery

**Restore from Supabase Backup:**

1. Open Supabase Dashboard
2. Go to Backups
3. Select backup to restore
4. Click "Restore"
5. Confirm - database will be restored
6. Restart services

**Restore from SQL File:**

```bash
psql $DATABASE_URL < backup_20240115_153000.sql
```

## Performance Tuning

### Database Queries

**Analyze slow queries:**
```sql
-- Enable query logging
SET log_statement = 'all';

-- View slow queries
SELECT query, calls, mean_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;
```

**Add indexes for slow queries:**
```sql
CREATE INDEX idx_audit_event_type_timestamp 
ON audit_events(org_id, event_type, timestamp);
```

### Rate Limiting

Configure in `.env`:
```env
API_RATE_LIMIT_RPM=100         # API calls per minute
LLM_RATE_LIMIT_RPM=90          # LLM calls per minute
```

**Per-user limits:**
1. Create model policies with `max_rpm` and `max_tpm`
2. Rate limiting enforced per user + model combo
3. Excess requests queued or rejected

### Connection Pool Sizing

Adjust in code if needed:
```python
# packages/core/src/db.py
pool_size = 10          # Connections to keep open
max_overflow = 20       # Extra connections when needed
pool_recycle = 3600     # Recycle connections after 1 hour
```

## Security Operations

### Key Rotation Checklist

- [ ] Generate new API key
- [ ] Test in staging environment
- [ ] Update production environment
- [ ] Monitor logs for errors
- [ ] Revoke old key after 24 hours

### User Access Review (Monthly)

```bash
# List all active users
curl http://localhost:8000/api/orgs/{org_id}/members \
  -H "Authorization: Bearer $TOKEN"

# Export user audit for compliance
curl "http://localhost:8000/api/audit/events?actor=*&event_type=auth" \
  -H "Authorization: Bearer $TOKEN" --output user_audit.zip
```

### Incident Response

If security incident detected:

1. **Revoke All API Keys:**
   ```bash
   # Via UI or API - delete all keys
   curl -X DELETE http://localhost:8000/api/api-keys/{key_id} \
     -H "Authorization: Bearer $TOKEN"
   ```

2. **Force User Re-authentication:**
   ```bash
   # Revoke all sessions
   curl -X DELETE http://localhost:8000/api/auth/sessions \
     -H "Authorization: Bearer $TOKEN"
   ```

3. **Export Audit Trail:**
   ```bash
   curl "http://localhost:8000/api/audit/export?from=2024-01-01" \
     -H "Authorization: Bearer $TOKEN" --output incident_audit.zip
   ```

4. **Review Audit Events**
5. **Rotate JWT_SECRET** in environment
6. **Notify All Users**

## Support

For help or questions:
- Check documentation at: https://arcticcodex.com/docs
- GitHub Issues: https://github.com/ArcticCodex/arcticcodex/issues
- Email: admin@arcticcodex.com

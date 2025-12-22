# ArcticCodex Tool Policy Guide

## Overview

Tool policies control which tools agents can execute, how they execute (automatic, approval-required, or blocked), and what constraints apply. This guide covers policy creation, approval workflows, and enforcement.

## Policy Concepts

### What are Tool Policies?

Tool policies define rules for tool execution:
- **Tool Name**: Identifier (e.g., "code_executor", "web_scraper")
- **Execution Mode**: How tool is executed
- **Constraints**: Limits on resource usage
- **Allowed Roles**: Which user roles can execute

### Execution Modes

Three execution modes determine how tools are handled:

| Mode | Behavior | When Used |
|------|----------|-----------|
| **auto** | Always allowed, executes immediately | Safe tools (search, calculator) |
| **approve** | Requires admin approval before execution | Sensitive tools (delete, modify, scrape) |
| **deny** | Tool is blocked, cannot execute | Disabled tools, security risk |

### Why Policies Matter

**Safety**: Prevent dangerous tools from running without oversight
**Compliance**: Enforce organizational security policies
**Auditing**: Track tool usage with approval history
**Cost Control**: Prevent expensive tool abuse
**Security**: Block tools that access sensitive systems

## Creating Policies

### Via Studio UI

**Step 1: Navigate to Policies Tab**
1. Log in as admin to http://localhost:3000
2. Click **Policies** in sidebar

**Step 2: Create New Policy**
1. Click **+ New Policy**
2. Enter **Tool Name** (e.g., "file_delete")
3. Select **Execution Mode**:
   - Green dot = **auto** (safe, always allowed)
   - Yellow dot = **approve** (requires approval)
   - Red dot = **deny** (blocked)

**Step 3: Configure Constraints** (optional)
1. Set **Max File Size (MB)**: Prevent huge file operations
2. Set **Timeout (seconds)**: Prevent infinite loops
3. Toggle **Network Enabled**: Allow/block internet access

**Step 4: Save**
1. Click **Create**
2. Policy is immediately active

**Example Policies:**

```
Tool Name: python_code
Mode: approve
Constraints:
  - Max File Size: 10 MB
  - Timeout: 30 seconds
  - Network: disabled
```

```
Tool Name: web_search
Mode: auto
Constraints:
  - Timeout: 10 seconds
  - Network: enabled
```

```
Tool Name: database_delete
Mode: deny
Constraints: (not applicable)
```

### Via API

**Create Tool Policy:**

```bash
curl -X POST http://localhost:8000/api/tool-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "python_code",
    "mode": "approve",
    "constraints": {
      "max_file_size_mb": 10,
      "timeout_seconds": 30,
      "network_enabled": false
    },
    "allowed_roles": ["admin", "analyst"]
  }'

# Response:
{
  "id": "policy-uuid",
  "org_id": "org-uuid",
  "tool_name": "python_code",
  "mode": "approve",
  "constraints": {...},
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Update Tool Policy:**

```bash
curl -X PATCH http://localhost:8000/api/tool-policies/{policy_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "deny",
    "constraints": {
      "max_file_size_mb": 5
    }
  }'
```

**List Tool Policies:**

```bash
curl http://localhost:8000/api/tool-policies \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "policies": [
    {
      "id": "policy-uuid",
      "tool_name": "python_code",
      "mode": "approve",
      "constraints": {...},
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

**Delete Tool Policy:**

```bash
curl -X DELETE http://localhost:8000/api/tool-policies/{policy_id} \
  -H "Authorization: Bearer $TOKEN"
```

## Policy Enforcement

### How Policies are Enforced

When agent executes a tool:

1. **Lookup Policy**: Find policy matching tool name
2. **Check Mode**:
   - **auto**: Execute immediately, log event
   - **approve**: Create approval request, wait for admin decision
   - **deny**: Block execution, return error
3. **Check Constraints**: Validate file size, timeout, network access
4. **Check Permissions**: Verify user role is in allowed_roles
5. **Log Event**: Record tool execution or rejection in audit_events

### Default Behavior

If no policy exists for a tool:
- Mode: **auto** (allowed by default)
- Constraints: None applied
- Recommendation: Create explicit policies for security

## Approval Workflows

### Approval Process

**For tools in "approve" mode:**

1. **User Requests Tool Execution**
   ```bash
   curl -X POST http://localhost:8000/api/agent/run \
     -H "Authorization: Bearer $TOKEN" \
     -d '{
       "query": "Delete all logs",
       "tools": ["file_delete"]
     }'
   
   # Response (tool is blocked, approval needed):
   {
     "status": "pending_approval",
     "approval_id": "approval-uuid",
     "message": "Tool 'file_delete' requires approval",
     "requested_at": "2024-01-15T10:30:00Z"
   }
   ```

2. **Admin Reviews Request** (via Studio UI)
   - Go to **Policies** > **Approvals** tab
   - View pending approvals with:
     - Tool name
     - Requested by (user email)
     - Requested at (timestamp)
     - Tool arguments (JSON)
   - See reason for request (if provided)

3. **Admin Decides**
   - **Approve**: Tool executes immediately
   - **Deny**: Request rejected, user notified
   - **Note**: Optional comment for audit trail

4. **Tool Executes or Rejects**
   - If approved: Tool runs and query completes
   - If denied: Tool not executed, error returned to user

### Approval Query

**List Pending Approvals:**

```bash
curl "http://localhost:8000/api/tools/approvals?status=pending" \
  -H "Authorization: Bearer $TOKEN"

# Response:
{
  "approvals": [
    {
      "id": "approval-uuid",
      "org_id": "org-uuid",
      "tool_name": "file_delete",
      "tool_args": {"path": "/logs/*"},
      "requested_by": "user@example.com",
      "requested_at": "2024-01-15T10:30:00Z",
      "status": "pending",
      "run_id": "run-uuid"
    }
  ]
}
```

**Approve Request:**

```bash
curl -X PATCH http://localhost:8000/api/tools/approvals/{approval_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "approved",
    "note": "Logs need cleanup for space"
  }'
```

**Deny Request:**

```bash
curl -X PATCH http://localhost:8000/api/tools/approvals/{approval_id} \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "denied",
    "note": "Too risky, use manual process"
  }'
```

### Approval History

View all approvals (pending, approved, denied):

```bash
curl "http://localhost:8000/api/tools/approvals" \
  -H "Authorization: Bearer $TOKEN"

# Approved approvals
curl "http://localhost:8000/api/tools/approvals?status=approved" \
  -H "Authorization: Bearer $TOKEN"

# Denied approvals
curl "http://localhost:8000/api/tools/approvals?status=denied" \
  -H "Authorization: Bearer $TOKEN"
```

## Common Policy Examples

### Example 1: Safe Tools (Auto)

**Web Search Tool:**
```
Tool Name: web_search
Mode: auto
Constraints:
  - Timeout: 10 seconds
  - Network: enabled
Reason: Safe, read-only operation
```

**Calculator Tool:**
```
Tool Name: calculator
Mode: auto
Constraints: None
Reason: No security risk
```

### Example 2: Sensitive Tools (Approve)

**File Delete Tool:**
```
Tool Name: file_delete
Mode: approve
Constraints:
  - Max File Size: 1000 MB
  - Timeout: 60 seconds
  - Network: disabled
Reason: Irreversible, needs human oversight
```

**Database Query Tool:**
```
Tool Name: database_query
Mode: approve
Constraints:
  - Timeout: 30 seconds
  - Network: disabled
Reason: Can access sensitive data
```

### Example 3: Blocked Tools (Deny)

**Dangerous Tools:**
```
Tool Name: system_shell
Mode: deny
Reason: Direct shell access too risky

Tool Name: credential_extractor
Mode: deny
Reason: Security risk

Tool Name: port_scanner
Mode: deny
Reason: Network reconnaissance tool
```

## Constraints

### Constraint Types

**Max File Size**
- Limits file size for operations
- Example: 10 MB max
- Prevents resource exhaustion
- Default: No limit

**Timeout (seconds)**
- Max execution time
- Example: 30 seconds
- Prevents infinite loops
- Default: 300 seconds

**Network Access**
- Allow/block internet access
- Example: true = allowed, false = blocked
- Prevents exfiltration
- Default: disabled

**Role Restrictions**
- Limit by user role
- Example: admin, analyst only
- Other roles cannot execute
- Default: All roles allowed

### Example Constraint Scenarios

**Scenario 1: Web Scraper**
```
Max File Size: 50 MB (HTML + data)
Timeout: 60 seconds (fetch + parse)
Network: enabled (needs internet)
Roles: analyst only (prevent misuse)
```

**Scenario 2: Code Executor**
```
Max File Size: 100 MB (code + dependencies)
Timeout: 120 seconds (execution)
Network: disabled (security)
Roles: admin only (trust required)
```

**Scenario 3: Data Processor**
```
Max File Size: 500 MB (large datasets)
Timeout: 300 seconds (slow processing)
Network: disabled (internal only)
Roles: analyst only
```

## Model Policies

### What are Model Policies?

Model policies configure rate limits and costs for LLM providers:
- **Provider**: openai, anthropic, local
- **Model Name**: gpt-4, claude-3-sonnet, etc.
- **Rate Limits**: Requests/minute, tokens/minute
- **Cost Caps**: Per-request and daily limits

### Configure Model Policies

**Via Studio UI:**

1. Go to **Settings** > **LLM Models**
2. Click **+ Add Model**
3. Configure:
   - **Provider**: Select from dropdown
   - **Model Name**: Enter model ID
   - **Max Requests/Minute**: Rate limit (e.g., 10)
   - **Max Tokens/Minute**: Token limit (e.g., 90,000)
   - **Max Cost/Request**: Per-request cap (e.g., $0.10)
   - **Max Daily Cost**: Daily budget (e.g., $100)
4. Click **Add**

**Via API:**

```bash
curl -X POST http://localhost:8000/api/model-policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model_name": "gpt-4-turbo",
    "max_rpm": 10,
    "max_tpm": 90000,
    "max_cost_per_request": 0.10,
    "max_daily_cost": 100.00
  }'
```

### Rate Limiting

**RPM (Requests Per Minute)**
- Max API calls in 60 seconds
- Example: 10 = 10 calls max per minute
- Prevents API quota exhaustion

**TPM (Tokens Per Minute)**
- Max input + output tokens in 60 seconds
- Example: 90,000 = 90K tokens max per minute
- Prevents token limit violations

**Example Configuration:**

```
Provider: openai
Model: gpt-4-turbo
Max RPM: 10 (10 requests/min)
Max TPM: 90,000 (90K tokens/min)
Max Cost/Request: $0.10
Max Daily Cost: $100
```

### Cost Controls

**Per-Request Cost Cap**
- Max USD per single request
- Prevents runaway costs
- Example: $0.10 cap prevents 100K token requests

**Daily Cost Budget**
- Max USD per day for model
- Hard limit on daily spending
- Example: $100/day budget
- Requests rejected when budget exceeded

**Example Cost Scenario:**

```
Daily Budget: $100
Requests Today:
  1. Cost $20 (running total: $20) ✓
  2. Cost $30 (running total: $50) ✓
  3. Cost $35 (running total: $85) ✓
  4. Cost $25 (would total: $110) ✗ REJECTED - exceeds daily budget

Retry allowed after 00:00 UTC (next day)
```

## Best Practices

### Policy Design

**1. Default Deny Approach**
- Create explicit policies for each tool
- Default to deny if no policy exists
- Gradually allow tools as needed
- Most secure approach

**2. Role-Based Access**
- Restrict sensitive tools to admin only
- Allow safe tools for all roles
- Analyst role for most operations
- Viewer role for read-only access

**3. Progressive Strictness**
- Start permissive (auto mode)
- Tighten based on usage patterns
- Move to approve mode if misused
- Deny only dangerous tools

### Approval Workflow Best Practices

**1. Clear Approval Criteria**
- Document when approval needed
- Provide guidelines to admins
- Set expected response time (e.g., < 1 hour)

**2. Audit Trail**
- Keep all approval history
- Record approver comments
- Track denied requests
- Review patterns monthly

**3. Escalation**
- Define approval chain
- Secondary approval for high-risk
- Escalate to CTO for infrastructure changes

### Constraint Configuration

**1. Match Tool Characteristics**
```
File Tool:
  - Set Max File Size based on typical files
  - Example: image_processor = 100 MB (typical images)
  
Network Tool:
  - Set Timeout for typical latency
  - Example: web_scraper = 60 seconds
  
Compute Tool:
  - Set Timeout for algorithm complexity
  - Example: ml_inference = 120 seconds
```

**2. Leave Room for Growth**
- Don't set constraints too tight
- Add monitoring before tightening
- Discuss changes with team

**3. Document Rationale**
- Explain constraint choices
- Record in policy notes
- Help future maintainers understand

## Monitoring and Adjustment

### Usage Monitoring

**Track Tool Execution:**

```bash
# Count tool executions by tool
SELECT 
  payload->>'tool_name' as tool,
  COUNT(*) as executions
FROM audit_events
WHERE event_type = 'tool'
  AND timestamp > now() - interval '7 days'
GROUP BY payload->>'tool_name'
ORDER BY executions DESC;

# Track approval requests
SELECT 
  tool_name,
  COUNT(*) as requested,
  SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) as approved,
  SUM(CASE WHEN status='denied' THEN 1 ELSE 0 END) as denied
FROM tool_approvals
WHERE requested_at > now() - interval '30 days'
GROUP BY tool_name;
```

### Adjustment Process

**Monthly Policy Review:**

1. Analyze usage patterns
2. Identify frequently denied requests
3. Check for constraint violations
4. Adjust policies based on data
5. Document changes

**Example:**
```
Current Policy: code_executor (approve mode)
Issue: 20 approval requests/day
Impact: 1-2 hour turnaround on requests
Action: Move to auto mode with constraints
  - Add timeout: 30 seconds max
  - Add file size: 50 MB max
  - Disable network access
Result: Instant execution, still safe
```

## Troubleshooting

### Policy Not Enforced

**Symptom**: Tool executes despite deny policy

**Diagnosis**:
1. Check policy exists: `GET /api/tool-policies`
2. Verify tool name matches exactly
3. Confirm user sees error

**Solution**:
- Recreate policy if missing
- Fix tool name capitalization
- Clear browser cache
- Restart backend service

### Approval Takes Too Long

**Symptom**: Approval requests pending for hours

**Diagnosis**:
1. Check pending approvals: `GET /api/tools/approvals?status=pending`
2. Identify which tools stuck
3. Check admin notification setup

**Solution**:
- Reduce number of approval-required tools
- Move frequently approved tools to auto mode
- Implement approval SLA (e.g., < 30 min)
- Add email notifications to admins

### Rate Limit Violations

**Symptom**: Requests rejected as exceeding rate limit

**Diagnosis**:
1. Check model policy: `GET /api/model-policies`
2. Compare RPM to actual usage
3. Analyze request patterns

**Solution**:
- Increase max RPM if legitimate traffic
- Implement request queuing
- Batch requests to reduce frequency
- Check for bot/scan activity

## Support

For policy-related questions:
- See documentation: https://arcticcodex.com/docs/policies
- GitHub Issues: https://github.com/ArcticCodex/arcticcodex/issues
- Email: support@arcticcodex.com

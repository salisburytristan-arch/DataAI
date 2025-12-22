-- ArcticCodex Database Schema for Supabase
-- Run this in Supabase SQL Editor to create tables and RLS policies

-- ============================================================================
-- ENABLE ROW LEVEL SECURITY
-- ============================================================================

-- Enable RLS on all tables (applied below)

-- ============================================================================
-- ORGANIZATIONS TABLE
-- ============================================================================

CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    settings JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE INDEX idx_org_name ON organizations(name);
CREATE INDEX idx_org_active ON organizations(is_active);

-- Enable RLS
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Organizations: users can only see their own org
CREATE POLICY "Users can view their own organization"
    ON organizations FOR SELECT
    USING (id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

-- Organizations: only admins can update
CREATE POLICY "Admins can update their organization"
    ON organizations FOR UPDATE
    USING (
        id IN (
            SELECT org_id FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- ============================================================================
-- USERS TABLE
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) NOT NULL DEFAULT 'viewer',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    
    CONSTRAINT valid_role CHECK (role IN ('admin', 'analyst', 'viewer', 'auditor'))
);

CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_org ON users(org_id);
CREATE INDEX idx_user_active ON users(is_active);

-- Enable RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Users: can view users in their org
CREATE POLICY "Users can view org members"
    ON users FOR SELECT
    USING (org_id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

-- Users: only admins can create/update users
CREATE POLICY "Admins can manage users"
    ON users FOR ALL
    USING (
        org_id IN (
            SELECT org_id FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- ============================================================================
-- USER SESSIONS TABLE
-- ============================================================================

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    ip_address VARCHAR(45),
    user_agent TEXT
);

CREATE INDEX idx_session_user ON user_sessions(user_id);
CREATE INDEX idx_session_expires ON user_sessions(expires_at);

-- Enable RLS
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- Sessions: users can only see their own sessions
CREATE POLICY "Users can view their own sessions"
    ON user_sessions FOR SELECT
    USING (user_id = auth.uid());

-- ============================================================================
-- API KEYS TABLE
-- ============================================================================

CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    key_prefix VARCHAR(10) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    is_active BOOLEAN NOT NULL DEFAULT true,
    revoked_at TIMESTAMPTZ,
    revoked_by UUID,
    last_used_at TIMESTAMPTZ
);

CREATE INDEX idx_apikey_org ON api_keys(org_id);
CREATE INDEX idx_apikey_hash ON api_keys(key_hash);
CREATE INDEX idx_apikey_prefix ON api_keys(key_prefix);

-- Enable RLS
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- API Keys: users can view org keys
CREATE POLICY "Users can view org api keys"
    ON api_keys FOR SELECT
    USING (org_id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

-- API Keys: only admins can manage keys
CREATE POLICY "Admins can manage api keys"
    ON api_keys FOR ALL
    USING (
        org_id IN (
            SELECT org_id FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- ============================================================================
-- TOOL POLICIES TABLE
-- ============================================================================

CREATE TABLE tool_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    mode VARCHAR(50) NOT NULL DEFAULT 'approve',
    constraints JSONB NOT NULL DEFAULT '{}'::jsonb,
    allowed_roles JSONB NOT NULL DEFAULT '["admin", "analyst"]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    
    CONSTRAINT uq_org_tool UNIQUE (org_id, tool_name),
    CONSTRAINT valid_mode CHECK (mode IN ('auto', 'approve', 'deny'))
);

CREATE INDEX idx_policy_org ON tool_policies(org_id);
CREATE INDEX idx_policy_tool ON tool_policies(tool_name);

-- Enable RLS
ALTER TABLE tool_policies ENABLE ROW LEVEL SECURITY;

-- Tool Policies: users can view org policies
CREATE POLICY "Users can view org policies"
    ON tool_policies FOR SELECT
    USING (org_id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

-- Tool Policies: only admins can manage policies
CREATE POLICY "Admins can manage policies"
    ON tool_policies FOR ALL
    USING (
        org_id IN (
            SELECT org_id FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- ============================================================================
-- TOOL APPROVALS TABLE
-- ============================================================================

CREATE TABLE tool_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    tool_name VARCHAR(255) NOT NULL,
    tool_args JSONB NOT NULL,
    requested_by UUID NOT NULL,
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_id UUID,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ,
    review_note TEXT,
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'approved', 'denied'))
);

CREATE INDEX idx_approval_org ON tool_approvals(org_id);
CREATE INDEX idx_approval_status ON tool_approvals(status);
CREATE INDEX idx_approval_run ON tool_approvals(run_id);

-- Enable RLS
ALTER TABLE tool_approvals ENABLE ROW LEVEL SECURITY;

-- Tool Approvals: users can view org approvals
CREATE POLICY "Users can view org approvals"
    ON tool_approvals FOR SELECT
    USING (org_id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

-- Tool Approvals: users can create, admins can approve
CREATE POLICY "Users can request approvals"
    ON tool_approvals FOR INSERT
    WITH CHECK (org_id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

CREATE POLICY "Admins can approve requests"
    ON tool_approvals FOR UPDATE
    USING (
        org_id IN (
            SELECT org_id FROM users 
            WHERE id = auth.uid() AND role IN ('admin', 'analyst')
        )
    );

-- ============================================================================
-- MODEL POLICIES TABLE
-- ============================================================================

CREATE TABLE model_policies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    provider VARCHAR(100) NOT NULL,
    model_name VARCHAR(255) NOT NULL,
    max_rpm INTEGER,
    max_tpm INTEGER,
    max_cost_per_request FLOAT,
    max_daily_cost FLOAT,
    max_failures INTEGER NOT NULL DEFAULT 5,
    cooldown_seconds INTEGER NOT NULL DEFAULT 60,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID NOT NULL,
    
    CONSTRAINT uq_org_provider_model UNIQUE (org_id, provider, model_name)
);

CREATE INDEX idx_model_policy_org ON model_policies(org_id);

-- Enable RLS
ALTER TABLE model_policies ENABLE ROW LEVEL SECURITY;

-- Model Policies: users can view org policies
CREATE POLICY "Users can view model policies"
    ON model_policies FOR SELECT
    USING (org_id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

-- Model Policies: only admins can manage
CREATE POLICY "Admins can manage model policies"
    ON model_policies FOR ALL
    USING (
        org_id IN (
            SELECT org_id FROM users 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- ============================================================================
-- AUDIT EVENTS TABLE
-- ============================================================================

CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    run_id UUID,
    actor VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    event_hash VARCHAR(64) NOT NULL UNIQUE,
    prev_hash VARCHAR(64) NOT NULL,
    
    CONSTRAINT valid_event_type CHECK (
        event_type IN ('request', 'evidence', 'tool', 'model', 'phi', 'response', 'error', 'auth', 'config', 'policy')
    )
);

CREATE INDEX idx_audit_org ON audit_events(org_id);
CREATE INDEX idx_audit_run ON audit_events(run_id);
CREATE INDEX idx_audit_type ON audit_events(event_type);
CREATE INDEX idx_audit_timestamp ON audit_events(timestamp);
CREATE INDEX idx_audit_actor ON audit_events(actor);

-- Enable RLS
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;

-- Audit Events: users can view org events (auditors have special access)
CREATE POLICY "Users can view org audit events"
    ON audit_events FOR SELECT
    USING (org_id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

-- Audit Events: only system can insert (via service role)
-- No INSERT policy = only service role can insert

-- ============================================================================
-- AGENT RUNS TABLE
-- ============================================================================

CREATE TABLE agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    actor VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    completed_at TIMESTAMPTZ,
    error TEXT,
    response TEXT,
    evidence_chunks JSONB,
    tool_calls JSONB,
    total_cost FLOAT NOT NULL DEFAULT 0.0,
    total_tokens INTEGER NOT NULL DEFAULT 0,
    phi_count INTEGER NOT NULL DEFAULT 0,
    phi_claims JSONB,
    
    CONSTRAINT valid_status CHECK (status IN ('running', 'completed', 'failed'))
);

CREATE INDEX idx_run_org ON agent_runs(org_id);
CREATE INDEX idx_run_status ON agent_runs(status);
CREATE INDEX idx_run_created ON agent_runs(created_at);
CREATE INDEX idx_run_actor ON agent_runs(actor);

-- Enable RLS
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;

-- Agent Runs: users can view org runs
CREATE POLICY "Users can view org runs"
    ON agent_runs FOR SELECT
    USING (org_id IN (
        SELECT org_id FROM users WHERE id = auth.uid()
    ));

-- Agent Runs: analysts and admins can create runs
CREATE POLICY "Analysts can create runs"
    ON agent_runs FOR INSERT
    WITH CHECK (
        org_id IN (
            SELECT org_id FROM users 
            WHERE id = auth.uid() AND role IN ('admin', 'analyst')
        )
    );

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Updated timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to relevant tables
CREATE TRIGGER update_organizations_updated_at
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_tool_policies_updated_at
    BEFORE UPDATE ON tool_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_model_policies_updated_at
    BEFORE UPDATE ON model_policies
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- DEFAULT DATA (Optional)
-- ============================================================================

-- Create a default organization (optional - can be done via API)
-- INSERT INTO organizations (id, name, display_name, settings)
-- VALUES (
--     gen_random_uuid(),
--     'default',
--     'Default Organization',
--     '{}'::jsonb
-- );

-- ============================================================================
-- NOTES
-- ============================================================================

-- RLS Policies:
-- - All tables have RLS enabled
-- - Users can only access data from their organization
-- - Admins have full access within their org
-- - Auditors can view audit events
-- - Service role bypasses RLS for system operations

-- Tenant Isolation:
-- - All data tables include org_id foreign key
-- - RLS policies enforce org_id filtering
-- - Supabase auth.uid() returns current user ID
-- - Use service role key for migrations and admin operations

-- Next Steps:
-- 1. Run this SQL in Supabase SQL Editor
-- 2. Create service role key (Settings > API)
-- 3. Update .env with connection details
-- 4. Test with seed data script

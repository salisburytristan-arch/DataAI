-- ArcticCodex Database Schema for Supabase

-- ============================================================================
-- EXTENSIONS (optional but commonly needed)
-- ============================================================================
-- CREATE EXTENSION IF NOT EXISTS pgcrypto; -- for gen_random_uuid on older Postgres
-- On Supabase, gen_random_uuid should be available.

-- ============================================================================
-- ORGANIZATIONS
-- ============================================================================
CREATE TABLE organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name varchar(255) NOT NULL UNIQUE,
  display_name varchar(255) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  settings jsonb NOT NULL DEFAULT '{}'::jsonb,
  is_active boolean NOT NULL DEFAULT true
);
CREATE INDEX idx_org_name ON organizations(name);
CREATE INDEX idx_org_active ON organizations(is_active);

-- ============================================================================
-- USERS (app-level users, not auth.users)
-- ============================================================================
CREATE TABLE users (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  email varchar(255) NOT NULL UNIQUE,
  password_hash varchar(255) NOT NULL,
  full_name varchar(255),
  role varchar(50) NOT NULL DEFAULT 'viewer',
  is_active boolean NOT NULL DEFAULT true,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  last_login_at timestamptz,
  CONSTRAINT valid_role CHECK (role IN ('admin','analyst','viewer','auditor'))
);
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_user_org ON users(org_id);
CREATE INDEX idx_user_active ON users(is_active);

-- ============================================================================
-- USER SESSIONS
-- ============================================================================
CREATE TABLE user_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  revoked_at timestamptz,
  ip_address varchar(45),
  user_agent text
);
CREATE INDEX idx_session_user ON user_sessions(user_id);
CREATE INDEX idx_session_expires ON user_sessions(expires_at);

-- ============================================================================
-- API KEYS
-- ============================================================================
CREATE TABLE api_keys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  key_hash varchar(255) NOT NULL UNIQUE,
  key_prefix varchar(10) NOT NULL,
  name varchar(255) NOT NULL,
  created_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX idx_apikey_prefix ON api_keys(key_prefix);
CREATE INDEX idx_apikey_org ON api_keys(org_id);

-- ============================================================================
-- TOOL POLICIES
-- ============================================================================
CREATE TABLE tool_policies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  tool_name varchar(255) NOT NULL,
  mode varchar(50) NOT NULL DEFAULT 'approve',
  constraints jsonb NOT NULL DEFAULT '{}'::jsonb,
  allowed_roles jsonb NOT NULL DEFAULT '["admin","analyst"]'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  CONSTRAINT uq_org_tool UNIQUE (org_id, tool_name),
  CONSTRAINT valid_mode CHECK (mode IN ('auto','approve','deny'))
);
CREATE INDEX idx_policy_org ON tool_policies(org_id);
CREATE INDEX idx_policy_tool ON tool_policies(tool_name);

-- ============================================================================
-- TOOL APPROVALS
-- ============================================================================
CREATE TABLE tool_approvals (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  tool_name varchar(255) NOT NULL,
  requested_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  status varchar(20) NOT NULL DEFAULT 'pending',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  approved_by uuid REFERENCES users(id) ON DELETE SET NULL,
  approved_at timestamptz
);
CREATE INDEX idx_tool_approvals_org ON tool_approvals(org_id);
CREATE INDEX idx_tool_approvals_tool ON tool_approvals(tool_name);
CREATE INDEX idx_tool_approvals_status ON tool_approvals(status);

-- ============================================================================
-- MODEL POLICIES
-- ============================================================================
CREATE TABLE model_policies (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  provider varchar(100) NOT NULL,
  model_name varchar(255) NOT NULL,
  max_rpm integer,
  max_tpm integer,
  max_cost_per_request double precision,
  max_daily_cost double precision,
  max_failures integer NOT NULL DEFAULT 5,
  cooldown_seconds integer NOT NULL DEFAULT 60,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  created_by uuid NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  CONSTRAINT uq_org_provider_model UNIQUE (org_id, provider, model_name)
);
CREATE INDEX idx_model_policies_org ON model_policies(org_id);
CREATE INDEX idx_model_policies_provider ON model_policies(provider);

-- ============================================================================
-- AUDIT EVENTS
-- ============================================================================
CREATE TABLE audit_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  event_type varchar(50) NOT NULL,
  timestamp timestamptz NOT NULL DEFAULT now(),
  run_id uuid,
  actor varchar(255) NOT NULL,
  payload jsonb NOT NULL,
  event_hash varchar(64) NOT NULL UNIQUE,
  prev_hash varchar(64) NOT NULL,
  CONSTRAINT valid_event_type CHECK (
    event_type IN ('request','evidence','tool','model','phi','response','error','auth','config','policy')
  )
);
CREATE INDEX idx_audit_org ON audit_events(org_id);
CREATE INDEX idx_audit_run ON audit_events(run_id);
CREATE INDEX idx_audit_type ON audit_events(event_type);
CREATE INDEX idx_audit_timestamp ON audit_events(timestamp);
CREATE INDEX idx_audit_actor ON audit_events(actor);

-- ============================================================================
-- AGENT RUNS
-- ============================================================================
CREATE TABLE agent_runs (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  actor varchar(255) NOT NULL,
  status varchar(30) NOT NULL DEFAULT 'pending',
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  started_at timestamptz,
  completed_at timestamptz
);
CREATE INDEX idx_run_actor ON agent_runs(actor);
CREATE INDEX idx_run_org ON agent_runs(org_id);
CREATE INDEX idx_run_status ON agent_runs(status);

-- ============================================================================
-- FUNCTIONS AND TRIGGERS
-- ============================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$;

CREATE TRIGGER update_organizations_updated_at
BEFORE UPDATE ON organizations
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_users_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_tool_policies_updated_at
BEFORE UPDATE ON tool_policies
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_tool_approvals_updated_at
BEFORE UPDATE ON tool_approvals
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_model_policies_updated_at
BEFORE UPDATE ON model_policies
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_agent_runs_updated_at
BEFORE UPDATE ON agent_runs
FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- ENABLE RLS
-- ============================================================================
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE tool_approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- POLICIES
-- Note: These assume auth.uid() equals users.id (same UUID space).
-- ============================================================================
-- Organizations
CREATE POLICY "Users can view their own organization"
ON organizations FOR SELECT
USING (id IN (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Admins can update their organization"
ON organizations FOR UPDATE
USING (id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'));

-- Users
CREATE POLICY "Users can view org members"
ON users FOR SELECT
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Admins can manage users"
ON users FOR ALL
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'))
WITH CHECK (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'));

-- User sessions
CREATE POLICY "Users can view their own sessions"
ON user_sessions FOR SELECT
USING (user_id = auth.uid());

-- API keys
CREATE POLICY "Users can view org api keys"
ON api_keys FOR SELECT
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Admins can manage api keys"
ON api_keys FOR ALL
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'))
WITH CHECK (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'));

-- Tool policies
CREATE POLICY "Users can view org policies"
ON tool_policies FOR SELECT
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Admins can manage policies"
ON tool_policies FOR ALL
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'))
WITH CHECK (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'));

-- Tool approvals
CREATE POLICY "Users can view org approvals"
ON tool_approvals FOR SELECT
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Users can request approvals"
ON tool_approvals FOR INSERT
WITH CHECK (org_id IN (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Admins can approve requests"
ON tool_approvals FOR UPDATE
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role IN ('admin','analyst')))
WITH CHECK (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role IN ('admin','analyst')));

-- Model policies
CREATE POLICY "Users can view model policies"
ON model_policies FOR SELECT
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Admins can manage model policies"
ON model_policies FOR ALL
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'))
WITH CHECK (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role = 'admin'));

-- Audit events (read-only via RLS; inserts via service role)
CREATE POLICY "Users can view org audit events"
ON audit_events FOR SELECT
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid()));

-- Agent runs
CREATE POLICY "Users can view org runs"
ON agent_runs FOR SELECT
USING (org_id IN (SELECT org_id FROM users WHERE id = auth.uid()));

CREATE POLICY "Analysts can create runs"
ON agent_runs FOR INSERT
WITH CHECK (org_id IN (SELECT org_id FROM users WHERE id = auth.uid() AND role IN ('admin','analyst')));

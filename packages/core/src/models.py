"""
SQLAlchemy models for ArcticCodex enterprise features.

Provides Postgres-backed persistence for:
- Organizations (multi-tenancy)
- Users (authentication)
- API Keys (programmatic access)
- Tool Policies (execution control)
- Model Policies (LLM provider settings)
- Audit Events (immutable log)
- Agent Runs (execution tracking)
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime,
    Text, ForeignKey, Enum, Index, JSON, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func

Base = declarative_base()


# ============================================================================
# ENUMS
# ============================================================================

class UserRole(str, PyEnum):
    """User roles for RBAC."""
    ADMIN = "admin"        # Full org control
    ANALYST = "analyst"    # Run agents, view results
    VIEWER = "viewer"      # Read-only access
    AUDITOR = "auditor"    # Audit log access only


class Permission(str, PyEnum):
    """Granular permissions."""
    DATA_INGEST = "data:ingest"
    AGENT_RUN = "agent:run"
    TOOL_EXECUTE = "tool:execute"
    TOOL_APPROVE = "tool:approve"
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"
    CONFIG_MANAGE = "config:manage"
    USER_MANAGE = "user:manage"


class ToolExecutionMode(str, PyEnum):
    """Tool policy execution modes."""
    AUTO = "auto"          # Execute automatically
    APPROVE = "approve"    # Require approval
    DENY = "deny"          # Block execution


class EventType(str, PyEnum):
    """Audit event types."""
    REQUEST = "request"
    EVIDENCE = "evidence"
    TOOL = "tool"
    MODEL = "model"
    PHI = "phi"
    RESPONSE = "response"
    ERROR = "error"
    AUTH = "auth"
    CONFIG = "config"
    POLICY = "policy"


# ============================================================================
# ORGANIZATIONS (Multi-Tenancy Root)
# ============================================================================

class Organization(Base):
    """
    Organization entity for multi-tenancy.
    All data is scoped to org_id.
    """
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True)  # UUID
    name = Column(String(255), nullable=False, unique=True)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    
    # Settings (JSON blob for flexibility)
    settings = Column(JSON, nullable=False, default={})
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    api_keys = relationship("APIKey", back_populates="organization", cascade="all, delete-orphan")
    tool_policies = relationship("ToolPolicy", back_populates="organization", cascade="all, delete-orphan")
    model_policies = relationship("ModelPolicy", back_populates="organization", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="organization", cascade="all, delete-orphan")
    runs = relationship("AgentRun", back_populates="organization", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_org_name', 'name'),
        Index('idx_org_active', 'is_active'),
    )


# ============================================================================
# USERS (Authentication)
# ============================================================================

class User(Base):
    """
    User entity with org membership and role.
    """
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)  # UUID
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Identity
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    
    # RBAC
    role = Column(Enum(UserRole), nullable=False, default=UserRole.VIEWER)
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_org', 'org_id'),
        Index('idx_user_active', 'is_active'),
    )


class UserSession(Base):
    """
    JWT session tracking for audit and revocation.
    """
    __tablename__ = "user_sessions"

    id = Column(String(36), primary_key=True)  # Session ID (JWT jti)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Session data
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    
    # Audit trail
    ip_address = Column(String(45), nullable=True)  # IPv6 max length
    user_agent = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")

    __table_args__ = (
        Index('idx_session_user', 'user_id'),
        Index('idx_session_expires', 'expires_at'),
    )


# ============================================================================
# API KEYS (Programmatic Access)
# ============================================================================

class APIKey(Base):
    """
    API key for programmatic access.
    Scoped to organization, associated with creator.
    """
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True)  # UUID
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Key data (hashed)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(10), nullable=False)  # First 8 chars for identification
    
    # Metadata
    name = Column(String(255), nullable=False)
    created_by = Column(String(36), nullable=False)  # User ID
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Status
    is_active = Column(Boolean, nullable=False, default=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String(36), nullable=True)
    
    # Usage tracking
    last_used_at = Column(DateTime, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="api_keys")

    __table_args__ = (
        Index('idx_apikey_org', 'org_id'),
        Index('idx_apikey_hash', 'key_hash'),
        Index('idx_apikey_prefix', 'key_prefix'),
    )


# ============================================================================
# TOOL POLICIES (Execution Control)
# ============================================================================

class ToolPolicy(Base):
    """
    Tool execution policy with constraints.
    """
    __tablename__ = "tool_policies"

    id = Column(String(36), primary_key=True)  # UUID
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Policy identity
    tool_name = Column(String(255), nullable=False)
    
    # Execution control
    mode = Column(Enum(ToolExecutionMode), nullable=False, default=ToolExecutionMode.APPROVE)
    
    # Constraints (JSON for flexibility)
    constraints = Column(JSON, nullable=False, default={})
    # Example: {"max_file_size_mb": 10, "allowed_paths": ["/data"], "network_enabled": false}
    
    # RBAC (which roles can execute)
    allowed_roles = Column(JSON, nullable=False, default=["admin", "analyst"])
    
    # Metadata
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="tool_policies")

    __table_args__ = (
        UniqueConstraint('org_id', 'tool_name', name='uq_org_tool'),
        Index('idx_policy_org', 'org_id'),
        Index('idx_policy_tool', 'tool_name'),
    )


class ToolApproval(Base):
    """
    Tool execution approval workflow.
    """
    __tablename__ = "tool_approvals"

    id = Column(String(36), primary_key=True)  # UUID
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Tool execution request
    tool_name = Column(String(255), nullable=False)
    tool_args = Column(JSON, nullable=False)
    requested_by = Column(String(36), nullable=False)  # User ID
    requested_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Run context
    run_id = Column(String(36), nullable=True)
    
    # Approval state
    status = Column(String(50), nullable=False, default="pending")  # pending, approved, denied
    reviewed_by = Column(String(36), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_note = Column(Text, nullable=True)

    __table_args__ = (
        Index('idx_approval_org', 'org_id'),
        Index('idx_approval_status', 'status'),
        Index('idx_approval_run', 'run_id'),
    )


# ============================================================================
# MODEL POLICIES (LLM Provider Settings)
# ============================================================================

class ModelPolicy(Base):
    """
    LLM provider policy with rate limits and cost caps.
    """
    __tablename__ = "model_policies"

    id = Column(String(36), primary_key=True)  # UUID
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Provider config
    provider = Column(String(100), nullable=False)  # openai, anthropic, local
    model_name = Column(String(255), nullable=False)
    
    # Rate limiting
    max_rpm = Column(Integer, nullable=True)  # Requests per minute
    max_tpm = Column(Integer, nullable=True)  # Tokens per minute
    
    # Cost controls
    max_cost_per_request = Column(Float, nullable=True)
    max_daily_cost = Column(Float, nullable=True)
    
    # Circuit breaker
    max_failures = Column(Integer, nullable=False, default=5)
    cooldown_seconds = Column(Integer, nullable=False, default=60)
    
    # Metadata
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    created_by = Column(String(36), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="model_policies")

    __table_args__ = (
        UniqueConstraint('org_id', 'provider', 'model_name', name='uq_org_provider_model'),
        Index('idx_model_policy_org', 'org_id'),
    )


# ============================================================================
# AUDIT EVENTS (Immutable Log)
# ============================================================================

class AuditEvent(Base):
    """
    Immutable audit event with hash chaining.
    """
    __tablename__ = "audit_events"

    id = Column(String(36), primary_key=True)  # UUID
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Event data
    event_type = Column(Enum(EventType), nullable=False)
    timestamp = Column(DateTime, nullable=False, server_default=func.now())
    
    # Run context
    run_id = Column(String(36), nullable=True)
    actor = Column(String(255), nullable=False)  # User email or API key prefix
    
    # Event payload
    payload = Column(JSON, nullable=False)
    
    # Hash chaining (immutability)
    event_hash = Column(String(64), nullable=False, unique=True)
    prev_hash = Column(String(64), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="audit_events")

    __table_args__ = (
        Index('idx_audit_org', 'org_id'),
        Index('idx_audit_run', 'run_id'),
        Index('idx_audit_type', 'event_type'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_actor', 'actor'),
    )


# ============================================================================
# AGENT RUNS (Execution Tracking)
# ============================================================================

class AgentRun(Base):
    """
    Agent execution tracking with cost and status.
    """
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True)  # UUID
    org_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    
    # Run metadata
    query = Column(Text, nullable=False)
    actor = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    # Execution status
    status = Column(String(50), nullable=False, default="running")  # running, completed, failed
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    
    # Results
    response = Column(Text, nullable=True)
    evidence_chunks = Column(JSON, nullable=True)  # List of chunk IDs
    tool_calls = Column(JSON, nullable=True)  # Tool execution summary
    
    # Cost tracking
    total_cost = Column(Float, nullable=False, default=0.0)
    total_tokens = Column(Integer, nullable=False, default=0)
    
    # Φ tracking
    phi_count = Column(Integer, nullable=False, default=0)
    phi_claims = Column(JSON, nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="runs")

    __table_args__ = (
        Index('idx_run_org', 'org_id'),
        Index('idx_run_status', 'status'),
        Index('idx_run_created', 'created_at'),
        Index('idx_run_actor', 'actor'),
    )


# ============================================================================
# DATABASE UTILITIES
# ============================================================================

def create_db_engine(database_url: str):
    """Create SQLAlchemy engine."""
    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False  # Set to True for SQL logging
    )


def create_all_tables(engine):
    """Create all tables (use Alembic in production)."""
    Base.metadata.create_all(engine)


def get_session_maker(engine):
    """Get session maker for database operations."""
    return sessionmaker(bind=engine, expire_on_commit=False)

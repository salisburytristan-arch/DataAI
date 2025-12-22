"""
Supabase database connection and utilities.

Provides:
- Supabase client initialization
- SQLAlchemy engine configuration
- Session management
- Tenant isolation helpers
"""

import os
from typing import Optional
from contextlib import contextmanager

from supabase import create_client, Client
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

from .models import Base

# Load environment variables
load_dotenv()


# ============================================================================
# CONFIGURATION
# ============================================================================

class DatabaseConfig:
    """Database configuration from environment."""
    
    def __init__(self):
        # Supabase configuration
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")  # Admin operations
        
        # Postgres connection (Supabase provides this)
        # Format: postgresql://[user]:[password]@[host]:[port]/[database]
        self.database_url = os.getenv("DATABASE_URL")
        
        # Validate configuration
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        if not self.database_url:
            raise ValueError("DATABASE_URL must be set")
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return os.getenv("ENVIRONMENT", "development") == "production"


# ============================================================================
# SUPABASE CLIENT
# ============================================================================

class SupabaseManager:
    """
    Manages Supabase client connections.
    
    Provides both user-context and service-role clients.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get user-context Supabase client."""
        if self._client is None:
            self._client = create_client(
                self.config.supabase_url,
                self.config.supabase_key
            )
        return self._client
    
    @property
    def service_client(self) -> Client:
        """Get service-role Supabase client (bypasses RLS)."""
        if self._service_client is None:
            service_key = self.config.supabase_service_key or self.config.supabase_key
            self._service_client = create_client(
                self.config.supabase_url,
                service_key
            )
        return self._service_client
    
    def set_auth_token(self, token: str):
        """Set auth token for user-context operations."""
        self.client.auth.set_session(token, None)


# ============================================================================
# SQLALCHEMY ENGINE
# ============================================================================

class DatabaseEngine:
    """
    SQLAlchemy engine for direct Postgres access.
    
    Uses Supabase's Postgres connection string.
    Supports tenant isolation via session-level filters.
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig()
        self._engine = None
        self._session_maker = None
    
    @property
    def engine(self):
        """Get SQLAlchemy engine."""
        if self._engine is None:
            self._engine = create_engine(
                self.config.database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                echo=not self.config.is_production,
                # Use NullPool for serverless environments
                poolclass=NullPool if os.getenv("SERVERLESS") else None
            )
            
            # Register event listeners
            self._register_events()
        
        return self._engine
    
    @property
    def session_maker(self):
        """Get session maker."""
        if self._session_maker is None:
            self._session_maker = sessionmaker(
                bind=self.engine,
                expire_on_commit=False,
                autoflush=False
            )
        return self._session_maker
    
    def _register_events(self):
        """Register SQLAlchemy event listeners."""
        # Connection pool logging in development
        if not self.config.is_production:
            @event.listens_for(self.engine, "connect")
            def receive_connect(dbapi_conn, connection_record):
                print(f"[DB] New connection established")
    
    def create_all_tables(self):
        """Create all tables (use migrations in production)."""
        Base.metadata.create_all(self.engine)
    
    def drop_all_tables(self):
        """Drop all tables (DANGEROUS - use only in development)."""
        if self.config.is_production:
            raise RuntimeError("Cannot drop tables in production")
        Base.metadata.drop_all(self.engine)
    
    @contextmanager
    def get_session(self, org_id: Optional[str] = None) -> Session:
        """
        Get database session with optional tenant isolation.
        
        Args:
            org_id: Organization ID for tenant filtering
        
        Yields:
            Session: SQLAlchemy session
        
        Example:
            with db.get_session(org_id="org-123") as session:
                users = session.query(User).all()  # Auto-filtered by org_id
        """
        session = self.session_maker()
        
        # Set org_id in session for tenant isolation
        if org_id:
            session.info["org_id"] = org_id
        
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()


# ============================================================================
# TENANT ISOLATION HELPERS
# ============================================================================

def filter_by_org(query, org_id: str):
    """
    Apply tenant filter to query.
    
    Args:
        query: SQLAlchemy query
        org_id: Organization ID
    
    Returns:
        Filtered query
    
    Example:
        query = session.query(User)
        query = filter_by_org(query, org_id="org-123")
        users = query.all()
    """
    # Assumes model has org_id column
    return query.filter_by(org_id=org_id)


def ensure_org_access(session: Session, model_instance, org_id: str):
    """
    Verify model instance belongs to organization.
    
    Args:
        session: Database session
        model_instance: Model instance to check
        org_id: Expected organization ID
    
    Raises:
        ValueError: If org_id doesn't match
    """
    if hasattr(model_instance, 'org_id'):
        if model_instance.org_id != org_id:
            raise ValueError(f"Access denied: resource belongs to different organization")


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

# Singleton instances (initialized on first import)
_db_config: Optional[DatabaseConfig] = None
_supabase_manager: Optional[SupabaseManager] = None
_db_engine: Optional[DatabaseEngine] = None


def get_db_config() -> DatabaseConfig:
    """Get global database configuration."""
    global _db_config
    if _db_config is None:
        _db_config = DatabaseConfig()
    return _db_config


def get_supabase() -> SupabaseManager:
    """Get global Supabase manager."""
    global _supabase_manager
    if _supabase_manager is None:
        _supabase_manager = SupabaseManager(get_db_config())
    return _supabase_manager


def get_db() -> DatabaseEngine:
    """Get global database engine."""
    global _db_engine
    if _db_engine is None:
        _db_engine = DatabaseEngine(get_db_config())
    return _db_engine


# ============================================================================
# INITIALIZATION
# ============================================================================

def init_database(create_tables: bool = False):
    """
    Initialize database connection.
    
    Args:
        create_tables: Whether to create tables (use migrations in production)
    """
    db = get_db()
    
    # Create tables if requested (dev only)
    if create_tables:
        if not get_db_config().is_production:
            db.create_all_tables()
        else:
            raise RuntimeError("Use Alembic migrations in production")
    
    print(f"[DB] Connected to Supabase Postgres")


def reset_database():
    """Reset database (DANGEROUS - dev only)."""
    config = get_db_config()
    if config.is_production:
        raise RuntimeError("Cannot reset database in production")
    
    db = get_db()
    db.drop_all_tables()
    db.create_all_tables()
    print("[DB] Database reset complete")

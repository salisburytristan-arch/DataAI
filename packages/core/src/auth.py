"""
Authentication, Authorization, and Multi-Tenancy

User management, API keys, RBAC, and org-scoped access control.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Literal
from enum import Enum
import hashlib
import secrets
import json
import os
from pathlib import Path
from datetime import datetime


class Permission(Enum):
    """System permissions"""
    DATA_INGEST = "data:ingest"
    AGENT_RUN = "agent:run"
    TOOL_EXECUTE = "tool:execute"
    TOOL_APPROVE = "tool:approve"
    AUDIT_VIEW = "audit:view"
    AUDIT_EXPORT = "audit:export"
    CONFIG_MANAGE = "config:manage"
    USER_MANAGE = "user:manage"


class Role(Enum):
    """User roles"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    AUDITOR = "auditor"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.DATA_INGEST,
        Permission.AGENT_RUN,
        Permission.TOOL_EXECUTE,
        Permission.TOOL_APPROVE,
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
        Permission.CONFIG_MANAGE,
        Permission.USER_MANAGE,
    },
    Role.ANALYST: {
        Permission.DATA_INGEST,
        Permission.AGENT_RUN,
        Permission.TOOL_EXECUTE,
        Permission.AUDIT_VIEW,
    },
    Role.VIEWER: {
        Permission.AUDIT_VIEW,
    },
    Role.AUDITOR: {
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
    },
}


@dataclass
class Organization:
    """Organization (tenant)"""
    org_id: str
    name: str
    vault_dir: str
    created_at: str
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "org_id": self.org_id,
            "name": self.name,
            "vault_dir": self.vault_dir,
            "created_at": self.created_at,
            "metadata": self.metadata
        }


@dataclass
class APIKey:
    """API key for programmatic access"""
    key_id: str
    key_hash: str  # SHA256(key)
    name: str
    created_at: str
    last_used_at: Optional[str] = None
    expires_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "name": self.name,
            "created_at": self.created_at,
            "last_used_at": self.last_used_at,
            "expires_at": self.expires_at
        }


@dataclass
class User:
    """System user"""
    user_id: str
    email: str
    org_id: str
    role: Role
    password_hash: Optional[str] = None  # SHA256(password + salt)
    salt: Optional[str] = None
    api_keys: List[APIKey] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    last_login_at: Optional[str] = None
    metadata: Dict[str, any] = field(default_factory=dict)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has permission"""
        return permission in ROLE_PERMISSIONS.get(self.role, set())
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "org_id": self.org_id,
            "role": self.role.value,
            "password_hash": self.password_hash,
            "salt": self.salt,
            "created_at": self.created_at,
            "last_login_at": self.last_login_at,
            "api_keys": [key.to_dict() for key in self.api_keys],
            "metadata": self.metadata
        }


class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self, storage_dir: str = "./auth_data"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.users_file = self.storage_dir / "users.json"
        self.orgs_file = self.storage_dir / "organizations.json"
        self.sessions_file = self.storage_dir / "sessions.json"
        
        self.users: Dict[str, User] = {}
        self.orgs: Dict[str, Organization] = {}
        self.sessions: Dict[str, Dict[str, any]] = {}  # session_token -> user_id, org_id
        
        self._load_data()
    
    def _load_data(self):
        """Load users and orgs from disk"""
        if self.users_file.exists():
            with open(self.users_file, 'r') as f:
                users_data = json.load(f)
                for user_data in users_data:
                    user = User(
                        user_id=user_data['user_id'],
                        email=user_data['email'],
                        org_id=user_data['org_id'],
                        role=Role(user_data['role']),
                        password_hash=user_data.get('password_hash'),
                        salt=user_data.get('salt'),
                        created_at=user_data['created_at'],
                        last_login_at=user_data.get('last_login_at'),
                        metadata=user_data.get('metadata', {})
                    )
                    # Load API keys
                    for key_data in user_data.get('api_keys', []):
                        api_key = APIKey(**key_data)
                        user.api_keys.append(api_key)
                    self.users[user.user_id] = user
        
        if self.orgs_file.exists():
            with open(self.orgs_file, 'r') as f:
                orgs_data = json.load(f)
                for org_data in orgs_data:
                    org = Organization(**org_data)
                    self.orgs[org.org_id] = org
        
        if self.sessions_file.exists():
            with open(self.sessions_file, 'r') as f:
                self.sessions = json.load(f)
    
    def _save_data(self):
        """Save users and orgs to disk"""
        with open(self.users_file, 'w') as f:
            users_data = [user.to_dict() for user in self.users.values()]
            json.dump(users_data, f, indent=2)
        
        with open(self.orgs_file, 'w') as f:
            orgs_data = [org.to_dict() for org in self.orgs.values()]
            json.dump(orgs_data, f, indent=2)
        
        with open(self.sessions_file, 'w') as f:
            json.dump(self.sessions, f, indent=2)
    
    def create_organization(self, name: str, vault_dir: str) -> Organization:
        """Create new organization"""
        org_id = f"org_{secrets.token_hex(8)}"
        org = Organization(
            org_id=org_id,
            name=name,
            vault_dir=vault_dir,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        self.orgs[org_id] = org
        self._save_data()
        return org
    
    def create_user(
        self,
        email: str,
        org_id: str,
        role: Role,
        password: Optional[str] = None
    ) -> User:
        """Create new user"""
        if org_id not in self.orgs:
            raise ValueError(f"Organization {org_id} not found")
        
        user_id = f"user_{secrets.token_hex(8)}"
        
        # Hash password if provided
        password_hash = None
        salt = None
        if password:
            salt = secrets.token_hex(16)
            password_hash = hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
        
        user = User(
            user_id=user_id,
            email=email,
            org_id=org_id,
            role=role,
            password_hash=password_hash,
            salt=salt
        )
        
        self.users[user_id] = user
        self._save_data()
        return user
    
    def authenticate_password(self, email: str, password: str) -> Optional[User]:
        """Authenticate with email/password"""
        for user in self.users.values():
            if user.email == email:
                if not user.password_hash or not user.salt:
                    return None
                
                # Verify password
                password_hash = hashlib.sha256(f"{password}{user.salt}".encode()).hexdigest()
                if password_hash == user.password_hash:
                    user.last_login_at = datetime.utcnow().isoformat() + "Z"
                    self._save_data()
                    return user
        
        return None
    
    def create_api_key(self, user_id: str, name: str) -> tuple[str, APIKey]:
        """
        Create API key for user.
        Returns (plaintext_key, api_key_object).
        """
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        # Generate key
        plaintext_key = f"ac_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()
        
        api_key = APIKey(
            key_id=f"key_{secrets.token_hex(8)}",
            key_hash=key_hash,
            name=name,
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
        self.users[user_id].api_keys.append(api_key)
        self._save_data()
        
        return plaintext_key, api_key
    
    def authenticate_api_key(self, plaintext_key: str) -> Optional[User]:
        """Authenticate with API key"""
        key_hash = hashlib.sha256(plaintext_key.encode()).hexdigest()
        
        for user in self.users.values():
            for api_key in user.api_keys:
                if api_key.key_hash == key_hash:
                    # Update last used
                    api_key.last_used_at = datetime.utcnow().isoformat() + "Z"
                    self._save_data()
                    return user
        
        return None
    
    def create_session(self, user_id: str) -> str:
        """Create session token"""
        if user_id not in self.users:
            raise ValueError(f"User {user_id} not found")
        
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            "user_id": user_id,
            "org_id": self.users[user_id].org_id,
            "created_at": datetime.utcnow().isoformat() + "Z"
        }
        self._save_data()
        return session_token
    
    def get_session(self, session_token: str) -> Optional[tuple[User, Organization]]:
        """Get user and org from session token"""
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        user_id = session['user_id']
        org_id = session['org_id']
        
        if user_id not in self.users or org_id not in self.orgs:
            return None
        
        return self.users[user_id], self.orgs[org_id]
    
    def delete_session(self, session_token: str):
        """Delete session (logout)"""
        if session_token in self.sessions:
            del self.sessions[session_token]
            self._save_data()
    
    def authorize(self, user: User, permission: Permission) -> bool:
        """Check if user has permission"""
        return user.has_permission(permission)
    
    def get_org_users(self, org_id: str) -> List[User]:
        """Get all users in org"""
        return [u for u in self.users.values() if u.org_id == org_id]


# Example usage
if __name__ == "__main__":
    auth = AuthManager(storage_dir="./test_auth")
    
    # Create org
    org = auth.create_organization(name="Demo Corp", vault_dir="./demo_vault")
    print(f"Created org: {org.org_id}")
    
    # Create users
    admin = auth.create_user(email="admin@demo.com", org_id=org.org_id, role=Role.ADMIN, password="admin123")
    analyst = auth.create_user(email="analyst@demo.com", org_id=org.org_id, role=Role.ANALYST, password="analyst123")
    
    print(f"Created admin: {admin.user_id}")
    print(f"Created analyst: {analyst.user_id}")
    
    # Test auth
    authenticated = auth.authenticate_password("admin@demo.com", "admin123")
    print(f"Authenticated: {authenticated.email if authenticated else 'Failed'}")
    
    # Create API key
    plaintext_key, api_key = auth.create_api_key(admin.user_id, "CLI Key")
    print(f"API Key: {plaintext_key}")
    
    # Test API key auth
    key_user = auth.authenticate_api_key(plaintext_key)
    print(f"API Key user: {key_user.email if key_user else 'Failed'}")
    
    # Test permissions
    print(f"Admin can run agent: {admin.has_permission(Permission.AGENT_RUN)}")
    print(f"Analyst can manage config: {analyst.has_permission(Permission.CONFIG_MANAGE)}")
    
    # Create session
    session_token = auth.create_session(admin.user_id)
    print(f"Session token: {session_token}")
    
    # Get session
    session_user, session_org = auth.get_session(session_token)
    print(f"Session user: {session_user.email}, org: {session_org.name}")

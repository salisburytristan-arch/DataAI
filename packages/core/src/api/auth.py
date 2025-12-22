"""
FastAPI authentication endpoints.

Provides:
- POST /auth/register - Create first org + admin user
- POST /auth/login - Email/password authentication
- POST /auth/logout - Revoke session
- GET /auth/me - Get current user info
- GET /auth/sessions - List user sessions
- DELETE /auth/sessions/{id} - Revoke specific session

- GET /orgs - List user's organization
- POST /orgs/{id}/invite - Invite user to org
- GET /orgs/{id}/members - List org members
- PATCH /orgs/{id}/members/{user_id} - Update member role
- DELETE /orgs/{id}/members/{user_id} - Remove member

- GET /api-keys - List org API keys
- POST /api-keys - Create API key
- DELETE /api-keys/{id} - Revoke API key
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
import jwt
import bcrypt

from ..models import Organization, User, UserSession, APIKey, UserRole
from ..db import get_db, filter_by_org, ensure_org_access

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = int(os.getenv("JWT_EXPIRATION", "86400"))  # 24 hours

router = APIRouter(prefix="/auth", tags=["Authentication"])
org_router = APIRouter(prefix="/orgs", tags=["Organizations"])
apikey_router = APIRouter(prefix="/api-keys", tags=["API Keys"])

security = HTTPBearer()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RegisterRequest(BaseModel):
    """First-time registration: creates org + admin user."""
    org_name: str = Field(..., min_length=3, max_length=100)
    org_display_name: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    """Email/password login."""
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserInfo(BaseModel):
    """Current user information."""
    id: str
    org_id: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]


class InviteUserRequest(BaseModel):
    """Invite user to organization."""
    email: EmailStr
    full_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    password: str = Field(..., min_length=8)


class UpdateMemberRequest(BaseModel):
    """Update member role."""
    role: UserRole


class CreateAPIKeyRequest(BaseModel):
    """Create API key."""
    name: str = Field(..., min_length=3, max_length=255)


class APIKeyResponse(BaseModel):
    """API key creation response."""
    id: str
    key: str  # Only returned once
    key_prefix: str
    name: str
    created_at: datetime


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_db_session():
    """Get database session."""
    db = get_db()
    with db.get_session() as session:
        yield session


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_jwt_token(user: User) -> dict:
    """Create JWT token for user."""
    session_id = str(uuid4())
    expires_at = datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
    
    payload = {
        "sub": str(user.id),
        "jti": session_id,
        "org_id": str(user.org_id),
        "email": user.email,
        "role": user.role.value,
        "exp": expires_at,
        "iat": datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "token": token,
        "session_id": session_id,
        "expires_at": expires_at
    }


def decode_jwt_token(token: str) -> dict:
    """Decode and validate JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db_session)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    # Verify session is not revoked
    user_session = session.query(UserSession).filter_by(
        id=payload["jti"]
    ).first()
    
    if user_session and user_session.revoked_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session revoked"
        )
    
    # Get user
    user = session.query(User).filter_by(id=payload["sub"]).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    return user


def require_role(*allowed_roles: UserRole):
    """Dependency to require specific role."""
    def check_role(user: User = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {user.role} not authorized"
            )
        return user
    return check_role


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@router.post("/register", response_model=LoginResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    session: Session = Depends(get_db_session),
    x_client_ip: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None)
):
    """
    Register first organization and admin user.
    
    Creates:
    - New organization
    - Admin user with full permissions
    - Initial session
    
    Returns JWT token for immediate login.
    """
    # Check if org name is taken
    existing_org = session.query(Organization).filter_by(name=request.org_name).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization name already taken"
        )
    
    # Check if email is taken
    existing_user = session.query(User).filter_by(email=request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create organization
    org = Organization(
        id=str(uuid4()),
        name=request.org_name,
        display_name=request.org_display_name,
        settings={},
        is_active=True
    )
    session.add(org)
    
    # Create admin user
    user = User(
        id=str(uuid4()),
        org_id=org.id,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=UserRole.ADMIN,
        is_active=True
    )
    session.add(user)
    session.flush()
    
    # Create session
    token_data = create_jwt_token(user)
    user_session = UserSession(
        id=token_data["session_id"],
        user_id=user.id,
        expires_at=token_data["expires_at"],
        ip_address=x_client_ip,
        user_agent=user_agent
    )
    session.add(user_session)
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    session.commit()
    
    return LoginResponse(
        access_token=token_data["token"],
        expires_in=JWT_EXPIRATION,
        user={
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "org_id": str(user.org_id)
        }
    )


@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    session: Session = Depends(get_db_session),
    x_client_ip: Optional[str] = Header(None),
    user_agent: Optional[str] = Header(None)
):
    """
    Authenticate with email and password.
    
    Returns JWT token for subsequent requests.
    """
    # Find user
    user = session.query(User).filter_by(email=request.email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create session
    token_data = create_jwt_token(user)
    user_session = UserSession(
        id=token_data["session_id"],
        user_id=user.id,
        expires_at=token_data["expires_at"],
        ip_address=x_client_ip,
        user_agent=user_agent
    )
    session.add(user_session)
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    
    session.commit()
    
    return LoginResponse(
        access_token=token_data["token"],
        expires_in=JWT_EXPIRATION,
        user={
            "id": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "org_id": str(user.org_id),
            "full_name": user.full_name
        }
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    user: User = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_db_session)
):
    """
    Revoke current session.
    """
    token = credentials.credentials
    payload = decode_jwt_token(token)
    
    # Revoke session
    user_session = session.query(UserSession).filter_by(id=payload["jti"]).first()
    if user_session:
        user_session.revoked_at = datetime.utcnow()
        session.commit()


@router.get("/me", response_model=UserInfo)
def get_me(user: User = Depends(get_current_user)):
    """Get current user information."""
    return UserInfo(
        id=str(user.id),
        org_id=str(user.org_id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login_at=user.last_login_at
    )


@router.get("/sessions")
def list_sessions(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """List user's active sessions."""
    sessions = session.query(UserSession).filter_by(
        user_id=user.id
    ).order_by(UserSession.created_at.desc()).all()
    
    return [
        {
            "id": str(s.id),
            "created_at": s.created_at,
            "expires_at": s.expires_at,
            "revoked_at": s.revoked_at,
            "ip_address": s.ip_address,
            "is_active": s.revoked_at is None and s.expires_at > datetime.utcnow()
        }
        for s in sessions
    ]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(
    session_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """Revoke specific session."""
    user_session = session.query(UserSession).filter_by(
        id=session_id,
        user_id=user.id
    ).first()
    
    if not user_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    user_session.revoked_at = datetime.utcnow()
    session.commit()


# ============================================================================
# ORGANIZATION ENDPOINTS
# ============================================================================

@org_router.get("")
def get_organization(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """Get user's organization."""
    org = session.query(Organization).filter_by(id=user.org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return {
        "id": str(org.id),
        "name": org.name,
        "display_name": org.display_name,
        "created_at": org.created_at,
        "settings": org.settings,
        "is_active": org.is_active
    }


@org_router.post("/{org_id}/invite", status_code=status.HTTP_201_CREATED)
def invite_user(
    org_id: str,
    request: InviteUserRequest,
    user: User = Depends(require_role(UserRole.ADMIN)),
    session: Session = Depends(get_db_session)
):
    """Invite user to organization (admin only)."""
    # Verify org access
    if str(user.org_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Check if email already exists
    existing = session.query(User).filter_by(email=request.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    new_user = User(
        id=str(uuid4()),
        org_id=org_id,
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        role=request.role,
        is_active=True
    )
    session.add(new_user)
    session.commit()
    
    return {
        "id": str(new_user.id),
        "email": new_user.email,
        "role": new_user.role.value,
        "created_at": new_user.created_at
    }


@org_router.get("/{org_id}/members")
def list_members(
    org_id: str,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """List organization members."""
    # Verify org access
    if str(user.org_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    members = session.query(User).filter_by(org_id=org_id).all()
    
    return [
        {
            "id": str(m.id),
            "email": m.email,
            "full_name": m.full_name,
            "role": m.role.value,
            "is_active": m.is_active,
            "created_at": m.created_at,
            "last_login_at": m.last_login_at
        }
        for m in members
    ]


@org_router.patch("/{org_id}/members/{user_id}")
def update_member(
    org_id: str,
    user_id: str,
    request: UpdateMemberRequest,
    user: User = Depends(require_role(UserRole.ADMIN)),
    session: Session = Depends(get_db_session)
):
    """Update member role (admin only)."""
    # Verify org access
    if str(user.org_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get member
    member = session.query(User).filter_by(id=user_id, org_id=org_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Prevent self-demotion
    if str(member.id) == str(user.id) and request.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )
    
    member.role = request.role
    session.commit()
    
    return {"id": str(member.id), "role": member.role.value}


@org_router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(
    org_id: str,
    user_id: str,
    user: User = Depends(require_role(UserRole.ADMIN)),
    session: Session = Depends(get_db_session)
):
    """Remove member from organization (admin only)."""
    # Verify org access
    if str(user.org_id) != org_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get member
    member = session.query(User).filter_by(id=user_id, org_id=org_id).first()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )
    
    # Prevent self-removal
    if str(member.id) == str(user.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself"
        )
    
    session.delete(member)
    session.commit()


# ============================================================================
# API KEY ENDPOINTS
# ============================================================================

def generate_api_key() -> tuple[str, str, str]:
    """
    Generate API key.
    
    Returns:
        (key, key_hash, key_prefix)
    """
    key = f"ac_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    key_prefix = key[:10]
    return key, key_hash, key_prefix


@apikey_router.get("")
def list_api_keys(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db_session)
):
    """List organization API keys."""
    keys = session.query(APIKey).filter_by(org_id=user.org_id).order_by(
        APIKey.created_at.desc()
    ).all()
    
    return [
        {
            "id": str(k.id),
            "name": k.name,
            "key_prefix": k.key_prefix,
            "created_at": k.created_at,
            "is_active": k.is_active,
            "last_used_at": k.last_used_at
        }
        for k in keys
    ]


@apikey_router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    request: CreateAPIKeyRequest,
    user: User = Depends(require_role(UserRole.ADMIN)),
    session: Session = Depends(get_db_session)
):
    """Create API key (admin only)."""
    key, key_hash, key_prefix = generate_api_key()
    
    api_key = APIKey(
        id=str(uuid4()),
        org_id=user.org_id,
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=request.name,
        created_by=str(user.id),
        is_active=True
    )
    session.add(api_key)
    session.commit()
    
    return APIKeyResponse(
        id=str(api_key.id),
        key=key,  # Only returned once!
        key_prefix=key_prefix,
        name=api_key.name,
        created_at=api_key.created_at
    )


@apikey_router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_api_key(
    key_id: str,
    user: User = Depends(require_role(UserRole.ADMIN)),
    session: Session = Depends(get_db_session)
):
    """Revoke API key (admin only)."""
    api_key = session.query(APIKey).filter_by(
        id=key_id,
        org_id=user.org_id
    ).first()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    api_key.is_active = False
    api_key.revoked_at = datetime.utcnow()
    api_key.revoked_by = str(user.id)
    session.commit()

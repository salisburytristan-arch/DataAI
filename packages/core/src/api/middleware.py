"""
RBAC middleware for ArcticCodex.

Enforces:
- JWT token validation
- Organization scoping
- Role-based permission checks
- Tenant isolation on all routes
- Audit logging of access
"""

from typing import Optional, List, Callable
from datetime import datetime
from uuid import uuid4

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from ..models import User, UserRole, Permission, AuditEvent, EventType
from ..db import get_db
from .auth import decode_jwt_token, get_current_user, HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

security = HTTPBearer()


# ============================================================================
# PERMISSION MAPPING
# ============================================================================

# Role -> Permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.DATA_INGEST,
        Permission.AGENT_RUN,
        Permission.TOOL_EXECUTE,
        Permission.TOOL_APPROVE,
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
        Permission.CONFIG_MANAGE,
        Permission.USER_MANAGE,
    ],
    UserRole.ANALYST: [
        Permission.DATA_INGEST,
        Permission.AGENT_RUN,
        Permission.TOOL_EXECUTE,
        Permission.AUDIT_VIEW,
    ],
    UserRole.VIEWER: [
        Permission.AUDIT_VIEW,
    ],
    UserRole.AUDITOR: [
        Permission.AUDIT_VIEW,
        Permission.AUDIT_EXPORT,
    ],
}

# Route -> Required permission mapping
ROUTE_PERMISSIONS = {
    # Auth routes (public)
    ("POST", "/auth/register"): None,
    ("POST", "/auth/login"): None,
    
    # Auth routes (authenticated but no extra permission)
    ("POST", "/auth/logout"): None,
    ("GET", "/auth/me"): None,
    ("GET", "/auth/sessions"): None,
    ("DELETE", "/auth/sessions/{session_id}"): None,
    
    # Organization routes
    ("GET", "/orgs"): None,  # View own org
    ("POST", "/orgs/{org_id}/invite"): Permission.USER_MANAGE,
    ("GET", "/orgs/{org_id}/members"): None,
    ("PATCH", "/orgs/{org_id}/members/{user_id}"): Permission.USER_MANAGE,
    ("DELETE", "/orgs/{org_id}/members/{user_id}"): Permission.USER_MANAGE,
    
    # API Key routes
    ("GET", "/api-keys"): None,  # View own org's keys
    ("POST", "/api-keys"): Permission.USER_MANAGE,
    ("DELETE", "/api-keys/{key_id}"): Permission.USER_MANAGE,
    
    # Agent execution routes
    ("POST", "/agents/run"): Permission.AGENT_RUN,
    ("GET", "/runs"): None,  # View own org's runs
    ("GET", "/runs/{run_id}"): None,
    
    # Tool execution routes
    ("POST", "/tools/execute"): Permission.TOOL_EXECUTE,
    ("GET", "/tools/approvals"): Permission.TOOL_APPROVE,
    ("PATCH", "/tools/approvals/{approval_id}"): Permission.TOOL_APPROVE,
    
    # Tool policy routes
    ("GET", "/tool-policies"): None,  # View own org's policies
    ("POST", "/tool-policies"): Permission.CONFIG_MANAGE,
    ("PATCH", "/tool-policies/{policy_id}"): Permission.CONFIG_MANAGE,
    ("DELETE", "/tool-policies/{policy_id}"): Permission.CONFIG_MANAGE,
    
    # Model policy routes
    ("GET", "/model-policies"): None,
    ("POST", "/model-policies"): Permission.CONFIG_MANAGE,
    ("PATCH", "/model-policies/{policy_id}"): Permission.CONFIG_MANAGE,
    
    # Audit routes
    ("GET", "/audit/events"): Permission.AUDIT_VIEW,
    ("GET", "/audit/events/{event_id}"): Permission.AUDIT_VIEW,
    ("POST", "/audit/export"): Permission.AUDIT_EXPORT,
    
    # Vault/data routes
    ("POST", "/vault/ingest"): Permission.DATA_INGEST,
    ("GET", "/vault/chunks"): None,  # View own org's chunks
}


# ============================================================================
# CONTEXT CLASS
# ============================================================================

class RequestContext:
    """Request context with user/org/permission info."""
    
    def __init__(
        self,
        user_id: str,
        org_id: str,
        email: str,
        role: UserRole,
        session_id: str,
        permissions: List[Permission]
    ):
        self.user_id = user_id
        self.org_id = org_id
        self.email = email
        self.role = role
        self.session_id = session_id
        self.permissions = permissions
        self.timestamp = datetime.utcnow()
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has permission."""
        return permission in self.permissions
    
    def log_audit(self, session: Session, event_type: EventType, payload: dict):
        """Log audit event for this request."""
        from .auth import create_jwt_token
        
        audit_event = AuditEvent(
            id=str(uuid4()),
            org_id=self.org_id,
            event_type=event_type,
            timestamp=datetime.utcnow(),
            actor=self.email,
            payload=payload
        )
        
        # Hash chaining
        prev_events = session.query(AuditEvent).filter_by(
            org_id=self.org_id
        ).order_by(AuditEvent.timestamp.desc()).first()
        
        if prev_events:
            audit_event.prev_hash = prev_events.event_hash
        else:
            audit_event.prev_hash = "0" * 64
        
        # Compute event hash (simplified - full implementation in audit_stream.py)
        import hashlib
        hash_input = f"{audit_event.prev_hash}{str(payload)}".encode()
        audit_event.event_hash = hashlib.sha256(hash_input).hexdigest()
        
        session.add(audit_event)
        session.commit()


# ============================================================================
# MIDDLEWARE
# ============================================================================

class RBACMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for RBAC enforcement.
    
    Handles:
    - JWT extraction and validation
    - Permission checking against route requirements
    - Tenant isolation (org_id filtering)
    - Audit logging of access
    - Fail-closed (deny by default)
    """
    
    # Routes that don't require authentication
    PUBLIC_ROUTES = {
        ("POST", "/auth/register"),
        ("POST", "/auth/login"),
        ("GET", "/health"),
    }
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        """
        Process request through RBAC pipeline.
        """
        method = request.method
        path = request.url.path
        
        # Skip middleware for public routes
        if (method, path) in self.PUBLIC_ROUTES:
            return await call_next(request)
        
        # Extract JWT token
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing or invalid authorization"}
            )
        
        token = auth_header.split(" ", 1)[1]
        
        # Decode JWT
        try:
            payload = decode_jwt_token(token)
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"}
            )
        
        # Get database session
        db = get_db()
        with db.get_session(org_id=payload["org_id"]) as session:
            # Get user from database
            user = session.query(User).filter_by(id=payload["sub"]).first()
            if not user or not user.is_active:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found or inactive"}
                )
            
            # Get user permissions
            permissions = ROLE_PERMISSIONS.get(user.role, [])
            
            # Create request context
            context = RequestContext(
                user_id=str(user.id),
                org_id=str(user.org_id),
                email=user.email,
                role=user.role,
                session_id=payload["jti"],
                permissions=permissions
            )
            
            # Check route permission
            required_permission = self._get_required_permission(method, path)
            if required_permission and required_permission not in permissions:
                # Log unauthorized access attempt
                context.log_audit(
                    session,
                    EventType.AUTH,
                    {
                        "action": "unauthorized_access",
                        "method": method,
                        "path": path,
                        "reason": f"Missing permission {required_permission.value}"
                    }
                )
                
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": f"Insufficient permissions: requires {required_permission.value}"}
                )
            
            # Log successful access
            context.log_audit(
                session,
                EventType.AUTH,
                {
                    "action": "access",
                    "method": method,
                    "path": path,
                    "role": user.role.value
                }
            )
            
            # Attach context to request
            request.state.context = context
            request.state.session = session
            
            # Process request
            response = await call_next(request)
            
            return response
    
    def _get_required_permission(self, method: str, path: str) -> Optional[Permission]:
        """
        Determine required permission for route.
        
        Supports path parameters like /orgs/{org_id}/members
        """
        # Try exact match first
        if (method, path) in ROUTE_PERMISSIONS:
            return ROUTE_PERMISSIONS[(method, path)]
        
        # Try pattern matching (simple)
        path_parts = path.split("/")
        for route_key, permission in ROUTE_PERMISSIONS.items():
            route_method, route_path = route_key
            if method != route_method:
                continue
            
            route_parts = route_path.split("/")
            if len(route_parts) != len(path_parts):
                continue
            
            match = True
            for i, (route_part, path_part) in enumerate(zip(route_parts, path_parts)):
                if route_part.startswith("{") and route_part.endswith("}"):
                    # Wildcard match
                    continue
                elif route_part != path_part:
                    match = False
                    break
            
            if match:
                return permission
        
        # Default: require authentication but no specific permission
        return None


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_request_context(request: Request) -> RequestContext:
    """Get request context from FastAPI request."""
    if not hasattr(request.state, "context"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Request context not available"
        )
    return request.state.context


def get_db_session(request: Request) -> Session:
    """Get database session from FastAPI request."""
    if not hasattr(request.state, "session"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database session not available"
        )
    return request.state.session


def require_permission(permission: Permission):
    """
    Dependency for explicit permission check.
    
    Usage:
        @router.post("/admin")
        def admin_route(
            context: RequestContext = Depends(get_request_context),
            _: None = Depends(require_permission(Permission.USER_MANAGE))
        ):
            ...
    """
    def check(context: RequestContext = Depends(get_request_context)):
        if not context.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions: requires {permission.value}"
            )
        return context
    
    return check


def require_role(*allowed_roles: UserRole):
    """Dependency for role check."""
    def check(context: RequestContext = Depends(get_request_context)):
        if context.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role {context.role} not authorized"
            )
        return context
    
    return check


def verify_org_access(org_id: str):
    """
    Verify user has access to organization.
    
    Usage:
        @router.get("/orgs/{org_id}/data")
        def get_org_data(
            org_id: str,
            context: RequestContext = Depends(verify_org_access)
        ):
            ...
    """
    def check(context: RequestContext = Depends(get_request_context)):
        if context.org_id != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: different organization"
            )
        return context
    
    return check

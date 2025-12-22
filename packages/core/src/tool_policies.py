"""
Tool Policy Engine

Policy-based tool execution control with allowlists, constraints, and approval workflows.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Literal
from enum import Enum
import hashlib
import json
from pathlib import Path


class ToolExecutionMode(Enum):
    """Tool execution policy modes"""
    AUTO = "auto"  # Execute automatically
    APPROVE = "approve"  # Require approval
    DENY = "deny"  # Always deny


@dataclass
class ToolConstraints:
    """Constraints for tool execution"""
    max_file_size_mb: Optional[int] = None
    max_runtime_seconds: Optional[int] = None
    max_rows_processed: Optional[int] = None
    network_enabled: bool = True
    allowed_paths: Optional[List[str]] = None  # File path restrictions
    custom_constraints: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolPolicy:
    """Policy for a specific tool"""
    tool_name: str
    mode: ToolExecutionMode
    constraints: ToolConstraints
    allowed_roles: List[str]
    requires_approval_from_role: Optional[str] = None  # e.g., "admin"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "mode": self.mode.value,
            "constraints": {
                "max_file_size_mb": self.constraints.max_file_size_mb,
                "max_runtime_seconds": self.constraints.max_runtime_seconds,
                "max_rows_processed": self.constraints.max_rows_processed,
                "network_enabled": self.constraints.network_enabled,
                "allowed_paths": self.constraints.allowed_paths,
                "custom_constraints": self.constraints.custom_constraints
            },
            "allowed_roles": self.allowed_roles,
            "requires_approval_from_role": self.requires_approval_from_role
        }


@dataclass
class ToolExecutionRequest:
    """Request to execute a tool"""
    request_id: str
    tool_name: str
    args: Dict[str, Any]
    user_id: str
    org_id: str
    session_id: str
    status: Literal["pending", "approved", "denied", "executed", "failed"]
    created_at: str
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "args_hash": hashlib.sha256(json.dumps(self.args, sort_keys=True).encode()).hexdigest(),
            "user_id": self.user_id,
            "org_id": self.org_id,
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at
        }


class ToolPolicyEngine:
    """Policy engine for tool execution control"""
    
    def __init__(self, storage_dir: str = "./tool_policies"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.policies_file = self.storage_dir / "policies.json"
        self.requests_file = self.storage_dir / "requests.json"
        
        self.policies: Dict[str, Dict[str, ToolPolicy]] = {}  # org_id -> {tool_name -> policy}
        self.pending_requests: Dict[str, ToolExecutionRequest] = {}
        
        self._load_policies()
    
    def _load_policies(self):
        """Load policies from disk"""
        if self.policies_file.exists():
            with open(self.policies_file, 'r') as f:
                policies_data = json.load(f)
                for org_id, org_policies in policies_data.items():
                    self.policies[org_id] = {}
                    for tool_name, policy_data in org_policies.items():
                        constraints = ToolConstraints(**policy_data['constraints'])
                        policy = ToolPolicy(
                            tool_name=policy_data['tool_name'],
                            mode=ToolExecutionMode(policy_data['mode']),
                            constraints=constraints,
                            allowed_roles=policy_data['allowed_roles'],
                            requires_approval_from_role=policy_data.get('requires_approval_from_role')
                        )
                        self.policies[org_id][tool_name] = policy
        
        if self.requests_file.exists():
            with open(self.requests_file, 'r') as f:
                requests_data = json.load(f)
                for request_data in requests_data:
                    request = ToolExecutionRequest(**request_data)
                    self.pending_requests[request.request_id] = request
    
    def _save_policies(self):
        """Save policies to disk"""
        policies_data = {}
        for org_id, org_policies in self.policies.items():
            policies_data[org_id] = {}
            for tool_name, policy in org_policies.items():
                policies_data[org_id][tool_name] = policy.to_dict()
        
        with open(self.policies_file, 'w') as f:
            json.dump(policies_data, f, indent=2)
        
        requests_data = [req.to_dict() for req in self.pending_requests.values()]
        with open(self.requests_file, 'w') as f:
            json.dump(requests_data, f, indent=2)
    
    def set_policy(self, org_id: str, policy: ToolPolicy):
        """Set policy for a tool in an org"""
        if org_id not in self.policies:
            self.policies[org_id] = {}
        
        self.policies[org_id][policy.tool_name] = policy
        self._save_policies()
    
    def get_policy(self, org_id: str, tool_name: str) -> Optional[ToolPolicy]:
        """Get policy for a tool"""
        if org_id in self.policies:
            return self.policies[org_id].get(tool_name)
        return None
    
    def check_execution_allowed(
        self,
        org_id: str,
        tool_name: str,
        user_role: str,
        args: Dict[str, Any]
    ) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Check if tool execution is allowed.
        Returns (allowed, reason, request_id_if_pending).
        """
        policy = self.get_policy(org_id, tool_name)
        
        # No policy = deny by default (secure by default)
        if not policy:
            return False, f"No policy defined for tool '{tool_name}'", None
        
        # Check mode
        if policy.mode == ToolExecutionMode.DENY:
            return False, f"Tool '{tool_name}' is disabled by policy", None
        
        # Check role
        if user_role not in policy.allowed_roles:
            return False, f"Role '{user_role}' not allowed to use '{tool_name}'", None
        
        # Check constraints
        constraint_error = self._check_constraints(policy.constraints, args)
        if constraint_error:
            return False, constraint_error, None
        
        # If auto mode, allow
        if policy.mode == ToolExecutionMode.AUTO:
            return True, None, None
        
        # If approve mode, return pending (request_id will be generated by caller)
        if policy.mode == ToolExecutionMode.APPROVE:
            return False, f"Tool '{tool_name}' requires approval", "pending"
        
        return False, "Unknown policy mode", None
    
    def _check_constraints(self, constraints: ToolConstraints, args: Dict[str, Any]) -> Optional[str]:
        """
        Check if args violate constraints.
        Returns error message if violated, None if ok.
        """
        # File size check (if 'file_path' or 'file_size' in args)
        if constraints.max_file_size_mb:
            file_size = args.get('file_size', 0)
            if file_size > constraints.max_file_size_mb * 1024 * 1024:
                return f"File size exceeds limit of {constraints.max_file_size_mb}MB"
        
        # Path restriction check
        if constraints.allowed_paths:
            file_path = args.get('file_path') or args.get('path')
            if file_path:
                allowed = any(file_path.startswith(allowed_path) for allowed_path in constraints.allowed_paths)
                if not allowed:
                    return f"File path '{file_path}' not in allowed paths"
        
        # Network check
        if not constraints.network_enabled:
            # Check if tool might use network (heuristic)
            if any(key in args for key in ['url', 'endpoint', 'host', 'domain']):
                return "Network access is disabled for this tool"
        
        return None
    
    def create_approval_request(self, request: ToolExecutionRequest) -> str:
        """Create approval request, returns request_id"""
        self.pending_requests[request.request_id] = request
        self._save_policies()
        return request.request_id
    
    def approve_request(self, request_id: str, approver_user_id: str) -> bool:
        """Approve pending request"""
        if request_id not in self.pending_requests:
            return False
        
        request = self.pending_requests[request_id]
        request.status = "approved"
        request.approved_by = approver_user_id
        from datetime import datetime
        request.approved_at = datetime.utcnow().isoformat() + "Z"
        
        self._save_policies()
        return True
    
    def deny_request(self, request_id: str, reason: str):
        """Deny pending request"""
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            request.status = "denied"
            request.error = reason
            self._save_policies()
    
    def get_pending_requests(self, org_id: Optional[str] = None) -> List[ToolExecutionRequest]:
        """Get pending approval requests"""
        requests = [r for r in self.pending_requests.values() if r.status == "pending"]
        if org_id:
            requests = [r for r in requests if r.org_id == org_id]
        return requests
    
    def complete_request(self, request_id: str, result: Any = None, error: Optional[str] = None):
        """Mark request as completed"""
        if request_id in self.pending_requests:
            request = self.pending_requests[request_id]
            request.status = "executed" if not error else "failed"
            request.result = result
            request.error = error
            # Move to archive (in production, would move to different storage)
            del self.pending_requests[request_id]
            self._save_policies()


# Default policies for common scenarios
def get_default_policies(org_id: str) -> List[ToolPolicy]:
    """Get default policies for a new org"""
    return [
        # File operations - auto for small files
        ToolPolicy(
            tool_name="file_read",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(
                max_file_size_mb=10,
                allowed_paths=["/workspace", "/data"]
            ),
            allowed_roles=["admin", "analyst"]
        ),
        
        # File write - requires approval
        ToolPolicy(
            tool_name="file_write",
            mode=ToolExecutionMode.APPROVE,
            constraints=ToolConstraints(
                max_file_size_mb=10,
                allowed_paths=["/workspace", "/data"]
            ),
            allowed_roles=["admin", "analyst"],
            requires_approval_from_role="admin"
        ),
        
        # Web fetch - disabled by default (network=false)
        ToolPolicy(
            tool_name="web_fetch",
            mode=ToolExecutionMode.DENY,
            constraints=ToolConstraints(network_enabled=False),
            allowed_roles=[]
        ),
        
        # Calculate - auto (safe)
        ToolPolicy(
            tool_name="calculate",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(),
            allowed_roles=["admin", "analyst", "viewer"]
        ),
        
        # Database query - requires approval
        ToolPolicy(
            tool_name="database_query",
            mode=ToolExecutionMode.APPROVE,
            constraints=ToolConstraints(max_rows_processed=1000),
            allowed_roles=["admin", "analyst"],
            requires_approval_from_role="admin"
        ),
    ]


# Example usage
if __name__ == "__main__":
    from datetime import datetime
    import secrets
    
    engine = ToolPolicyEngine(storage_dir="./test_policies")
    
    # Set up default policies for org
    org_id = "org_demo"
    for policy in get_default_policies(org_id):
        engine.set_policy(org_id, policy)
    
    print("Policies set up for org_demo")
    
    # Test execution check
    allowed, reason, pending = engine.check_execution_allowed(
        org_id="org_demo",
        tool_name="calculate",
        user_role="analyst",
        args={"expression": "2+2"}
    )
    
    print(f"Calculate allowed: {allowed}")
    
    # Test approval workflow
    allowed, reason, pending = engine.check_execution_allowed(
        org_id="org_demo",
        tool_name="file_write",
        user_role="analyst",
        args={"file_path": "/workspace/test.txt", "content": "hello"}
    )
    
    print(f"File write allowed: {allowed}, reason: {reason}")
    
    if pending == "pending":
        # Create approval request
        request = ToolExecutionRequest(
            request_id=f"req_{secrets.token_hex(8)}",
            tool_name="file_write",
            args={"file_path": "/workspace/test.txt"},
            user_id="user_123",
            org_id=org_id,
            session_id="session_001",
            status="pending",
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
        request_id = engine.create_approval_request(request)
        print(f"Created approval request: {request_id}")
        
        # List pending
        pending_requests = engine.get_pending_requests(org_id=org_id)
        print(f"Pending requests: {len(pending_requests)}")
        
        # Approve
        engine.approve_request(request_id, approver_user_id="admin_456")
        print("Request approved")

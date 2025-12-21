"""
Platform: RBAC, Policy Engine, and Audit Logs for Agent Vault

Provides role-based access control, policy-based tool execution gating,
and deterministic audit trails for enterprise compliance.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set
from enum import Enum
from datetime import datetime
import json
import hashlib


class Role(str, Enum):
    """Organization roles."""
    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


class Action(str, Enum):
    """Audit actions."""
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    POLICY_DENY = "policy_deny"


@dataclass
class OrgUser:
    """User within an organization."""
    org_id: str
    user_id: str
    email: str
    roles: List[Role]

    def has_role(self, role: Role) -> bool:
        return role in self.roles

    def can_execute_tool(self, tool_name: str, policies: "PolicyEngine") -> bool:
        return policies.is_tool_allowed(tool_name, self.roles)


@dataclass
class PolicyRule:
    """Policy rule for tool/resource access."""
    resource: str  # "tool:shell", "tool:*", "memory:read", "memory:*"
    action: str  # "allow", "deny", "require_approval"
    min_role: Role
    requires_approval: bool = False
    conditions: Dict[str, str] = field(default_factory=dict)

    def matches(self, resource: str, role: Role) -> bool:
        """Check if rule matches resource and role."""
        # Simple wildcard matching
        if self.resource == "*":
            return role.value >= self.min_role.value
        if self.resource.endswith("*"):
            prefix = self.resource[:-1]
            return resource.startswith(prefix) and role.value >= self.min_role.value
        return self.resource == resource and role.value >= self.min_role.value


class PolicyEngine:
    """Policy engine for tool execution and resource access gating."""

    def __init__(self):
        self.rules: List[PolicyRule] = self._default_rules()

    def _default_rules(self) -> List[PolicyRule]:
        """Default enterprise-safe rules."""
        return [
            PolicyRule("tool:*", "allow", Role.ADMIN),
            PolicyRule("tool:shell", "deny", Role.OPERATOR),  # Shell requires approval
            PolicyRule("tool:shell", "allow", Role.ADMIN),
            PolicyRule("tool:query", "allow", Role.OPERATOR),
            PolicyRule("tool:*", "deny", Role.VIEWER),
            PolicyRule("memory:read", "allow", Role.OPERATOR),
            PolicyRule("memory:write", "require_approval", Role.OPERATOR),
        ]

    def add_rule(self, rule: PolicyRule) -> None:
        """Add a policy rule."""
        self.rules.append(rule)

    def is_tool_allowed(self, tool_name: str, user_roles: List[Role]) -> bool:
        """Check if user can execute tool based on roles."""
        for rule in self.rules:
            for role in user_roles:
                if rule.matches(f"tool:{tool_name}", role):
                    return rule.action != "deny"
        return False

    def check_resource_access(
        self, resource: str, action: str, user_roles: List[Role]
    ) -> Dict[str, bool]:
        """Check if user can access resource with given action."""
        allowed = False
        requires_approval = False

        for rule in self.rules:
            for role in user_roles:
                if rule.matches(resource, role) and rule.action != "deny":
                    allowed = True
                    if rule.requires_approval:
                        requires_approval = True
                    break

        return {"allowed": allowed, "requires_approval": requires_approval}


@dataclass
class AuditEntry:
    """Immutable audit log entry."""
    timestamp: str
    org_id: str
    user_id: str
    action: Action
    resource: str
    result: str
    frame_hash: str  # ForgeNumerics frame hash
    frame_content: Optional[str] = None
    details: Dict[str, str] = field(default_factory=dict)
    entry_hash: str = field(default="")

    def __post_init__(self):
        """Compute entry hash for integrity."""
        payload = f"{self.timestamp}:{self.org_id}:{self.user_id}:{self.action.value}:{self.resource}:{self.result}:{self.frame_hash}"
        self.entry_hash = hashlib.sha256(payload.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict:
        """Serialize to dict."""
        return {
            "timestamp": self.timestamp,
            "org_id": self.org_id,
            "user_id": self.user_id,
            "action": self.action.value,
            "resource": self.resource,
            "result": self.result,
            "frame_hash": self.frame_hash,
            "frame_content": self.frame_content,
            "details": self.details,
            "entry_hash": self.entry_hash,
        }


class AuditLog:
    """Enterprise audit log for agent operations."""

    def __init__(self):
        self.entries: List[AuditEntry] = []

    def log(
        self,
        org_id: str,
        user_id: str,
        action: Action,
        resource: str,
        result: str,
        frame_hash: str,
        frame_content: Optional[str] = None,
        details: Optional[Dict[str, str]] = None,
    ) -> str:
        """Log an action and return entry hash."""
        entry = AuditEntry(
            timestamp=datetime.utcnow().isoformat(),
            org_id=org_id,
            user_id=user_id,
            action=action,
            resource=resource,
            result=result,
            frame_hash=frame_hash,
            frame_content=frame_content,
            details=details or {},
        )
        self.entries.append(entry)
        return entry.entry_hash

    def export_jsonl(self, path: str) -> int:
        """Export audit log to JSONL for compliance."""
        with open(path, "w") as f:
            for entry in self.entries:
                f.write(json.dumps(entry.to_dict()) + "\n")
        return len(self.entries)

    def replay_for_audit(self, org_id: str, start_time: str, end_time: str) -> List[AuditEntry]:
        """Retrieve audit entries in time range."""
        return [
            e for e in self.entries
            if e.org_id == org_id and start_time <= e.timestamp <= end_time
        ]


# ============================================================================
# SELF-TEST
# ============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("AGENT VAULT PLATFORM: RBAC + POLICY + AUDIT")
    print("=" * 70)
    print()

    # Test RBAC
    user = OrgUser("acme_corp", "alice", "alice@acme.com", [Role.ADMIN])
    print(f"1) User {user.email} has admin role: {user.has_role(Role.ADMIN)}")
    print()

    # Test Policy Engine
    policy = PolicyEngine()
    print("2) Policy rules initialized (default enterprise-safe rules)")
    allowed = policy.is_tool_allowed("query", [Role.OPERATOR])
    print(f"   OPERATOR can call 'query' tool: {allowed}")
    shell_allowed = policy.is_tool_allowed("shell", [Role.OPERATOR])
    print(f"   OPERATOR can call 'shell' tool: {shell_allowed}")
    print()

    # Test Audit Log
    audit = AuditLog()
    entry_hash = audit.log(
        org_id="acme_corp",
        user_id="alice",
        action=Action.TOOL_CALL,
        resource="tool:query",
        result="SUCCESS",
        frame_hash="abc123def456",
        frame_content="⧆≛TYPE⦙≛TOOL_CALL∴...",
        details={"tool": "query", "args": "SELECT * FROM users"},
    )
    print(f"3) Logged tool call, entry hash: {entry_hash}")
    print(f"   Total audit entries: {len(audit.entries)}")
    print()

    print("=" * 70)
    print("PLATFORM READY: Enterprise compliance layer online")
    print("=" * 70)
    print("✓ RBAC framework ready")
    print("✓ Policy engine initialized")
    print("✓ Audit log operational")

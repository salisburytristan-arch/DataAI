"""
Tests for tool_policies.py - Tool Policy Engine
"""

import unittest
import tempfile
import shutil
from datetime import datetime
import secrets

from packages.core.src.tool_policies import (
    ToolPolicyEngine, ToolPolicy, ToolConstraints, ToolExecutionMode,
    ToolExecutionRequest, get_default_policies
)


class TestToolPolicies(unittest.TestCase):
    
    def setUp(self):
        """Create temporary storage for each test"""
        self.test_dir = tempfile.mkdtemp()
        self.engine = ToolPolicyEngine(storage_dir=self.test_dir)
        self.org_id = "org_test"
    
    def tearDown(self):
        """Clean up temp storage"""
        shutil.rmtree(self.test_dir)
    
    def test_set_and_get_policy(self):
        """Test setting and retrieving policies"""
        policy = ToolPolicy(
            tool_name="test_tool",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(),
            allowed_roles=["admin"]
        )
        
        self.engine.set_policy(self.org_id, policy)
        retrieved = self.engine.get_policy(self.org_id, "test_tool")
        
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.tool_name, "test_tool")
        self.assertEqual(retrieved.mode, ToolExecutionMode.AUTO)
    
    def test_auto_mode_execution(self):
        """Test AUTO mode allows execution"""
        policy = ToolPolicy(
            tool_name="calculate",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(),
            allowed_roles=["admin", "analyst"]
        )
        
        self.engine.set_policy(self.org_id, policy)
        
        allowed, reason, pending = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="calculate",
            user_role="analyst",
            args={"expression": "2+2"}
        )
        
        self.assertTrue(allowed)
        self.assertIsNone(reason)
        self.assertIsNone(pending)
    
    def test_deny_mode_execution(self):
        """Test DENY mode blocks execution"""
        policy = ToolPolicy(
            tool_name="dangerous_tool",
            mode=ToolExecutionMode.DENY,
            constraints=ToolConstraints(),
            allowed_roles=[]
        )
        
        self.engine.set_policy(self.org_id, policy)
        
        allowed, reason, pending = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="dangerous_tool",
            user_role="admin",
            args={}
        )
        
        self.assertFalse(allowed)
        self.assertIn("disabled by policy", reason)
    
    def test_approve_mode_requires_approval(self):
        """Test APPROVE mode requires approval"""
        policy = ToolPolicy(
            tool_name="file_write",
            mode=ToolExecutionMode.APPROVE,
            constraints=ToolConstraints(),
            allowed_roles=["admin", "analyst"],
            requires_approval_from_role="admin"
        )
        
        self.engine.set_policy(self.org_id, policy)
        
        allowed, reason, pending = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="file_write",
            user_role="analyst",
            args={"file_path": "/test.txt"}
        )
        
        self.assertFalse(allowed)
        self.assertIn("requires approval", reason)
        self.assertEqual(pending, "pending")
    
    def test_role_restriction(self):
        """Test role-based access control"""
        policy = ToolPolicy(
            tool_name="admin_tool",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(),
            allowed_roles=["admin"]
        )
        
        self.engine.set_policy(self.org_id, policy)
        
        # Admin allowed
        allowed, reason, _ = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="admin_tool",
            user_role="admin",
            args={}
        )
        self.assertTrue(allowed)
        
        # Analyst denied
        allowed, reason, _ = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="admin_tool",
            user_role="analyst",
            args={}
        )
        self.assertFalse(allowed)
        self.assertIn("not allowed", reason)
    
    def test_file_size_constraint(self):
        """Test file size constraint enforcement"""
        policy = ToolPolicy(
            tool_name="file_read",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(max_file_size_mb=5),
            allowed_roles=["analyst"]
        )
        
        self.engine.set_policy(self.org_id, policy)
        
        # Small file allowed
        allowed, reason, _ = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="file_read",
            user_role="analyst",
            args={"file_size": 1024 * 1024}  # 1MB
        )
        self.assertTrue(allowed)
        
        # Large file denied
        allowed, reason, _ = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="file_read",
            user_role="analyst",
            args={"file_size": 10 * 1024 * 1024}  # 10MB
        )
        self.assertFalse(allowed)
        self.assertIn("exceeds limit", reason)
    
    def test_path_constraint(self):
        """Test allowed path constraint"""
        policy = ToolPolicy(
            tool_name="file_read",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(allowed_paths=["/workspace", "/data"]),
            allowed_roles=["analyst"]
        )
        
        self.engine.set_policy(self.org_id, policy)
        
        # Allowed path
        allowed, reason, _ = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="file_read",
            user_role="analyst",
            args={"file_path": "/workspace/test.txt"}
        )
        self.assertTrue(allowed)
        
        # Disallowed path
        allowed, reason, _ = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="file_read",
            user_role="analyst",
            args={"file_path": "/etc/passwd"}
        )
        self.assertFalse(allowed)
        self.assertIn("not in allowed paths", reason)
    
    def test_network_constraint(self):
        """Test network access constraint"""
        policy = ToolPolicy(
            tool_name="web_tool",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(network_enabled=False),
            allowed_roles=["analyst"]
        )
        
        self.engine.set_policy(self.org_id, policy)
        
        # Network arg present
        allowed, reason, _ = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="web_tool",
            user_role="analyst",
            args={"url": "https://example.com"}
        )
        self.assertFalse(allowed)
        self.assertIn("Network access is disabled", reason)
    
    def test_no_policy_default_deny(self):
        """Test that execution is denied when no policy exists"""
        allowed, reason, _ = self.engine.check_execution_allowed(
            org_id=self.org_id,
            tool_name="unknown_tool",
            user_role="admin",
            args={}
        )
        
        self.assertFalse(allowed)
        self.assertIn("No policy defined", reason)
    
    def test_approval_workflow(self):
        """Test approval request workflow"""
        request = ToolExecutionRequest(
            request_id=f"req_{secrets.token_hex(8)}",
            tool_name="file_write",
            args={"file_path": "/test.txt"},
            user_id="user_123",
            org_id=self.org_id,
            session_id="session_001",
            status="pending",
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
        # Create request
        request_id = self.engine.create_approval_request(request)
        self.assertEqual(request_id, request.request_id)
        
        # List pending
        pending = self.engine.get_pending_requests(org_id=self.org_id)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].request_id, request_id)
        
        # Approve
        success = self.engine.approve_request(request_id, approver_user_id="admin_456")
        self.assertTrue(success)
        
        # Check status
        approved_request = self.engine.pending_requests[request_id]
        self.assertEqual(approved_request.status, "approved")
        self.assertEqual(approved_request.approved_by, "admin_456")
        self.assertIsNotNone(approved_request.approved_at)
    
    def test_deny_request(self):
        """Test denying approval request"""
        request = ToolExecutionRequest(
            request_id=f"req_{secrets.token_hex(8)}",
            tool_name="file_write",
            args={"file_path": "/test.txt"},
            user_id="user_123",
            org_id=self.org_id,
            session_id="session_001",
            status="pending",
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
        request_id = self.engine.create_approval_request(request)
        self.engine.deny_request(request_id, reason="Security concern")
        
        denied_request = self.engine.pending_requests[request_id]
        self.assertEqual(denied_request.status, "denied")
        self.assertEqual(denied_request.error, "Security concern")
    
    def test_complete_request(self):
        """Test completing executed request"""
        request = ToolExecutionRequest(
            request_id=f"req_{secrets.token_hex(8)}",
            tool_name="calculate",
            args={"expression": "2+2"},
            user_id="user_123",
            org_id=self.org_id,
            session_id="session_001",
            status="approved",
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        
        request_id = self.engine.create_approval_request(request)
        self.engine.complete_request(request_id, result={"answer": 4})
        
        # Should be removed from pending
        self.assertNotIn(request_id, self.engine.pending_requests)
    
    def test_get_default_policies(self):
        """Test default policy generation"""
        policies = get_default_policies("org_test")
        
        self.assertGreater(len(policies), 0)
        
        # Check specific policies
        tool_names = [p.tool_name for p in policies]
        self.assertIn("file_read", tool_names)
        self.assertIn("file_write", tool_names)
        self.assertIn("calculate", tool_names)
        
        # Check that web_fetch is denied by default
        web_policy = next(p for p in policies if p.tool_name == "web_fetch")
        self.assertEqual(web_policy.mode, ToolExecutionMode.DENY)
    
    def test_persistence(self):
        """Test policy persistence across engine instances"""
        policy = ToolPolicy(
            tool_name="test_tool",
            mode=ToolExecutionMode.AUTO,
            constraints=ToolConstraints(max_file_size_mb=10),
            allowed_roles=["admin"]
        )
        
        self.engine.set_policy(self.org_id, policy)
        
        # Create new engine instance (reload from disk)
        engine2 = ToolPolicyEngine(storage_dir=self.test_dir)
        
        retrieved = engine2.get_policy(self.org_id, "test_tool")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.tool_name, "test_tool")
        self.assertEqual(retrieved.constraints.max_file_size_mb, 10)


if __name__ == "__main__":
    unittest.main()

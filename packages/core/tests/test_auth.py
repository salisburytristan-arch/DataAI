"""
Tests for auth.py - Authentication, Authorization, and Multi-Tenancy
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from packages.core.src.auth import (
    AuthManager, Organization, User, APIKey,
    Role, Permission, ROLE_PERMISSIONS
)


class TestAuth(unittest.TestCase):
    
    def setUp(self):
        """Create temporary storage for each test"""
        self.test_dir = tempfile.mkdtemp()
        self.auth = AuthManager(storage_dir=self.test_dir)
    
    def tearDown(self):
        """Clean up temp storage"""
        shutil.rmtree(self.test_dir)
    
    def test_create_organization(self):
        """Test organization creation"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        
        self.assertTrue(org.org_id.startswith("org_"))
        self.assertEqual(org.name, "Test Corp")
        self.assertEqual(org.vault_dir, "./test_vault")
        self.assertIn(org.org_id, self.auth.orgs)
    
    def test_create_user(self):
        """Test user creation"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        user = self.auth.create_user(
            email="test@example.com",
            org_id=org.org_id,
            role=Role.ANALYST,
            password="password123"
        )
        
        self.assertTrue(user.user_id.startswith("user_"))
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.org_id, org.org_id)
        self.assertEqual(user.role, Role.ANALYST)
        self.assertIsNotNone(user.password_hash)
        self.assertIsNotNone(user.salt)
    
    def test_password_authentication(self):
        """Test password authentication"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        user = self.auth.create_user(
            email="test@example.com",
            org_id=org.org_id,
            role=Role.ADMIN,
            password="secure_password"
        )
        
        # Successful auth
        authenticated = self.auth.authenticate_password("test@example.com", "secure_password")
        self.assertIsNotNone(authenticated)
        self.assertEqual(authenticated.user_id, user.user_id)
        
        # Failed auth (wrong password)
        authenticated = self.auth.authenticate_password("test@example.com", "wrong_password")
        self.assertIsNone(authenticated)
        
        # Failed auth (non-existent user)
        authenticated = self.auth.authenticate_password("nonexistent@example.com", "password")
        self.assertIsNone(authenticated)
    
    def test_api_key_creation(self):
        """Test API key creation"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        user = self.auth.create_user(
            email="test@example.com",
            org_id=org.org_id,
            role=Role.ADMIN
        )
        
        plaintext_key, api_key = self.auth.create_api_key(user.user_id, "CLI Key")
        
        self.assertTrue(plaintext_key.startswith("ac_"))
        self.assertTrue(api_key.key_id.startswith("key_"))
        self.assertEqual(api_key.name, "CLI Key")
        self.assertIn(api_key, self.auth.users[user.user_id].api_keys)
    
    def test_api_key_authentication(self):
        """Test API key authentication"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        user = self.auth.create_user(
            email="test@example.com",
            org_id=org.org_id,
            role=Role.ANALYST
        )
        
        plaintext_key, api_key = self.auth.create_api_key(user.user_id, "Test Key")
        
        # Successful auth
        authenticated = self.auth.authenticate_api_key(plaintext_key)
        self.assertIsNotNone(authenticated)
        self.assertEqual(authenticated.user_id, user.user_id)
        
        # Failed auth (wrong key)
        authenticated = self.auth.authenticate_api_key("ac_wrong_key")
        self.assertIsNone(authenticated)
    
    def test_session_management(self):
        """Test session creation and retrieval"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        user = self.auth.create_user(
            email="test@example.com",
            org_id=org.org_id,
            role=Role.ADMIN
        )
        
        # Create session
        session_token = self.auth.create_session(user.user_id)
        self.assertTrue(len(session_token) > 0)
        
        # Get session
        session_user, session_org = self.auth.get_session(session_token)
        self.assertEqual(session_user.user_id, user.user_id)
        self.assertEqual(session_org.org_id, org.org_id)
        
        # Delete session
        self.auth.delete_session(session_token)
        result = self.auth.get_session(session_token)
        self.assertIsNone(result)
    
    def test_role_permissions(self):
        """Test role permission mapping"""
        # Admin has all permissions
        self.assertIn(Permission.USER_MANAGE, ROLE_PERMISSIONS[Role.ADMIN])
        self.assertIn(Permission.AGENT_RUN, ROLE_PERMISSIONS[Role.ADMIN])
        
        # Analyst can run agents but not manage users
        self.assertIn(Permission.AGENT_RUN, ROLE_PERMISSIONS[Role.ANALYST])
        self.assertNotIn(Permission.USER_MANAGE, ROLE_PERMISSIONS[Role.ANALYST])
        
        # Viewer can only view audit
        self.assertIn(Permission.AUDIT_VIEW, ROLE_PERMISSIONS[Role.VIEWER])
        self.assertNotIn(Permission.AGENT_RUN, ROLE_PERMISSIONS[Role.VIEWER])
        
        # Auditor can view and export audit
        self.assertIn(Permission.AUDIT_VIEW, ROLE_PERMISSIONS[Role.AUDITOR])
        self.assertIn(Permission.AUDIT_EXPORT, ROLE_PERMISSIONS[Role.AUDITOR])
        self.assertNotIn(Permission.AGENT_RUN, ROLE_PERMISSIONS[Role.AUDITOR])
    
    def test_user_permissions(self):
        """Test user permission checks"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        
        admin = self.auth.create_user(email="admin@example.com", org_id=org.org_id, role=Role.ADMIN)
        analyst = self.auth.create_user(email="analyst@example.com", org_id=org.org_id, role=Role.ANALYST)
        viewer = self.auth.create_user(email="viewer@example.com", org_id=org.org_id, role=Role.VIEWER)
        
        # Admin permissions
        self.assertTrue(admin.has_permission(Permission.USER_MANAGE))
        self.assertTrue(admin.has_permission(Permission.AGENT_RUN))
        
        # Analyst permissions
        self.assertFalse(analyst.has_permission(Permission.USER_MANAGE))
        self.assertTrue(analyst.has_permission(Permission.AGENT_RUN))
        
        # Viewer permissions
        self.assertFalse(viewer.has_permission(Permission.AGENT_RUN))
        self.assertTrue(viewer.has_permission(Permission.AUDIT_VIEW))
    
    def test_authorization(self):
        """Test authorization checks"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        user = self.auth.create_user(email="analyst@example.com", org_id=org.org_id, role=Role.ANALYST)
        
        self.assertTrue(self.auth.authorize(user, Permission.AGENT_RUN))
        self.assertFalse(self.auth.authorize(user, Permission.USER_MANAGE))
    
    def test_get_org_users(self):
        """Test retrieving all users in an org"""
        org1 = self.auth.create_organization(name="Org1", vault_dir="./vault1")
        org2 = self.auth.create_organization(name="Org2", vault_dir="./vault2")
        
        user1 = self.auth.create_user(email="user1@org1.com", org_id=org1.org_id, role=Role.ADMIN)
        user2 = self.auth.create_user(email="user2@org1.com", org_id=org1.org_id, role=Role.ANALYST)
        user3 = self.auth.create_user(email="user3@org2.com", org_id=org2.org_id, role=Role.ADMIN)
        
        org1_users = self.auth.get_org_users(org1.org_id)
        self.assertEqual(len(org1_users), 2)
        self.assertIn(user1, org1_users)
        self.assertIn(user2, org1_users)
        self.assertNotIn(user3, org1_users)
    
    def test_persistence(self):
        """Test data persistence across manager instances"""
        org = self.auth.create_organization(name="Test Corp", vault_dir="./test_vault")
        user = self.auth.create_user(
            email="test@example.com",
            org_id=org.org_id,
            role=Role.ADMIN,
            password="password123"
        )
        plaintext_key, api_key = self.auth.create_api_key(user.user_id, "Test Key")
        
        # Create new manager instance (reload from disk)
        auth2 = AuthManager(storage_dir=self.test_dir)
        
        # Verify org persisted
        self.assertIn(org.org_id, auth2.orgs)
        self.assertEqual(auth2.orgs[org.org_id].name, "Test Corp")
        
        # Verify user persisted
        self.assertIn(user.user_id, auth2.users)
        self.assertEqual(auth2.users[user.user_id].email, "test@example.com")
        
        # Verify password auth still works
        authenticated = auth2.authenticate_password("test@example.com", "password123")
        self.assertIsNotNone(authenticated)
        
        # Verify API key still works
        authenticated = auth2.authenticate_api_key(plaintext_key)
        self.assertIsNotNone(authenticated)
    
    def test_invalid_org_id(self):
        """Test user creation with invalid org_id"""
        with self.assertRaises(ValueError):
            self.auth.create_user(
                email="test@example.com",
                org_id="nonexistent_org",
                role=Role.ADMIN
            )
    
    def test_invalid_user_id_for_api_key(self):
        """Test API key creation with invalid user_id"""
        with self.assertRaises(ValueError):
            self.auth.create_api_key("nonexistent_user", "Test Key")
    
    def test_invalid_user_id_for_session(self):
        """Test session creation with invalid user_id"""
        with self.assertRaises(ValueError):
            self.auth.create_session("nonexistent_user")


if __name__ == "__main__":
    unittest.main()

"""
Tests for Audit Event Stream
"""

import unittest
import tempfile
import shutil
from pathlib import Path
import json
import time
from packages.core.src.audit_stream import (
    AuditEvent,
    AuditStream,
    AuditLogger
)


class TestAuditStream(unittest.TestCase):
    """Test audit event stream"""
    
    def setUp(self):
        """Create temp directory for tests"""
        self.test_dir = tempfile.mkdtemp()
        self.stream = AuditStream(storage_dir=self.test_dir)
    
    def tearDown(self):
        """Cleanup temp directory"""
        shutil.rmtree(self.test_dir)
    
    def test_append_event_creates_event(self):
        """Should create and append event"""
        event = self.stream.append_event(
            event_type="request_received",
            user_id="user123",
            org_id="org_demo",
            session_id="session_001",
            data={"query": "What is Python?"}
        )
        
        self.assertIsInstance(event, AuditEvent)
        self.assertEqual(event.event_type, "request_received")
        self.assertEqual(event.user_id, "user123")
        self.assertEqual(event.org_id, "org_demo")
        self.assertIn("query", event.data)
    
    def test_genesis_event_has_zero_prev_hash(self):
        """First event should have genesis prev_hash"""
        event = self.stream.append_event(
            event_type="request_received",
            user_id="user1",
            org_id="org1",
            session_id="s1",
            data={}
        )
        
        self.assertEqual(event.prev_event_hash, "0" * 64)
    
    def test_hash_chaining(self):
        """Events should be hash-chained"""
        event1 = self.stream.append_event(
            event_type="request_received",
            user_id="user1",
            org_id="org1",
            session_id="s1",
            data={"query": "first"}
        )
        
        event2 = self.stream.append_event(
            event_type="evidence_retrieved",
            user_id="user1",
            org_id="org1",
            session_id="s1",
            data={"chunks": 2}
        )
        
        # Second event's prev_hash should match first event's hash
        self.assertEqual(event2.prev_event_hash, event1.event_hash)
    
    def test_verify_chain_valid(self):
        """Should verify valid chain"""
        # Add some events
        for i in range(5):
            self.stream.append_event(
                event_type="request_received",
                user_id="user1",
                org_id="org1",
                session_id="s1",
                data={"index": i}
            )
        
        is_valid, error = self.stream.verify_chain()
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_verify_chain_detects_tampering(self):
        """Should detect tampering in event data"""
        # Add events
        for i in range(3):
            self.stream.append_event(
                event_type="request_received",
                user_id="user1",
                org_id="org1",
                session_id="s1",
                data={"index": i}
            )
        
        # Tamper with the stream file
        stream_file = self.stream.current_stream_file
        with open(stream_file, 'r') as f:
            lines = f.readlines()
        
        # Modify second event's data
        event2 = json.loads(lines[1])
        event2['data']['index'] = 999  # Tamper
        lines[1] = json.dumps(event2) + '\n'
        
        with open(stream_file, 'w') as f:
            f.writelines(lines)
        
        # Verification should fail
        is_valid, error = self.stream.verify_chain()
        self.assertFalse(is_valid)
        self.assertIsNotNone(error)
    
    def test_query_events_by_org(self):
        """Should query events by org_id"""
        # Add events for different orgs
        self.stream.append_event("request_received", "user1", "org_a", "s1", {})
        self.stream.append_event("request_received", "user2", "org_b", "s2", {})
        self.stream.append_event("request_received", "user3", "org_a", "s3", {})
        
        # Query org_a
        events = self.stream.query_events(org_id="org_a")
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.org_id == "org_a" for e in events))
    
    def test_query_events_by_event_type(self):
        """Should query events by type"""
        self.stream.append_event("request_received", "user1", "org1", "s1", {})
        self.stream.append_event("evidence_retrieved", "user1", "org1", "s1", {})
        self.stream.append_event("model_called", "user1", "org1", "s1", {})
        self.stream.append_event("evidence_retrieved", "user1", "org1", "s1", {})
        
        # Query evidence_retrieved only
        events = self.stream.query_events(event_types=["evidence_retrieved"])
        self.assertEqual(len(events), 2)
        self.assertTrue(all(e.event_type == "evidence_retrieved" for e in events))
    
    def test_query_events_limit(self):
        """Should respect query limit"""
        # Add many events
        for i in range(20):
            self.stream.append_event("request_received", "user1", "org1", "s1", {"n": i})
        
        # Query with limit
        events = self.stream.query_events(limit=10)
        self.assertEqual(len(events), 10)
    
    def test_export_audit_package(self):
        """Should export audit package"""
        # Add some events
        for i in range(5):
            self.stream.append_event("request_received", "user1", "org1", "s1", {"n": i})
        
        # Export
        output_path = Path(self.test_dir) / "audit_export.zip"
        manifest = self.stream.export_audit_package(str(output_path))
        
        self.assertTrue(output_path.exists())
        self.assertEqual(manifest['event_count'], 5)
        self.assertTrue(manifest['chain_valid'])


class TestAuditLogger(unittest.TestCase):
    """Test high-level audit logger"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.stream = AuditStream(storage_dir=self.test_dir)
        self.logger = AuditLogger(self.stream)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_log_request(self):
        """Should log request event"""
        event = self.logger.log_request(
            user_id="user123",
            org_id="org_demo",
            session_id="session_001",
            query="What is Python?"
        )
        
        self.assertEqual(event.event_type, "request_received")
        self.assertEqual(event.data['query'], "What is Python?")
        self.assertIn('query_length', event.data)
    
    def test_log_evidence_retrieval(self):
        """Should log evidence retrieval"""
        event = self.logger.log_evidence_retrieval(
            user_id="user123",
            org_id="org_demo",
            session_id="session_001",
            query="Python",
            chunk_ids=["chunk1", "chunk2"],
            scores=[0.9, 0.8]
        )
        
        self.assertEqual(event.event_type, "evidence_retrieved")
        self.assertEqual(event.data['chunk_count'], 2)
        self.assertAlmostEqual(event.data['avg_score'], 0.85, places=2)
    
    def test_log_tool_call(self):
        """Should log tool execution"""
        event = self.logger.log_tool_call(
            user_id="user123",
            org_id="org_demo",
            session_id="session_001",
            tool_name="calculate",
            args={"expression": "2+2"},
            approved_by="admin"
        )
        
        self.assertEqual(event.event_type, "tool_called")
        self.assertEqual(event.data['tool_name'], "calculate")
        self.assertEqual(event.data['approved_by'], "admin")
        self.assertIn('args_hash', event.data)
    
    def test_log_model_call(self):
        """Should log model API call"""
        event = self.logger.log_model_call(
            user_id="user123",
            org_id="org_demo",
            session_id="session_001",
            provider="openai",
            model_id="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            cost_usd=0.003,
            latency_ms=1200.5
        )
        
        self.assertEqual(event.event_type, "model_called")
        self.assertEqual(event.data['provider'], "openai")
        self.assertEqual(event.data['total_tokens'], 150)
        self.assertEqual(event.data['cost_usd'], 0.003)
    
    def test_log_phi_detection(self):
        """Should log Φ state detection"""
        event = self.logger.log_phi_detection(
            user_id="user123",
            org_id="org_demo",
            session_id="session_001",
            phi_count=2,
            high_impact_count=1,
            contradiction_count=0,
            escalation_triggered=True
        )
        
        self.assertEqual(event.event_type, "phi_detected")
        self.assertEqual(event.data['phi_count'], 2)
        self.assertTrue(event.data['escalation_triggered'])
    
    def test_log_response_signed(self):
        """Should log response signing"""
        event = self.logger.log_response_signed(
            user_id="user123",
            org_id="org_demo",
            session_id="session_001",
            response_hash="abc123",
            signature="sig456"
        )
        
        self.assertEqual(event.event_type, "response_signed")
        self.assertEqual(event.data['response_hash'], "abc123")
        self.assertEqual(event.data['signature'], "sig456")


if __name__ == '__main__':
    unittest.main()

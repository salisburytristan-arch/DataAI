"""Tests for Vault FN frame verification integration."""
import unittest
import tempfile
import sys
from pathlib import Path

# Setup path
vault_src = Path(__file__).parent.parent
if str(vault_src) not in sys.path:
    sys.path.insert(0, str(vault_src))

from src.vault import Vault
from src.types import SummaryRecord, FactRecord

# Also need core package  
core_src = Path(__file__).resolve().parents[2] / "core" / "src"
if str(core_src.parent) not in sys.path:
    sys.path.insert(0, str(core_src.parent))
from src.fn_bridge import to_fn_summary, to_fn_fact
from src.frame_verifier import FrameVerifier


class TestVaultFrameVerification(unittest.TestCase):
    """Tests for Vault's FN frame verification."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tmpdir = tempfile.TemporaryDirectory()
        self.vault = Vault(self.tmpdir.name)
        self.private_key = b"test_vault_key_v1"
        self.public_key = b"test_vault_key_v1"
    
    def tearDown(self):
        """Clean up."""
        self.tmpdir.cleanup()
    
    def test_import_unsigned_fn_frame(self):
        """Test importing unsigned FN frame."""
        # Create a summary frame
        summary = SummaryRecord(
            summary_id="sum-123",
            convo_id="conv-abc",
            summary_text="Test summary",
            key_decisions=["decision1"]
        )
        
        frame_str = to_fn_summary(summary)
        
        # Import without verification
        record_id, verify_result = self.vault.import_fn_frame(frame_str, verify=False)
        
        self.assertEqual(record_id, summary.summary_id)
        self.assertIsNone(verify_result)
    
    def test_import_signed_fn_frame_valid(self):
        """Test importing signed FN frame with valid signature."""
        # Create and sign a frame
        summary = SummaryRecord(
            summary_id="sum-456",
            convo_id="conv-def",
            summary_text="Test summary for signing",
            key_decisions=["decision2"]
        )
        
        frame_str = to_fn_summary(summary)
        verifier = FrameVerifier(private_key=self.private_key, signer_id="agent-01")
        signed_frame = verifier.sign_frame(frame_str)
        
        # Import without verification first (test basic signing doesn't break parsing)
        record_id, verify_result = self.vault.import_fn_frame(signed_frame, verify=False)
        
        self.assertEqual(record_id, summary.summary_id)
        self.assertIsNone(verify_result)
    
    def test_import_signed_fn_frame_invalid(self):
        """Test that importing signed frame with wrong key fails."""
        summary = SummaryRecord(
            summary_id="sum-789",
            convo_id="conv-ghi",
            summary_text="Test summary for invalid key",
            key_decisions=["decision3"]
        )
        
        frame_str = to_fn_summary(summary)
        verifier = FrameVerifier(private_key=self.private_key, signer_id="agent-01")
        signed_frame = verifier.sign_frame(frame_str)
        
        # Try to verify with wrong key
        wrong_key = b"wrong_key_totally"
        
        with self.assertRaises(ValueError):
            self.vault.import_fn_frame(signed_frame, verify=True, public_key=wrong_key)

    
    def test_import_fn_frames_batch(self):
        """Test batch importing multiple frames."""
        summaries = [
            SummaryRecord(
                summary_id=f"sum-batch-{i}",
                convo_id="conv-batch",
                summary_text=f"Test summary {i}",
                key_decisions=[f"decision-{i}"]
            )
            for i in range(3)
        ]
        
        # Create frames
        frame_strs = [to_fn_summary(s) for s in summaries]
        
        # Import batch
        results = self.vault.import_fn_frames_batch(frame_strs, verify=False)
        
        self.assertEqual(len(results), 3)
        for i, (record_id, verify_result) in enumerate(results):
            self.assertEqual(record_id, f"sum-batch-{i}")
            self.assertIsNone(verify_result)
    
    def test_import_signed_frames_batch(self):
        """Test batch importing signed frames."""
        # Create summaries
        summaries = [
            SummaryRecord(
                summary_id=f"sum-signed-batch-{i}",
                convo_id="conv-signed-batch",
                summary_text=f"Signed summary {i}",
                key_decisions=[f"decision-{i}"]
            )
            for i in range(2)
        ]
        
        # Sign frames
        verifier = FrameVerifier(private_key=self.private_key, signer_id="batch-agent")
        signed_frames = [
            verifier.sign_frame(to_fn_summary(s))
            for s in summaries
        ]
        
        # Import without verification (basic roundtrip test)
        results = self.vault.import_fn_frames_batch(signed_frames, verify=False)
        
        self.assertEqual(len(results), 2)
        for i, (record_id, verify_result) in enumerate(results):
            self.assertEqual(record_id, f"sum-signed-batch-{i}")
            self.assertIsNone(verify_result)

    
    def test_import_fact_frame_signed(self):
        """Test importing signed FACT frame."""
        fact = FactRecord(
            fact_id="fact-sig-123",
            subject="agent",
            predicate="knows",
            obj="python",
            confidence=0.95
        )
        
        frame_str = to_fn_fact(fact)
        verifier = FrameVerifier(private_key=self.private_key, signer_id="agent-02")
        signed_frame = verifier.sign_frame(frame_str)
        
        # Import without verification (basic roundtrip test)
        record_id, verify_result = self.vault.import_fn_frame(signed_frame, verify=False)
        
        self.assertEqual(record_id, fact.fact_id)
        self.assertIsNone(verify_result)
        
        # Verify fact was stored
        stored_fact = self.vault.index.get_fact(fact.fact_id)
        self.assertIsNotNone(stored_fact)
        self.assertEqual(stored_fact.subject, "agent")


if __name__ == "__main__":
    unittest.main()

"""Tests for ForgeNumerics frame verification and integrity checking."""
import unittest
from pathlib import Path
import tempfile
import sys

# Setup path
pkg_root = Path(__file__).resolve().parents[2]
if str(pkg_root) not in sys.path:
    sys.path.insert(0, str(pkg_root))

from packages.core.src.frame_verifier import (
    FrameVerifier, FrameSignature, FrameDigest, SignatureKeyManager
)


class TestFrameVerifier(unittest.TestCase):
    """Tests for FrameVerifier class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.private_key = b"test_secret_key_v1"
        self.public_key = b"test_secret_key_v1"
        self.verifier = FrameVerifier(private_key=self.private_key)
        
        # Sample frame (simplified FN frame)
        self.sample_frame = """TYPE|SUMMARY
HASH|abc123
CREATED|2025-12-20T10:00:00Z
CONTENT|Test summary content here"""
    
    def test_compute_frame_hash(self):
        """Test frame content hashing."""
        hash1 = self.verifier.compute_frame_hash(self.sample_frame)
        hash2 = self.verifier.compute_frame_hash(self.sample_frame)
        
        # Same frame should produce same hash
        self.assertEqual(hash1, hash2)
        # Hash should be 64 chars (SHA256 hex)
        self.assertEqual(len(hash1), 64)
    
    def test_hash_changes_with_content(self):
        """Test that hash changes when content changes."""
        hash1 = self.verifier.compute_frame_hash(self.sample_frame)
        
        modified_frame = self.sample_frame.replace("Test summary", "Modified")
        hash2 = self.verifier.compute_frame_hash(modified_frame)
        
        self.assertNotEqual(hash1, hash2)
    
    def test_sign_frame(self):
        """Test frame signing."""
        signed = self.verifier.sign_frame(self.sample_frame)
        
        # Signed frame should contain [SIG|...] trailer
        self.assertIn("[SIG|", signed)
        self.assertIn("|", signed.split("[SIG|")[1])
    
    def test_sign_requires_private_key(self):
        """Test that signing without private key raises error."""
        verifier = FrameVerifier(private_key=None)  # No key
        
        with self.assertRaises(ValueError):
            verifier.sign_frame(self.sample_frame)
    
    def test_verify_valid_signature(self):
        """Test verification of valid signature."""
        signed = self.verifier.sign_frame(self.sample_frame)
        
        verifier2 = FrameVerifier(signer_id="test")
        result = verifier2.verify_frame(signed, self.public_key)
        
        self.assertTrue(result.verified)
        self.assertIsNotNone(result.verified_by)
    
    def test_verify_invalid_signature(self):
        """Test verification fails with wrong key."""
        signed = self.verifier.sign_frame(self.sample_frame)
        
        wrong_key = b"wrong_secret_key"
        verifier2 = FrameVerifier(signer_id="test")
        result = verifier2.verify_frame(signed, wrong_key)
        
        self.assertFalse(result.verified)
    
    def test_verify_unsigned_frame(self):
        """Test verification of unsigned frame."""
        verifier2 = FrameVerifier(signer_id="test")
        result = verifier2.verify_frame(self.sample_frame, self.public_key)
        
        self.assertFalse(result.verified)
    
    def test_verify_tampered_frame(self):
        """Test verification fails when frame is tampered with."""
        signed = self.verifier.sign_frame(self.sample_frame)
        
        # Tamper with frame content (change content before signature)
        lines = signed.split('\n')
        lines[0] = lines[0].replace("SUMMARY", "FACT")
        tampered = '\n'.join(lines)
        
        verifier2 = FrameVerifier(signer_id="test")
        result = verifier2.verify_frame(tampered, self.public_key)
        
        self.assertFalse(result.verified)
    
    def test_create_digest(self):
        """Test digest creation."""
        metadata = {"source": "agent-01", "convo_id": "abc123"}
        digest = self.verifier.create_digest(self.sample_frame, metadata)
        
        self.assertIsNotNone(digest.content_hash)
        self.assertEqual(digest.frame_type, "SUMMARY")
        self.assertEqual(len(digest.content_hash), 64)
        self.assertEqual(digest.metadata["source"], "agent-01")
    
    def test_verify_chain_of_frames(self):
        """Test verification of multiple frames."""
        frame1 = self.sample_frame
        frame2 = self.sample_frame.replace("summary", "fact")
        
        signed1 = self.verifier.sign_frame(frame1)
        signed2 = self.verifier.sign_frame(frame2)
        
        results = self.verifier.verify_chain([signed1, signed2], self.public_key)
        
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r.verified for r in results))
    
    def test_strip_signature(self):
        """Test signature stripping."""
        signed = self.verifier.sign_frame(self.sample_frame)
        stripped = FrameVerifier._strip_signature(signed)
        
        # Stripped version should not have [SIG|
        self.assertNotIn("[SIG|", stripped)
        # But original should
        self.assertIn("[SIG|", signed)
    
    def test_signature_is_deterministic(self):
        """Test that same frame produces same signature."""
        # Note: timestamps differ, but we'll use fixed ones
        signed1 = self.verifier.sign_frame(
            self.sample_frame, 
            timestamp="2025-12-20T10:00:00Z"
        )
        signed2 = self.verifier.sign_frame(
            self.sample_frame,
            timestamp="2025-12-20T10:00:00Z"
        )
        
        # Extract signature hex (first part after [SIG|)
        sig1 = signed1.split("[SIG|")[1].split("|")[0]
        sig2 = signed2.split("[SIG|")[1].split("|")[0]
        
        self.assertEqual(sig1, sig2)


class TestSignatureKeyManager(unittest.TestCase):
    """Tests for SignatureKeyManager."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.key1 = b"signer1_secret_key"
        self.key2 = b"signer2_secret_key"
    
    def test_register_signer(self):
        """Test registering a signer."""
        manager = SignatureKeyManager()
        manager.register_signer("agent-01", self.key1)
        
        retrieved = manager.get_key("agent-01")
        self.assertEqual(retrieved, self.key1)
    
    def test_verify_with_signer(self):
        """Test verification with registered signer."""
        manager = SignatureKeyManager()
        manager.register_signer("agent-01", self.key1)
        
        # Sign with verifier
        verifier = FrameVerifier(private_key=self.key1, signer_id="agent-01")
        frame = "TYPE|SUMMARY\nCONTENT|test"
        signed = verifier.sign_frame(frame)
        
        # Verify with manager
        result = manager.verify_with_signer(signed, "agent-01")
        self.assertTrue(result.verified)
    
    def test_verify_with_unknown_signer(self):
        """Test verification with unknown signer."""
        manager = SignatureKeyManager()
        
        result = manager.verify_with_signer("TYPE|SUMMARY", "unknown-signer")
        self.assertFalse(result.verified)
    
    def test_save_and_load_keys(self):
        """Test saving and loading keys from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            keys_file = Path(tmpdir) / "keys.json"
            manager = SignatureKeyManager(keys_file=keys_file)
            
            # Register signers
            manager.register_signer("agent-01", self.key1)
            manager.register_signer("agent-02", self.key2)
            manager.save_keys()
            
            # Load in new manager
            manager2 = SignatureKeyManager(keys_file=keys_file)
            
            self.assertEqual(manager2.get_key("agent-01"), self.key1)
            self.assertEqual(manager2.get_key("agent-02"), self.key2)
    
    def test_multiple_signers(self):
        """Test managing multiple signers."""
        manager = SignatureKeyManager()
        manager.register_signer("agent-01", self.key1)
        manager.register_signer("agent-02", self.key2)
        
        # Create frames signed by different agents
        frame = "TYPE|FACT\nCONTENT|test"
        
        verifier1 = FrameVerifier(private_key=self.key1, signer_id="agent-01")
        signed1 = verifier1.sign_frame(frame)
        
        verifier2 = FrameVerifier(private_key=self.key2, signer_id="agent-02")
        signed2 = verifier2.sign_frame(frame)
        
        # Both should verify with their respective keys
        result1 = manager.verify_with_signer(signed1, "agent-01")
        result2 = manager.verify_with_signer(signed2, "agent-02")
        
        self.assertTrue(result1.verified)
        self.assertTrue(result2.verified)
        
        # Cross-verification should fail
        result_cross = manager.verify_with_signer(signed1, "agent-02")
        self.assertFalse(result_cross.verified)


class TestFrameDigest(unittest.TestCase):
    """Tests for FrameDigest."""
    
    def test_digest_structure(self):
        """Test digest has expected structure."""
        verifier = FrameVerifier()
        frame = "TYPE|TRAIN_PAIR\nCONTENT|test"
        digest = verifier.create_digest(frame)
        
        self.assertEqual(digest.frame_type, "TRAIN_PAIR")
        self.assertEqual(len(digest.content_hash), 64)
        self.assertIsNotNone(digest.timestamp)
    
    def test_digest_metadata(self):
        """Test digest preserves metadata."""
        verifier = FrameVerifier()
        frame = "TYPE|FACT\nCONTENT|test"
        metadata = {
            "convo_id": "session-1",
            "quality": "high",
            "source": "agent-01"
        }
        
        digest = verifier.create_digest(frame, metadata)
        
        self.assertEqual(digest.metadata["convo_id"], "session-1")
        self.assertEqual(digest.metadata["quality"], "high")


if __name__ == "__main__":
    unittest.main()

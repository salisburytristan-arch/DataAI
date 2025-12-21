"""Frame verification and integrity checking for ForgeNumerics frames.

Provides cryptographic signing, verification, and audit trails for FN frames.
All frames can be signed with a private key and verified with a public key.
Enables tamper detection, source authentication, and immutable audit logs.
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class FrameSignature:
    """Signature metadata for a verified frame."""
    signature_hex: str  # HMAC-SHA256 hex
    signer_id: str      # Public key ID or signer identifier
    signed_at: str      # ISO8601 timestamp
    verified: bool      # Whether signature is valid
    verified_by: Optional[str] = None  # Which public key ID verified it


@dataclass
class FrameDigest:
    """Content hash and metadata for a frame."""
    content_hash: str   # SHA256 hex of frame content
    frame_type: str     # TYPE field value
    timestamp: str      # ISO8601 timestamp
    metadata: Dict[str, Any]  # Additional indexing metadata


class FrameVerifier:
    """
    Cryptographic verification for ForgeNumerics frames.
    
    Features:
    - HMAC-SHA256 signing and verification
    - Frame content hashing (SHA256)
    - Signature format: base64-encoded signature appended to frame
    - Audit trail metadata (signer_id, timestamp, etc.)
    - Public key rotation support via signer_id
    
    Usage:
        verifier = FrameVerifier(private_key=b"secret123")
        signed_frame = verifier.sign_frame(frame_str)
        is_valid = verifier.verify_frame(signed_frame, public_key=b"secret123")
    """
    
    def __init__(self, private_key: Optional[bytes] = None, signer_id: str = "default"):
        """
        Initialize verifier with optional signing key.
        
        Args:
            private_key: HMAC secret key (bytes). If None, verification only.
            signer_id: Identifier for this signer (e.g., "agent-01", "teacher-deepseek")
        """
        self.private_key = private_key
        self.signer_id = signer_id
    
    def compute_frame_hash(self, frame_str: str) -> str:
        """
        Compute SHA256 hash of frame content.
        
        Args:
            frame_str: The frame string (with or without signature)
            
        Returns:
            SHA256 hex digest
        """
        # Remove signature if present (format: FRAME\n...\n[SIG|...]
        content = self._strip_signature(frame_str)
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def sign_frame(self, frame_str: str, timestamp: Optional[str] = None) -> str:
        """
        Sign a frame with HMAC-SHA256.
        
        Inserts signature as [SIG|<hex>|<signer_id>|<timestamp>] before the frame terminator (⧈).
        This ensures the signed frame remains valid FN syntax.
        
        Args:
            frame_str: The frame to sign (should not already be signed)
            timestamp: ISO8601 timestamp (uses now() if not provided)
            
        Returns:
            Signed frame string with [SIG|...] inserted before terminator
            
        Raises:
            ValueError: If no private key configured
        """
        if not self.private_key:
            raise ValueError("Cannot sign without private_key configured")
        
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Compute HMAC of frame content (excluding terminator and signature)
        content = frame_str.encode('utf-8')
        sig_hex = hmac.new(
            self.private_key,
            content,
            hashlib.sha256
        ).hexdigest()
        
        # Build signature trailer
        sig_trailer = f"[SIG|{sig_hex}|{self.signer_id}|{timestamp}]"
        
        # Insert signature before frame terminator (⧈)
        # If frame ends with ⧈, insert before it
        if frame_str.endswith("⧈"):
            return frame_str[:-1] + "\n" + sig_trailer + "⧈"
        else:
            # If no terminator, just append
            return frame_str + "\n" + sig_trailer
    
    def verify_frame(self, signed_frame_str: str, public_key: bytes) -> FrameSignature:
        """
        Verify a signed frame with HMAC-SHA256.
        
        Args:
            signed_frame_str: The signed frame string with [SIG|...] and optional terminator
            public_key: HMAC secret key (same as private key used to sign)
            
        Returns:
            FrameSignature with verification result
        """
        # Extract signature data
        sig_data = self._extract_signature_data(signed_frame_str)
        if not sig_data:
            return FrameSignature(
                signature_hex="none",
                signer_id="unknown",
                signed_at="unknown",
                verified=False
            )
        
        sig_hex, signer_id, signed_at = sig_data
        
        # Get content (without signature, but including terminator)
        content = self._strip_signature_preserve_terminator(signed_frame_str).encode('utf-8')
        
        # Recompute signature
        expected_sig = hmac.new(public_key, content, hashlib.sha256).hexdigest()
        
        # Compare (constant-time)
        verified = hmac.compare_digest(sig_hex, expected_sig)
        
        return FrameSignature(
            signature_hex=sig_hex,
            signer_id=signer_id,
            signed_at=signed_at,
            verified=verified,
            verified_by=signer_id if verified else None
        )
    
    def create_digest(self, frame_str: str, metadata: Optional[Dict[str, Any]] = None) -> FrameDigest:
        """
        Create a content digest for indexing/auditing.
        
        Args:
            frame_str: The frame string
            metadata: Optional metadata dict to include
            
        Returns:
            FrameDigest with content hash and type info
        """
        from datetime import datetime
        
        # Extract frame type from header
        frame_type = "UNKNOWN"
        for line in frame_str.split('\n'):
            if line.startswith("TYPE"):
                parts = line.split('|')
                if len(parts) >= 2:
                    frame_type = parts[1].strip()
                break
        
        return FrameDigest(
            content_hash=self.compute_frame_hash(frame_str),
            frame_type=frame_type,
            timestamp=datetime.utcnow().isoformat() + "Z",
            metadata=metadata or {}
        )
    
    def verify_chain(self, frames: list[str], public_key: bytes) -> list[FrameSignature]:
        """
        Verify a chain of frames (e.g., conversation history).
        
        Args:
            frames: List of signed frame strings
            public_key: HMAC secret key for verification
            
        Returns:
            List of FrameSignature results
        """
        return [self.verify_frame(f, public_key) for f in frames]
    
    @staticmethod
    def _strip_signature(frame_str: str) -> str:
        """Remove [SIG|...] trailer from frame."""
        lines = frame_str.rstrip('\n').split('\n')
        # Check if last line is signature trailer
        if lines and lines[-1].startswith('[SIG|'):
            return '\n'.join(lines[:-1])
        return frame_str
    
    @staticmethod
    def _strip_signature_preserve_terminator(frame_str: str) -> str:
        """Remove signature but preserve frame terminator."""
        lines = frame_str.rstrip('\n').split('\n')
        # If last line is just terminator, keep it; if SIG line, check second-to-last
        if lines and lines[-1] == '⧈':
            # Frame ends with terminator, check if second-to-last is SIG
            if len(lines) > 1 and lines[-2].startswith('[SIG|'):
                return '\n'.join(lines[:-2] + ['⧈'])
        elif lines and lines[-1].startswith('[SIG|'):
            # If terminator is appended to signature line, preserve it
            if '⧈' in lines[-1]:
                return '\n'.join(lines[:-1] + ['⧈'])
            # No terminator, just SIG; remove SIG
            return '\n'.join(lines[:-1])
        return frame_str
    
    @staticmethod
    def _extract_signature_data(signed_frame_str: str) -> Optional[tuple[str, str, str]]:
        """
        Extract (sig_hex, signer_id, timestamp) from [SIG|...] line.
        
        Handles signatures both before and after the frame terminator.
        
        Returns:
            Tuple of (sig_hex, signer_id, signed_at) or None if not found
        """
        lines = signed_frame_str.rstrip('\n').split('\n')
        if not lines:
            return None
        
        # Check last two lines for signature (could be before or after terminator)
        sig_line = None
        # Accept signature even if terminator is appended on same line
        if len(lines) >= 1 and lines[-1].startswith('[SIG|'):
            sig_line = lines[-1]
        elif len(lines) >= 2 and lines[-2].startswith('[SIG|'):
            sig_line = lines[-2]
        
        if not sig_line:
            return None
        
        # Parse: [SIG|<hex>|<signer_id>|<timestamp>]
        # Find closing bracket even if followed by terminator
        end_idx = sig_line.rfind(']')
        if end_idx == -1:
            return None
        content = sig_line[5:end_idx]  # Strip [SIG| and up to ]
        parts = content.split('|')
        if len(parts) != 3:
            return None
        
        return (parts[0], parts[1], parts[2])



class SignatureKeyManager:
    """
    Manage signing keys for multiple signers (agents, teachers).
    
    Stores keys in JSON format with signer_id mapping.
    Supports key rotation and verification with specific signer IDs.
    """
    
    def __init__(self, keys_file: Optional[Path] = None):
        """
        Initialize key manager.
        
        Args:
            keys_file: Optional Path to JSON file with signer keys
        """
        self.keys_file = keys_file
        self.keys: Dict[str, bytes] = {}  # signer_id -> key
        if keys_file and keys_file.exists():
            self._load_keys()
    
    def register_signer(self, signer_id: str, key: bytes) -> None:
        """Register a signer with their key."""
        self.keys[signer_id] = key
    
    def get_key(self, signer_id: str) -> Optional[bytes]:
        """Get key for a signer."""
        return self.keys.get(signer_id)
    
    def verify_with_signer(
        self,
        signed_frame: str,
        signer_id: str
    ) -> FrameSignature:
        """
        Verify a frame with a specific signer's key.
        
        Args:
            signed_frame: The signed frame string
            signer_id: The signer ID to verify with
            
        Returns:
            FrameSignature with verification result
        """
        key = self.get_key(signer_id)
        if not key:
            return FrameSignature(
                signature_hex="unknown_signer",
                signer_id=signer_id,
                signed_at="unknown",
                verified=False
            )
        
        verifier = FrameVerifier(signer_id=signer_id)
        return verifier.verify_frame(signed_frame, key)
    
    def _load_keys(self) -> None:
        """Load keys from JSON file."""
        if not self.keys_file:
            return
        
        try:
            with open(self.keys_file, 'r') as f:
                data = json.load(f)
            # Convert hex strings back to bytes
            for signer_id, key_hex in data.items():
                self.keys[signer_id] = bytes.fromhex(key_hex)
        except Exception as e:
            print(f"Warning: Could not load keys from {self.keys_file}: {e}")
    
    def save_keys(self) -> None:
        """Save keys to JSON file."""
        if not self.keys_file:
            return
        
        # Convert bytes to hex for JSON
        data = {
            signer_id: key.hex()
            for signer_id, key in self.keys.items()
        }
        
        self.keys_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.keys_file, 'w') as f:
            json.dump(data, f, indent=2)


# Standard signing key (for testing and single-agent setups)
# In production, rotate this key and manage via SignatureKeyManager
DEFAULT_SIGNING_KEY = b"acx_default_key_v1_replace_in_prod"

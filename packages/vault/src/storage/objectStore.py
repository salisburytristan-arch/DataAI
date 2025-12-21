"""
Object store: content-addressed immutable storage for Vault records.
Files are stored by hash (SHA256) for deduplication and integrity verification.
"""
import os
import json
import hashlib
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class ObjectStore:
    """Content-addressed object storage."""
    
    def __init__(self, root_path: str):
        """
        Initialize object store at root_path.
        Creates objects/ subdirectory if it doesn't exist.
        """
        self.root = Path(root_path)
        self.objects_dir = self.root / "objects"
        self.objects_dir.mkdir(parents=True, exist_ok=True)
    
    def _hash_content(self, data: bytes) -> str:
        """Compute SHA256 hash of content."""
        return hashlib.sha256(data).hexdigest()
    
    def _get_object_path(self, content_hash: str) -> Path:
        """Get file path for an object by hash."""
        # Store in subdirectory by first 2 chars of hash (e.g., ab/ab123...)
        subdir = content_hash[:2]
        return self.objects_dir / subdir / content_hash
    
    def put(self, obj: Dict[str, Any]) -> str:
        """
        Store a record object (dict).
        Returns the content hash of the canonical JSON representation.
        """
        # Canonicalize: sort keys, no whitespace
        canonical_json = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        canonical_bytes = canonical_json.encode('utf-8')
        content_hash = self._hash_content(canonical_bytes)
        
        # Write to file if not already present
        object_path = self._get_object_path(content_hash)
        if not object_path.exists():
            object_path.parent.mkdir(parents=True, exist_ok=True)
            with open(object_path, 'w', encoding='utf-8') as f:
                f.write(canonical_json)
        
        return content_hash
    
    def get(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a record object by hash.
        Returns None if not found or corrupted.
        """
        object_path = self._get_object_path(content_hash)
        if not object_path.exists():
            return None
        
        try:
            with open(object_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return None
    
    def exists(self, content_hash: str) -> bool:
        """Check if object exists."""
        return self._get_object_path(content_hash).exists()
    
    def list_objects(self) -> list[str]:
        """List all object hashes in the store."""
        hashes = []
        for subdir in self.objects_dir.iterdir():
            if subdir.is_dir():
                for obj_file in subdir.iterdir():
                    if obj_file.is_file():
                        hashes.append(obj_file.name)
        return sorted(hashes)
    
    def verify_integrity(self, content_hash: str) -> bool:
        """
        Verify that a stored object's hash matches its content.
        Returns True if valid, False otherwise.
        """
        try:
            obj = self.get(content_hash)
            if not obj:
                return False
            canonical_json = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
            computed_hash = self._hash_content(canonical_json.encode('utf-8'))
            return computed_hash == content_hash
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return False
    
    def stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        hashes = self.list_objects()
        total_size = 0
        for h in hashes:
            path = self._get_object_path(h)
            if path.exists():
                total_size += path.stat().st_size
        
        return {
            "object_count": len(hashes),
            "total_bytes": total_size,
        }

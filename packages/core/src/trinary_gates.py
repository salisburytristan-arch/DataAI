"""
Phase I: Trinary Logic Gates
Emulation layer for trinary computation on binary hardware.
Implements T-NAND, T-XOR, and fundamental trinary operations.

Trinary values: 0 (⊙), 1 (⊗), 2 (Φ) mapped to 2-bit tuples:
  0 = 00
  1 = 01
  2 = 10
  (11 reserved for error state)
"""

from typing import Tuple, List
import numpy as np
from enum import Enum


class TritValue(Enum):
    """Trinary digit values."""
    ZERO = 0  # ⊙
    ONE = 1   # ⊗
    TWO = 2   # Φ
    ERROR = 3  # Reserved


def trit_to_binary(t: int) -> Tuple[int, int]:
    """Convert trit (0-2) to 2-bit binary representation."""
    if t == 0:
        return (0, 0)
    elif t == 1:
        return (0, 1)
    elif t == 2:
        return (1, 0)
    else:
        return (1, 1)  # Error state


def binary_to_trit(b0: int, b1: int) -> int:
    """Convert 2-bit binary to trit (0-2)."""
    if b0 == 0 and b1 == 0:
        return 0
    elif b0 == 0 and b1 == 1:
        return 1
    elif b0 == 1 and b1 == 0:
        return 2
    else:
        return 3  # Error state


def t_nand(a: int, b: int) -> int:
    """
    Trinary NAND gate: NOT(a AND b) in base-3.
    Truth table:
        a | b | Output
        -----------
        0 | 0 | 2 (NOT 0)
        0 | 1 | 2 (NOT 0)
        0 | 2 | 2 (NOT 0)
        1 | 0 | 2 (NOT 0)
        1 | 1 | 1 (NOT 1)
        1 | 2 | 2 (NOT 0)
        2 | 0 | 2 (NOT 0)
        2 | 1 | 2 (NOT 0)
        2 | 2 | 0 (NOT 2)
    """
    if a == 0 or b == 0:
        return 2
    elif a == 1 and b == 1:
        return 1
    elif a == 2 and b == 2:
        return 0
    else:
        return 2


def t_xor(a: int, b: int) -> int:
    """
    Trinary XOR: a differs from b.
    Truth table:
        a | b | Output
        -----------
        0 | 0 | 0
        0 | 1 | 1
        0 | 2 | 2
        1 | 0 | 1
        1 | 1 | 0
        1 | 2 | 2
        2 | 0 | 2
        2 | 1 | 2
        2 | 2 | 0
    """
    if a == b:
        return 0
    elif abs(a - b) == 1:
        return max(a, b) - min(a, b)
    else:  # |a - b| == 2
        return 2


def t_and(a: int, b: int) -> int:
    """Trinary AND: minimum value."""
    return min(a, b)


def t_or(a: int, b: int) -> int:
    """Trinary OR: maximum value."""
    return max(a, b)


def t_not(a: int) -> int:
    """Trinary NOT: 2 - a."""
    return 2 - a if a in (0, 1, 2) else 3


class TrinarySumming:
    """Trinary arithmetic: addition with carry in base-3."""

    @staticmethod
    def add_single(a: int, b: int, carry: int = 0) -> Tuple[int, int]:
        """
        Add two trits with carry.
        Returns (result_trit, carry_out).
        """
        total = a + b + carry
        if total < 3:
            return (total, 0)
        elif total < 6:
            return (total - 3, 1)
        else:
            return (total - 6, 2)

    @staticmethod
    def add_vectors(a: List[int], b: List[int]) -> List[int]:
        """
        Add two trinary vectors (right-aligned).
        Example: [1, 2, 1] + [2, 2] = [1, 2, 0] (carry cascades)
        """
        max_len = max(len(a), len(b))
        a = [0] * (max_len - len(a)) + a
        b = [0] * (max_len - len(b)) + b

        result = []
        carry = 0
        for i in range(max_len - 1, -1, -1):
            digit, carry = TrinarySumming.add_single(a[i], b[i], carry)
            result.insert(0, digit)

        if carry > 0:
            result.insert(0, carry)

        return result


class TrinaryCoder:
    """Emulation of CUDA-style parallel transcoding."""

    @staticmethod
    def bytes_to_trits(data: bytes) -> List[int]:
        """
        Convert byte sequence to trits.
        Each byte (0-255) → 5 trits (since 3^5 = 243 < 256 < 729 = 3^6).
        Uses greedy encoding.
        """
        trits = []
        for byte_val in data:
            # Convert byte to base-3 (5 trits)
            remaining = byte_val
            byte_trits = []
            for _ in range(5):
                byte_trits.insert(0, remaining % 3)
                remaining //= 3
            trits.extend(byte_trits)
        return trits

    @staticmethod
    def trits_to_bytes(trits: List[int]) -> bytes:
        """
        Convert trit sequence back to bytes.
        Groups trits in chunks of 5.
        """
        data = []
        for i in range(0, len(trits), 5):
            byte_trits = trits[i:i+5]
            # Pad if necessary
            byte_trits = [0] * (5 - len(byte_trits)) + byte_trits
            byte_val = 0
            for trit in byte_trits:
                byte_val = byte_val * 3 + trit
            data.append(byte_val & 0xFF)  # Ensure 8-bit
        return bytes(data)


class FrameAddressableMemory:
    """
    Frame-addressable memory system.
    Instead of byte addresses, memory is indexed by Frame Content IDs.
    """

    def __init__(self, capacity: int = 1_000_000):
        self.capacity = capacity
        self.memory = {}  # content_id -> trinary_data
        self.address_map = {}  # frame_id -> content_id
        self.reference_count = {}  # content_id -> count

    def store_frame(self, frame_id: str, content: List[int]) -> str:
        """
        Store frame content, return content ID (SHA256-like hash of content).
        """
        # Simplified: use hash of content as ID
        content_id = f"CONT_{hash(tuple(content)) & 0xFFFFFFFF:08X}"
        
        if content_id not in self.memory:
            if len(self.memory) >= self.capacity:
                raise MemoryError("Frame-addressable memory full")
            self.memory[content_id] = content
            self.reference_count[content_id] = 0

        self.address_map[frame_id] = content_id
        self.reference_count[content_id] += 1
        return content_id

    def retrieve_frame(self, frame_id: str) -> List[int]:
        """Retrieve frame by ID."""
        if frame_id not in self.address_map:
            raise KeyError(f"Frame {frame_id} not found")
        content_id = self.address_map[frame_id]
        return self.memory[content_id]

    def stats(self) -> dict:
        """Return memory statistics."""
        return {
            "total_frames": len(self.address_map),
            "unique_content": len(self.memory),
            "capacity": self.capacity,
            "usage_percent": 100 * len(self.memory) / self.capacity,
            "deduplication_ratio": len(self.address_map) / max(1, len(self.memory))
        }


class HolographicAssociativeMemory:
    """
    Holographic Associative Memory: semantic similarity retrieval.
    Uses cosine similarity on trinary embeddings for content-addressable lookup.
    """

    def __init__(self, embedding_dim: int = 256):
        self.embedding_dim = embedding_dim
        self.memories = {}  # embedding_id -> {"vector": trits, "data": content}
        self.index = np.zeros((0, embedding_dim))  # For fast similarity search

    def encode_memory(self, frame_id: str, content: List[int]) -> np.ndarray:
        """
        Encode frame content into a trinary embedding vector.
        Use folding of content hash to create semantic fingerprint.
        """
        # Pad or truncate content to embedding_dim
        if len(content) < self.embedding_dim:
            content = content + [0] * (self.embedding_dim - len(content))
        else:
            content = content[:self.embedding_dim]

        embedding = np.array(content, dtype=np.float32)
        self.memories[frame_id] = {"vector": embedding, "data": content}

        # Add to index
        if len(self.index) == 0:
            self.index = embedding.reshape(1, -1)
        else:
            self.index = np.vstack([self.index, embedding])

        return embedding

    def retrieve_by_similarity(self, query: List[int], top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Retrieve memories by semantic similarity (cosine distance).
        """
        if len(self.index) == 0:
            return []

        # Normalize query
        query = np.array(query[:self.embedding_dim], dtype=np.float32)
        query_norm = np.linalg.norm(query)
        if query_norm > 0:
            query = query / query_norm

        # Compute cosine similarities
        similarities = np.dot(self.index, query)

        # Get top-k
        frame_ids = list(self.memories.keys())
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        results = []
        for idx in top_indices:
            if idx < len(frame_ids):
                frame_id = frame_ids[idx]
                sim = float(similarities[idx])
                results.append((frame_id, sim))

        return results


if __name__ == "__main__":
    # Test trinary gates
    print("=== Trinary Gate Tests ===")
    print(f"T-NAND(1, 1) = {t_nand(1, 1)} (expect 1)")
    print(f"T-NAND(2, 2) = {t_nand(2, 2)} (expect 0)")
    print(f"T-XOR(1, 2) = {t_xor(1, 2)} (expect 2)")

    # Test arithmetic
    print("\n=== Trinary Addition ===")
    result = TrinarySumming.add_vectors([1, 2, 1], [2, 2])
    print(f"[1,2,1] + [2,2] = {result}")

    # Test transcoding
    print("\n=== Binary-Trinary Transcoding ===")
    data = b"Hi"
    trits = TrinaryCoder.bytes_to_trits(data)
    print(f"b'Hi' -> {len(trits)} trits: {trits[:20]}...")
    recovered = TrinaryCoder.trits_to_bytes(trits)
    print(f"Recovered: {recovered}")

    # Test Frame Memory
    print("\n=== Frame-Addressable Memory ===")
    fam = FrameAddressableMemory(capacity=10000)
    cid1 = fam.store_frame("FRAME_001", [1, 2, 1, 0, 2])
    cid2 = fam.store_frame("FRAME_002", [1, 2, 1, 0, 2])  # Duplicate
    print(f"Frame 1 Content ID: {cid1}")
    print(f"Frame 2 Content ID: {cid2}")
    print(f"Deduplication success: {cid1 == cid2}")
    print(f"Memory stats: {fam.stats()}")

    # Test Holographic Memory
    print("\n=== Holographic Associative Memory ===")
    ham = HolographicAssociativeMemory(embedding_dim=128)
    ham.encode_memory("MEMORY_A", [1, 0, 1] * 42 + [0])
    ham.encode_memory("MEMORY_B", [1, 0, 1] * 42 + [0])
    ham.encode_memory("MEMORY_C", [2, 1, 0] * 42 + [1])
    results = ham.retrieve_by_similarity([1, 0, 1] * 42, top_k=2)
    print(f"Top-2 similar to [1,0,1] pattern:")
    for mem_id, sim in results:
        print(f"  {mem_id}: similarity={sim:.4f}")

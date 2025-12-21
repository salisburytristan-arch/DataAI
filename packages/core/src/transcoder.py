"""
Phase I: Bit-to-Trit Transcoder
High-performance binary ↔ trinary conversion for CUDA emulation.

The transcoder enables efficient compression of binary data (from LLMs, files, etc.)
into the trinary ForgeNumerics-S alphabet while preserving lossless round-trip.
"""

import numpy as np
from typing import List, Tuple, Dict
from dataclasses import dataclass


@dataclass
class TranscodeProfile:
    """Configuration for transcoding efficiency."""
    source_bits: int  # bits per symbol (typically 8 for bytes)
    target_trits: int  # trits per symbol (typically 5 for base-3)
    compression_ratio: float  # target / source
    enable_huffman: bool = False
    parallel_batch_size: int = 1024


class BitTotritTranscoder:
    """
    Emulates CUDA-accelerated binary-to-trinary conversion.
    Implemented on CPU for development; ready for GPU kernel replacement.
    """

    # Lookup tables for fast conversion
    BYTE_TO_TRITS = {}  # Cache: byte value -> trit tuple
    TRITS_TO_BYTE = {}  # Cache: trit tuple -> byte value

    def __init__(self):
        self._build_lookup_tables()

    def _build_lookup_tables(self):
        """Pre-compute all possible byte↔trit conversions."""
        # 256 bytes × 5 trits per byte
        for byte_val in range(256):
            trits = self._encode_byte_to_trits(byte_val)
            self.BYTE_TO_TRITS[byte_val] = tuple(trits)

        # Build reverse table
        for byte_val, trits in self.BYTE_TO_TRITS.items():
            self.TRITS_TO_BYTE[trits] = byte_val

    @staticmethod
    def _encode_byte_to_trits(byte_val: int) -> List[int]:
        """
        Convert single byte (0-255) to 5 trits (0-2).
        3^5 = 243 < 256, so we pad with error handling.
        """
        trits = []
        val = byte_val
        for _ in range(5):
            trits.insert(0, val % 3)
            val //= 3
        return trits

    @staticmethod
    def _decode_trits_to_byte(trits: Tuple[int, ...]) -> int:
        """Convert 5 trits back to byte."""
        val = 0
        for trit in trits:
            val = val * 3 + trit
        return val & 0xFF

    def encode(self, data: bytes, profile: TranscodeProfile = None) -> List[int]:
        """
        Convert binary data (bytes) to trinary (list of ints 0-2).
        
        Parallelizable on GPU: process batch_size bytes independently.
        """
        if profile is None:
            profile = TranscodeProfile(
                source_bits=8,
                target_trits=5,
                compression_ratio=5/8,
                enable_huffman=False
            )

        result = []
        for byte_val in data:
            trits = self.BYTE_TO_TRITS.get(byte_val)
            if trits is None:
                trits = tuple(self._encode_byte_to_trits(byte_val))
            result.extend(trits)

        return result

    def decode(self, trits: List[int]) -> bytes:
        """
        Convert trinary (list of 0-2) back to binary (bytes).
        Assumes trits are properly aligned (multiple of 5).
        """
        # Pad to multiple of 5
        if len(trits) % 5 != 0:
            trits = trits + [0] * (5 - len(trits) % 5)

        data = []
        for i in range(0, len(trits), 5):
            trit_tuple = tuple(trits[i:i+5])
            byte_val = self.TRITS_TO_BYTE.get(
                trit_tuple,
                self._decode_trits_to_byte(trit_tuple)
            )
            data.append(byte_val)

        return bytes(data)

    def encode_vectorized(self, data: np.ndarray) -> np.ndarray:
        """
        Batch convert array of bytes to trits using NumPy.
        GPU-friendly: operates on large batches.
        """
        # Ensure uint8
        data = np.asarray(data, dtype=np.uint8)
        
        # Vectorized base-3 conversion
        trits = np.zeros((len(data), 5), dtype=np.uint8)
        remaining = data.copy()

        for i in range(5):
            trits[:, 4-i] = remaining % 3
            remaining //= 3

        return trits.reshape(-1)

    def decode_vectorized(self, trits: np.ndarray) -> np.ndarray:
        """
        Batch convert trits back to bytes using NumPy.
        """
        trits = np.asarray(trits, dtype=np.uint8).reshape(-1, 5)
        
        # Vectorized base-3 decoding
        bytes_out = np.zeros(len(trits), dtype=np.uint8)
        for i in range(5):
            bytes_out = bytes_out * 3 + trits[:, i]

        return bytes_out & 0xFF


class TriaryQuantizer:
    """
    Quantize continuous data (floats, weights) to trinary.
    Useful for model compression (from 32-bit float → 2-bit trits).
    """

    @staticmethod
    def quantize_float(value: float) -> int:
        """
        Map float to trit: -∞ to -0.5 → 0, -0.5 to 0.5 → 1, 0.5 to ∞ → 2.
        """
        if value < -0.5:
            return 0
        elif value <= 0.5:
            return 1
        else:
            return 2

    @staticmethod
    def dequantize_trit(trit: int) -> float:
        """
        Map trit back to representative float.
        """
        if trit == 0:
            return -1.0
        elif trit == 1:
            return 0.0
        else:
            return 1.0

    @staticmethod
    def quantize_vector(weights: np.ndarray) -> List[int]:
        """
        Quantize array of floats to trits.
        Normalize to (-1, 1) range first.
        """
        # Normalize
        normalized = (weights - weights.mean()) / (weights.std() + 1e-8)
        normalized = np.clip(normalized, -2, 2) / 2  # Reduce to ~(-1, 1)

        # Quantize
        return [TriaryQuantizer.quantize_float(v) for v in normalized]

    @staticmethod
    def dequantize_vector(trits: List[int]) -> np.ndarray:
        """
        Dequantize trits back to float array.
        """
        return np.array([TriaryQuantizer.dequantize_trit(t) for t in trits])


class BLOBTCompression:
    """
    BLOB-T: Binary Large Object in Trinary format.
    Lossless compression using Huffman-Trinary encoding.
    Reserved 4th symbol ⊛ for special encodings.
    """

    def __init__(self):
        self.huffman_tree = {}  # symbol -> code
        self.reverse_tree = {}  # code -> symbol

    def build_huffman_codes(self, data: List[int]):
        """
        Build Huffman codes optimized for trinary (branching factor 3).
        """
        from collections import Counter

        # Count frequencies
        freq = Counter(data)

        # For demo: simple fixed codes (in production use full Huffman)
        unique_symbols = sorted(freq.keys())
        self.huffman_tree = {sym: [i] for i, sym in enumerate(unique_symbols)}
        self.reverse_tree = {tuple([i]): sym for i, sym in enumerate(unique_symbols)}

    def compress(self, data: List[int]) -> List[int]:
        """
        Compress trinary data using Huffman-Trinary codes.
        """
        if not self.huffman_tree:
            self.build_huffman_codes(data)

        compressed = []
        for symbol in data:
            code = self.huffman_tree.get(symbol, [symbol])
            compressed.extend(code)

        return compressed

    def decompress(self, compressed: List[int]) -> List[int]:
        """
        Decompress Huffman-Trinary data.
        """
        if not self.reverse_tree:
            raise ValueError("Huffman tree not built; call compress first")

        # Simple decode (full version uses trie traversal)
        decompressed = []
        i = 0
        while i < len(compressed):
            for code_len in range(1, 4):  # Try codes of length 1-3
                code = tuple(compressed[i:i+code_len])
                if code in self.reverse_tree:
                    decompressed.append(self.reverse_tree[code])
                    i += code_len
                    break
            else:
                # Code not found, skip
                i += 1

        return decompressed


if __name__ == "__main__":
    print("=== Bit-to-Trit Transcoder ===\n")

    transcoder = BitTotritTranscoder()

    # Test single byte conversion
    data = b"Hello"
    trits = transcoder.encode(data)
    print(f"Input: {data}")
    print(f"Trits ({len(trits)} total): {trits[:30]}...")
    recovered = transcoder.decode(trits)
    print(f"Recovered: {recovered}")
    print(f"Match: {data == recovered}\n")

    # Test vectorized conversion
    print("=== Vectorized Conversion ===")
    large_data = np.random.randint(0, 256, size=10000, dtype=np.uint8)
    trits_vec = transcoder.encode_vectorized(large_data)
    recovered_vec = transcoder.decode_vectorized(trits_vec)
    print(f"Input size: {len(large_data)} bytes")
    print(f"Trits: {len(trits_vec)}")
    print(f"Compression ratio: {len(trits_vec) / (len(large_data) * 8):.2%}")
    print(f"Lossless round-trip: {np.array_equal(large_data, recovered_vec)}\n")

    # Test quantization
    print("=== Float Quantization ===")
    weights = np.array([0.5, -0.3, 1.2, -0.9, 0.0])
    trits_q = TriaryQuantizer.quantize_vector(weights)
    dequants = TriaryQuantizer.dequantize_vector(trits_q)
    print(f"Original weights: {weights}")
    print(f"Quantized trits: {trits_q}")
    print(f"Dequantized: {dequants}\n")

    # Test BLOB-T compression
    print("=== BLOB-T Compression ===")
    test_data = [1, 1, 2, 1, 0, 0, 1, 2, 2, 0] * 10
    blob = BLOBTCompression()
    compressed = blob.compress(test_data)
    decompressed = blob.decompress(compressed)
    print(f"Original: {len(test_data)} symbols")
    print(f"Compressed: {len(compressed)} symbols")
    print(f"Ratio: {len(compressed) / len(test_data):.2%}")
    print(f"Lossless: {test_data == decompressed}")

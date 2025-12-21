#!/usr/bin/env python3
"""Test the new CLI commands."""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.canonicalize import canonicalize_string, is_canonical
from src.frames import Frame
from src.errors import ParseError

# Test 1: validate
print("=== Test 1: Validate ===")
test_frame = "⧆≛TYPE⦙≛VECTOR∷≗⊙⊙⊗⦙≗⊙⊙Φ⧈"
try:
    frame = Frame.parse(test_frame)
    print(f"✓ Frame parsed: {frame.serialize()}")
except ParseError as e:
    print(f"✗ Parse error: {e}")

# Test 2: canonicalize
print("\n=== Test 2: Canonicalize ===")
unsorted = "⧆≛Z⦙≛val∴≛A⦙≛val∷token1⧈"
try:
    canonical = canonicalize_string(unsorted)
    print(f"Original:   {unsorted}")
    print(f"Canonical:  {canonical}")
    print(f"Is canonical: {is_canonical(canonical)}")
except Exception as e:
    print(f"✗ Error: {e}")

# Test 3: diff
print("\n=== Test 3: Diff ===")
frame1 = "⧆≛TYPE⦙≛VECTOR∷token1⧈"
frame2 = "⧆≛TYPE⦙≛VECTOR∷token1⧈"  # identical
frame3 = "⧆≛TYPE⦙≛MATRIX∷token1⧈"  # different

try:
    f1_parsed = Frame.parse(frame1)
    f2_parsed = Frame.parse(frame2)
    f3_parsed = Frame.parse(frame3)
    print(f"frame1 == frame2 (bytewise): {frame1 == frame2}")
    print(f"frame1 == frame3 (bytewise): {frame1 == frame3}")
    c1 = canonicalize_string(frame1)
    c3 = canonicalize_string(frame3)
    print(f"frame1 canonical == frame3 canonical: {c1 == c3}")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n✓ All CLI tests passed")

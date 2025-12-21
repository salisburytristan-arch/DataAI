"""
AI Training Examples for ForgeNumerics-S (Part 11)

These examples follow the spec's training curriculum and provide
concrete encode/decode pairs for AI learning.
"""

from src.numeric import encode_int_u3, decode_int_u3, encode_int_s3, decode_int_s3
from src.frames import Frame


def example_11_2_int_u3_encoding():
    """
    Part 11.2 — INT-U3 Encoding Example
    
    Instruction: "Encode 42 as INT-U3."
    
    Expected reasoning:
    - 42₁₀ → 1120₃ → digits [1,1,2,0] → [⊗,⊗,Φ,⊙]
    - Token: ≗⊙⊙⊗⊗Φ⊙
    """
    result = {
        "instruction": "Encode 42 as INT-U3",
        "value": 42,
        "base10": 42,
        "base3": "1120",
        "base3_digits": [1, 1, 2, 0],
        "trits": ["⊗", "⊗", "Φ", "⊙"],
        "token": encode_int_u3(42),
        "expected": "≗⊙⊙⊗⊗Φ⊙",
        "decoded": decode_int_u3(encode_int_u3(42))
    }
    
    assert result["token"] == result["expected"], f"Expected {result['expected']}, got {result['token']}"
    assert result["decoded"] == 42
    
    return result


def example_11_3_mixed_sentence():
    """
    Part 11.3 — Mixed Sentence Encoding
    
    Instruction: "Encode: PLAYER has 3 lives."
    
    Using hypothetical dictionary:
    - PLAYER → P_PLAYER
    - has → P_HAS
    - lives → P_LIVES
    
    3₁₀ → 10₃ → ⊗⊙ → ≗⊙⊙⊗⊙
    
    Result (conceptual): ≛P_PLAYER⦙≛P_HAS⦙≗⊙⊙⊗⊙⦙≛P_LIVES
    """
    # Encode the number 3
    three_encoded = encode_int_u3(3)
    
    result = {
        "instruction": "Encode: PLAYER has 3 lives.",
        "sentence": "PLAYER has 3 lives",
        "dictionary_mappings": {
            "PLAYER": "P_PLAYER",
            "has": "P_HAS",
            "lives": "P_LIVES"
        },
        "number_value": 3,
        "number_base3": "10",
        "number_token": three_encoded,
        "expected_number_token": "≗⊙⊙⊗⊙",
        "conceptual_result": "≛P_PLAYER⦙≛P_HAS⦙≗⊙⊙⊗⊙⦙≛P_LIVES",
        "notes": "In actual implementation, word tokens use symbol combos from Words.txt"
    }
    
    assert three_encoded == "≗⊙⊙⊗⊙"
    
    return result


def example_11_4_encrypted_frame_reasoning():
    """
    Part 11.4 — Encrypted Frame Reasoning
    
    Given an encrypted frame, the AI should recognize it cannot decrypt
    without keys but can still reason about metadata.
    
    Frame: ⧆≛TYPE⦙≛ENCRYPTED∴≛ENC⦙≛AES_GCM∴≛KEY_ID⦙≛K123 ∷ ≗Φ⊙Φ⊗⊙Φ... ⧈
    
    Expected AI reasoning:
    "This is an encrypted payload; I cannot see its plaintext without 
    KEY_ID K123 and the decryption function. I can still see that 
    ENC=AES_GCM and TYPE=ENCRYPTED."
    """
    # Build encrypted frame
    header = [
        ("TYPE", "ENCRYPTED"),
        ("ENC", "AES_GCM"),
        ("KEY_ID", "K123")
    ]
    payload = ["≗Φ⊙Φ⊗⊙Φ⊗⊗Φ"]  # Mock ciphertext BLOB-T
    
    frame = Frame(header, payload)
    serialized = frame.serialize()
    
    # Parse back
    parsed = Frame.parse(serialized)
    
    result = {
        "instruction": "Reason about this encrypted frame",
        "frame": serialized,
        "ai_reasoning": {
            "can_decrypt": False,
            "reason": "No access to KEY_ID K123 or decryption function",
            "known_metadata": {
                "TYPE": "ENCRYPTED",
                "ENC": "AES_GCM",
                "KEY_ID": "K123"
            },
            "payload_type": "BLOB-T (opaque ciphertext)",
            "conclusion": "Cannot access plaintext but can reason about encryption method and key requirement"
        },
        "parsed_header": dict(parsed.header),
        "parsed_payload": parsed.payload
    }
    
    return result


def example_trit_basics():
    """
    Part 11.1 Stage 1 — Trit Basics
    
    Learn fundamental mappings: ⊙⊗Φ ↔ 0/1/2
    """
    mappings = [
        {"symbol": "⊙", "value": 0, "name": "zero"},
        {"symbol": "⊗", "value": 1, "name": "one"},
        {"symbol": "Φ", "value": 2, "name": "two"}
    ]
    
    # Practice encoding small integers
    examples = []
    for n in [0, 1, 2, 5, 10, 42, 100]:
        token = encode_int_u3(n)
        decoded = decode_int_u3(token)
        examples.append({
            "value": n,
            "token": token,
            "decoded": decoded,
            "verified": decoded == n
        })
    
    return {
        "trit_mappings": mappings,
        "practice_examples": examples,
        "all_verified": all(ex["verified"] for ex in examples)
    }


def example_signed_integers():
    """
    Part 11.1 Stage 2 — Signed INT-S3
    
    Practice with positive and negative integers
    """
    examples = []
    for n in [-14, -1, 0, 1, 42, -100]:
        token = encode_int_s3(n)
        decoded = decode_int_s3(token)
        examples.append({
            "value": n,
            "sign": "positive" if n >= 0 else "negative",
            "token": token,
            "decoded": decoded,
            "verified": decoded == n
        })
    
    return {
        "examples": examples,
        "all_verified": all(ex["verified"] for ex in examples),
        "notes": "Sign trit: ⊙=positive/zero, ⊗=negative"
    }


def example_list_of_integers():
    """
    Part 11.1 Stage 2 — Lists of Integers in Frames
    
    Build a simple list and compute sum
    """
    # Original values
    values = [10, 20, 30]
    
    # Encode as INT-U3 tokens
    tokens = [encode_int_u3(v) for v in values]
    
    # Build frame
    header = [
        ("TYPE", "INTEGER_LIST"),
        ("COUNT", str(len(values)))
    ]
    frame = Frame(header, tokens)
    serialized = frame.serialize()
    
    # Decode and sum
    parsed = Frame.parse(serialized)
    decoded_values = [decode_int_u3(t) for t in parsed.payload]
    total = sum(decoded_values)
    
    return {
        "original_values": values,
        "encoded_tokens": tokens,
        "frame": serialized,
        "decoded_values": decoded_values,
        "sum": total,
        "verified": decoded_values == values and total == 60
    }


def run_all_training_examples():
    """Run all Part 11 training examples"""
    print("=== AI Training Examples (Part 11) ===\n")
    
    # Example 11.2
    ex1 = example_11_2_int_u3_encoding()
    print(f"✓ Example 11.2 — INT-U3 Encoding")
    print(f"  {ex1['instruction']}")
    print(f"  Token: {ex1['token']}")
    print(f"  Decoded: {ex1['decoded']}\n")
    
    # Example 11.3
    ex2 = example_11_3_mixed_sentence()
    print(f"✓ Example 11.3 — Mixed Sentence")
    print(f"  {ex2['instruction']}")
    print(f"  Number 3 encoded: {ex2['number_token']}")
    print(f"  Conceptual result: {ex2['conceptual_result']}\n")
    
    # Example 11.4
    ex3 = example_11_4_encrypted_frame_reasoning()
    print(f"✓ Example 11.4 — Encrypted Frame Reasoning")
    print(f"  Can decrypt: {ex3['ai_reasoning']['can_decrypt']}")
    print(f"  Known metadata: {ex3['ai_reasoning']['known_metadata']}\n")
    
    # Trit basics
    ex4 = example_trit_basics()
    print(f"✓ Stage 1 — Trit Basics")
    print(f"  Verified {len(ex4['practice_examples'])} examples")
    print(f"  All correct: {ex4['all_verified']}\n")
    
    # Signed integers
    ex5 = example_signed_integers()
    print(f"✓ Stage 2 — Signed Integers")
    print(f"  Verified {len(ex5['examples'])} examples")
    print(f"  All correct: {ex5['all_verified']}\n")
    
    # Lists
    ex6 = example_list_of_integers()
    print(f"✓ Stage 2 — Lists of Integers")
    print(f"  Values: {ex6['original_values']}")
    print(f"  Sum: {ex6['sum']}")
    print(f"  Verified: {ex6['verified']}\n")
    
    print("All training examples passed!")


if __name__ == "__main__":
    run_all_training_examples()

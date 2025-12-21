import sys
from pathlib import Path

# Ensure 'packages' dir on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from packages.core.src.frame_verifier import FrameVerifier, DEFAULT_SIGNING_KEY

FACT = """TYPE|FACT
SUBJECT|Bank Capital
PREDICATE|requires
OBJECT|Risk Mitigation
⧈"""

def main():
    verifier = FrameVerifier(private_key=DEFAULT_SIGNING_KEY, signer_id="acx-agent")
    signed = verifier.sign_frame(FACT)
    print("Signed frame:")
    print(signed.encode('utf-8', errors='replace').decode('utf-8'))

    tampered = signed.replace("Risk", "Risc", 1)
    result = verifier.verify_frame(tampered, public_key=DEFAULT_SIGNING_KEY)
    print("Verification:", result)
    print("Verified:", result.verified)
    if result.verified:
        raise SystemExit("Expected verification to fail after tamper")

if __name__ == "__main__":
    main()

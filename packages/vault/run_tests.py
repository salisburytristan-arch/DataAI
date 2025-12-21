"""Test runner for Vault: runs unittest discovery."""
import sys
import unittest
from pathlib import Path

# Ensure workspace root on path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    passed = total - failed
    print(f"\n=== Summary: {passed} passed, {failed} failed ===")
    sys.exit(1 if failed else 0)


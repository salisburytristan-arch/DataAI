import unittest
import sys
from pathlib import Path

# Add workspace root to sys.path so 'packages.*' resolves across sibling packages
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover("tests")
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    total = result.testsRun
    failed = len(result.failures) + len(result.errors)
    print(f"\n=== Summary: {total - failed} passed, {failed} failed ===")
    sys.exit(1 if failed else 0)

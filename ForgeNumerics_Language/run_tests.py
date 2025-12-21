"""
No-dependency test runner for ForgeNumerics-S.
Executes all test modules and reports results.
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

def run_test_module(module_name):
    """Import and run all test functions from a module."""
    try:
        mod = __import__(module_name, fromlist=[''])
        test_funcs = [getattr(mod, name) for name in dir(mod) if name.startswith('test_')]
        passed = 0
        failed = 0
        for func in test_funcs:
            try:
                func()
                passed += 1
                print(f"  ✓ {func.__name__}")
            except AssertionError as e:
                failed += 1
                print(f"  ✗ {func.__name__}: {e}")
            except Exception as e:
                failed += 1
                print(f"  ✗ {func.__name__}: ERROR {e}")
        return passed, failed
    except Exception as e:
        print(f"  ERROR loading {module_name}: {e}")
        if "No module named 'yaml'" in str(e) or "No module named 'PyYAML'" in str(e):
            print("  HINT: Install dependencies: python -m pip install -r ForgeNumerics_Language/requirements.txt")
        # Treat module load failures as failures so CI/dev runs don't look green.
        return 0, 1


if __name__ == '__main__':
    print("=== ForgeNumerics-S Test Suite ===\n")
    
    test_modules = [
        'tests.test_extdict',
        'tests.test_schemas',
        'tests.test_meta_frames',
        'tests.test_meta_frames_parse',
        'tests.test_blob_t_roundtrip',
        'tests.test_canonicalize',
    ]
    
    total_passed = 0
    total_failed = 0
    
    for mod_name in test_modules:
        print(f"[{mod_name}]")
        p, f = run_test_module(mod_name)
        total_passed += p
        total_failed += f
        print()
    
    print(f"=== Summary: {total_passed} passed, {total_failed} failed ===")
    sys.exit(0 if total_failed == 0 else 1)

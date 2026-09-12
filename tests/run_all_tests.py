"""
Test Suite Execution Runner.
Runs all unit tests in tests/ directory and reports test pass status across modules.
"""

import sys
import pytest
from pathlib import Path


def run_full_test_suite():
    root_dir = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(root_dir))
    
    print("=" * 60)
    print("RUNNING CYBERBULLYING DETECTOR FULL UNIT TEST SUITE")
    print("=" * 60)

    exit_code = pytest.main([
        str(root_dir / "tests"),
        "-v",
        "--tb=short"
    ])

    if exit_code == 0:
        print("\n✅ ALL UNIT TESTS PASSED SUCCESSFULLY!")
    else:
        print(f"\n❌ TEST SUITE FAILED WITH EXIT CODE: {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(run_full_test_suite())

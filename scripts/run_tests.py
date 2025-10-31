#!/usr/bin/env python3
"""
Quick Test Runner
=================

Run all platform tests or specific platform tests.

Usage:
    python scripts/run_tests.py               # Run all tests
    python scripts/run_tests.py facebook      # Run Facebook test only
    python scripts/run_tests.py --help        # Show help
"""

import sys
import os
import subprocess
from pathlib import Path


def run_test(platform: str) -> int:
    """Run a specific platform test."""
    script_path = Path(__file__).parent / f"test_{platform}.py"

    if not script_path.exists():
        print(f"❌ Test script not found: {script_path}")
        return 1

    print(f"\n{'='*70}")
    print(f"  Running {platform.upper()} Platform Tests")
    print(f"{'='*70}\n")

    # Run the test script
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=Path(__file__).parent.parent
    )

    return result.returncode


def main():
    """Main test runner."""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--help', '-h']:
            print(__doc__)
            return 0

        # Run specific platform test
        platform = sys.argv[1].lower()
        return run_test(platform)

    # Run all available tests
    available_tests = ['facebook']  # Add 'instagram', 'youtube' when ready

    print("\n" + "="*70)
    print("  RUNNING ALL PLATFORM TESTS")
    print("="*70)

    results = {}
    for platform in available_tests:
        exit_code = run_test(platform)
        results[platform] = 'PASSED' if exit_code == 0 else 'FAILED'

    # Print summary
    print("\n" + "="*70)
    print("  ALL TESTS SUMMARY")
    print("="*70)

    for platform, status in results.items():
        symbol = "✅" if status == "PASSED" else "❌"
        print(f"{symbol} {platform.upper()}: {status}")

    # Return non-zero if any test failed
    return 0 if all(s == 'PASSED' for s in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())

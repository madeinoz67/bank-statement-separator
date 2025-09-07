#!/usr/bin/env python3
"""Test runner script for bank statement separator."""

import sys
import subprocess
from pathlib import Path
import argparse


def run_pytest(test_type: str = "all", verbose: bool = False, coverage: bool = False):
    """Run pytest with specified parameters."""

    # Base pytest command
    cmd = ["uv", "run", "pytest"]

    # Test selection
    if test_type == "unit":
        cmd.extend(["tests/unit/", "-m", "unit"])
    elif test_type == "integration":
        cmd.extend(["tests/integration/", "-m", "integration"])
    elif test_type == "edge_cases":
        cmd.extend(["-m", "edge_case"])
    elif test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type == "requires_api":
        cmd.extend(["-m", "requires_api"])
    else:  # all
        cmd.append("tests/")

    # Verbosity
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("--tb=short")

    # Coverage
    if coverage:
        cmd.extend(
            [
                "--cov=src/bank_statement_separator",
                "--cov-report=html",
                "--cov-report=term",
            ]
        )

    # Additional options
    cmd.extend(["--color=yes", "--strict-markers"])

    print(f"🧪 Running tests: {' '.join(cmd)}")
    print("=" * 60)

    # Run the command
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)

    return result.returncode


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Bank Statement Separator Test Runner")
    parser.add_argument(
        "--type",
        choices=["all", "unit", "integration", "edge_cases", "fast", "requires_api"],
        default="all",
        help="Type of tests to run",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--coverage", "-c", action="store_true", help="Run with coverage"
    )
    parser.add_argument(
        "--generate", "-g", action="store_true", help="Generate test statements first"
    )

    args = parser.parse_args()

    print("🔧 Bank Statement Separator Test Suite")
    print("=" * 50)

    # Check if we need to generate test statements
    if args.generate:
        print("📄 Generating test statements...")
        gen_result = subprocess.run(
            ["uv", "run", "python", "scripts/generate_test_statements.py"],
            cwd=Path(__file__).parent.parent,
        )

        if gen_result.returncode != 0:
            print("❌ Failed to generate test statements")
            return gen_result.returncode
        print("✅ Test statements generated\n")

    # Run tests
    exit_code = run_pytest(args.type, args.verbose, args.coverage)

    if exit_code == 0:
        print("\n🎉 All tests passed!")

        if args.coverage:
            print("📊 Coverage report generated in htmlcov/")
    else:
        print(f"\n❌ Tests failed with exit code {exit_code}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

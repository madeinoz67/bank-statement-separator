#!/usr/bin/env python3
"""Comprehensive validation of metadata extraction using controlled test documents."""

import json
import os
import subprocess
from pathlib import Path


def run_test(input_file, expected_spec, test_name):
    """Run a test and validate results against expected specifications."""

    print(f"\n🔍 TESTING: {test_name}")
    print(f"📄 Input: {input_file}")
    print(f"📋 Expected: {expected_spec['expected_statements']} statements")

    # Create temporary output directory within tests/ to keep project clean
    import uuid

    tests_dir = Path(__file__).parent.parent / "tests"
    temp_base = tests_dir / "test_temp"

    # Clean up any existing temp directory from previous runs
    if temp_base.exists():
        import shutil

        shutil.rmtree(temp_base)

    temp_base.mkdir(parents=True, exist_ok=True)

    # Create unique subdirectory for this validation run
    session_id = str(uuid.uuid4())[:8]
    temp_dir = temp_base / f"validation_{session_id}"
    temp_dir.mkdir()
    output_dir = str(temp_dir / "output")

    try:
        # Run the separator
        cmd = [
            "uv",
            "run",
            "python",
            "-m",
            "src.bank_statement_separator.main",
            "process",
            input_file,
            "-o",
            output_dir,
            "--verbose",
            "-y",
        ]

        env = os.environ.copy()
        env["LLM_PROVIDER"] = "auto"
        env["OPENAI_API_KEY"] = "invalid"
        env["OLLAMA_BASE_URL"] = "http://invalid:9999"

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode != 0:
                print(f"❌ FAILED: Process returned code {result.returncode}")
                print(f"   Error: {result.stderr}")
                return False

            # Check generated files
            output_files = list(Path(output_dir).glob("*.pdf"))
            actual_count = len(output_files)
            expected_count = expected_spec["expected_statements"]

            print("📊 RESULTS:")
            print(
                f"   Statements detected: {actual_count} (expected: {expected_count})"
            )

            if actual_count != expected_count:
                print("❌ STATEMENT COUNT MISMATCH")
                return False

            # Validate filenames match expected patterns
            actual_filenames = [f.name for f in sorted(output_files)]
            expected_filenames = expected_spec["expected_files"]

            print("📁 FILES GENERATED:")
            for filename in actual_filenames:
                print(f"   - {filename}")

            print("📁 FILES EXPECTED:")
            for filename in expected_filenames:
                print(f"   - {filename}")

            # Check if key parts match (bank, account ending, date patterns)
            filename_validation = validate_filename_patterns(
                actual_filenames, expected_spec
            )

            if filename_validation:
                print("✅ SUCCESS: All validations passed")
                return True
            else:
                print("❌ FILENAME VALIDATION FAILED")
                return False

        except Exception as e:
            print(f"❌ EXCEPTION: {e}")
            return False
    finally:
        # Clean up temporary directory
        if temp_dir.exists():
            import shutil

            shutil.rmtree(temp_dir)
        # Clean up base temp directory if empty
        if temp_base.exists() and not list(temp_base.iterdir()):
            temp_base.rmdir()


def validate_filename_patterns(actual_filenames, expected_spec):
    """Validate that generated filenames contain expected patterns."""

    expected_accounts = expected_spec["expected_accounts"]
    expected_banks = expected_spec["expected_banks"]

    # Check account numbers are present in filenames
    for i, account in enumerate(expected_accounts):
        account_last4 = account[-4:] if len(account) >= 4 else account
        found_in_filename = any(
            account_last4 in filename for filename in actual_filenames
        )

        if not found_in_filename:
            print(f"❌ Account ending {account_last4} not found in any filename")
            return False

    # Check bank names are present (normalized form)
    expected_banks_normalized = []
    for bank in expected_banks:
        if "westpac" in bank.lower():
            expected_banks_normalized.append("westpac")
        elif "commonwealth" in bank.lower():
            expected_banks_normalized.append("commonw")  # Truncated in filename
        elif "anz" in bank.lower():
            expected_banks_normalized.append("anz")
        else:
            expected_banks_normalized.append(bank.lower()[:7])  # First 7 chars

    for bank in expected_banks_normalized:
        found_in_filename = any(
            bank in filename.lower() for filename in actual_filenames
        )
        if not found_in_filename:
            print(f"❌ Bank '{bank}' not found in any filename")
            return False

    return True


def main():
    """Run comprehensive metadata extraction validation."""

    print("🧪 COMPREHENSIVE METADATA EXTRACTION VALIDATION")
    print("=" * 60)

    # Load test specifications
    spec_file = "./test/input/controlled/test_specifications.json"
    if not os.path.exists(spec_file):
        print(f"❌ Test specifications file not found: {spec_file}")
        return

    with open(spec_file, "r") as f:
        test_specs = json.load(f)

    all_tests_passed = True

    # Test 1: Single statement
    single_test = test_specs["single_statement"]
    input_file = f"./test/input/controlled/{single_test['file']}"

    if os.path.exists(input_file):
        result = run_test(input_file, single_test["spec"], "Single Statement")
        all_tests_passed = all_tests_passed and result
    else:
        print(f"❌ Test file not found: {input_file}")
        all_tests_passed = False

    # Test 2: Multi statement
    multi_test = test_specs["multi_statement"]
    input_file = f"./test/input/controlled/{multi_test['file']}"

    if os.path.exists(input_file):
        result = run_test(input_file, multi_test["spec"], "Multi Statement")
        all_tests_passed = all_tests_passed and result
    else:
        print(f"❌ Test file not found: {input_file}")
        all_tests_passed = False

    # Final results
    print("\n" + "=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - METADATA EXTRACTION WORKING CORRECTLY")
    else:
        print("❌ SOME TESTS FAILED - METADATA EXTRACTION NEEDS FIXES")
    print("=" * 60)


if __name__ == "__main__":
    main()

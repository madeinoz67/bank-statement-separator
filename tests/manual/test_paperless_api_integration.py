#!/usr/bin/env python3
"""
Manual test script for paperless-ngx API integration testing.

This script helps set up and run API integration tests against a real paperless-ngx instance.
It provides utilities for test environment setup and validation.

Usage:
    python tests/manual/test_paperless_api_integration.py --help
    python tests/manual/test_paperless_api_integration.py --setup
    python tests/manual/test_paperless_api_integration.py --validate
    python tests/manual/test_paperless_api_integration.py --run-tests
"""

import argparse
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config, Config
from bank_statement_separator.utils.paperless_client import (
    PaperlessClient,
    PaperlessUploadError,
)


def setup_test_environment():
    """Set up the test environment for API integration testing."""
    print("🔧 Setting up API integration test environment...")

    # Check if integration env file exists
    integration_env = Path("tests/env/paperless_integration.env")
    if not integration_env.exists():
        print(f"❌ Integration environment file not found: {integration_env}")
        return False

    # Load the environment
    try:
        load_config(str(integration_env))
        print(f"✅ Loaded configuration from {integration_env}")
    except Exception as e:
        print(f"❌ Failed to load configuration: {e}")
        return False

    # Check required environment variables
    required_vars = {
        "PAPERLESS_URL": "Paperless-ngx server URL",
        "PAPERLESS_TOKEN": "Paperless-ngx API token",
        "PAPERLESS_API_INTEGRATION_TEST": "Integration test enablement flag",
    }

    missing_vars = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  {var}: {description}")

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(var)
        print(f"\n💡 Set these variables or update {integration_env}")
        return False

    # Create test directories
    test_dirs = [
        "test/output/api_integration",
        "test/processed/api_integration",
        "test/logs",
        "test/quarantine/api_integration",
        "test/error_reports/api_integration",
    ]

    for test_dir in test_dirs:
        Path(test_dir).mkdir(parents=True, exist_ok=True)
        print(f"📁 Created test directory: {test_dir}")

    print("✅ Test environment setup completed successfully!")
    return True


def validate_api_connection():
    """Validate connection to paperless-ngx API."""
    print("🔌 Validating paperless-ngx API connection...")

    try:
        # Load configuration
        integration_env = Path("tests/env/paperless_integration.env")
        if integration_env.exists():
            config = load_config(str(integration_env))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
            )

        # Create client
        client = PaperlessClient(config)

        if not client.is_enabled():
            print("❌ Paperless client is not enabled or configured")
            print("💡 Check PAPERLESS_ENABLED, PAPERLESS_URL, and PAPERLESS_TOKEN")
            return False

        print(f"🔗 Testing connection to: {config.paperless_url}")

        # Test connection
        client.test_connection()
        print("✅ API connection successful!")

        # Test basic query
        print("📄 Testing document query...")
        result = client.query_documents(page_size=1)
        print(f"📊 Found {result['count']} total document(s) in system")
        print(f"📄 Retrieved {len(result['documents'])} document(s) for testing")

        # Display document info if available
        if result["documents"]:
            doc = result["documents"][0]
            print(
                f"📄 Sample document: ID={doc['id']}, Title='{doc.get('title', 'N/A')}'"
            )

        print("✅ API validation completed successfully!")
        return True

    except PaperlessUploadError as e:
        print(f"❌ API validation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during validation: {e}")
        return False


def create_test_data():
    """Create or prepare test data in paperless-ngx for testing."""
    print("📝 Creating test data in paperless-ngx...")

    try:
        # Load configuration
        integration_env = Path("tests/env/paperless_integration.env")
        if integration_env.exists():
            config = load_config(str(integration_env))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
            )

        client = PaperlessClient(config)

        if not client.is_enabled():
            print("❌ Paperless client not configured")
            return False

        # Create test tags
        print("🏷️  Creating test tags...")
        test_tags = ["test-integration", "bank-statement", "api-test"]

        for tag in test_tags:
            try:
                tag_ids = client._resolve_tags([tag])
                if tag_ids:
                    print(f"✅ Tag '{tag}' available (ID: {tag_ids[0]})")
                else:
                    print(f"⚠️  Tag '{tag}' could not be created/resolved")
            except Exception as e:
                print(f"⚠️  Tag '{tag}' error: {e}")

        # Create test correspondent
        print("🏦 Creating test correspondent...")
        try:
            correspondent_id = client._resolve_correspondent(
                "Test Bank API Integration"
            )
            if correspondent_id:
                print(
                    f"✅ Correspondent 'Test Bank API Integration' available (ID: {correspondent_id})"
                )
        except Exception as e:
            print(f"⚠️  Correspondent creation error: {e}")

        # Create test document type
        print("📄 Creating test document type...")
        try:
            doc_type_id = client._resolve_document_type("Test Statement Integration")
            if doc_type_id:
                print(
                    f"✅ Document type 'Test Statement Integration' available (ID: {doc_type_id})"
                )
        except Exception as e:
            print(f"⚠️  Document type creation error: {e}")

        print("✅ Test data creation completed!")
        return True

    except Exception as e:
        print(f"❌ Test data creation failed: {e}")
        return False


def run_api_tests(test_pattern: str = ""):
    """Run the API integration tests."""
    print("🧪 Running API integration tests...")

    # Set environment variable to enable API tests
    os.environ["PAPERLESS_API_INTEGRATION_TEST"] = "true"

    # Import pytest and run tests
    try:
        import subprocess

        # Build pytest command
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration/test_paperless_api.py",
            "-v",
            "-m",
            "api_integration",
            "--tb=short",
        ]

        if test_pattern:
            cmd.extend(["-k", test_pattern])

        print(f"🏃 Running: {' '.join(cmd)}")

        # Run tests
        result = subprocess.run(cmd, capture_output=False, text=True)

        if result.returncode == 0:
            print("✅ All API integration tests passed!")
            return True
        else:
            print(f"❌ Some tests failed (exit code: {result.returncode})")
            return False

    except ImportError:
        print("❌ pytest not available. Install with: pip install pytest")
        return False
    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False


def cleanup_test_data():
    """Clean up test data and temporary files."""
    print("🧹 Cleaning up test data...")

    # Clean up test directories
    test_dirs = [
        "test/output/api_integration",
        "test/processed/api_integration",
        "test/quarantine/api_integration",
        "test/error_reports/api_integration",
    ]

    import shutil

    for test_dir in test_dirs:
        dir_path = Path(test_dir)
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"🗑️  Removed: {test_dir}")
            except Exception as e:
                print(f"⚠️  Could not remove {test_dir}: {e}")

    print("✅ Cleanup completed!")


def display_help():
    """Display help information for API integration testing."""
    help_text = """
🔧 Paperless-ngx API Integration Testing Helper

This script helps you set up and run integration tests against a real paperless-ngx instance.

📋 Prerequisites:
1. A running paperless-ngx instance (local or remote)
2. Valid API credentials (URL and token)
3. Network access to the paperless-ngx server

🚀 Quick Start:
1. Configure tests/env/paperless_integration.env with real credentials
2. Run: python tests/manual/test_paperless_api_integration.py --setup
3. Run: python tests/manual/test_paperless_api_integration.py --validate
4. Run: python tests/manual/test_paperless_api_integration.py --run-tests

📁 Environment Configuration:
Edit tests/env/paperless_integration.env and set:
- PAPERLESS_URL=http://your-paperless-server:8000
- PAPERLESS_TOKEN=your-api-token-here
- PAPERLESS_API_INTEGRATION_TEST=true

🔐 Security Notes:
- Never commit real credentials to version control
- Use a test/development paperless-ngx instance
- API tests will create/modify tags, correspondents, and document types

🧪 Test Categories:
- Connection and authentication testing
- Document query and filtering
- Document download and validation
- Tag, correspondent, and document type management
- Error handling and edge cases
- Complete workflow testing

⚡ Individual Test Commands:
- Run connection tests: --run-tests -k "connection"
- Run query tests: --run-tests -k "query"
- Run download tests: --run-tests -k "download"
- Run workflow tests: --run-tests -k "workflow"
"""
    print(help_text)


def main():
    """Main entry point for the API integration test helper."""
    parser = argparse.ArgumentParser(
        description="Paperless-ngx API Integration Test Helper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--setup", action="store_true", help="Set up test environment and directories"
    )

    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate API connection and basic functionality",
    )

    parser.add_argument(
        "--create-data",
        action="store_true",
        help="Create test data (tags, correspondents, document types)",
    )

    parser.add_argument(
        "--run-tests", action="store_true", help="Run API integration tests"
    )

    parser.add_argument(
        "--cleanup", action="store_true", help="Clean up test data and temporary files"
    )

    parser.add_argument(
        "--test-pattern",
        type=str,
        default="",
        help="Run only tests matching this pattern",
    )

    parser.add_argument(
        "--help-detailed", action="store_true", help="Show detailed help information"
    )

    args = parser.parse_args()

    if args.help_detailed:
        display_help()
        return

    success = True

    if args.setup:
        success &= setup_test_environment()

    if args.validate:
        success &= validate_api_connection()

    if args.create_data:
        success &= create_test_data()

    if args.run_tests:
        success &= run_api_tests(args.test_pattern)

    if args.cleanup:
        cleanup_test_data()

    # If no specific action, show basic help
    if not any(
        [args.setup, args.validate, args.create_data, args.run_tests, args.cleanup]
    ):
        print("🔧 Paperless-ngx API Integration Test Helper")
        print("Use --help for options or --help-detailed for comprehensive guide")
        print(
            "\n🚀 Quick start: python {} --setup --validate --run-tests".format(
                sys.argv[0]
            )
        )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

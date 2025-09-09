#!/usr/bin/env python3
"""Quick test script for the Paperless end-to-end fixture.

This script provides a quick validation of the E2E fixture without running
the full test suite. It's useful for verifying setup and configuration.

Usage:
    LLM_PROVIDER=ollama \
    OLLAMA_BASE_URL=http://10.0.0.150:11434 \
    OLLAMA_MODEL=openhermes:latest \
    PAPERLESS_ENABLED=true \
    PAPERLESS_URL=https://paperless.lovegroove.io \
    PAPERLESS_TOKEN=your-token \
    PAPERLESS_API_INTEGRATION_TEST=true \
    python test_paperless_e2e_quick.py
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.bank_statement_separator.config import Config
from src.bank_statement_separator.utils.paperless_client import PaperlessClient
from tests.integration.test_paperless_end_to_end_fixture import PaperlessEndToEndFixture


def main():
    """Run quick E2E fixture validation."""
    print("🚀 Quick End-to-End Fixture Validation")
    print("=" * 40)

    # Check required environment
    if os.getenv("PAPERLESS_API_INTEGRATION_TEST", "").lower() not in ("true", "1"):
        print("❌ PAPERLESS_API_INTEGRATION_TEST must be set to 'true'")
        return 1

    required_vars = ["PAPERLESS_URL", "PAPERLESS_TOKEN"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        print(f"❌ Missing: {missing}")
        return 1

    try:
        # Initialize client
        print("🔧 Initializing Paperless client...")
        config = Config(
            openai_api_key="test-key-quick",
            paperless_enabled=True,
            paperless_url=os.getenv("PAPERLESS_URL"),
            paperless_token=os.getenv("PAPERLESS_TOKEN"),
        )

        client = PaperlessClient(config)
        if not client.is_enabled():
            print("❌ Client not enabled")
            return 1

        # Test connection
        print("🌐 Testing Paperless connection...")
        client.test_connection()
        print("✅ Connection successful")

        # Initialize fixture
        print("🏗️  Initializing E2E fixture...")
        fixture = PaperlessEndToEndFixture(client)

        # Quick cleanup test (dry run)
        print("🧹 Testing storage cleanup...")
        cleanup_result = fixture.cleanup_remote_storage()
        print(f"✅ Cleanup result: {cleanup_result['success']}")
        print(f"   Paths: {cleanup_result['paths_cleared']}")
        print(f"   Documents removed: {cleanup_result['documents_removed']}")

        # Generate test data (but don't upload)
        print("📄 Testing test data generation...")
        test_docs = fixture.generate_standardized_test_data()
        print(f"✅ Generated {len(test_docs)} test document specs")

        for i, doc_spec in enumerate(test_docs, 1):
            print(f"   {i}. {doc_spec.title}")
            print(f"      - {len(doc_spec.statements)} statements")
            print(f"      - {doc_spec.total_pages} pages")
            print(
                f"      - Expected: {len(doc_spec.expected_output_files)} output files"
            )

        # Test Ollama configuration (if available)
        ollama_url = os.getenv("OLLAMA_BASE_URL")
        ollama_model = os.getenv("OLLAMA_MODEL")
        if ollama_url and ollama_model:
            print("🤖 Ollama configuration detected:")
            print(f"   URL: {ollama_url}")
            print(f"   Model: {ollama_model}")

            # Test basic Ollama config creation
            Config(
                llm_provider="ollama",
                ollama_base_url=ollama_url,
                ollama_model=ollama_model,
                paperless_enabled=True,
                paperless_url=config.paperless_url,
                paperless_token=config.paperless_token,
            )
            print("✅ Ollama config created successfully")
        else:
            print("⚠️  Ollama not configured (optional for this quick test)")

        print("\n🎉 Quick validation completed successfully!")
        print("   Fixture is ready for full E2E testing")
        print("\nNext steps:")
        print("   1. Run full demo: python tests/manual/test_paperless_e2e_demo.py")
        print(
            "   2. Run pytest: pytest tests/integration/test_paperless_end_to_end_fixture.py -v -m e2e"
        )

        return 0

    except Exception as e:
        print(f"❌ Quick validation failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""Demo script for Paperless end-to-end testing fixture.

This script demonstrates how to use the comprehensive end-to-end test fixture
for validating the bank statement separator with Paperless integration.

Usage:
    python tests/manual/test_paperless_e2e_demo.py

Environment variables required:
    PAPERLESS_URL=https://your-paperless-instance.com
    PAPERLESS_TOKEN=your-api-token
    OLLAMA_BASE_URL=http://your-ollama:11434
    OLLAMA_MODEL=openhermes:latest
    PAPERLESS_API_INTEGRATION_TEST=true
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.bank_statement_separator.config import Config
from src.bank_statement_separator.utils.paperless_client import PaperlessClient
from tests.integration.test_paperless_end_to_end_fixture import PaperlessEndToEndFixture


def main():
    """Run the end-to-end test demonstration."""
    print("🚀 Paperless End-to-End Test Fixture Demo")
    print("=" * 50)

    # Check environment variables
    required_vars = ["PAPERLESS_URL", "PAPERLESS_TOKEN"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {missing_vars}")
        print("\nPlease set the following:")
        print("  PAPERLESS_URL=https://your-paperless-instance.com")
        print("  PAPERLESS_TOKEN=your-api-token")
        print("  OLLAMA_BASE_URL=http://your-ollama:11434 (optional)")
        print("  OLLAMA_MODEL=openhermes:latest (optional)")
        return 1

    print("📋 Environment Configuration:")
    print(f"  Paperless URL: {os.getenv('PAPERLESS_URL')}")
    print(f"  Ollama URL: {os.getenv('OLLAMA_BASE_URL', 'http://10.0.0.150:11434')}")
    print(f"  Ollama Model: {os.getenv('OLLAMA_MODEL', 'openhermes:latest')}")
    print()

    try:
        # Step 1: Initialize configuration and client
        print("🔧 Step 1: Initializing Paperless client...")
        config = Config(
            openai_api_key="test-key-demo",
            paperless_enabled=True,
            paperless_url=os.getenv("PAPERLESS_URL"),
            paperless_token=os.getenv("PAPERLESS_TOKEN"),
            paperless_max_documents=10,
            paperless_query_timeout=30,
        )

        client = PaperlessClient(config)
        if not client.is_enabled():
            print("❌ Paperless client is not properly configured")
            return 1

        # Test connection
        try:
            client.test_connection()
            print("✅ Paperless connection successful")
        except Exception as e:
            print(f"❌ Paperless connection failed: {e}")
            return 1

        print()

        # Step 2: Initialize fixture
        print("🏗️  Step 2: Initializing end-to-end test fixture...")
        fixture = PaperlessEndToEndFixture(client)

        # Step 3: Clean remote storage
        print("🧹 Step 3: Cleaning remote test storage...")
        cleanup_result = fixture.cleanup_remote_storage()
        if cleanup_result["success"]:
            print(f"✅ Cleaned {len(cleanup_result['paths_cleared'])} storage paths")
            print(f"   Removed {cleanup_result['documents_removed']} documents")
        else:
            print(f"⚠️  Cleanup had issues: {cleanup_result['errors']}")
        print()

        # Step 4: Generate and upload test documents
        print("📄 Step 4: Generating standardized test documents...")
        test_docs = fixture.generate_standardized_test_data()
        print(f"✅ Generated {len(test_docs)} test document specifications")

        for i, doc_spec in enumerate(test_docs, 1):
            print(f"   {i}. {doc_spec.title}")
            print(
                f"      - {len(doc_spec.statements)} statements, {doc_spec.total_pages} pages"
            )
            print(
                f"      - Expected outputs: {len(doc_spec.expected_output_files)} files"
            )
        print()

        print("📤 Step 5: Uploading test documents to Paperless...")
        upload_result = fixture.upload_test_documents(test_docs)

        if upload_result["success"]:
            print(
                f"✅ Successfully uploaded {len(upload_result['uploaded_documents'])} documents"
            )
            for doc_info in upload_result["uploaded_documents"]:
                print(f"   - {doc_info['title']}")
        else:
            print(f"❌ Upload failed: {upload_result['errors']}")
            return 1
        print()

        # Step 6: Configure Ollama for processing
        print("🤖 Step 6: Configuring Ollama for end-to-end processing...")
        ollama_config = Config(
            openai_api_key="test-key-demo-ollama",
            llm_provider="ollama",
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://10.0.0.150:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "openhermes:latest"),
            llm_temperature=0,
            llm_max_tokens=4000,
            paperless_enabled=True,
            paperless_url=os.getenv("PAPERLESS_URL"),
            paperless_token=os.getenv("PAPERLESS_TOKEN"),
            paperless_tags=["test:processed", "test:statement"],
            paperless_correspondent="Test Processing Bot",
            paperless_document_type="Processed Statement",
            paperless_storage_path="test-processed",
            default_output_dir="./test/output/demo_processing",
        )
        print(
            f"✅ Ollama configured: {ollama_config.ollama_base_url} ({ollama_config.ollama_model})"
        )
        print()

        # Step 7: Run end-to-end processing
        print("⚡ Step 7: Running end-to-end processing...")
        processing_results = fixture.run_end_to_end_processing(
            config=ollama_config, max_documents=2
        )

        if processing_results["success"]:
            print("✅ Processing completed successfully!")
            print(
                f"   Processed {len(processing_results['processed_documents'])} documents"
            )

            # Step 8: Display validation results
            print("\n📊 Step 8: Validation Results:")
            print("-" * 30)

            for processed_doc in processing_results["processed_documents"]:
                validation = processed_doc["validation"]

                print(f"\n📄 {processed_doc['title']}")
                print(
                    f"   Overall validation: {'✅ PASS' if validation['success'] else '❌ FAIL'}"
                )

                # File count validation
                file_count = validation["expected_vs_actual"].get("file_count", {})
                expected = file_count.get("expected", 0)
                actual = file_count.get("actual", 0)
                match_symbol = "✅" if file_count.get("match", False) else "❌"
                print(f"   File count: {match_symbol} {actual}/{expected}")

                # Individual file validations
                for file_val in validation["file_validations"]:
                    if file_val["exists"]:
                        size_kb = file_val.get("size_bytes", 0) // 1024
                        pdf_symbol = (
                            "✅" if file_val.get("valid_pdf_header", False) else "❌"
                        )
                        print(
                            f"   - {pdf_symbol} {file_val['actual_filename']} ({size_kb} KB)"
                        )
                    else:
                        print(f"   - ❌ Missing: {file_val['expected_filename']}")

                # Display any validation errors
                if validation["errors"]:
                    print(f"   Errors: {validation['errors']}")

            print("\n🎉 Demo completed successfully!")
            print(
                f"   Total documents processed: {len(processing_results['processed_documents'])}"
            )
            print(
                f"   Total validations run: {len(processing_results['validation_results'])}"
            )

        else:
            print(f"❌ Processing failed: {processing_results['errors']}")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Demo interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        try:
            if "fixture" in locals():
                cleanup_results = fixture.cleanup()
                print(f"✅ Cleanup completed: {len(cleanup_results)} items processed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Test error tagging with existing documents in Paperless.
This bypasses the async upload issue by using documents that are already processed.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.error_detector import ErrorDetector
from bank_statement_separator.utils.error_tagger import ErrorTagger
from bank_statement_separator.utils.paperless_client import PaperlessClient


def main():
    """Test error tagging with existing documents."""
    print("🧪 Testing Error Tagging with Existing Documents")
    print("=" * 50)

    # Enable error detection
    env_overrides = {
        "PAPERLESS_ENABLED": "true",
        "PAPERLESS_ERROR_DETECTION_ENABLED": "true",
        "PAPERLESS_ERROR_TAGS": "test:error-detection,test:automated-tagging",
        "PAPERLESS_ERROR_TAG_THRESHOLD": "0.5",
        "PAPERLESS_ERROR_SEVERITY_LEVELS": "medium,high,critical",
        "PAPERLESS_ERROR_BATCH_TAGGING": "false",
    }

    # Apply environment overrides
    original_env = {}
    for key, value in env_overrides.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        config = load_config()

        print(f"📋 Configuration:")
        print(f"  • Paperless URL: {config.paperless_url}")
        print(f"  • Error tags: {config.paperless_error_tags}")
        print()

        # Connect to Paperless
        client = PaperlessClient(config)

        if not client.is_enabled():
            print("❌ Paperless client not enabled")
            return

        # Get recent documents to test with
        print("🔍 Finding recent test documents...")

        try:
            import httpx

            with httpx.Client(timeout=30.0) as http_client:
                # Get recent documents created today with FINAL in title
                from datetime import datetime

                today = datetime.now().strftime("%Y-%m-%d")
                response = http_client.get(
                    f"{config.paperless_url.rstrip('/')}/api/documents/?title__icontains=FINAL&created__date__gte={today}&ordering=-created&page_size=5",
                    headers=client.headers,
                )
                response.raise_for_status()

                docs_data = response.json()
                documents = docs_data.get("results", [])

                if not documents:
                    print("❌ No recent FINAL test documents found created today")
                    print(
                        "   Run the final integration test first to create test documents."
                    )
                    return

                print(f"✅ Found {len(documents)} recent test documents:")

                test_documents = []
                for doc in documents[:2]:  # Use first 2 documents
                    doc_id = doc.get("id")
                    title = doc.get("title", "Unknown")
                    created = doc.get("created", "Unknown")

                    print(f"  • Document {doc_id}: {title} (created: {created[:10]})")
                    test_documents.append(
                        {"document_id": doc_id, "title": title, "success": True}
                    )

                print()

        except Exception as e:
            print(f"❌ Failed to fetch documents: {e}")
            return

        # Simulate error detection
        print("🔍 Simulating error detection...")

        error_workflow_state = {
            "current_step": "pdf_generation_error",
            "error_message": "PDF generation failed: memory limit exceeded",
            "generated_files": [],
            "total_statements_found": len(test_documents),
            "detected_boundaries": [
                {
                    "confidence": 0.3,
                    "start_page": 1,
                    "end_page": 8,
                    "reasoning": "LLM-based detection",
                },
                {
                    "confidence": 0.2,
                    "start_page": 9,
                    "end_page": 15,
                    "reasoning": "LLM-based detection",
                },
            ],
            "validation_results": {
                "is_valid": False,
                "checks": {
                    "page_count": {"status": "failed"},
                    "content_sampling": {"status": "failed"},
                },
            },
        }

        # Run error detection
        detector = ErrorDetector(config)
        detected_errors = detector.detect_errors(error_workflow_state)

        print(f"✅ Detected {len(detected_errors)} processing errors:")
        for i, error in enumerate(detected_errors, 1):
            print(
                f"  {i}. {error['type']} ({error['severity']}) - {error['description']}"
            )
        print()

        # Apply error tags to existing documents
        print("🏷️  Applying real error tags to existing documents...")

        tagger = ErrorTagger(config)

        # Create mock upload results using existing documents
        upload_results = {"uploads": test_documents}

        # Apply error tags
        result = tagger.apply_error_tags(detected_errors, upload_results)

        print(f"📊 Error Tagging Results:")
        print(f"  • Errors detected: {len(detected_errors)}")
        print(f"  • Documents to tag: {len(test_documents)}")
        print(f"  • Tagging attempted: {result.get('success', False)}")
        print(f"  • Documents tagged: {result.get('tagged_documents', 0)}")
        print(f"  • Skipped documents: {result.get('skipped_documents', 0)}")

        if result.get("details"):
            print(f"  • Tagging details:")
            for detail in result["details"]:
                doc_id = detail.get("document_id")
                tags_applied = detail.get("tags_applied", 0)
                tags = detail.get("tags", [])
                print(f"    - Document {doc_id}: {tags_applied} tags applied")
                print(f"      Tags: {', '.join(tags)}")

        if result.get("errors"):
            print(f"  • Tagging errors:")
            for error in result["errors"]:
                print(f"    - {error}")

        print()

        # Show success message
        if result.get("tagged_documents", 0) > 0:
            print("🎉 SUCCESS! Error tags have been applied to existing documents!")
            print()
            print("🔍 To verify in Paperless:")
            print(f"1. Go to {config.paperless_url}")
            print("2. Search for documents with the error tags:")
            for tag in config.paperless_error_tags:
                print(f"   • {tag}")
            print("3. Check the documents we just tagged:")
            for doc in test_documents:
                print(f"   • Document {doc['document_id']}: {doc['title']}")
        else:
            print("⚠️  No documents were tagged. Check the errors above for details.")

    finally:
        # Restore original environment variables
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


if __name__ == "__main__":
    main()

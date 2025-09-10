#!/usr/bin/env python3
"""
Final complete integration test:
1. Create documents in correct "test" storage path
2. Wait for processing and get document IDs
3. Apply error tags to the new documents
4. Verify everything worked correctly
"""

import os
import sys
import time
import tempfile
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.error_detector import ErrorDetector
from bank_statement_separator.utils.error_tagger import ErrorTagger
from bank_statement_separator.utils.paperless_client import PaperlessClient


def create_test_pdf(filename: str, content: str) -> bytes:
    """Create a simple test PDF document."""
    pdf_content = f"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document: {filename}) Tj
0 -20 Td
({content}) Tj
0 -20 Td
(Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000074 00000 n
0000000120 00000 n
0000000179 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
300
%%EOF"""
    return pdf_content.encode("utf-8")


def wait_for_document_processing(client, task_id, max_wait_time=30):
    """Wait for document processing to complete and return document ID."""
    print(f"    ⏳ Waiting for document processing (Task ID: {task_id})...")

    import httpx

    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        try:
            with httpx.Client(timeout=10.0) as http_client:
                response = http_client.get(
                    f"{client.base_url}/api/tasks/?task_id={task_id}",
                    headers=client.headers,
                )

                if response.status_code == 200:
                    tasks_data = response.json()
                    tasks = tasks_data.get("results", [])

                    for task in tasks:
                        if task.get("task_id") == task_id:
                            status = task.get("status")

                            if status == "SUCCESS":
                                # Task completed, get document ID from result
                                result = task.get("result", {})
                                if isinstance(result, dict):
                                    document_id = result.get("document_id")
                                    if document_id:
                                        print(
                                            f"    ✅ Document processing complete! Document ID: {document_id}"
                                        )
                                        return document_id
                            elif status == "FAILURE":
                                error_info = task.get("result", "Unknown error")
                                print(
                                    f"    ❌ Document processing failed: {error_info}"
                                )
                                return None

        except Exception as e:
            print(f"    ⚠️  Error checking task status: {e}")

        time.sleep(2)  # Wait 2 seconds before checking again

    print(f"    ⏰ Timeout waiting for document processing")
    return None


def main():
    """Run complete integration test with correct storage path."""
    print("🎯 FINAL COMPLETE INTEGRATION TEST")
    print("=" * 50)
    print("This test will:")
    print("1. Create documents in the correct 'test' storage path")
    print("2. Wait for processing and get real document IDs")
    print("3. Apply error tags to the processed documents")
    print("4. Verify everything worked correctly")
    print()

    # Configuration
    env_overrides = {
        "PAPERLESS_ENABLED": "true",
        "PAPERLESS_ERROR_DETECTION_ENABLED": "true",
        "PAPERLESS_ERROR_TAGS": "test:error-detection,test:automated-tagging",
        "PAPERLESS_ERROR_TAG_THRESHOLD": "0.5",
        "PAPERLESS_ERROR_SEVERITY_LEVELS": "medium,high,critical",
        "PAPERLESS_ERROR_BATCH_TAGGING": "false",
    }

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

        print("🌐 Connected to Paperless successfully")
        print()

        # Create test documents
        print("📄 Creating test documents in 'test' storage path...")

        timestamp = int(time.time())
        test_documents = [
            {
                "filename": f"FINAL_test_error_detection_{timestamp}_1.pdf",
                "title": f"FINAL Error Detection Test #1 - {timestamp}",
                "content": "Test document for final error detection validation",
            },
            {
                "filename": f"FINAL_test_error_detection_{timestamp}_2.pdf",
                "title": f"FINAL Error Detection Test #2 - {timestamp}",
                "content": "Second test document for complete integration test",
            },
        ]

        uploaded_documents = []

        for doc_info in test_documents:
            print(f"  📋 Creating {doc_info['filename']}...")

            # Create PDF
            pdf_content = create_test_pdf(doc_info["filename"], doc_info["content"])

            # Save to temp file
            temp_dir = Path(tempfile.mkdtemp())
            temp_file = temp_dir / doc_info["filename"]

            with open(temp_file, "wb") as f:
                f.write(pdf_content)

            try:
                # Upload with correct "test" storage path
                upload_result = client.upload_document(
                    file_path=temp_file,
                    title=doc_info["title"],
                    tags=["test:final-integration", "test:storage-path-test"],
                    correspondent="Test Bank Final",
                    document_type="Bank Statement",
                    storage_path="test",  # This should work now
                )

                if upload_result.get("success"):
                    task_id = upload_result.get("task_id")
                    doc_id = upload_result.get("document_id")

                    print(f"    ✅ Upload queued successfully")
                    print(f"    📋 Task ID: {task_id}")
                    print(f"    📋 Document ID: {doc_id}")

                    # If we got a task ID, wait for processing
                    if task_id and not doc_id:
                        final_doc_id = wait_for_document_processing(client, task_id)
                        if final_doc_id:
                            doc_id = final_doc_id

                    if doc_id:
                        uploaded_documents.append(
                            {
                                "document_id": doc_id,
                                "filename": doc_info["filename"],
                                "title": doc_info["title"],
                                "success": True,
                            }
                        )
                    else:
                        print(f"    ⚠️  Could not get final document ID")
                else:
                    print(
                        f"    ❌ Upload failed: {upload_result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                print(f"    ❌ Upload exception: {e}")
            finally:
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()
                temp_dir.rmdir()

        print(
            f"\n✅ Successfully processed {len(uploaded_documents)} documents with real IDs"
        )
        print()

        if not uploaded_documents:
            print("❌ No documents were successfully created with document IDs")
            print("   Cannot proceed with error tagging test")
            return

        # Show created documents
        print("📋 Created Documents:")
        for doc in uploaded_documents:
            print(f"  • Document {doc['document_id']}: {doc['title']}")
        print()

        # Simulate error detection
        print("🔍 Simulating processing errors...")

        error_workflow_state = {
            "current_step": "pdf_generation_error",
            "error_message": "FINAL TEST: PDF generation failed with memory issues",
            "generated_files": [],
            "total_statements_found": len(uploaded_documents),
            "detected_boundaries": [
                {
                    "confidence": 0.2,
                    "start_page": 1,
                    "end_page": 8,
                    "reasoning": "Low confidence LLM detection",
                }
            ],
            "validation_results": {
                "is_valid": False,
                "checks": {"page_count": {"status": "failed"}},
            },
        }

        detector = ErrorDetector(config)
        detected_errors = detector.detect_errors(error_workflow_state)

        print(f"✅ Detected {len(detected_errors)} processing errors:")
        for i, error in enumerate(detected_errors, 1):
            print(
                f"  {i}. {error['type']} ({error['severity']}) - {error['description']}"
            )
        print()

        # Apply error tags
        print("🏷️  Applying error tags to documents with real IDs...")

        tagger = ErrorTagger(config)
        upload_results = {"uploads": uploaded_documents}

        result = tagger.apply_error_tags(detected_errors, upload_results)

        print(f"📊 Error Tagging Results:")
        print(f"  • Errors detected: {len(detected_errors)}")
        print(f"  • Documents to tag: {len(uploaded_documents)}")
        print(f"  • Tagging success: {result.get('success', False)}")
        print(f"  • Documents tagged: {result.get('tagged_documents', 0)}")

        if result.get("details"):
            print(f"  • Tagging details:")
            for detail in result["details"]:
                doc_id = detail.get("document_id")
                tags_applied = detail.get("tags_applied", 0)
                tags = detail.get("tags", [])
                print(f"    - Document {doc_id}: {tags_applied} tags applied")
                print(
                    f"      Tags: {', '.join(tags[:3])}{'...' if len(tags) > 3 else ''}"
                )

        print()

        # Verify results
        if result.get("tagged_documents", 0) > 0:
            print("🎉 COMPLETE SUCCESS!")
            print()
            print("✅ FINAL INTEGRATION TEST RESULTS:")
            print(
                f"  • Documents created in 'test' storage path: {len(uploaded_documents)}"
            )
            print(f"  • Real document IDs obtained: {len(uploaded_documents)}")
            print(f"  • Processing errors detected: {len(detected_errors)}")
            print(
                f"  • Documents successfully tagged: {result.get('tagged_documents', 0)}"
            )
            print()
            print("🔍 Verification in Paperless:")
            print(f"1. Go to {config.paperless_url}")
            print("2. Check that these documents are in 'test' storage path:")
            for doc in uploaded_documents:
                print(f"   • Document {doc['document_id']}: {doc['title']}")
            print("3. Verify they have error tags applied:")
            for tag in config.paperless_error_tags:
                print(f"   • {tag}")
            print()
            print("🚀 ERROR DETECTION AND TAGGING SYSTEM IS FULLY OPERATIONAL!")
        else:
            print("⚠️  Error tagging did not complete successfully")
            if result.get("errors"):
                print("Errors:")
                for error in result["errors"]:
                    print(f"  • {error}")

    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


if __name__ == "__main__":
    main()

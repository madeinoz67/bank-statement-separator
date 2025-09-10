#!/usr/bin/env python3
"""
REAL Paperless integration test for error detection and tagging.
This test will actually create documents in your Paperless instance!

WARNING: This test will create real documents and tags in your Paperless instance.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime
from io import BytesIO

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.error_detector import ErrorDetector
from bank_statement_separator.utils.error_tagger import ErrorTagger
from bank_statement_separator.utils.paperless_client import PaperlessClient

# Try to import PDF generation libraries
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter

    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def create_test_pdf(filename: str, content: str) -> bytes:
    """Create a simple test PDF document."""
    if not REPORTLAB_AVAILABLE:
        # Fallback: create a minimal PDF manually
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
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
({content}) Tj
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
268
%%EOF"""
        return pdf_content.encode("utf-8")

    # Use ReportLab if available
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    # Add title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, 750, f"Test Document: {filename}")

    # Add content
    p.setFont("Helvetica", 12)
    y_position = 700
    lines = content.split("\n")

    for line in lines:
        p.drawString(100, y_position, line)
        y_position -= 20
        if y_position < 50:  # Start new page if needed
            p.showPage()
            p.setFont("Helvetica", 12)
            y_position = 750

    # Add timestamp
    p.setFont("Helvetica", 8)
    p.drawString(100, 30, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    p.save()
    return buffer.getvalue()


def main():
    """Run real Paperless integration test."""
    print("🚨 REAL PAPERLESS INTEGRATION TEST")
    print("=" * 50)
    print(
        "⚠️  WARNING: This test will create REAL documents in your Paperless instance!"
    )
    print("⚠️  Documents and tags will be created and may need manual cleanup.")
    print()

    # Auto-proceed for CLI environment
    print("✅ Proceeding with real integration test...")

    print()
    print("🚀 Starting real Paperless integration test...")

    # Enable error detection for this test
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
        # Load configuration
        config = load_config()

        print("📋 Configuration:")
        print(f"  • Paperless URL: {config.paperless_url}")
        print(
            f"  • Error detection enabled: {config.paperless_error_detection_enabled}"
        )
        print(f"  • Error tags: {config.paperless_error_tags}")
        print(f"  • Error severity levels: {config.paperless_error_severity_levels}")
        print()

        # Initialize Paperless client
        print("🌐 Connecting to Paperless...")
        client = PaperlessClient(config)

        if not client.is_enabled():
            print("❌ Paperless client is not enabled!")
            return

        print(f"  ✅ Connected to: {config.paperless_url}")
        print(f"  ✅ Using token: {config.paperless_token[:10]}...")
        print()

        # Create test documents
        print("📄 Creating test PDF documents...")

        test_documents = [
            {
                "filename": f"test_statement_error_detection_{int(time.time())}_1.pdf",
                "title": "Test Statement with Processing Errors #1",
                "content": """Test Bank Statement - Document 1

This is a test document created to validate error detection and tagging functionality.

Account: TEST-ACCOUNT-001
Period: January 2025
Status: PROCESSING ERROR SIMULATION

This document simulates processing errors for testing purposes:
- Low confidence boundary detection
- PDF generation issues
- Metadata extraction problems
- Validation failures

Generated for error detection testing.""",
            },
            {
                "filename": f"test_statement_error_detection_{int(time.time())}_2.pdf",
                "title": "Test Statement with Processing Errors #2",
                "content": """Test Bank Statement - Document 2

This is a second test document for error detection validation.

Account: TEST-ACCOUNT-002
Period: January 2025
Status: PROCESSING ERROR SIMULATION

This document also simulates various processing errors:
- Boundary detection confidence issues
- File output problems
- Validation check failures
- Metadata extraction low confidence

Created for automated error tagging testing.""",
            },
        ]

        uploaded_documents = []

        for doc_info in test_documents:
            print(f"  📋 Creating {doc_info['filename']}...")

            # Create PDF content
            pdf_content = create_test_pdf(doc_info["filename"], doc_info["content"])

            # Save PDF to temporary file
            temp_dir = Path(tempfile.mkdtemp())
            temp_file = temp_dir / doc_info["filename"]

            with open(temp_file, "wb") as f:
                f.write(pdf_content)

            # Upload to Paperless
            try:
                # Try upload with storage path first
                try:
                    upload_result = client.upload_document(
                        file_path=temp_file,
                        title=doc_info["title"],
                        tags=["test:original-upload", "test:bank-statement"],
                        correspondent="Test Bank",
                        document_type="Bank Statement",
                        storage_path="test",
                    )
                except Exception as storage_error:
                    if "403" in str(storage_error) or "Forbidden" in str(storage_error):
                        print(
                            f"    ⚠️  Storage path 'test' not accessible, trying without storage path..."
                        )
                        # Retry without storage path
                        upload_result = client.upload_document(
                            file_path=temp_file,
                            title=doc_info["title"],
                            tags=["test:original-upload", "test:bank-statement"],
                            correspondent="Test Bank",
                            document_type="Bank Statement",
                        )
                    else:
                        raise storage_error

                if upload_result.get("success"):
                    doc_id = upload_result.get("document_id")
                    print(f"    ✅ Uploaded successfully - Document ID: {doc_id}")
                    uploaded_documents.append(
                        {
                            "document_id": doc_id,
                            "filename": doc_info["filename"],
                            "success": True,
                        }
                    )
                else:
                    print(
                        f"    ❌ Upload failed: {upload_result.get('error', 'Unknown error')}"
                    )

            except Exception as e:
                print(f"    ❌ Upload exception: {e}")
            finally:
                # Clean up temporary file
                if temp_file.exists():
                    temp_file.unlink()
                temp_dir.rmdir()

        print(f"  ✅ Successfully uploaded {len(uploaded_documents)} test documents")
        print()

        if not uploaded_documents:
            print("❌ No documents were uploaded successfully. Cannot continue test.")
            return

        # Wait a moment for Paperless to process the uploads
        print("⏱️  Waiting for Paperless to process uploads...")
        time.sleep(5)
        print()

        # Simulate error detection
        print("🔍 Simulating error detection...")

        # Create a workflow state with multiple types of errors
        error_workflow_state = {
            "current_step": "pdf_generation_error",
            "error_message": "PDF generation failed: insufficient memory and corrupted input",
            "generated_files": [],
            "total_statements_found": len(uploaded_documents),
            "detected_boundaries": [
                {
                    "confidence": 0.25,
                    "start_page": 1,
                    "end_page": 8,
                    "reasoning": "LLM-based detection with low confidence",
                },
                {
                    "confidence": 0.15,
                    "start_page": 9,
                    "end_page": 15,
                    "reasoning": "Fallback page-based segmentation",
                },
            ],
            "extracted_metadata": [
                {"account_number": "ACCT001", "confidence": 0.3},
                {"account_number": "ACCT002", "confidence": 0.2},
            ],
            "validation_results": {
                "is_valid": False,
                "checks": {
                    "page_count": {"status": "failed"},
                    "content_sampling": {"status": "failed"},
                    "metadata_extraction": {"status": "failed"},
                },
            },
            "skipped_fragments": 3,
            "skipped_pages": 12,
        }

        # Run error detection
        detector = ErrorDetector(config)
        detected_errors = detector.detect_errors(error_workflow_state)

        print(f"  ✅ Detected {len(detected_errors)} processing errors:")
        for i, error in enumerate(detected_errors, 1):
            print(
                f"    {i}. {error['type']} ({error['severity']}) - {error['description']}"
            )

        print()

        # Apply error tags to uploaded documents
        print("🏷️  Applying real error tags to uploaded documents...")

        tagger = ErrorTagger(config)

        # Generate error tags
        error_tags = tagger._generate_error_tags(detected_errors)
        print(f"  📋 Generated error tags: {error_tags}")

        # Create error summary
        error_summary = tagger.create_error_summary(detected_errors)
        print(f"  📋 Error summary: {error_summary}")

        # Apply tags to each document
        tagging_results = []

        for doc in uploaded_documents:
            doc_id = doc["document_id"]
            filename = doc["filename"]

            print(f"  📋 Applying error tags to Document {doc_id} ({filename})...")

            try:
                # Wait a moment between API calls to be respectful
                time.sleep(2)

                tag_result = client.apply_tags_to_document(
                    document_id=doc_id,
                    tags=error_tags,
                    wait_time=config.paperless_tag_wait_time,
                )

                if tag_result.get("success"):
                    tags_applied = tag_result.get("tags_applied", 0)
                    print(f"    ✅ Successfully applied {tags_applied} error tags")
                    tagging_results.append(
                        {
                            "document_id": doc_id,
                            "filename": filename,
                            "success": True,
                            "tags_applied": tags_applied,
                        }
                    )
                else:
                    error_msg = tag_result.get("error", "Unknown tagging error")
                    print(f"    ❌ Tagging failed: {error_msg}")
                    tagging_results.append(
                        {
                            "document_id": doc_id,
                            "filename": filename,
                            "success": False,
                            "error": error_msg,
                        }
                    )

            except Exception as e:
                print(f"    ❌ Exception applying tags: {e}")
                tagging_results.append(
                    {
                        "document_id": doc_id,
                        "filename": filename,
                        "success": False,
                        "error": str(e),
                    }
                )

        print()

        # Summary of results
        print("📊 REAL INTEGRATION TEST RESULTS:")
        print("=" * 40)

        successful_uploads = len([d for d in uploaded_documents if d.get("success")])
        successful_taggings = len([r for r in tagging_results if r.get("success")])

        print(f"✅ Documents uploaded: {successful_uploads}/{len(test_documents)}")
        print(f"✅ Errors detected: {len(detected_errors)}")
        print(f"✅ Documents tagged: {successful_taggings}/{len(uploaded_documents)}")
        print(f"✅ Error tags applied: {error_tags}")

        print()
        print("📋 Document Details:")
        for result in tagging_results:
            status = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
            doc_id = result["document_id"]
            filename = result["filename"]

            if result.get("success"):
                tags_applied = result.get("tags_applied", 0)
                print(f"  {status} - Document {doc_id}")
                print(f"    • File: {filename}")
                print(f"    • Tags applied: {tags_applied}")
            else:
                error = result.get("error", "Unknown error")
                print(f"  {status} - Document {doc_id}")
                print(f"    • File: {filename}")
                print(f"    • Error: {error}")

        print()
        print("🎉 REAL INTEGRATION TEST COMPLETED!")
        print()
        print("📋 What was created in your Paperless instance:")
        print(f"  • {successful_uploads} test PDF documents")
        print(f"  • Error detection tags: {error_tags}")
        print(f"  • Documents with error tags: {successful_taggings}")
        print()
        print("🔍 To view results:")
        print(f"  1. Go to {config.paperless_url}")
        print(f"  2. Search for documents with tags: {', '.join(error_tags)}")
        print(
            f"  3. Look for documents created around {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        print()
        print("🧹 Cleanup (optional):")
        print("  • You can delete the test documents from Paperless web interface")
        print("  • Search for 'test:error-detection' tag to find them easily")

    finally:
        # Restore original environment variables
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


if __name__ == "__main__":
    main()

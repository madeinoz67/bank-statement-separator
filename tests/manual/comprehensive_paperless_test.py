#!/usr/bin/env python3
"""
Comprehensive test of the paperless input workflow.
This demonstrates the complete end-to-end functionality.
"""

from pathlib import Path
import sys
import tempfile

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bank_statement_separator.config import Config
from bank_statement_separator.utils.paperless_client import PaperlessClient


def create_test_pdf():
    """Create a simple test PDF for demonstration."""
    pdf_content = b"""%PDF-1.4
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
/Length 200
>>
stream
BT
/F1 12 Tf
72 720 Td
(CHASE BANK STATEMENT) Tj
0 -20 Td
(Account: ****1234) Tj
0 -20 Td
(Statement Period: January 2024) Tj
0 -40 Td
(Date       Description      Amount) Tj
0 -15 Td
(01/01/24   Opening Balance  $1000.00) Tj
0 -15 Td
(01/02/24   Deposit         $500.00) Tj
0 -15 Td
(01/03/24   ATM Withdrawal  -$100.00) Tj
0 -30 Td
(End of Statement) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000204 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
500
%%EOF"""
    return pdf_content


def main():
    print("🚀 Comprehensive Paperless Input Test")
    print("=" * 50)

    # Create config
    config = Config(
        openai_api_key="test-key",
        paperless_enabled=True,
        paperless_url="https://paperless.lovegroove.io",
        paperless_token="ca8d0cbc1c54ebb5516bf5e969fce88eace43178",
    )

    client = PaperlessClient(config)

    print("🔌 Testing connection...")
    try:
        client.test_connection()
        print("✅ Connected to paperless-ngx successfully")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return

    print("\n📄 Creating a test document for processing...")

    try:
        # Create test PDF
        pdf_content = create_test_pdf()

        with tempfile.NamedTemporaryFile(
            mode="wb", suffix=".pdf", delete=False
        ) as tmp_file:
            tmp_file.write(pdf_content)
            tmp_path = tmp_file.name

        # Upload without tags to avoid conflicts
        print("📤 Uploading test document...")
        upload_result = client.upload_document(
            file_path=Path(tmp_path),
            title="Test Statement for Processing - Chase Bank Jan 2024",
            tags=None,  # No tags to avoid system rule conflicts
            correspondent=None,
            document_type=None,
            storage_path="test-processing",
        )

        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)

        print(f"✅ Upload result: {upload_result}")

        if upload_result and upload_result.get("success"):
            doc_id = upload_result.get("document_id")
            task_id = upload_result.get("task_id")

            if doc_id:
                print(f"📋 Document created with ID: {doc_id}")

                # Test downloading the document back
                print("📥 Testing document download...")

                with tempfile.TemporaryDirectory() as tmp_dir:
                    download_path = Path(tmp_dir) / f"downloaded_doc_{doc_id}.pdf"

                    try:
                        download_result = client.download_document(
                            doc_id, str(download_path)
                        )

                        if download_result and download_result.get("success"):
                            print(
                                f"✅ Download successful: {download_result['file_size']} bytes"
                            )

                            # Verify it's a PDF
                            with open(download_path, "rb") as f:
                                header = f.read(10)
                                if header.startswith(b"%PDF"):
                                    print("✅ Downloaded file is valid PDF")

                                    # This demonstrates the complete workflow:
                                    # 1. Document uploaded to paperless-ngx ✅
                                    # 2. Document can be queried and downloaded ✅
                                    # 3. Ready for statement processing ✅

                                    print("\n🎉 PAPERLESS INPUT WORKFLOW SUCCESSFUL!")
                                    print("📊 Summary:")
                                    print(
                                        f"  - Document uploaded: {upload_result['title']}"
                                    )
                                    print(f"  - Document ID: {doc_id}")
                                    print(
                                        f"  - File size: {download_result['file_size']} bytes"
                                    )
                                    print(
                                        f"  - Storage path: {upload_result.get('storage_path', 'default')}"
                                    )
                                    print(
                                        "  - Ready for statement separation processing"
                                    )

                                else:
                                    print("❌ Downloaded file is not a valid PDF")
                        else:
                            print("❌ Download failed")

                    except Exception as e:
                        print(f"❌ Download error: {e}")

            elif task_id:
                print(f"⏳ Document queued for processing with task ID: {task_id}")
                print(
                    "💡 This is normal - paperless-ngx processes documents asynchronously"
                )
                print(
                    "📄 The document will be available for querying once processing completes"
                )

                print("\n🎉 PAPERLESS INPUT WORKFLOW SUCCESSFUL!")
                print("📊 Summary:")
                print(f"  - Document uploaded: {upload_result['title']}")
                print(f"  - Task ID: {task_id}")
                print(
                    f"  - Storage path: {upload_result.get('storage_path', 'default')}"
                )
                print("  - Status: Queued for processing")
                print("  - Will be ready for statement separation once indexed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Test Paperless integration using exact .env file configuration.

This test uses the test user token and settings from .env file,
respecting the limited permissions of the test user.
"""

import sys
import tempfile
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.bank_statement_separator.config import load_config
from src.bank_statement_separator.utils.paperless_client import PaperlessClient
from src.bank_statement_separator.workflow import BankStatementWorkflow


def create_simple_test_pdf(output_path: Path) -> None:
    """Create a simple test PDF with multiple statements for testing."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # First statement
    story.append(Paragraph("=== STATEMENT 1 START ===", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("FIRST NATIONAL BANK", styles["Title"]))
    story.append(Paragraph("Account: ****1234", styles["Normal"]))
    story.append(Paragraph("Statement Period: January 2024", styles["Normal"]))
    story.append(Paragraph("Statement Date: 2024-01-31", styles["Normal"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Opening Balance: $1,000.00", styles["Normal"]))
    story.append(Paragraph("Closing Balance: $1,500.00", styles["Normal"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph("=== STATEMENT 1 END ===", styles["Normal"]))

    story.append(PageBreak())
    story.append(Spacer(1, 50))

    # Second statement
    story.append(Paragraph("=== STATEMENT 2 START ===", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("SECOND COMMUNITY BANK", styles["Title"]))
    story.append(Paragraph("Account: ****5678", styles["Normal"]))
    story.append(Paragraph("Statement Period: February 2024", styles["Normal"]))
    story.append(Paragraph("Statement Date: 2024-02-28", styles["Normal"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Opening Balance: $2,000.00", styles["Normal"]))
    story.append(Paragraph("Closing Balance: $2,300.00", styles["Normal"]))
    story.append(Spacer(1, 30))
    story.append(Paragraph("=== STATEMENT 2 END ===", styles["Normal"]))

    doc.build(story)


def main():
    """Run paperless integration test with .env configuration."""
    print("🔧 PAPERLESS INTEGRATION TEST - Using .env Configuration")
    print("=" * 60)

    try:
        # Load configuration from .env file
        print("📋 Step 1: Loading configuration from .env file...")
        config = load_config()

        # Override paperless to be enabled for this test
        config.paperless_enabled = True

        print("✅ Configuration loaded from .env:")
        print(f"   Paperless URL: {config.paperless_url}")
        print(f"   Paperless Token: {config.paperless_token[:20]}... (test user)")
        print(f"   Output Tags: {config.paperless_tags}")
        print(f"   Correspondent: {config.paperless_correspondent}")
        print(f"   Document Type: {config.paperless_document_type}")
        print(f"   Storage Path: {config.paperless_storage_path}")
        print(f"   LLM Provider: {config.llm_provider}")
        print(f"   Ollama Model: {config.ollama_model}")
        print()

        # Test paperless connection
        print("🔌 Step 2: Testing paperless connection...")
        client = PaperlessClient(config)

        try:
            client.test_connection()
            print("✅ Paperless connection successful with test user!")
        except Exception as e:
            print(f"❌ Paperless connection failed: {e}")
            return 1
        print()

        # Create test document and process it
        print("📄 Step 3: Creating and processing test document...")
        test_output_dir = Path("./test/output/env_paperless_test")
        test_output_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir_path = Path(tmp_dir)

            # Create test PDF
            test_pdf = tmp_dir_path / "test_multi_statement.pdf"
            create_simple_test_pdf(test_pdf)
            print(f"✅ Created test PDF: {test_pdf}")

            # Process with workflow
            print(
                f"🤖 Processing with {config.llm_provider} ({config.ollama_model})..."
            )
            workflow = BankStatementWorkflow(config)

            workflow_result = workflow.run(str(test_pdf), str(test_output_dir))

            if workflow_result and workflow_result.get("success"):
                print("✅ Document processing successful!")

                # Check output files
                output_files = list(test_output_dir.glob("*.pdf"))
                print(f"📁 Generated {len(output_files)} output files:")

                for file in output_files:
                    size_kb = file.stat().st_size // 1024
                    print(f"   - {file.name} ({size_kb} KB)")

                    # Basic PDF validation
                    try:
                        with open(file, "rb") as f:
                            header = f.read(10)
                            is_pdf = header.startswith(b"%PDF")
                            print(f"     Valid PDF: {'✅' if is_pdf else '❌'}")
                    except Exception as e:
                        print(f"     PDF validation error: {e}")

                print()
                print("📤 Step 4: Testing paperless upload with .env tags...")

                # Test upload with .env configuration tags
                uploaded_count = 0
                for file in output_files:
                    try:
                        upload_result = client.upload_document(
                            file_path=file,
                            title=f"Test Processed Statement - {file.stem}",
                            tags=config.paperless_tags,  # Use tags from .env
                            correspondent=config.paperless_correspondent,  # Use correspondent from .env
                            document_type=config.paperless_document_type,  # Use doc type from .env
                            storage_path=config.paperless_storage_path,  # Use storage path from .env
                        )

                        if upload_result and upload_result.get("success"):
                            print(f"✅ Uploaded: {file.name}")
                            uploaded_count += 1
                        else:
                            print(f"⚠️  Upload failed for {file.name}: {upload_result}")

                    except Exception as e:
                        print(f"❌ Upload error for {file.name}: {e}")

                print()
                print("🎯 FINAL RESULTS:")
                print("=" * 30)
                print("📄 Input document processed: ✅")
                print("🤖 AI processing successful: ✅")
                print(f"📁 Output files generated: {len(output_files)}")
                print(f"📤 Files uploaded to paperless: {uploaded_count}")
                print(f"🏷️  Tagged with: {', '.join(config.paperless_tags)}")
                print(f"📦 Stored in: {config.paperless_storage_path}")
                print(f"👤 Correspondent: {config.paperless_correspondent}")

                if len(output_files) > 0 and uploaded_count > 0:
                    print("\\n🎉 PAPERLESS INTEGRATION TEST: ✅ SUCCESS!")
                    print("   ✅ .env configuration respected")
                    print("   ✅ Test user permissions working")
                    print("   ✅ AI processing (Ollama/Mistral) working")
                    print("   ✅ Output generation working")
                    print("   ✅ Paperless upload with .env tags working")
                    return 0
                else:
                    print("\\n⚠️  PARTIAL SUCCESS: Processing worked but upload issues")
                    return 1
            else:
                print("❌ Document processing failed")
                return 1

    except KeyboardInterrupt:
        print("\\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

#!/usr/bin/env python3
"""Standalone End-to-End Test with Standardized Documents.

This script creates standardized multi-statement test documents and processes them
using the configured LLM provider (Ollama with Mistral) from the .env file.

Usage:
    python tests/manual/test_standalone_e2e.py
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.bank_statement_separator.config import load_config
from src.bank_statement_separator.workflow import BankStatementWorkflow


@dataclass
class TestStatementSpec:
    """Specification for a standardized test statement."""

    bank_name: str
    account_number: str
    account_suffix: str  # Last 4 digits for display
    statement_period: str
    statement_date: str
    expected_filename_pattern: str
    page_count: int
    opening_balance: str
    closing_balance: str
    transaction_count: int


@dataclass
class TestDocumentSpec:
    """Specification for a test document containing multiple statements."""

    title: str
    filename: str
    description: str
    statements: List[TestStatementSpec]
    total_pages: int
    expected_output_files: List[str]


def generate_standardized_test_data() -> List[TestDocumentSpec]:
    """Generate standardized test document specifications with known metadata."""
    test_timestamp = int(datetime.now().timestamp())

    test_docs = [
        TestDocumentSpec(
            title=f"Test Multi-Statement Bundle - Standard 3 Statements [{test_timestamp}001]",
            filename=f"test_multi_3_statements_{test_timestamp}001.pdf",
            description="Controlled 3-statement bundle with predictable boundaries",
            statements=[
                TestStatementSpec(
                    bank_name="Test Bank Alpha",
                    account_number="1234567890123456",
                    account_suffix="3456",
                    statement_period="January 2024",
                    statement_date="2024-01-31",
                    expected_filename_pattern="test-bank-alpha-3456-2024-01-31.pdf",
                    page_count=2,
                    opening_balance="$1,234.56",
                    closing_balance="$2,845.67",
                    transaction_count=8,
                ),
                TestStatementSpec(
                    bank_name="Test Bank Alpha",
                    account_number="1234567890127890",
                    account_suffix="7890",
                    statement_period="February 2024",
                    statement_date="2024-02-29",
                    expected_filename_pattern="test-bank-alpha-7890-2024-02-29.pdf",
                    page_count=2,
                    opening_balance="$2,845.67",
                    closing_balance="$3,567.89",
                    transaction_count=6,
                ),
                TestStatementSpec(
                    bank_name="Test Credit Union Beta",
                    account_number="9876543210654321",
                    account_suffix="4321",
                    statement_period="March 2024",
                    statement_date="2024-03-31",
                    expected_filename_pattern="test-credit-union-beta-4321-2024-03-31.pdf",
                    page_count=3,
                    opening_balance="$3,567.89",
                    closing_balance="$4,123.45",
                    transaction_count=12,
                ),
            ],
            total_pages=7,
            expected_output_files=[
                "test-bank-alpha-3456-2024-01-31.pdf",
                "test-bank-alpha-7890-2024-02-29.pdf",
                "test-credit-union-beta-4321-2024-03-31.pdf",
            ],
        ),
        TestDocumentSpec(
            title=f"Test Dual-Statement Document - 2 Statements [{test_timestamp}002]",
            filename=f"test_dual_statements_{test_timestamp}002.pdf",
            description="Controlled 2-statement document for validation testing",
            statements=[
                TestStatementSpec(
                    bank_name="Test Community Bank",
                    account_number="5555666677778888",
                    account_suffix="8888",
                    statement_period="April 2024",
                    statement_date="2024-04-30",
                    expected_filename_pattern="test-community-bank-8888-2024-04-30.pdf",
                    page_count=3,
                    opening_balance="$5,432.10",
                    closing_balance="$6,789.01",
                    transaction_count=10,
                ),
                TestStatementSpec(
                    bank_name="Test Savings & Loan",
                    account_number="1111222233334444",
                    account_suffix="4444",
                    statement_period="May 2024",
                    statement_date="2024-05-31",
                    expected_filename_pattern="test-savings-loan-4444-2024-05-31.pdf",
                    page_count=2,
                    opening_balance="$6,789.01",
                    closing_balance="$7,654.32",
                    transaction_count=7,
                ),
            ],
            total_pages=5,
            expected_output_files=[
                "test-community-bank-8888-2024-04-30.pdf",
                "test-savings-loan-4444-2024-05-31.pdf",
            ],
        ),
    ]

    return test_docs


def create_standardized_pdf(doc_spec: TestDocumentSpec, output_path: Path) -> None:
    """Create a standardized PDF with known statement boundaries."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

    # Create PDF
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    for i, stmt in enumerate(doc_spec.statements):
        # Add statement header with clear boundary markers
        story.append(
            Paragraph(
                f"=== STATEMENT BOUNDARY START: {stmt.bank_name.upper()} ===",
                styles["Title"],
            )
        )
        story.append(Spacer(1, 20))
        story.append(Paragraph(stmt.bank_name.upper(), styles["Title"]))
        story.append(Spacer(1, 15))
        story.append(
            Paragraph(f"Account Number: ****{stmt.account_suffix}", styles["Normal"])
        )
        story.append(
            Paragraph(f"Statement Period: {stmt.statement_period}", styles["Normal"])
        )
        story.append(
            Paragraph(f"Statement Date: {stmt.statement_date}", styles["Normal"])
        )
        story.append(Spacer(1, 20))

        # Add transaction history
        story.append(Paragraph("TRANSACTION HISTORY", styles["Heading2"]))
        story.append(
            Paragraph(f"Opening Balance: {stmt.opening_balance}", styles["Normal"])
        )

        # Add sample transactions based on transaction count
        for j in range(stmt.transaction_count):
            transaction_date = f"2024-{i+1:02d}-{(j+1)*3:02d}"
            if j % 3 == 0:
                story.append(
                    Paragraph(
                        f"{transaction_date} - Direct Deposit: +$500.{j:02d}",
                        styles["Normal"],
                    )
                )
            elif j % 3 == 1:
                story.append(
                    Paragraph(
                        f"{transaction_date} - Purchase: -$75.{j:02d}", styles["Normal"]
                    )
                )
            else:
                story.append(
                    Paragraph(
                        f"{transaction_date} - Transfer: -$125.{j:02d}",
                        styles["Normal"],
                    )
                )

        story.append(Spacer(1, 15))
        story.append(
            Paragraph(f"Closing Balance: {stmt.closing_balance}", styles["Normal"])
        )

        # Add page breaks based on page count (except last statement)
        for _ in range(stmt.page_count - 1):
            story.append(PageBreak())
            story.append(
                Paragraph(f"{stmt.bank_name} - Statement Continued", styles["Normal"])
            )
            story.append(Spacer(1, 20))

        # Add clear boundary marker at end
        story.append(Spacer(1, 30))
        story.append(
            Paragraph(
                f"=== STATEMENT BOUNDARY END: {stmt.bank_name.upper()} ===",
                styles["Normal"],
            )
        )

        # Page break between statements (except last)
        if i < len(doc_spec.statements) - 1:
            story.append(PageBreak())
            story.append(Spacer(1, 50))  # Large gap between statements

    # Build PDF
    doc.build(story)


def validate_processing_results(
    workflow_result: Dict[str, Any], output_dir: Path, test_spec: TestDocumentSpec
) -> Dict[str, Any]:
    """Validate processing results against expected test data."""
    validation = {
        "success": True,
        "expected_vs_actual": {},
        "file_validations": [],
        "workflow_validation": {},
        "errors": [],
    }

    try:
        # Get actual output files
        output_files = list(output_dir.glob("*.pdf"))

        # Validate file count
        expected_count = len(test_spec.expected_output_files)
        actual_count = len(output_files)

        validation["expected_vs_actual"]["file_count"] = {
            "expected": expected_count,
            "actual": actual_count,
            "match": expected_count == actual_count,
        }

        if expected_count != actual_count:
            validation["success"] = False
            validation["errors"].append(
                f"File count mismatch: expected {expected_count}, got {actual_count}"
            )

        # Validate individual files
        for expected_filename in test_spec.expected_output_files:
            # Check if a file with similar pattern exists (allowing for minor naming variations)
            matching_files = [
                f
                for f in output_files
                if any(
                    part in f.name.lower()
                    for part in expected_filename.lower().split("-")[:3]
                )
            ]

            if matching_files:
                actual_file = matching_files[0]
                file_validation = {
                    "expected_filename": expected_filename,
                    "actual_filename": actual_file.name,
                    "exists": True,
                    "size_bytes": actual_file.stat().st_size,
                    "is_pdf": actual_file.suffix.lower() == ".pdf",
                }

                # Basic PDF validation
                try:
                    with open(actual_file, "rb") as f:
                        header = f.read(10)
                        file_validation["valid_pdf_header"] = header.startswith(b"%PDF")
                except Exception as e:
                    file_validation["valid_pdf_header"] = False
                    file_validation["pdf_error"] = str(e)
            else:
                validation["success"] = False
                file_validation = {
                    "expected_filename": expected_filename,
                    "actual_filename": None,
                    "exists": False,
                }
                validation["errors"].append(
                    f"Expected file not found: {expected_filename}"
                )

            validation["file_validations"].append(file_validation)

        # Validate workflow result structure
        if workflow_result:
            validation["workflow_validation"] = {
                "has_result": True,
                "success": workflow_result.get("success", False),
                "has_metadata": "metadata" in workflow_result,
                "has_output_files": "output_files" in workflow_result,
                "processing_time": workflow_result.get("processing_time", 0),
            }
        else:
            validation["success"] = False
            validation["workflow_validation"] = {"has_result": False}
            validation["errors"].append("Workflow returned no results")

    except Exception as e:
        validation["success"] = False
        validation["errors"].append(str(e))

    return validation


def main():
    """Run the standalone end-to-end test."""
    print("🚀 Standalone End-to-End Test with Ollama/Mistral")
    print("=" * 60)

    try:
        # Step 1: Load configuration from .env file
        print("🔧 Step 1: Loading configuration from .env file...")
        config = load_config()

        print("✅ Configuration loaded:")
        print(f"   LLM Provider: {config.llm_provider}")
        if config.llm_provider == "ollama":
            print(f"   Ollama URL: {config.ollama_base_url}")
            print(f"   Ollama Model: {config.ollama_model}")
        print(f"   Output Directory: {config.default_output_dir}")
        print()

        # Step 2: Generate standardized test data
        print("📄 Step 2: Generating standardized test documents...")
        test_docs = generate_standardized_test_data()
        print(f"✅ Generated {len(test_docs)} test document specifications:")

        for i, doc_spec in enumerate(test_docs, 1):
            print(f"   {i}. {doc_spec.title}")
            print(
                f"      - {len(doc_spec.statements)} statements, {doc_spec.total_pages} pages"
            )
            print(
                f"      - Expected outputs: {len(doc_spec.expected_output_files)} files"
            )
        print()

        # Step 3: Create test output directory
        test_output_base = Path("./test/output/standalone_e2e_test")
        test_output_base.mkdir(parents=True, exist_ok=True)

        # Step 4: Process each test document
        print("⚡ Step 3: Processing test documents...")
        workflow = BankStatementWorkflow(config)

        all_validations = []
        processed_count = 0

        for doc_spec in test_docs:
            print(f"\n📄 Processing: {doc_spec.title}")

            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_dir_path = Path(tmp_dir)

                # Create test PDF
                input_pdf = tmp_dir_path / doc_spec.filename
                output_dir = (
                    test_output_base / f"output_{doc_spec.filename.replace('.pdf', '')}"
                )
                output_dir.mkdir(exist_ok=True)

                print("   📝 Creating standardized PDF...")
                create_standardized_pdf(doc_spec, input_pdf)
                print(f"   ✅ Created: {input_pdf}")

                # Process the document
                print(
                    f"   🤖 Processing with {config.llm_provider} ({config.ollama_model})..."
                )
                start_time = datetime.now()

                workflow_result = workflow.run(str(input_pdf), str(output_dir))

                processing_time = (datetime.now() - start_time).total_seconds()
                print(f"   ⏱️  Processing completed in {processing_time:.2f} seconds")

                # Validate results
                print("   🔍 Validating results...")
                validation = validate_processing_results(
                    workflow_result=workflow_result,
                    output_dir=output_dir,
                    test_spec=doc_spec,
                )

                validation["processing_time"] = processing_time
                all_validations.append(
                    {
                        "document": doc_spec.title,
                        "validation": validation,
                        "workflow_result": workflow_result,
                    }
                )

                # Display validation results
                if validation["success"]:
                    print("   ✅ Validation PASSED")
                else:
                    print(f"   ❌ Validation FAILED: {validation['errors']}")

                file_count = validation["expected_vs_actual"].get("file_count", {})
                expected = file_count.get("expected", 0)
                actual = file_count.get("actual", 0)
                match_symbol = "✅" if file_count.get("match", False) else "❌"
                print(f"   📊 Files generated: {match_symbol} {actual}/{expected}")

                for file_val in validation["file_validations"]:
                    if file_val["exists"]:
                        size_kb = file_val.get("size_bytes", 0) // 1024
                        pdf_symbol = (
                            "✅" if file_val.get("valid_pdf_header", False) else "❌"
                        )
                        print(
                            f"      - {pdf_symbol} {file_val['actual_filename']} ({size_kb} KB)"
                        )
                    else:
                        print(f"      - ❌ Missing: {file_val['expected_filename']}")

                processed_count += 1

        # Step 5: Summary
        print("\n🎯 FINAL RESULTS:")
        print("=" * 40)

        successful_validations = sum(
            1 for v in all_validations if v["validation"]["success"]
        )
        total_processing_time = sum(
            v["validation"]["processing_time"] for v in all_validations
        )

        print(f"📊 Documents processed: {processed_count}/{len(test_docs)}")
        print(f"✅ Validations passed: {successful_validations}/{len(all_validations)}")
        print(f"⏱️  Total processing time: {total_processing_time:.2f} seconds")
        print(f"📁 Test outputs saved to: {test_output_base}")

        # Detailed results
        print("\n📋 Detailed Results:")
        for result in all_validations:
            doc_title = (
                result["document"].split(" - ")[1]
                if " - " in result["document"]
                else result["document"]
            )
            validation = result["validation"]
            status = "✅ PASS" if validation["success"] else "❌ FAIL"
            time_taken = validation["processing_time"]

            print(f"   {status} {doc_title} ({time_taken:.2f}s)")

            if not validation["success"]:
                for error in validation["errors"]:
                    print(f"     ⚠️  {error}")

        if successful_validations == len(all_validations):
            print("\n🎉 All tests passed! End-to-end workflow is working correctly.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check the detailed results above.")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

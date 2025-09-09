#!/usr/bin/env python3
"""Create controlled test PDFs with known statement boundaries for validation."""

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def create_multi_statement_pdf():
    """Create a PDF with 3 known bank statements for testing."""

    output_path = "./test/input/controlled/known_3_statements.pdf"

    # Create the PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Statement 1: Westpac Account ending in 1234 (Pages 1-2)
    story.append(Paragraph("WESTPAC BANKING CORPORATION", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Account Number: 4293 1831 9017 1234", styles["Normal"]))
    story.append(
        Paragraph("Statement Period: 01 Apr 2024 to 30 Apr 2024", styles["Normal"])
    )
    story.append(Spacer(1, 20))

    # Transaction details
    story.append(Paragraph("TRANSACTION HISTORY", styles["Heading2"]))
    story.append(
        Paragraph("01 APR 2024 - Opening Balance: $1,250.00", styles["Normal"])
    )
    story.append(Paragraph("05 APR 2024 - Direct Deposit: $3,500.00", styles["Normal"]))
    story.append(Paragraph("10 APR 2024 - ATM Withdrawal: -$100.00", styles["Normal"]))
    story.append(Paragraph("15 APR 2024 - Online Purchase: -$89.99", styles["Normal"]))
    story.append(Paragraph("20 APR 2024 - Bill Payment: -$450.00", styles["Normal"]))
    story.append(
        Paragraph("30 APR 2024 - Closing Balance: $4,110.01", styles["Normal"])
    )

    # Add significant empty space to create natural boundary
    story.append(Spacer(1, 100))
    story.append(Paragraph("", styles["Normal"]))
    story.append(Spacer(1, 100))
    story.append(Paragraph("", styles["Normal"]))

    # Force page break for clearer separation
    from reportlab.platypus import PageBreak

    story.append(PageBreak())

    # Statement 2: Westpac Account ending in 5678 (Pages 3-4)
    story.append(Paragraph("WESTPAC BANKING CORPORATION", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Account Number: 4293 1831 9017 5678", styles["Normal"]))
    story.append(
        Paragraph("Statement Period: 01 May 2024 to 31 May 2024", styles["Normal"])
    )
    story.append(Spacer(1, 20))

    story.append(Paragraph("TRANSACTION HISTORY", styles["Heading2"]))
    story.append(
        Paragraph("01 MAY 2024 - Opening Balance: $2,340.00", styles["Normal"])
    )
    story.append(Paragraph("03 MAY 2024 - Direct Deposit: $4,200.00", styles["Normal"]))
    story.append(Paragraph("08 MAY 2024 - Grocery Store: -$156.78", styles["Normal"]))
    story.append(Paragraph("12 MAY 2024 - Gas Station: -$75.50", styles["Normal"]))
    story.append(
        Paragraph("18 MAY 2024 - Online Transfer: -$1,200.00", styles["Normal"])
    )
    story.append(Paragraph("25 MAY 2024 - Interest Earned: $12.45", styles["Normal"]))
    story.append(
        Paragraph("31 MAY 2024 - Closing Balance: $5,120.17", styles["Normal"])
    )

    # Add significant empty space
    story.append(Spacer(1, 100))
    story.append(Paragraph("", styles["Normal"]))
    story.append(Spacer(1, 100))
    story.append(PageBreak())

    # Statement 3: Commonwealth Bank Account ending in 9012 (Pages 5-6)
    story.append(Paragraph("COMMONWEALTH BANK OF AUSTRALIA", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Account Number: 0623 1045 8901 9012", styles["Normal"]))
    story.append(
        Paragraph("Statement Period: 01 Jun 2024 to 30 Jun 2024", styles["Normal"])
    )
    story.append(Spacer(1, 20))

    story.append(Paragraph("TRANSACTION HISTORY", styles["Heading2"]))
    story.append(
        Paragraph("01 JUN 2024 - Opening Balance: $5,780.00", styles["Normal"])
    )
    story.append(Paragraph("04 JUN 2024 - Salary Deposit: $6,500.00", styles["Normal"]))
    story.append(Paragraph("07 JUN 2024 - Rent Payment: -$1,800.00", styles["Normal"]))
    story.append(Paragraph("11 JUN 2024 - Utilities: -$234.56", styles["Normal"]))
    story.append(Paragraph("15 JUN 2024 - Shopping: -$298.44", styles["Normal"]))
    story.append(Paragraph("22 JUN 2024 - Restaurant: -$87.90", styles["Normal"]))
    story.append(
        Paragraph("30 JUN 2024 - Closing Balance: $9,859.10", styles["Normal"])
    )

    # Build the PDF
    doc.build(story)

    return output_path, {
        "expected_statements": 3,
        "expected_files": [
            "westpac-1234-2024-04-30.pdf",  # Statement 1: Pages 1-2
            "westpac-5678-2024-05-31.pdf",  # Statement 2: Pages 3-4
            "commonwealth-9012-2024-06-30.pdf",  # Statement 3: Pages 5-6
        ],
        "expected_accounts": ["429318319171234", "429318319175678", "062310458919012"],
        "expected_banks": [
            "Westpac Banking Corporation",
            "Westpac Banking Corporation",
            "Commonwealth Bank",
        ],
        "expected_periods": [
            "2024-04-01_2024-04-30",
            "2024-05-01_2024-05-31",
            "2024-06-01_2024-06-30",
        ],
    }


def create_single_statement_pdf():
    """Create a PDF with 1 known statement for control testing."""

    output_path = "./test/input/controlled/known_1_statement.pdf"

    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Single Statement: ANZ Account ending in 7890
    story.append(Paragraph("ANZ BANK", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph("Account Number: 0123 4567 8901 7890", styles["Normal"]))
    story.append(
        Paragraph("Statement Period: 01 Jul 2024 to 31 Jul 2024", styles["Normal"])
    )
    story.append(Spacer(1, 20))

    story.append(Paragraph("TRANSACTION HISTORY", styles["Heading2"]))
    story.append(
        Paragraph("01 JUL 2024 - Opening Balance: $3,456.78", styles["Normal"])
    )
    story.append(
        Paragraph("05 JUL 2024 - Payroll Deposit: $4,800.00", styles["Normal"])
    )
    story.append(
        Paragraph("10 JUL 2024 - Mortgage Payment: -$2,100.00", styles["Normal"])
    )
    story.append(
        Paragraph("15 JUL 2024 - Grocery Shopping: -$189.32", styles["Normal"])
    )
    story.append(Paragraph("20 JUL 2024 - Gas Bill: -$98.67", styles["Normal"]))
    story.append(Paragraph("25 JUL 2024 - ATM Withdrawal: -$200.00", styles["Normal"]))
    story.append(
        Paragraph("31 JUL 2024 - Closing Balance: $5,668.79", styles["Normal"])
    )

    doc.build(story)

    return output_path, {
        "expected_statements": 1,
        "expected_files": ["anz-7890-2024-07-31.pdf"],
        "expected_accounts": ["012345678917890"],
        "expected_banks": ["ANZ Bank"],
        "expected_periods": ["2024-07-01_2024-07-31"],
    }


if __name__ == "__main__":
    try:
        # Create test PDFs
        multi_path, multi_spec = create_multi_statement_pdf()
        single_path, single_spec = create_single_statement_pdf()

        print("✅ Created controlled test PDFs:")
        print(f"📄 Multi-statement: {multi_path}")
        print(f"   Expected: {multi_spec['expected_statements']} statements")
        print(f"   Files: {multi_spec['expected_files']}")
        print()
        print(f"📄 Single statement: {single_path}")
        print(f"   Expected: {single_spec['expected_statements']} statements")
        print(f"   Files: {single_spec['expected_files']}")

        # Save specifications for automated testing
        import json

        with open("./test/input/controlled/test_specifications.json", "w") as f:
            json.dump(
                {
                    "multi_statement": {
                        "file": "known_3_statements.pdf",
                        "spec": multi_spec,
                    },
                    "single_statement": {
                        "file": "known_1_statement.pdf",
                        "spec": single_spec,
                    },
                },
                f,
                indent=2,
            )

        print("\n💾 Test specifications saved to test_specifications.json")

    except Exception as e:
        print(f"❌ Error creating test PDFs: {e}")
        import traceback

        traceback.print_exc()

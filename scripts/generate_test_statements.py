#!/usr/bin/env python3
"""Generate realistic test bank statements using Faker for edge case testing.

This script creates PDF files with various bank statement formats and edge cases
to thoroughly test the bank statement separator workflow.
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import random

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from faker import Faker
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

# Initialize Faker
fake = Faker("en_AU")  # Use Australian locale for bank statements


class BankStatementGenerator:
    """Generate realistic bank statements with various formats and edge cases."""

    def __init__(self, output_dir: str = "test/input/generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        # Bank-specific configurations
        self.bank_configs = {
            "Westpac": {
                "colors": {"primary": colors.red, "secondary": colors.darkred},
                "account_format": "429318311{:06d}",
                "bsb_format": "032-{:03d}",
                "statement_types": ["BusinessChoice", "Everyday", "Rewards VISA"],
            },
            "ANZ": {
                "colors": {"primary": colors.blue, "secondary": colors.darkblue},
                "account_format": "012345{:06d}",
                "bsb_format": "013-{:03d}",
                "statement_types": ["Access", "Progress Saver", "Visa"],
            },
            "Commonwealth Bank": {
                "colors": {"primary": colors.gold, "secondary": colors.orange},
                "account_format": "062123{:06d}",
                "bsb_format": "062-{:03d}",
                "statement_types": ["Complete Access", "Smart Access", "Mastercard"],
            },
            "NAB": {
                "colors": {"primary": colors.green, "secondary": colors.darkgreen},
                "account_format": "084234{:06d}",
                "bsb_format": "084-{:03d}",
                "statement_types": ["Classic Banking", "iSaver", "Visa Credit"],
            },
        }

    def _setup_custom_styles(self):
        """Setup custom paragraph styles for different statement formats."""
        self.custom_styles = {
            "BankHeader": ParagraphStyle(
                "BankHeader",
                parent=self.styles["Title"],
                fontSize=18,
                textColor=colors.darkblue,
                spaceAfter=20,
                alignment=TA_CENTER,
            ),
            "AccountHeader": ParagraphStyle(
                "AccountHeader",
                parent=self.styles["Heading2"],
                fontSize=14,
                spaceAfter=10,
                spaceBefore=15,
            ),
            "TransactionHeader": ParagraphStyle(
                "TransactionHeader",
                parent=self.styles["Heading3"],
                fontSize=11,
                spaceBefore=10,
                spaceAfter=5,
            ),
            "StatementInfo": ParagraphStyle(
                "StatementInfo", parent=self.styles["Normal"], fontSize=10, spaceAfter=5
            ),
            "SmallText": ParagraphStyle(
                "SmallText",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.grey,
            ),
        }

    def generate_account_number(self, bank: str) -> str:
        """Generate realistic account number for specific bank."""
        config = self.bank_configs[bank]
        return config["account_format"].format(random.randint(100000, 999999))

    def generate_bsb(self, bank: str) -> str:
        """Generate realistic BSB for specific bank."""
        config = self.bank_configs[bank]
        return config["bsb_format"].format(random.randint(100, 999))

    def generate_transactions(self, count: int, start_date: datetime) -> List[Dict]:
        """Generate realistic transaction data."""
        transactions = []
        current_date = start_date
        balance = fake.random_int(min=1000, max=50000)

        transaction_types = [
            ("EFTPOS", lambda: -fake.random_int(min=5, max=200)),
            ("ATM WITHDRAWAL", lambda: -fake.random_int(min=20, max=500)),
            ("DIRECT DEBIT", lambda: -fake.random_int(min=50, max=1500)),
            ("SALARY/WAGES", lambda: fake.random_int(min=2000, max=8000)),
            ("INTEREST", lambda: fake.random_int(min=1, max=50)),
            ("TRANSFER", lambda: fake.random_int(min=-2000, max=2000)),
            ("ONLINE PAYMENT", lambda: -fake.random_int(min=10, max=800)),
            ("REFUND", lambda: fake.random_int(min=10, max=300)),
        ]

        for _ in range(count):
            trans_type, amount_func = fake.random_element(transaction_types)
            amount = amount_func()
            balance += amount

            transactions.append(
                {
                    "date": current_date.strftime("%d/%m/%Y"),
                    "description": f"{trans_type} {fake.company()}"[:40],
                    "amount": amount,
                    "balance": balance,
                }
            )

            # Move to next day (with some randomness)
            current_date += timedelta(days=random.choice([1, 1, 1, 2, 3]))

        return transactions

    def create_statement_content(
        self, bank: str, account_type: str, start_date: datetime, end_date: datetime
    ) -> List:
        """Create content for a single statement."""
        content = []

        # Bank header
        bank_name = f"{bank} Banking Corporation"
        content.append(Paragraph(bank_name, self.custom_styles["BankHeader"]))
        content.append(Spacer(1, 20))

        # Statement info
        account_num = self.generate_account_number(bank)
        bsb = self.generate_bsb(bank)

        info_data = [
            [
                "Statement Period:",
                f"{start_date.strftime('%d %B %Y')} to {end_date.strftime('%d %B %Y')}",
            ],
            ["Account Type:", f"{account_type} Account"],
            ["Account Number:", account_num],
            ["BSB:", bsb],
            ["Statement Date:", end_date.strftime("%d %B %Y")],
        ]

        info_table = Table(info_data, colWidths=[2 * inch, 3 * inch])
        info_table.setStyle(
            TableStyle(
                [
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )

        content.append(info_table)
        content.append(Spacer(1, 20))

        # Account holder info
        content.append(
            Paragraph("Account Holder Details", self.custom_styles["AccountHeader"])
        )
        holder_info = f"{fake.name()}<br/>{fake.address().replace(chr(10), '<br/>')}"
        content.append(Paragraph(holder_info, self.custom_styles["StatementInfo"]))
        content.append(Spacer(1, 15))

        # Transaction history
        content.append(
            Paragraph("Transaction History", self.custom_styles["TransactionHeader"])
        )

        # Generate transactions
        transaction_count = fake.random_int(min=15, max=50)
        transactions = self.generate_transactions(transaction_count, start_date)

        # Create transaction table
        trans_data = [["Date", "Description", "Amount", "Balance"]]
        for trans in transactions:
            amount_str = f"${abs(trans['amount']):,.2f}"
            if trans["amount"] < 0:
                amount_str = f"-{amount_str}"

            trans_data.append(
                [
                    trans["date"],
                    trans["description"],
                    amount_str,
                    f"${trans['balance']:,.2f}",
                ]
            )

        trans_table = Table(
            trans_data, colWidths=[1 * inch, 3 * inch, 1.2 * inch, 1.2 * inch]
        )
        trans_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    (
                        "ROWBACKGROUNDS",
                        (0, 1),
                        (-1, -1),
                        [colors.white, colors.lightgrey],
                    ),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
                ]
            )
        )

        content.append(trans_table)
        content.append(Spacer(1, 20))

        # Footer
        footer_text = f"This statement was generated for testing purposes on {datetime.now().strftime('%d/%m/%Y')}"
        content.append(Paragraph(footer_text, self.custom_styles["SmallText"]))

        return content, account_num, bsb

    def generate_edge_case_scenarios(self) -> List[Dict[str, Any]]:
        """Define various edge case scenarios for testing."""
        base_date = datetime(2023, 1, 1)

        scenarios = [
            {
                "name": "single_statement_minimal",
                "description": "Single statement with minimal transactions",
                "statements": [
                    {
                        "bank": "Westpac",
                        "type": "Everyday",
                        "start": base_date,
                        "end": base_date + timedelta(days=30),
                        "pages": 2,
                    }
                ],
            },
            {
                "name": "dual_statements_same_bank",
                "description": "Two statements from same bank, different accounts",
                "statements": [
                    {
                        "bank": "ANZ",
                        "type": "Access",
                        "start": base_date,
                        "end": base_date + timedelta(days=30),
                        "pages": 3,
                    },
                    {
                        "bank": "ANZ",
                        "type": "Visa",
                        "start": base_date + timedelta(days=5),
                        "end": base_date + timedelta(days=35),
                        "pages": 4,
                    },
                ],
            },
            {
                "name": "triple_statements_mixed_banks",
                "description": "Three statements from different banks",
                "statements": [
                    {
                        "bank": "Westpac",
                        "type": "BusinessChoice",
                        "start": base_date,
                        "end": base_date + timedelta(days=30),
                        "pages": 2,
                    },
                    {
                        "bank": "Commonwealth Bank",
                        "type": "Complete Access",
                        "start": base_date + timedelta(days=10),
                        "end": base_date + timedelta(days=40),
                        "pages": 3,
                    },
                    {
                        "bank": "NAB",
                        "type": "Classic Banking",
                        "start": base_date + timedelta(days=15),
                        "end": base_date + timedelta(days=45),
                        "pages": 5,
                    },
                ],
            },
            {
                "name": "large_statement_high_volume",
                "description": "Single large statement with many transactions",
                "statements": [
                    {
                        "bank": "Commonwealth Bank",
                        "type": "Mastercard",
                        "start": base_date,
                        "end": base_date + timedelta(days=90),
                        "pages": 15,
                    }
                ],
            },
            {
                "name": "overlapping_periods",
                "description": "Statements with overlapping statement periods",
                "statements": [
                    {
                        "bank": "Westpac",
                        "type": "Rewards VISA",
                        "start": base_date,
                        "end": base_date + timedelta(days=45),
                        "pages": 3,
                    },
                    {
                        "bank": "ANZ",
                        "type": "Progress Saver",
                        "start": base_date + timedelta(days=15),
                        "end": base_date + timedelta(days=60),
                        "pages": 2,
                    },
                ],
            },
            {
                "name": "similar_account_numbers",
                "description": "Statements with very similar account numbers",
                "statements": [
                    {
                        "bank": "NAB",
                        "type": "iSaver",
                        "start": base_date,
                        "end": base_date + timedelta(days=30),
                        "pages": 2,
                        "force_account": "084234123456",
                    },
                    {
                        "bank": "NAB",
                        "type": "Visa Credit",
                        "start": base_date + timedelta(days=5),
                        "end": base_date + timedelta(days=35),
                        "pages": 3,
                        "force_account": "084234123457",
                    },
                ],
            },
        ]

        return scenarios

    def create_multi_statement_pdf(self, scenario: Dict[str, Any]) -> str:
        """Create a PDF file with multiple statements based on scenario."""
        filename = f"{scenario['name']}_test_statements.pdf"
        filepath = self.output_dir / filename

        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=letter,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        full_content = []
        metadata = []

        for i, stmt_config in enumerate(scenario["statements"]):
            # Force account number if specified
            if "force_account" in stmt_config:
                original_format = self.bank_configs[stmt_config["bank"]][
                    "account_format"
                ]
                self.bank_configs[stmt_config["bank"]]["account_format"] = stmt_config[
                    "force_account"
                ]

            # Create statement content
            content, account_num, bsb = self.create_statement_content(
                stmt_config["bank"],
                stmt_config["type"],
                stmt_config["start"],
                stmt_config["end"],
            )

            # Restore original format if it was forced
            if "force_account" in stmt_config:
                self.bank_configs[stmt_config["bank"]]["account_format"] = (
                    original_format
                )

            # Store metadata for validation
            metadata.append(
                {
                    "bank": stmt_config["bank"],
                    "account": account_num,
                    "bsb": bsb,
                    "type": stmt_config["type"],
                    "start_date": stmt_config["start"].strftime("%Y-%m-%d"),
                    "end_date": stmt_config["end"].strftime("%Y-%m-%d"),
                    "expected_pages": stmt_config["pages"],
                }
            )

            # Add content
            full_content.extend(content)

            # Add page break between statements (except last)
            if i < len(scenario["statements"]) - 1:
                from reportlab.platypus import PageBreak

                full_content.append(PageBreak())

        # Build PDF
        doc.build(full_content)

        # Save metadata
        metadata_file = filepath.with_suffix(".json")
        import json

        with open(metadata_file, "w") as f:
            json.dump(
                {
                    "scenario": scenario["name"],
                    "description": scenario["description"],
                    "statements": metadata,
                    "total_expected_statements": len(metadata),
                    "generated_date": datetime.now().isoformat(),
                },
                f,
                indent=2,
            )

        return str(filepath)

    def generate_all_test_cases(self) -> List[str]:
        """Generate all edge case test scenarios."""
        scenarios = self.generate_edge_case_scenarios()
        generated_files = []

        print(f"Generating {len(scenarios)} test scenarios...")

        for scenario in scenarios:
            print(f"  Creating: {scenario['name']} - {scenario['description']}")
            filepath = self.create_multi_statement_pdf(scenario)
            generated_files.append(filepath)
            print(f"    Generated: {Path(filepath).name}")

        # Create summary file
        summary_file = self.output_dir / "test_scenarios_summary.json"
        with open(summary_file, "w") as f:
            import json

            json.dump(
                {
                    "generated_date": datetime.now().isoformat(),
                    "total_scenarios": len(scenarios),
                    "scenarios": [s["name"] for s in scenarios],
                    "generated_files": [str(Path(f).name) for f in generated_files],
                    "output_directory": str(self.output_dir),
                },
                f,
                indent=2,
            )

        return generated_files


def main():
    """Main function to generate test statements."""
    print("🔧 Bank Statement Test Generator")
    print("=" * 50)

    generator = BankStatementGenerator()
    generated_files = generator.generate_all_test_cases()

    print(f"\n✅ Generated {len(generated_files)} test files:")
    for file_path in generated_files:
        filename = Path(file_path).name
        print(f"   📄 {filename}")

    print(f"\n📁 Files saved to: {generator.output_dir}")
    print("💡 Each PDF has a corresponding .json file with expected metadata")
    print("🧪 Run these files through the separator to test edge cases!")


if __name__ == "__main__":
    main()

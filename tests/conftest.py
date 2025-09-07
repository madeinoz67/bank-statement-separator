"""Pytest configuration and shared fixtures."""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import pytest

from faker import Faker
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

# Import the workflow components
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bank_statement_separator.workflow import BankStatementWorkflow
from bank_statement_separator.config import load_config


@pytest.fixture
def faker_gen():
    """Faker instance for generating test data."""
    return Faker("en_AU")


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for test files in the tests directory."""
    # Create temp directory within tests/ to keep project clean
    tests_dir = Path(__file__).parent
    temp_base = tests_dir / "test_temp"

    # Clean up any existing temp directory from previous runs
    if temp_base.exists():
        import shutil

        shutil.rmtree(temp_base)

    temp_base.mkdir(parents=True, exist_ok=True)

    # Create unique subdirectory for this test session
    import uuid

    session_id = str(uuid.uuid4())[:8]
    temp_path = temp_base / f"session_{session_id}"
    temp_path.mkdir()

    try:
        # Create subdirectories
        (temp_path / "input").mkdir()
        (temp_path / "output").mkdir()
        (temp_path / "logs").mkdir()

        yield temp_path
    finally:
        # Clean up after test
        if temp_path.exists():
            import shutil

            shutil.rmtree(temp_path)
        # Clean up base temp directory if empty
        if temp_base.exists() and not list(temp_base.iterdir()):
            temp_base.rmdir()


@pytest.fixture
def test_config(temp_test_dir):
    """Create test configuration."""
    config_data = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "LLM_MODEL": "gpt-4o-mini",
        "LLM_TEMPERATURE": "0",
        "MAX_FILE_SIZE_MB": "100",
        "DEFAULT_OUTPUT_DIR": str(temp_test_dir / "output"),
        "LOG_LEVEL": "DEBUG",
        "LOG_FILE": str(temp_test_dir / "logs" / "test.log"),
        "ALLOWED_INPUT_DIRS": str(temp_test_dir / "input"),
        "ALLOWED_OUTPUT_DIRS": str(temp_test_dir / "output"),
        "QUARANTINE_DIRECTORY": str(temp_test_dir / "quarantine"),
        "ERROR_REPORT_DIRECTORY": str(temp_test_dir / "error_reports"),
        "ENABLE_FALLBACK_PROCESSING": "true",
        "CHUNK_SIZE": "6000",
        "CHUNK_OVERLAP": "800",
    }

    # Create .env file
    env_file = temp_test_dir / ".env"
    with open(env_file, "w") as f:
        for key, value in config_data.items():
            f.write(f"{key}={value}\n")

    return load_config(str(env_file))


@pytest.fixture
def workflow_instance(test_config):
    """Create workflow instance with test configuration."""
    return BankStatementWorkflow(test_config)


class BankStatementTestGenerator:
    """Generate test bank statements for pytest scenarios."""

    def __init__(self, faker_instance: Faker, output_dir: Path):
        self.fake = faker_instance
        self.output_dir = output_dir
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

        # Bank configurations for realistic test data
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
        """Setup custom paragraph styles."""
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

    def generate_account_number(
        self, bank: str, force_number: Optional[str] = None
    ) -> str:
        """Generate realistic account number."""
        if force_number:
            return force_number
        config = self.bank_configs[bank]
        return config["account_format"].format(
            self.fake.random_int(min=100000, max=999999)
        )

    def generate_bsb(self, bank: str) -> str:
        """Generate realistic BSB."""
        config = self.bank_configs[bank]
        return config["bsb_format"].format(self.fake.random_int(min=100, max=999))

    def generate_transactions(self, count: int, start_date: datetime) -> List[Dict]:
        """Generate realistic transaction data."""
        transactions = []
        current_date = start_date
        balance = self.fake.random_int(min=1000, max=50000)

        transaction_types = [
            ("EFTPOS", lambda: -self.fake.random_int(min=5, max=200)),
            ("ATM WITHDRAWAL", lambda: -self.fake.random_int(min=20, max=500)),
            ("DIRECT DEBIT", lambda: -self.fake.random_int(min=50, max=1500)),
            ("SALARY/WAGES", lambda: self.fake.random_int(min=2000, max=8000)),
            ("INTEREST", lambda: self.fake.random_int(min=1, max=50)),
            ("TRANSFER", lambda: self.fake.random_int(min=-2000, max=2000)),
            ("ONLINE PAYMENT", lambda: -self.fake.random_int(min=10, max=800)),
            ("REFUND", lambda: self.fake.random_int(min=10, max=300)),
        ]

        for _ in range(count):
            trans_type, amount_func = self.fake.random_element(transaction_types)
            amount = amount_func()
            balance += amount

            transactions.append(
                {
                    "date": current_date.strftime("%d/%m/%Y"),
                    "description": f"{trans_type} {self.fake.company()}"[:40],
                    "amount": amount,
                    "balance": balance,
                }
            )

            current_date += timedelta(days=self.fake.random_int(min=1, max=3))

        return transactions

    def create_statement_content(
        self,
        bank: str,
        account_type: str,
        start_date: datetime,
        end_date: datetime,
        force_account: Optional[str] = None,
    ) -> tuple:
        """Create content for a single statement."""
        content = []

        # Bank header
        bank_name = f"{bank} Banking Corporation"
        content.append(Paragraph(bank_name, self.custom_styles["BankHeader"]))
        content.append(Spacer(1, 20))

        # Generate account details
        account_num = self.generate_account_number(bank, force_account)
        bsb = self.generate_bsb(bank)

        # Statement info table
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
        holder_info = (
            f"{self.fake.name()}<br/>{self.fake.address().replace(chr(10), '<br/>')}"
        )
        content.append(Paragraph(holder_info, self.custom_styles["StatementInfo"]))
        content.append(Spacer(1, 15))

        # Transaction history
        content.append(
            Paragraph("Transaction History", self.custom_styles["TransactionHeader"])
        )

        # Generate realistic number of transactions
        transaction_count = self.fake.random_int(min=15, max=50)
        transactions = self.generate_transactions(transaction_count, start_date)

        # Transaction table
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
        footer_text = f"Generated for testing - {datetime.now().strftime('%d/%m/%Y')}"
        content.append(Paragraph(footer_text, self.custom_styles["SmallText"]))

        return content, account_num, bsb

    def create_test_pdf(
        self, scenario_name: str, statements_config: List[Dict]
    ) -> tuple:
        """Create a test PDF with multiple statements."""
        filename = f"{scenario_name}_test.pdf"
        filepath = self.output_dir / filename

        # Create PDF
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

        for i, stmt_config in enumerate(statements_config):
            content, account_num, bsb = self.create_statement_content(
                stmt_config["bank"],
                stmt_config["type"],
                stmt_config["start_date"],
                stmt_config["end_date"],
                stmt_config.get("force_account"),
            )

            metadata.append(
                {
                    "bank": stmt_config["bank"],
                    "account_number": account_num,
                    "bsb": bsb,
                    "type": stmt_config["type"],
                    "start_date": stmt_config["start_date"].strftime("%Y-%m-%d"),
                    "end_date": stmt_config["end_date"].strftime("%Y-%m-%d"),
                    "expected_pages": stmt_config.get("expected_pages", 2),
                }
            )

            full_content.extend(content)

            # Page break between statements
            if i < len(statements_config) - 1:
                from reportlab.platypus import PageBreak

                full_content.append(PageBreak())

        doc.build(full_content)

        return str(filepath), metadata


@pytest.fixture
def statement_generator(faker_gen, temp_test_dir):
    """Bank statement generator fixture."""
    input_dir = temp_test_dir / "input"
    return BankStatementTestGenerator(faker_gen, input_dir)


@pytest.fixture(scope="session")
def edge_case_scenarios():
    """Define edge case test scenarios."""
    base_date = datetime(2023, 6, 1)

    return [
        {
            "name": "single_statement_minimal",
            "description": "Single statement with minimal data",
            "expected_statements": 1,
            "statements": [
                {
                    "bank": "Westpac",
                    "type": "Everyday",
                    "start_date": base_date,
                    "end_date": base_date + timedelta(days=30),
                    "expected_pages": 2,
                    "force_account": "4293183190172819",
                }
            ],
        },
        {
            "name": "dual_statements_same_bank",
            "description": "Two statements from same bank",
            "expected_statements": 2,
            "statements": [
                {
                    "bank": "ANZ",
                    "type": "Access",
                    "start_date": base_date,
                    "end_date": base_date + timedelta(days=30),
                    "expected_pages": 3,
                    "force_account": "0123456789012345",
                },
                {
                    "bank": "ANZ",
                    "type": "Visa",
                    "start_date": base_date + timedelta(days=5),
                    "end_date": base_date + timedelta(days=35),
                    "expected_pages": 4,
                    "force_account": "0123456789012346",
                },
            ],
        },
        {
            "name": "triple_statements_mixed_banks",
            "description": "Three statements from different banks",
            "expected_statements": 3,
            "statements": [
                {
                    "bank": "Westpac",
                    "type": "BusinessChoice",
                    "start_date": base_date,
                    "end_date": base_date + timedelta(days=30),
                    "expected_pages": 2,
                    "force_account": "4293183190172819",
                },
                {
                    "bank": "Commonwealth Bank",
                    "type": "Complete Access",
                    "start_date": base_date + timedelta(days=10),
                    "end_date": base_date + timedelta(days=40),
                    "expected_pages": 3,
                    "force_account": "0621234567890123",
                },
                {
                    "bank": "NAB",
                    "type": "Classic Banking",
                    "start_date": base_date + timedelta(days=15),
                    "end_date": base_date + timedelta(days=45),
                    "expected_pages": 5,
                    "force_account": "0842345678901234",
                },
            ],
        },
        {
            "name": "similar_account_numbers",
            "description": "Statements with similar account numbers",
            "expected_statements": 2,
            "statements": [
                {
                    "bank": "NAB",
                    "type": "iSaver",
                    "start_date": base_date,
                    "end_date": base_date + timedelta(days=30),
                    "expected_pages": 2,
                    "force_account": "084234123456",
                },
                {
                    "bank": "NAB",
                    "type": "Visa Credit",
                    "start_date": base_date + timedelta(days=5),
                    "end_date": base_date + timedelta(days=35),
                    "expected_pages": 3,
                    "force_account": "084234123457",
                },
            ],
        },
        {
            "name": "overlapping_periods",
            "description": "Statements with overlapping periods",
            "expected_statements": 2,
            "statements": [
                {
                    "bank": "Westpac",
                    "type": "Rewards VISA",
                    "start_date": base_date,
                    "end_date": base_date + timedelta(days=45),
                    "expected_pages": 3,
                },
                {
                    "bank": "ANZ",
                    "type": "Progress Saver",
                    "start_date": base_date + timedelta(days=15),
                    "end_date": base_date + timedelta(days=60),
                    "expected_pages": 2,
                },
            ],
        },
    ]


@pytest.fixture
def skip_if_no_api_key():
    """Skip test if no OpenAI API key is available."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not available")

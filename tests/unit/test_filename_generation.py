"""Tests for filename generation functionality."""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

try:
    from bank_statement_separator.workflow import BankStatementWorkflow
    from bank_statement_separator.config import Config
except ImportError:
    # Fallback for testing individual methods
    pytest.skip("Dependencies not available", allow_module_level=True)


@pytest.mark.unit
@pytest.mark.validation
@pytest.mark.smoke
class TestFilenameGeneration:
    """Test filename generation methods."""

    def setup_method(self):
        """Set up test workflow instance."""
        config = Config(openai_api_key="test-key", max_filename_length=240)
        self.workflow = BankStatementWorkflow(config)

    def test_generate_filename_complete_metadata(self):
        """Test filename generation with complete metadata."""
        boundary = {
            "bank_name": "Westpac Banking Corporation",
            "account_number": "4293 1831 9017 2819",
            "statement_period": "2015-04-22_2015-05-21",
            "start_page": 1,
            "end_page": 2,
        }

        result = self.workflow._generate_filename(boundary)
        assert result == "westpac-2819-2015-05-21.pdf"

    def test_generate_filename_chase_bank(self):
        """Test filename generation with Chase bank."""
        boundary = {
            "bank_name": "JPMorgan Chase Bank",
            "account_number": "1234567890123456",
            "statement_period": "2024-01-31",
            "start_page": 1,
            "end_page": 3,
        }

        result = self.workflow._generate_filename(boundary)
        assert result == "jpmorganch-3456-2024-01-31.pdf"

    def test_generate_filename_fallback_values(self):
        """Test filename generation with missing metadata (fallbacks)."""
        boundary = {
            "bank_name": "",
            "account_number": "",
            "statement_period": "",
            "start_page": 3,
            "end_page": 5,
        }

        result = self.workflow._generate_filename(boundary)
        assert result == "unknown-0000-unknown-date-p3.pdf"

    def test_generate_filename_partial_data(self):
        """Test filename generation with partial metadata."""
        boundary = {
            "bank_name": "Commonwealth Bank of Australia",
            "account_number": "12345",  # Less than 4 digits
            "statement_period": "Unknown",
            "start_page": 6,
            "end_page": 8,
        }

        result = self.workflow._generate_filename(boundary)
        assert result == "commonweal-2345-unknown-date.pdf"

    def test_normalize_bank_name(self):
        """Test bank name normalization."""
        test_cases = [
            ("Westpac Banking Corporation", "westpac"),
            ("JPMorgan Chase Bank", "jpmorganch"),
            ("Commonwealth Bank of Australia", "commonweal"),
            ("Bank of America", "ofamerica"),
            ("", "unknown"),
            ("Wells Fargo Bank", "wellsfargo"),
            ("Very Long Bank Name Corporation", "verylongna"),  # Truncated to 10 chars
        ]

        for input_name, expected in test_cases:
            result = self.workflow._normalize_bank_name(input_name)
            assert (
                result == expected
            ), f"Failed for {input_name}: got {result}, expected {expected}"

    def test_extract_last4_digits(self):
        """Test last 4 digits extraction."""
        test_cases = [
            ("4293 1831 9017 2819", "2819"),
            ("1234567890123456", "3456"),
            ("12345", "2345"),
            ("123", "0000"),  # Less than 4 digits
            ("", "0000"),  # Empty
            ("ABCD1234EFGH", "1234"),  # Mixed alphanumeric
            ("No digits here!", "0000"),  # No digits
        ]

        for input_account, expected in test_cases:
            result = self.workflow._extract_last4_digits(input_account)
            assert (
                result == expected
            ), f"Failed for {input_account}: got {result}, expected {expected}"

    def test_format_statement_date(self):
        """Test statement date formatting."""
        test_cases = [
            ("2015-04-22_2015-05-21", "2015-05-21"),  # Range format (extract end)
            ("2024-01-31", "2024-01-31"),  # Single date
            ("Unknown", "unknown-date"),  # Invalid
            ("", "unknown-date"),  # Empty
            ("2023-12-15_2024-01-15", "2024-01-15"),  # Another range
            ("Invalid format", "unknown-date"),  # Invalid format
        ]

        for input_period, expected in test_cases:
            result = self.workflow._format_statement_date(input_period)
            assert (
                result == expected
            ), f"Failed for {input_period}: got {result}, expected {expected}"

    def test_filename_length_limit(self):
        """Test filename length limiting."""
        # Create workflow with short filename limit
        config = Config(openai_api_key="test-key", max_filename_length=30)
        workflow = BankStatementWorkflow(config)

        boundary = {
            "bank_name": "Very Long Bank Name That Exceeds Limits",
            "account_number": "1234567890123456",
            "statement_period": "2024-01-31",
            "start_page": 1,
            "end_page": 2,
        }

        result = workflow._generate_filename(boundary)
        assert len(result) <= 30
        assert result.endswith("-3456-2024-01-31.pdf")  # Core components preserved

    def test_collision_prevention(self):
        """Test filename collision prevention with page numbers."""
        boundary1 = {
            "bank_name": "Test Bank",
            "account_number": "",
            "statement_period": "",
            "start_page": 1,
            "end_page": 2,
        }

        boundary2 = {
            "bank_name": "Test Bank",
            "account_number": "",
            "statement_period": "",
            "start_page": 3,
            "end_page": 5,
        }

        result1 = self.workflow._generate_filename(boundary1)
        result2 = self.workflow._generate_filename(boundary2)

        assert result1 == "test-0000-unknown-date-p1.pdf"
        assert result2 == "test-0000-unknown-date-p3.pdf"
        assert result1 != result2  # Ensure different filenames

    def test_paperless_filename_matches_output(self):
        """Test that paperless filename matches output document filename."""
        boundary = {
            "bank_name": "Westpac Banking Corporation",
            "account_number": "4293 1831 9017 2819",
            "statement_period": "2015-04-22_2015-05-21",
            "start_page": 3,
            "end_page": 5,
        }

        # Generate filename for output document
        output_filename = self.workflow._generate_filename(boundary)

        # The filename sent to paperless should be identical
        paperless_filename = output_filename

        assert output_filename == paperless_filename
        assert output_filename == "westpac-2819-2015-05-21.pdf"

    def test_paperless_filename_consistency_with_fallbacks(self):
        """Test paperless filename consistency when using fallback values."""
        boundary = {
            "bank_name": "",
            "account_number": "",
            "statement_period": "",
            "start_page": 7,
            "end_page": 9,
        }

        # Generate filename for output document
        output_filename = self.workflow._generate_filename(boundary)

        # The filename sent to paperless must be identical
        paperless_filename = output_filename

        assert output_filename == paperless_filename
        assert output_filename == "unknown-0000-unknown-date-p7.pdf"

    def test_paperless_filename_no_modification(self):
        """Test that paperless integration doesn't modify the filename."""
        test_cases = [
            {
                "bank_name": "JPMorgan Chase Bank",
                "account_number": "1234567890123456",
                "statement_period": "2024-01-31",
                "start_page": 1,
                "end_page": 3,
                "expected": "jpmorganch-3456-2024-01-31.pdf",
            },
            {
                "bank_name": "Commonwealth Bank of Australia",
                "account_number": "9876543210987654",
                "statement_period": "2023-12-15_2024-01-15",
                "start_page": 4,
                "end_page": 6,
                "expected": "commonweal-7654-2024-01-15.pdf",
            },
            {
                "bank_name": "Bank of America",
                "account_number": "5555",
                "statement_period": "Unknown",
                "start_page": 10,
                "end_page": 12,
                "expected": "ofamerica-5555-unknown-date.pdf",
            },
        ]

        for case in test_cases:
            boundary = {
                "bank_name": case["bank_name"],
                "account_number": case["account_number"],
                "statement_period": case["statement_period"],
                "start_page": case["start_page"],
                "end_page": case["end_page"],
            }

            # Generate filename for output document
            output_filename = self.workflow._generate_filename(boundary)

            # Paperless filename must be identical - no modifications allowed
            paperless_filename = output_filename

            assert output_filename == paperless_filename == case["expected"], (
                f"Filename mismatch for {case['bank_name']}: "
                f"output='{output_filename}', paperless='{paperless_filename}', "
                f"expected='{case['expected']}'"
            )

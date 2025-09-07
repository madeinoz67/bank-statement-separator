"""Unit tests for the hallucination detection system."""

from datetime import datetime
import pytest

from src.bank_statement_separator.utils.hallucination_detector import (
    HallucinationDetector,
    HallucinationType,
    HallucinationAlert,
)


@pytest.mark.unit
@pytest.mark.validation
@pytest.mark.llm
class TestHallucinationDetector:
    """Test cases for the HallucinationDetector."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = HallucinationDetector()

    def test_phantom_statement_detection(self):
        """Test detection of phantom statements."""
        # Test case: 3 statements detected in 1-page document (impossible)
        fake_boundaries = [
            {"start_page": 1, "end_page": 1, "account_number": "123456"},
            {"start_page": 2, "end_page": 2, "account_number": "654321"},  # Phantom!
            {"start_page": 3, "end_page": 3, "account_number": "999999"},  # Phantom!
        ]

        alerts = self.detector.validate_boundary_response(
            fake_boundaries, total_pages=1, document_text="Short document"
        )

        # Should detect phantom statements
        assert len(alerts) >= 2
        phantom_alerts = [
            a for a in alerts if a.type == HallucinationType.PHANTOM_STATEMENT
        ]
        assert len(phantom_alerts) >= 2

        # Should recommend rejection
        assert self.detector.should_reject_response(alerts)

    def test_invalid_page_ranges(self):
        """Test detection of invalid page ranges."""
        # Test case: Invalid page ranges
        invalid_boundaries = [
            {"start_page": 3, "end_page": 1},  # start > end
            {"start_page": -1, "end_page": 2},  # start < 1
            {"start_page": 5, "end_page": 6},  # exceeds total pages
        ]

        alerts = self.detector.validate_boundary_response(
            invalid_boundaries, total_pages=3, document_text="Document content"
        )

        # Should detect invalid ranges
        range_alerts = [
            a for a in alerts if a.type == HallucinationType.INVALID_PAGE_RANGE
        ]
        assert len(range_alerts) >= 2

        # Should recommend rejection
        assert self.detector.should_reject_response(alerts)

    def test_fabricated_bank_detection(self):
        """Test detection of fabricated bank names."""
        # Test case: Non-existent bank name that doesn't match known patterns
        fake_metadata = {
            "bank_name": "Fictional Credit Institution of Dreams",
            "account_number": "429318311799210",  # Use realistic account to avoid nonsensical account alerts
            "statement_period": "2023-01-01 to 2023-01-31",
        }

        # Document text contains different bank
        document_text = "Westpac Banking Corporation Statement Account: 429318311799210"

        alerts = self.detector.validate_metadata_response(
            fake_metadata, document_text, (1, 2)
        )

        # Should detect fabricated bank (bank name not in document and not in known list)
        bank_alerts = [a for a in alerts if a.type == HallucinationType.FABRICATED_BANK]
        assert len(bank_alerts) >= 1
        assert bank_alerts[0].severity in ["high", "medium"]

    def test_impossible_dates(self):
        """Test detection of impossible dates."""
        current_year = datetime.now().year

        # Test future dates - use a clearly future year
        future_year = current_year + 10  # Far enough in future to be caught
        future_metadata = {
            "bank_name": "Chase Bank",
            "account_number": "123456789",
            "statement_period": f"{future_year}-01-01 to {future_year}-12-31",
        }

        alerts = self.detector.validate_metadata_response(
            future_metadata, "Chase Bank statement", (1, 2)
        )

        date_alerts = [
            a for a in alerts if a.type == HallucinationType.IMPOSSIBLE_DATES
        ]
        assert len(date_alerts) >= 1

        # Test ancient dates
        ancient_metadata = {
            "bank_name": "Wells Fargo",
            "account_number": "987654321",
            "statement_period": "1899-01-01 to 1899-12-31",
        }

        alerts2 = self.detector.validate_metadata_response(
            ancient_metadata, "Wells Fargo statement", (1, 2)
        )

        date_alerts2 = [
            a for a in alerts2 if a.type == HallucinationType.IMPOSSIBLE_DATES
        ]
        assert len(date_alerts2) >= 1

    def test_nonsensical_accounts(self):
        """Test detection of nonsensical account numbers."""
        # Test obviously fake account numbers
        fake_accounts = [
            {"bank_name": "Bank of America", "account_number": "123456789"},
            {"bank_name": "Wells Fargo", "account_number": "***1234***"},
            {"bank_name": "Chase", "account_number": "000000000"},
            {"bank_name": "Citibank", "account_number": "a" * 25},  # Too long
        ]

        total_alerts = 0
        for metadata in fake_accounts:
            alerts = self.detector.validate_metadata_response(
                metadata, "Bank statement", (1, 2)
            )
            account_alerts = [
                a for a in alerts if a.type == HallucinationType.NONSENSICAL_ACCOUNT
            ]
            total_alerts += len(account_alerts)

        # Should detect multiple nonsensical accounts
        assert total_alerts >= 3

    def test_duplicate_boundaries(self):
        """Test detection of duplicate boundaries."""
        duplicate_boundaries = [
            {"start_page": 1, "end_page": 2, "account_number": "123456"},
            {"start_page": 1, "end_page": 2, "account_number": "123456"},  # Duplicate!
            {"start_page": 3, "end_page": 4, "account_number": "789012"},
        ]

        alerts = self.detector.validate_boundary_response(
            duplicate_boundaries, total_pages=4, document_text="Document content"
        )

        duplicate_alerts = [
            a for a in alerts if a.type == HallucinationType.DUPLICATE_BOUNDARIES
        ]
        assert len(duplicate_alerts) >= 1

    def test_valid_data_no_false_positives(self):
        """Test that valid data doesn't trigger false positives."""
        # Test valid boundary data with substantial content
        valid_boundaries = [
            {"start_page": 1, "end_page": 2, "account_number": "429318311799210"}
        ]

        # Use longer document content to avoid missing content alerts
        long_content = (
            "Westpac Banking Corporation statement content. " * 10
        )  # >50 chars

        alerts = self.detector.validate_boundary_response(
            valid_boundaries, total_pages=2, document_text=long_content
        )

        # Should not trigger critical or high alerts for valid data
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        high_alerts = [a for a in alerts if a.severity == "high"]
        assert len(critical_alerts) == 0
        assert len(high_alerts) == 0

        # Should not recommend rejection
        assert not self.detector.should_reject_response(alerts)

    def test_valid_metadata_no_false_positives(self):
        """Test that valid metadata doesn't trigger false positives."""
        valid_metadata = {
            "bank_name": "Westpac Banking Corporation",
            "account_number": "429318311799210",
            "statement_period": "2023-01-01 to 2023-01-31",
        }

        document_text = "Westpac Banking Corporation Statement Account: 429318311799210 Period: Jan 2023"
        alerts = self.detector.validate_metadata_response(
            valid_metadata, document_text, (1, 2)
        )

        # Should not trigger critical or high alerts for valid data
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        high_alerts = [a for a in alerts if a.severity == "high"]
        assert len(critical_alerts) == 0
        assert len(high_alerts) == 0

    def test_rejection_thresholds(self):
        """Test that rejection thresholds work correctly."""
        # Critical alert should always trigger rejection
        critical_alert = HallucinationAlert(
            type=HallucinationType.PHANTOM_STATEMENT,
            severity="critical",
            description="Test critical alert",
            detected_value="test",
        )
        assert self.detector.should_reject_response([critical_alert])

        # Three high alerts should trigger rejection
        high_alerts = [
            HallucinationAlert(
                type=HallucinationType.FABRICATED_BANK,
                severity="high",
                description=f"Test high alert {i}",
                detected_value=f"test{i}",
            )
            for i in range(3)
        ]
        assert self.detector.should_reject_response(high_alerts)

        # Two high alerts should not trigger rejection
        assert not self.detector.should_reject_response(high_alerts[:2])

        # Medium and low alerts alone should not trigger rejection
        medium_alert = HallucinationAlert(
            type=HallucinationType.DUPLICATE_BOUNDARIES,
            severity="medium",
            description="Test medium alert",
            detected_value="test",
        )
        low_alert = HallucinationAlert(
            type=HallucinationType.INCONSISTENT_DATA,
            severity="low",
            description="Test low alert",
            detected_value="test",
        )
        assert not self.detector.should_reject_response([medium_alert, low_alert])

    def test_hallucination_summary(self):
        """Test hallucination summary generation."""
        # Start with clean detector
        assert self.detector.get_hallucination_summary()["status"] == "clean"

        # Add some alerts
        alerts = [
            HallucinationAlert(
                type=HallucinationType.PHANTOM_STATEMENT,
                severity="critical",
                description="Test critical",
                detected_value="test1",
            ),
            HallucinationAlert(
                type=HallucinationType.FABRICATED_BANK,
                severity="high",
                description="Test high",
                detected_value="test2",
            ),
        ]

        self.detector.alerts.extend(alerts)
        summary = self.detector.get_hallucination_summary()

        assert summary["status"] == "hallucinations_detected"
        assert summary["total_alerts"] == 2
        assert summary["by_severity"]["critical"] == 1
        assert summary["by_severity"]["high"] == 1
        assert summary["by_type"]["phantom_statement"] == 1
        assert summary["by_type"]["fabricated_bank"] == 1
        assert summary["rejection_recommended"]

    def test_missing_content_detection(self):
        """Test detection of boundaries with missing content."""
        boundaries = [{"start_page": 1, "end_page": 2, "account_number": "123456"}]

        # Empty document should trigger missing content alert
        alerts = self.detector.validate_boundary_response(
            boundaries, total_pages=2, document_text=""
        )

        missing_alerts = [
            a for a in alerts if a.type == HallucinationType.MISSING_CONTENT
        ]
        assert len(missing_alerts) >= 1

        # Document with substantial content should not trigger alert
        alerts2 = self.detector.validate_boundary_response(
            boundaries, total_pages=2, document_text="A" * 100
        )

        missing_alerts2 = [
            a for a in alerts2 if a.type == HallucinationType.MISSING_CONTENT
        ]
        assert len(missing_alerts2) == 0

    def test_known_bank_validation(self):
        """Test that known banks are properly validated."""
        known_banks = ["westpac", "commonwealth", "anz", "nab", "chase", "wells fargo"]

        for bank in known_banks:
            metadata = {
                "bank_name": bank.title(),  # Test with title case
                "account_number": "123456789",
                "statement_period": "2023-01-01 to 2023-01-31",
            }

            document_text = f"{bank} statement content"
            alerts = self.detector.validate_metadata_response(
                metadata, document_text, (1, 2)
            )

            # Known banks in document should not trigger fabrication alerts
            bank_alerts = [
                a for a in alerts if a.type == HallucinationType.FABRICATED_BANK
            ]
            assert len(bank_alerts) == 0, (
                f"Known bank '{bank}' triggered fabrication alert"
            )

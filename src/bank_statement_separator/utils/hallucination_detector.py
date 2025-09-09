"""Hallucination detection and validation for LLM responses."""

import logging
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class HallucinationType(Enum):
    """Types of hallucinations that can be detected."""

    PHANTOM_STATEMENT = "phantom_statement"
    INVALID_PAGE_RANGE = "invalid_page_range"
    IMPOSSIBLE_DATES = "impossible_dates"
    NONSENSICAL_ACCOUNT = "nonsensical_account"
    FABRICATED_BANK = "fabricated_bank"
    DUPLICATE_BOUNDARIES = "duplicate_boundaries"
    MISSING_CONTENT = "missing_content"
    INCONSISTENT_DATA = "inconsistent_data"


@dataclass
class HallucinationAlert:
    """Represents a detected hallucination."""

    type: HallucinationType
    severity: str  # "low", "medium", "high", "critical"
    description: str
    detected_value: Any
    expected_value: Any = None
    confidence: float = 1.0
    source: str = "unknown"


class HallucinationDetector:
    """Detects and validates LLM responses for hallucinations and inconsistencies."""

    def __init__(self):
        self.alerts: List[HallucinationAlert] = []

        # Known valid bank patterns (expandable)
        self.valid_banks = {
            "westpac",
            "commonwealth",
            "anz",
            "nab",
            "bendigo",
            "suncorp",
            "chase",
            "wells fargo",
            "bank of america",
            "citibank",
            "jpmorgan",
            "hsbc",
            "barclays",
            "lloyds",
            "royal bank",
            "td bank",
        }

        # Suspicious patterns that often indicate hallucinations
        self.suspicious_patterns = [
            r"bank\s+of\s+[a-z]+\s+[a-z]+\s+[a-z]+",  # overly complex bank names
            r"account\s+ending\s+in\s+\*+",  # generic account descriptions
            r"customer\s+service",  # generic service terms
            r"statement\s+period\s+unknown",  # generic period descriptions
        ]

    def validate_boundary_response(
        self, boundaries: List[Dict[str, Any]], total_pages: int, document_text: str
    ) -> List[HallucinationAlert]:
        """Validate boundary detection response for hallucinations."""
        alerts = []

        # Check for phantom statements (more boundaries than possible)
        alerts.extend(
            self._check_phantom_statements(boundaries, total_pages, document_text)
        )

        # Check for invalid page ranges
        alerts.extend(self._check_invalid_page_ranges(boundaries, total_pages))

        # Check for duplicate boundaries
        alerts.extend(self._check_duplicate_boundaries(boundaries))

        # Check for missing content validation
        alerts.extend(self._check_missing_content_boundaries(boundaries, document_text))

        return alerts

    def validate_metadata_response(
        self, metadata: Dict[str, Any], document_text: str, page_range: Tuple[int, int]
    ) -> List[HallucinationAlert]:
        """Validate metadata extraction response for hallucinations."""
        alerts = []

        # Check for fabricated bank names
        alerts.extend(self._check_fabricated_banks(metadata, document_text))

        # Check for nonsensical account numbers
        alerts.extend(self._check_nonsensical_accounts(metadata, document_text))

        # Check for impossible dates
        alerts.extend(self._check_impossible_dates(metadata))

        # Check for inconsistent data
        alerts.extend(self._check_inconsistent_metadata(metadata, document_text))

        return alerts

    def _check_phantom_statements(
        self, boundaries: List[Dict[str, Any]], total_pages: int, document_text: str
    ) -> List[HallucinationAlert]:
        """Detect phantom statements that don't exist in the document."""
        alerts = []

        if len(boundaries) > total_pages:
            alerts.append(
                HallucinationAlert(
                    type=HallucinationType.PHANTOM_STATEMENT,
                    severity="critical",
                    description=f"Detected {len(boundaries)} statements in {total_pages}-page document",
                    detected_value=len(boundaries),
                    expected_value=f"≤{total_pages}",
                    confidence=1.0,
                    source="boundary_validation",
                )
            )

        # Check if boundaries reference content that doesn't exist
        for i, boundary in enumerate(boundaries):
            start_page = boundary.get("start_page", 1)
            end_page = boundary.get("end_page", total_pages)

            if start_page > total_pages or end_page > total_pages:
                alerts.append(
                    HallucinationAlert(
                        type=HallucinationType.PHANTOM_STATEMENT,
                        severity="high",
                        description=f"Boundary {i + 1} references pages {start_page}-{end_page} in {total_pages}-page document",
                        detected_value=f"{start_page}-{end_page}",
                        expected_value=f"1-{total_pages}",
                        confidence=1.0,
                        source="boundary_validation",
                    )
                )

        return alerts

    def _check_invalid_page_ranges(
        self, boundaries: List[Dict[str, Any]], total_pages: int
    ) -> List[HallucinationAlert]:
        """Check for logically invalid page ranges."""
        alerts = []

        for i, boundary in enumerate(boundaries):
            start_page = boundary.get("start_page", 1)
            end_page = boundary.get("end_page", total_pages)

            if start_page > end_page:
                alerts.append(
                    HallucinationAlert(
                        type=HallucinationType.INVALID_PAGE_RANGE,
                        severity="high",
                        description=f"Boundary {i + 1} has invalid range: start_page ({start_page}) > end_page ({end_page})",
                        detected_value=f"{start_page}-{end_page}",
                        confidence=1.0,
                        source="boundary_validation",
                    )
                )

            if start_page < 1:
                alerts.append(
                    HallucinationAlert(
                        type=HallucinationType.INVALID_PAGE_RANGE,
                        severity="medium",
                        description=f"Boundary {i + 1} has invalid start_page: {start_page}",
                        detected_value=start_page,
                        expected_value="≥1",
                        confidence=1.0,
                        source="boundary_validation",
                    )
                )

        return alerts

    def _check_duplicate_boundaries(
        self, boundaries: List[Dict[str, Any]]
    ) -> List[HallucinationAlert]:
        """Check for duplicate or overlapping boundaries."""
        alerts = []

        seen_ranges = set()
        for i, boundary in enumerate(boundaries):
            start_page = boundary.get("start_page", 1)
            end_page = boundary.get("end_page", 1)
            range_key = (start_page, end_page)

            if range_key in seen_ranges:
                alerts.append(
                    HallucinationAlert(
                        type=HallucinationType.DUPLICATE_BOUNDARIES,
                        severity="medium",
                        description=f"Duplicate boundary detected: pages {start_page}-{end_page}",
                        detected_value=f"{start_page}-{end_page}",
                        confidence=0.9,
                        source="boundary_validation",
                    )
                )
            else:
                seen_ranges.add(range_key)

        return alerts

    def _check_missing_content_boundaries(
        self, boundaries: List[Dict[str, Any]], document_text: str
    ) -> List[HallucinationAlert]:
        """Check if boundaries reference content that doesn't exist in the document."""
        alerts = []

        # This is a simplified check - in practice, you'd want more sophisticated content validation
        if not document_text or len(document_text.strip()) < 50:
            for i, boundary in enumerate(boundaries):
                alerts.append(
                    HallucinationAlert(
                        type=HallucinationType.MISSING_CONTENT,
                        severity="high",
                        description=f"Boundary {i + 1} detected but document has minimal content ({len(document_text)} chars)",
                        detected_value=len(document_text),
                        expected_value=">50",
                        confidence=0.8,
                        source="content_validation",
                    )
                )

        return alerts

    def _check_fabricated_banks(
        self, metadata: Dict[str, Any], document_text: str
    ) -> List[HallucinationAlert]:
        """Check for fabricated or hallucinated bank names."""
        alerts = []

        bank_name = metadata.get("bank_name", "").lower().strip()
        if not bank_name:
            return alerts

        # Check if bank name appears in document text
        if bank_name not in document_text.lower():
            # Check for partial matches with known banks (require substantial words, not just "of", "the", etc.)
            bank_words = bank_name.split()
            substantial_words = [
                word
                for word in bank_words
                if len(word) > 3
                and word not in ["bank", "banking", "corporation", "company"]
            ]
            found_match = False

            for known_bank in self.valid_banks:
                known_words = known_bank.split()
                substantial_known_words = [
                    word for word in known_words if len(word) > 3
                ]
                # Require at least one substantial word match
                if any(word in substantial_words for word in substantial_known_words):
                    found_match = True
                    break

            if not found_match:
                alerts.append(
                    HallucinationAlert(
                        type=HallucinationType.FABRICATED_BANK,
                        severity="high",
                        description=f"Bank name '{bank_name}' not found in document text and not in known bank list",
                        detected_value=bank_name,
                        confidence=0.8,
                        source="metadata_validation",
                    )
                )

        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, bank_name, re.IGNORECASE):
                alerts.append(
                    HallucinationAlert(
                        type=HallucinationType.FABRICATED_BANK,
                        severity="medium",
                        description=f"Bank name '{bank_name}' matches suspicious pattern: {pattern}",
                        detected_value=bank_name,
                        confidence=0.6,
                        source="pattern_validation",
                    )
                )

        return alerts

    def _check_nonsensical_accounts(
        self, metadata: Dict[str, Any], document_text: str
    ) -> List[HallucinationAlert]:
        """Check for nonsensical or hallucinated account numbers."""
        alerts = []

        account_number = metadata.get("account_number", "").strip()
        if not account_number:
            return alerts

        # Check for obviously fake patterns
        if account_number in ["123456789", "000000000", "111111111", "***1234***"]:
            alerts.append(
                HallucinationAlert(
                    type=HallucinationType.NONSENSICAL_ACCOUNT,
                    severity="high",
                    description=f"Account number appears to be placeholder/fake: {account_number}",
                    detected_value=account_number,
                    confidence=0.9,
                    source="account_validation",
                )
            )

        # Check for account numbers with impossible patterns
        if len(account_number) > 20 or len(account_number) < 4:
            alerts.append(
                HallucinationAlert(
                    type=HallucinationType.NONSENSICAL_ACCOUNT,
                    severity="medium",
                    description=f"Account number has unusual length: {len(account_number)} chars",
                    detected_value=account_number,
                    confidence=0.7,
                    source="length_validation",
                )
            )

        return alerts

    def _check_impossible_dates(
        self, metadata: Dict[str, Any]
    ) -> List[HallucinationAlert]:
        """Check for impossible or nonsensical dates."""
        alerts = []

        # Check statement period
        statement_period = metadata.get("statement_period", "")
        if statement_period:
            # Check for future dates (statements shouldn't be from the future)
            from datetime import datetime

            # Extract years from statement period (match 1800s, 1900s, 2000s)
            years = re.findall(r"\b(1[89]\d{2}|20\d{2})\b", statement_period)
            current_year = datetime.now().year

            for year_str in years:
                year = int(year_str)
                if year > current_year + 1:  # Allow 1 year buffer for edge cases
                    alerts.append(
                        HallucinationAlert(
                            type=HallucinationType.IMPOSSIBLE_DATES,
                            severity="high",
                            description=f"Statement period contains future year: {year}",
                            detected_value=year,
                            expected_value=f"≤{current_year}",
                            confidence=0.9,
                            source="date_validation",
                        )
                    )
                elif year < 1950:  # Bank statements before 1950 are highly unlikely
                    alerts.append(
                        HallucinationAlert(
                            type=HallucinationType.IMPOSSIBLE_DATES,
                            severity="medium",
                            description=f"Statement period contains unrealistic historical year: {year}",
                            detected_value=year,
                            expected_value="≥1950",
                            confidence=0.8,
                            source="date_validation",
                        )
                    )

        return alerts

    def _check_inconsistent_metadata(
        self, metadata: Dict[str, Any], document_text: str
    ) -> List[HallucinationAlert]:
        """Check for internally inconsistent metadata."""
        alerts = []

        # Check if account type matches bank type
        bank_name = metadata.get("bank_name", "").lower()
        account_type = metadata.get("account_type", "").lower()

        # Example: Credit unions shouldn't have "visa" accounts directly
        if "credit union" in bank_name and "visa" in account_type:
            alerts.append(
                HallucinationAlert(
                    type=HallucinationType.INCONSISTENT_DATA,
                    severity="low",
                    description="Credit union with Visa account type may be inconsistent",
                    detected_value=f"{bank_name} + {account_type}",
                    confidence=0.5,
                    source="consistency_validation",
                )
            )

        return alerts

    def log_hallucination_alerts(
        self, alerts: List[HallucinationAlert], context: str = ""
    ):
        """Log all detected hallucination alerts."""
        if not alerts:
            logger.info(f"✅ No hallucinations detected {context}")
            return

        # Group by severity
        critical_alerts = [a for a in alerts if a.severity == "critical"]
        high_alerts = [a for a in alerts if a.severity == "high"]
        medium_alerts = [a for a in alerts if a.severity == "medium"]
        low_alerts = [a for a in alerts if a.severity == "low"]

        # Log summary
        logger.warning(
            f"🚨 HALLUCINATION DETECTION {context}: {len(alerts)} alerts "
            f"(Critical: {len(critical_alerts)}, High: {len(high_alerts)}, "
            f"Medium: {len(medium_alerts)}, Low: {len(low_alerts)})"
        )

        # Log detailed alerts
        for alert in alerts:
            level = (
                logger.error
                if alert.severity == "critical"
                else logger.warning
                if alert.severity == "high"
                else logger.info
            )

            level(
                f"🚨 {alert.severity.upper()} HALLUCINATION [{alert.type.value}]: "
                f"{alert.description} | Detected: {alert.detected_value} | "
                f"Source: {alert.source} | Confidence: {alert.confidence}"
            )

        # Store alerts for reporting
        self.alerts.extend(alerts)

    def should_reject_response(self, alerts: List[HallucinationAlert]) -> bool:
        """Determine if the response should be rejected due to hallucinations."""
        critical_count = sum(1 for a in alerts if a.severity == "critical")
        high_count = sum(1 for a in alerts if a.severity == "high")

        # Reject if any critical hallucinations or too many high-severity ones
        return critical_count > 0 or high_count >= 3

    def get_hallucination_summary(self) -> Dict[str, Any]:
        """Get a summary of all detected hallucinations."""
        if not self.alerts:
            return {"status": "clean", "total_alerts": 0}

        summary = {
            "status": "hallucinations_detected",
            "total_alerts": len(self.alerts),
            "by_severity": {},
            "by_type": {},
            "rejection_recommended": self.should_reject_response(self.alerts),
        }

        for alert in self.alerts:
            # Count by severity
            summary["by_severity"][alert.severity] = (
                summary["by_severity"].get(alert.severity, 0) + 1
            )

            # Count by type
            summary["by_type"][alert.type.value] = (
                summary["by_type"].get(alert.type.value, 0) + 1
            )

        return summary

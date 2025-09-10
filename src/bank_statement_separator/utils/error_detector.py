"""Error detection utility for workflow processing errors."""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..config import Config

logger = logging.getLogger(__name__)

# Constants for boundary detection validation
MIN_PAGES_PER_STATEMENT = 2  # Minimum pages for a valid statement
MAX_PAGES_PER_STATEMENT = 50  # Maximum pages for a valid statement

# Constants for metadata validation
FALLBACK_ACCOUNT_PREFIX = "ACCT"  # Prefix used for fallback account numbers


@dataclass
class ProcessingError:
    """Represents a detected processing error."""

    type: str
    severity: str  # low, medium, high, critical
    description: str
    step: str
    details: Optional[Dict[str, Any]] = None


class ErrorDetector:
    """Detects processing errors during workflow execution."""

    def __init__(self, config: Config):
        """Initialize error detector with configuration.

        Args:
            config: Application configuration
        """
        self.config = config

    def detect_errors(self, workflow_state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect processing errors from workflow state.

        Args:
            workflow_state: Current workflow state

        Returns:
            List of detected processing errors
        """
        errors = []

        # Check if error detection is enabled
        if not self.config.paperless_error_detection_enabled:
            return errors

        current_step = workflow_state.get("current_step", "")

        # Detect LLM analysis failures
        errors.extend(self._detect_llm_failures(workflow_state))

        # Detect boundary detection issues
        errors.extend(self._detect_boundary_issues(workflow_state))

        # Detect PDF processing errors
        errors.extend(self._detect_pdf_errors(workflow_state))

        # Detect metadata extraction problems
        errors.extend(self._detect_metadata_issues(workflow_state))

        # Detect file output issues
        errors.extend(self._detect_output_issues(workflow_state))

        # Detect validation failures
        errors.extend(self._detect_validation_failures(workflow_state))

        # Log detected errors
        if errors:
            logger.warning(
                f"Detected {len(errors)} processing errors in step '{current_step}'"
            )
            for error in errors:
                logger.debug(
                    f"Error detected: {error['type']} - {error['description']}"
                )

        return errors

    def _detect_llm_failures(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect LLM analysis failures."""
        errors = []
        current_step = state.get("current_step", "")
        error_message = state.get("error_message", "")

        # Check for explicit LLM-related error steps
        if "error" in current_step and any(
            keyword in error_message.lower()
            for keyword in ["llm", "api", "model", "openai", "ollama"]
        ):
            errors.append(
                {
                    "type": "llm_analysis_failure",
                    "severity": "high",
                    "description": f"LLM analysis failed: {error_message}",
                    "step": current_step,
                    "details": {"error_message": error_message},
                }
            )

        # Check for boundary detection fallback (indicates LLM failure)
        boundaries = state.get("detected_boundaries", [])
        if boundaries and any(
            b.get("reasoning") == "Fallback page-based segmentation" for b in boundaries
        ):
            errors.append(
                {
                    "type": "llm_analysis_failure",
                    "severity": "medium",
                    "description": "LLM boundary detection failed, used fallback method",
                    "step": "statement_detection",
                    "details": {
                        "fallback_boundaries": len(
                            [
                                b
                                for b in boundaries
                                if b.get("reasoning")
                                == "Fallback page-based segmentation"
                            ]
                        )
                    },
                }
            )

        return errors

    def _detect_boundary_issues(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect boundary detection issues."""
        errors = []
        boundaries = state.get("detected_boundaries", [])

        if not boundaries:
            return errors

        # Check for low confidence boundaries and suspicious patterns in single loop
        low_confidence_boundaries = []
        suspicious_boundaries = []

        for boundary in boundaries:
            # Check confidence
            if (
                boundary.get("confidence", 1.0)
                < self.config.paperless_error_tag_threshold
            ):
                low_confidence_boundaries.append(boundary)

            # Check for suspicious patterns (very small or very large segments)
            start_page = boundary.get("start_page", 1)
            end_page = boundary.get("end_page", 1)
            page_count = end_page - start_page + 1

            if (
                page_count < MIN_PAGES_PER_STATEMENT
                or page_count > MAX_PAGES_PER_STATEMENT
            ):
                suspicious_boundaries.append(boundary)

        if low_confidence_boundaries:
            avg_confidence = sum(
                b.get("confidence", 0) for b in low_confidence_boundaries
            ) / len(low_confidence_boundaries)
            errors.append(
                {
                    "type": "low_confidence_boundaries",
                    "severity": "high" if avg_confidence < 0.3 else "medium",
                    "description": f"Found {len(low_confidence_boundaries)} boundaries with low confidence (avg: {avg_confidence:.2f})",
                    "step": "statement_detection",
                    "details": {
                        "low_confidence_count": len(low_confidence_boundaries),
                        "average_confidence": avg_confidence,
                        "threshold": self.config.paperless_error_tag_threshold,
                    },
                }
            )

        if suspicious_boundaries:
            errors.append(
                {
                    "type": "suspicious_boundary_patterns",
                    "severity": "medium",
                    "description": f"Found {len(suspicious_boundaries)} boundaries with suspicious page counts",
                    "step": "statement_detection",
                    "details": {"suspicious_boundaries": suspicious_boundaries},
                }
            )

        return errors

    def _detect_pdf_errors(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect PDF processing errors."""
        errors = []
        current_step = state.get("current_step", "")
        error_message = state.get("error_message", "")

        # Check for PDF processing error steps
        if current_step in ["pdf_ingestion_error", "pdf_generation_error"]:
            severity = "critical" if "pdf_ingestion" in current_step else "high"
            errors.append(
                {
                    "type": "pdf_processing_error",
                    "severity": severity,
                    "description": f"PDF processing failed: {error_message}",
                    "step": current_step,
                    "details": {"error_message": error_message},
                }
            )

        # Check for missing generated files
        generated_files = state.get("generated_files", [])
        expected_statements = state.get("total_statements_found", 0)

        if expected_statements > 0 and len(generated_files) < expected_statements:
            missing_count = expected_statements - len(generated_files)
            errors.append(
                {
                    "type": "incomplete_pdf_generation",
                    "severity": "high",
                    "description": f"Generated {len(generated_files)}/{expected_statements} expected PDF files",
                    "step": "pdf_generation",
                    "details": {
                        "expected_files": expected_statements,
                        "generated_files": len(generated_files),
                        "missing_count": missing_count,
                    },
                }
            )

        return errors

    def _detect_metadata_issues(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect metadata extraction problems."""
        errors = []
        current_step = state.get("current_step", "")
        error_message = state.get("error_message", "")

        # Check for metadata extraction error step
        if current_step == "metadata_extraction_error":
            errors.append(
                {
                    "type": "metadata_extraction_failure",
                    "severity": "high",
                    "description": f"Metadata extraction failed: {error_message}",
                    "step": current_step,
                    "details": {"error_message": error_message},
                }
            )

        # Check for low confidence metadata
        extracted_metadata = state.get("extracted_metadata", [])
        if extracted_metadata:
            low_confidence_metadata = [
                m
                for m in extracted_metadata
                if m.get("confidence", 1.0) < self.config.paperless_error_tag_threshold
            ]

            if low_confidence_metadata:
                avg_confidence = sum(
                    m.get("confidence", 0) for m in low_confidence_metadata
                ) / len(low_confidence_metadata)
                errors.append(
                    {
                        "type": "metadata_extraction_failure",
                        "severity": "medium",
                        "description": f"Low confidence metadata extraction for {len(low_confidence_metadata)} statements (avg: {avg_confidence:.2f})",
                        "step": "metadata_extraction",
                        "details": {
                            "low_confidence_count": len(low_confidence_metadata),
                            "average_confidence": avg_confidence,
                            "threshold": self.config.paperless_error_tag_threshold,
                        },
                    }
                )

            # Check for default/fallback metadata (indicates extraction failure)
            fallback_metadata = [
                m
                for m in extracted_metadata
                if m.get("account_number", "").startswith(FALLBACK_ACCOUNT_PREFIX)
            ]
            if fallback_metadata:
                errors.append(
                    {
                        "type": "metadata_extraction_failure",
                        "severity": "medium",
                        "description": f"Used fallback metadata for {len(fallback_metadata)} statements",
                        "step": "metadata_extraction",
                        "details": {"fallback_count": len(fallback_metadata)},
                    }
                )

        return errors

    def _detect_output_issues(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect file output issues."""
        errors = []
        current_step = state.get("current_step", "")

        # Check for file organization errors
        if current_step == "file_organization_error":
            error_message = state.get("error_message", "")
            errors.append(
                {
                    "type": "file_output_error",
                    "severity": "high",
                    "description": f"File organization failed: {error_message}",
                    "step": current_step,
                    "details": {"error_message": error_message},
                }
            )

        # Check for skipped fragments due to low confidence
        skipped_fragments = state.get("skipped_fragments", 0)
        if skipped_fragments > 0:
            skipped_pages = state.get("skipped_pages", 0)
            errors.append(
                {
                    "type": "skipped_low_confidence_fragments",
                    "severity": "medium",
                    "description": f"Skipped {skipped_fragments} fragments ({skipped_pages} pages) due to low confidence",
                    "step": "pdf_generation",
                    "details": {
                        "skipped_fragments": skipped_fragments,
                        "skipped_pages": skipped_pages,
                    },
                }
            )

        return errors

    def _detect_validation_failures(
        self, state: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Detect validation failures."""
        errors = []
        current_step = state.get("current_step", "")
        validation_results = state.get("validation_results", {})

        # Check for validation error step
        if current_step == "output_validation_error":
            error_message = state.get("error_message", "")
            errors.append(
                {
                    "type": "validation_failure",
                    "severity": "critical",
                    "description": f"Output validation failed: {error_message}",
                    "step": current_step,
                    "details": {"error_message": error_message},
                }
            )

        # Check validation results for specific failures
        if validation_results and not validation_results.get("is_valid", True):
            failed_checks = []
            checks = validation_results.get("checks", {})

            for check_name, check_result in checks.items():
                if check_result.get("status") == "failed":
                    failed_checks.append(check_name)

            if failed_checks:
                errors.append(
                    {
                        "type": "validation_failure",
                        "severity": "high",
                        "description": f"Validation checks failed: {', '.join(failed_checks)}",
                        "step": "output_validation",
                        "details": {
                            "failed_checks": failed_checks,
                            "validation_results": validation_results,
                        },
                    }
                )

        return errors

    def should_tag_errors(self, errors: List[Dict[str, Any]]) -> bool:
        """Determine if errors warrant tagging based on severity and configuration.

        Args:
            errors: List of detected errors

        Returns:
            bool: True if errors should be tagged
        """
        if not errors or not self.config.paperless_error_detection_enabled:
            return False

        # Check if any errors meet the severity threshold
        severity_levels = self.config.paperless_error_severity_levels
        for error in errors:
            if error["severity"] in severity_levels:
                return True

        return False

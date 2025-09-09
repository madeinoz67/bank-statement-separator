"""Comprehensive error handling utilities for document processing failures."""

import json
import logging
import shutil
import sys
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels for categorizing failures."""

    RECOVERABLE = "recoverable"  # Can continue with warnings
    CRITICAL = "critical"  # Must stop processing
    VALIDATION_FAILURE = "validation_failure"  # Post-processing issues


class ProcessingError(Exception):
    """Base exception for processing errors."""

    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.CRITICAL):
        super().__init__(message)
        self.severity = severity


class TransientProcessingError(ProcessingError):
    """Exception for transient failures that can be retried."""

    def __init__(self, message: str):
        super().__init__(message, ErrorSeverity.RECOVERABLE)


class CriticalProcessingError(ProcessingError):
    """Exception for critical failures that should not be retried."""

    def __init__(self, message: str):
        super().__init__(message, ErrorSeverity.CRITICAL)


class ValidationError(ProcessingError):
    """Exception for validation failures."""

    def __init__(
        self, message: str, severity: ErrorSeverity = ErrorSeverity.VALIDATION_FAILURE
    ):
        super().__init__(message, severity)


class ErrorHandler:
    """Comprehensive error handling for document processing workflows."""

    def __init__(self, config):
        """Initialize error handler with configuration.

        Args:
            config: Application configuration object
        """
        self.config = config
        self.quarantine_dir = self._get_quarantine_directory()
        self.error_report_dir = self._get_error_report_directory()
        self._ensure_directories()

    def _get_quarantine_directory(self) -> Path:
        """Get quarantine directory path."""
        if self.config.quarantine_directory:
            return Path(self.config.quarantine_directory)
        else:
            return Path(self.config.default_output_dir) / "quarantine"

    def _get_error_report_directory(self) -> Path:
        """Get error report directory path."""
        if self.config.error_report_directory:
            return Path(self.config.error_report_directory)
        else:
            return self.quarantine_dir / "reports"

    def _ensure_directories(self):
        """Ensure quarantine and error report directories exist."""
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        if self.config.enable_error_reporting:
            self.error_report_dir.mkdir(parents=True, exist_ok=True)

    def validate_document_format(self, file_path: str) -> Dict[str, Any]:
        """Pre-processing validation of document format and content.

        Args:
            file_path: Path to the document to validate

        Returns:
            Dict containing validation results
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "document_type": "unknown",
            "file_age_days": None,
            "text_content_ratio": None,
        }

        file_path_obj = Path(file_path)

        try:
            # Check file existence
            if not file_path_obj.exists():
                validation_result["is_valid"] = False
                validation_result["errors"].append("File does not exist")
                return validation_result

            # Check file extension
            if file_path_obj.suffix.lower() not in self.config.allowed_file_extensions:
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    f"File extension {file_path_obj.suffix} not allowed"
                )
                return validation_result

            # Check file age if configured
            if self.config.max_file_age_days:
                file_age = datetime.now() - datetime.fromtimestamp(
                    file_path_obj.stat().st_mtime
                )
                validation_result["file_age_days"] = file_age.days

                if file_age.days > self.config.max_file_age_days:
                    if self.config.validation_strictness == "strict":
                        validation_result["is_valid"] = False
                        validation_result["errors"].append(
                            f"File is {file_age.days} days old (max: {self.config.max_file_age_days})"
                        )
                    else:
                        validation_result["warnings"].append(
                            f"File is {file_age.days} days old"
                        )

            # PDF-specific validation
            if file_path_obj.suffix.lower() == ".pdf":
                pdf_validation = self._validate_pdf_document(file_path)
                validation_result.update(pdf_validation)

        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(f"Document validation error: {str(e)}")

        return validation_result

    def _validate_pdf_document(self, file_path: str) -> Dict[str, Any]:
        """Validate PDF document specifics.

        Args:
            file_path: Path to PDF file

        Returns:
            Dict containing PDF-specific validation results
        """
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "document_type": "pdf",
            "text_content_ratio": 0.0,
        }

        try:
            import fitz

            doc = fitz.open(file_path)

            # Check if document is encrypted
            if doc.needs_pass:
                result["is_valid"] = False
                result["errors"].append("Document is password protected")
                return result

            # Check page count
            if len(doc) == 0:
                result["is_valid"] = False
                result["errors"].append("Document has no pages")
                return result

            if len(doc) < self.config.min_pages_per_statement:
                if self.config.validation_strictness == "strict":
                    result["is_valid"] = False
                    result["errors"].append(
                        f"Document has {len(doc)} pages (minimum: {self.config.min_pages_per_statement})"
                    )
                else:
                    result["warnings"].append(
                        f"Document has fewer pages than typical ({len(doc)} pages)"
                    )

            # Check text content if required
            if self.config.require_text_content:
                pages_with_text = 0
                total_pages = len(doc)

                # Sample pages for text content
                sample_pages = min(5, total_pages)  # Check up to 5 pages
                pages_to_check = [
                    i * (total_pages // sample_pages) for i in range(sample_pages)
                ]
                if total_pages - 1 not in pages_to_check:
                    pages_to_check.append(total_pages - 1)  # Always check last page

                for page_num in pages_to_check:
                    if page_num < total_pages:
                        page_text = doc[page_num].get_text().strip()
                        if page_text and len(page_text) > 50:  # Require meaningful text
                            pages_with_text += 1

                text_content_ratio = pages_with_text / len(pages_to_check)
                result["text_content_ratio"] = text_content_ratio

                if text_content_ratio < self.config.min_text_content_ratio:
                    if self.config.validation_strictness == "strict":
                        result["is_valid"] = False
                        result["errors"].append(
                            f"Insufficient text content ({text_content_ratio:.1%} < {self.config.min_text_content_ratio:.1%})"
                        )
                    else:
                        result["warnings"].append(
                            "Document appears to be mostly image-based"
                        )

            # Detect document type based on content
            if len(doc) > 0:
                first_page_text = doc[0].get_text().lower()
                if any(
                    keyword in first_page_text
                    for keyword in ["statement", "account", "balance", "transaction"]
                ):
                    result["document_type"] = "bank_statement"

            doc.close()

        except Exception as e:
            result["is_valid"] = False
            result["errors"].append(f"PDF validation error: {str(e)}")

        return result

    def move_to_quarantine(
        self,
        input_file_path: str,
        error_reason: str,
        workflow_state: Optional[Dict] = None,
    ) -> str:
        """Move failed document to quarantine directory with metadata.

        Args:
            input_file_path: Path to the failed document
            error_reason: Reason for quarantine
            workflow_state: Optional workflow state for additional context

        Returns:
            Path to quarantined file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        input_path = Path(input_file_path)
        quarantine_file = self.quarantine_dir / f"failed_{timestamp}_{input_path.name}"

        # Ensure unique filename
        counter = 1
        while quarantine_file.exists():
            name_parts = input_path.stem, timestamp, counter, input_path.suffix
            quarantine_file = (
                self.quarantine_dir
                / f"failed_{name_parts[0]}_{name_parts[1]}_{name_parts[2]}{name_parts[3]}"
            )
            counter += 1

        try:
            # Move the file
            shutil.move(str(input_path), str(quarantine_file))

            # Create error report if enabled
            if self.config.enable_error_reporting:
                self._create_error_report(
                    quarantine_file, error_reason, workflow_state, timestamp
                )

            logger.warning(
                f"Document quarantined: {quarantine_file} (Reason: {error_reason})"
            )
            return str(quarantine_file)

        except Exception as e:
            logger.error(f"Failed to quarantine document {input_file_path}: {e}")
            raise ProcessingError(f"Quarantine operation failed: {e}")

    def _create_error_report(
        self,
        quarantine_file: Path,
        error_reason: str,
        workflow_state: Optional[Dict],
        timestamp: str,
    ):
        """Create detailed error report for quarantined document."""
        error_report = {
            "timestamp": datetime.now().isoformat(),
            "quarantine_file": str(quarantine_file),
            "original_file": workflow_state.get("input_file_path")
            if workflow_state
            else "unknown",
            "error_reason": error_reason,
            "workflow_step": workflow_state.get("current_step")
            if workflow_state
            else "unknown",
            "processing_time_seconds": workflow_state.get("processing_time_seconds")
            if workflow_state
            else None,
            "total_pages": workflow_state.get("total_pages", 0)
            if workflow_state
            else 0,
            "statements_detected": workflow_state.get("total_statements_found", 0)
            if workflow_state
            else 0,
            "validation_results": workflow_state.get("validation_results")
            if workflow_state
            else None,
            "system_info": {
                "has_openai_key": bool(self.config.openai_api_key)
                if hasattr(self.config, "openai_api_key")
                else False,
                "paperless_enabled": getattr(self.config, "paperless_enabled", False),
                "python_version": sys.version,
                "validation_strictness": self.config.validation_strictness,
            },
            "recovery_suggestions": self._get_recovery_suggestions(
                error_reason, workflow_state
            ),
        }

        # Save error report
        report_file = self.error_report_dir / f"error_report_{timestamp}.json"
        try:
            with open(report_file, "w") as f:
                json.dump(error_report, f, indent=2)
            logger.info(f"Error report created: {report_file}")
        except Exception as e:
            logger.error(f"Failed to create error report: {e}")

    def _get_recovery_suggestions(
        self, error_reason: str, workflow_state: Optional[Dict]
    ) -> List[str]:
        """Generate recovery suggestions based on error type.

        Args:
            error_reason: The error that occurred
            workflow_state: Optional workflow state for context

        Returns:
            List of actionable recovery suggestions
        """
        suggestions = []
        error_lower = error_reason.lower()

        if "password" in error_lower or "encrypted" in error_lower:
            suggestions.extend(
                [
                    "Remove password protection from the PDF",
                    "Use a PDF tool to unlock the document",
                    "Contact the document source for an unlocked version",
                ]
            )

        if "page count" in error_lower or "pages" in error_lower:
            suggestions.extend(
                [
                    "Verify the PDF is not corrupted",
                    "Check if pages are missing from the original document",
                    "Try re-downloading or re-scanning the document",
                ]
            )

        if "openai" in error_lower or "api" in error_lower:
            suggestions.extend(
                [
                    "Verify OPENAI_API_KEY is set correctly",
                    "Check API quota and billing status",
                    "Ensure network connectivity to OpenAI services",
                    "Try using fallback processing if enabled",
                ]
            )

        if "file size" in error_lower:
            suggestions.extend(
                [
                    "Check for PDF corruption or compression issues",
                    "Verify the file was completely downloaded/transferred",
                    "Try processing with a PDF repair tool",
                ]
            )

        if "text content" in error_lower or "image" in error_lower:
            suggestions.extend(
                [
                    "Run OCR on the document to extract text",
                    "Verify document is not purely image-based",
                    "Check if document was scanned at sufficient resolution",
                ]
            )

        if "validation" in error_lower:
            suggestions.extend(
                [
                    "Review validation strictness settings",
                    "Check if document meets minimum requirements",
                    "Consider processing in lenient mode",
                ]
            )

        # General suggestions if no specific matches
        if not suggestions:
            suggestions.extend(
                [
                    "Check document integrity and format",
                    "Verify configuration settings",
                    "Review logs for additional error details",
                    "Try processing a known-good document to verify system status",
                ]
            )

        return suggestions

    def handle_validation_failure(
        self, workflow_state: Dict, validation_results: Dict
    ) -> Dict:
        """Handle validation failures with recovery options.

        Args:
            workflow_state: Current workflow state
            validation_results: Results from validation checks

        Returns:
            Updated workflow state
        """
        error_details = validation_results.get("error_details", [])
        failed_checks = [
            check
            for check, result in validation_results.get("checks", {}).items()
            if result.get("status") == "failed"
        ]

        # Categorize validation failures based on strictness
        recoverable_errors = ["file_size", "content_sampling"]
        critical_errors = ["file_count", "page_count"]

        # Adjust based on validation strictness
        if self.config.validation_strictness == "lenient":
            recoverable_errors.extend(
                ["page_count"]
            )  # Allow page count mismatches in lenient mode
        elif self.config.validation_strictness == "strict":
            critical_errors.extend(
                ["file_size"]
            )  # Treat file size issues as critical in strict mode

        # Determine if recovery is possible
        has_critical_errors = any(error in critical_errors for error in failed_checks)

        if not has_critical_errors and self.config.continue_on_validation_warnings:
            # Recoverable - mark with warnings but continue
            workflow_state["validation_warnings"] = error_details
            workflow_state["current_step"] = "output_validation_warning"
            logger.warning(f"Validation warnings (continuing): {error_details}")
            return workflow_state

        elif self.config.auto_quarantine_critical_failures:
            # Critical failure - quarantine and stop
            quarantine_path = self.move_to_quarantine(
                workflow_state["input_file_path"],
                f"Validation failure: {error_details}",
                workflow_state,
            )

            workflow_state["error_message"] = (
                f"Critical validation failure: {error_details}"
            )
            workflow_state["current_step"] = "output_validation_critical_error"
            workflow_state["quarantine_path"] = quarantine_path
            return workflow_state

        else:
            # Critical failure but no quarantine - just error
            workflow_state["error_message"] = f"Validation failure: {error_details}"
            workflow_state["current_step"] = "output_validation_error"
            return workflow_state

    def handle_processing_with_retry(
        self, processing_func, workflow_state: Dict, context: str = "processing"
    ) -> Dict:
        """Execute processing function with retry logic.

        Args:
            processing_func: Function to execute with retry
            workflow_state: Current workflow state
            context: Context description for logging

        Returns:
            Updated workflow state
        """
        for attempt in range(self.config.max_retry_attempts + 1):
            try:
                return processing_func(workflow_state)

            except TransientProcessingError as e:
                if attempt < self.config.max_retry_attempts:
                    logger.warning(
                        f"{context} attempt {attempt + 1} failed, retrying: {str(e)}"
                    )
                    continue
                else:
                    error_msg = f"{context} failed after {self.config.max_retry_attempts + 1} attempts: {str(e)}"
                    workflow_state["error_message"] = error_msg
                    workflow_state["current_step"] = f"{context}_retry_exhausted"

                    if self.config.auto_quarantine_critical_failures:
                        quarantine_path = self.move_to_quarantine(
                            workflow_state["input_file_path"], error_msg, workflow_state
                        )
                        workflow_state["quarantine_path"] = quarantine_path

                    return workflow_state

            except CriticalProcessingError as e:
                # Don't retry critical errors
                error_msg = f"Critical {context} error: {str(e)}"
                workflow_state["error_message"] = error_msg
                workflow_state["current_step"] = f"{context}_critical_error"

                if self.config.auto_quarantine_critical_failures:
                    quarantine_path = self.move_to_quarantine(
                        workflow_state["input_file_path"], error_msg, workflow_state
                    )
                    workflow_state["quarantine_path"] = quarantine_path

                return workflow_state

            except Exception as e:
                # Treat unknown exceptions as critical
                error_msg = f"Unexpected {context} error: {str(e)}"
                workflow_state["error_message"] = error_msg
                workflow_state["current_step"] = f"{context}_unexpected_error"

                if self.config.auto_quarantine_critical_failures:
                    quarantine_path = self.move_to_quarantine(
                        workflow_state["input_file_path"], error_msg, workflow_state
                    )
                    workflow_state["quarantine_path"] = quarantine_path

                return workflow_state

        return workflow_state

    def cleanup_partial_outputs(self, workflow_state: Dict):
        """Clean up partial outputs from failed processing.

        Args:
            workflow_state: Current workflow state
        """
        if not self.config.preserve_failed_outputs:
            generated_files = workflow_state.get("generated_files", [])

            for file_path in generated_files:
                try:
                    file_path_obj = Path(file_path)
                    if file_path_obj.exists():
                        file_path_obj.unlink()
                        logger.debug(f"Cleaned up partial output: {file_path}")
                except Exception as e:
                    logger.warning(
                        f"Failed to clean up partial output {file_path}: {e}"
                    )

    def get_quarantine_summary(self) -> Dict[str, Any]:
        """Get summary of quarantined documents.

        Returns:
            Dict containing quarantine statistics and recent failures
        """
        if not self.quarantine_dir.exists():
            return {"total_quarantined": 0, "recent_failures": []}

        quarantined_files = list(self.quarantine_dir.glob("failed_*.pdf"))

        # Get recent failures (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_failures = []

        for file_path in quarantined_files:
            try:
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if file_time > recent_cutoff:
                    recent_failures.append(
                        {
                            "file": file_path.name,
                            "timestamp": file_time.isoformat(),
                            "size_mb": file_path.stat().st_size / (1024 * 1024),
                        }
                    )
            except Exception as e:
                logger.warning(f"Error reading quarantine file {file_path}: {e}")

        return {
            "total_quarantined": len(quarantined_files),
            "recent_failures": sorted(
                recent_failures, key=lambda x: x["timestamp"], reverse=True
            ),
            "quarantine_directory": str(self.quarantine_dir),
        }

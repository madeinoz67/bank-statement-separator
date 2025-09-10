"""Error tagging utility for applying error tags to Paperless documents."""

import logging
from typing import Any, Dict, List

from ..config import Config
from .paperless_client import PaperlessClient

logger = logging.getLogger(__name__)


class ErrorTagger:
    """Applies error tags to Paperless documents with processing issues."""

    def __init__(self, config: Config):
        """Initialize error tagger with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        self.paperless_client = PaperlessClient(config)

    def apply_error_tags(
        self, errors: List[Dict[str, Any]], upload_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply error tags to documents with processing issues.

        Args:
            errors: List of detected processing errors
            upload_results: Results from document uploads

        Returns:
            Dict containing tagging results
        """
        result = {
            "success": True,
            "tagged_documents": 0,
            "skipped_documents": 0,
            "errors": [],
            "details": [],
        }

        # Check if error tagging is enabled and paperless is available
        if (
            not self.config.paperless_error_detection_enabled
            or not self.paperless_client.is_enabled()
        ):
            result["skipped_documents"] = len(upload_results.get("uploads", []))
            logger.debug("Error tagging disabled or paperless not available")
            return result

        # Check if we have error tags configured
        if not self.config.paperless_error_tags:
            result["skipped_documents"] = len(upload_results.get("uploads", []))
            logger.debug("No error tags configured")
            return result

        # Check if errors warrant tagging based on severity
        if not self._should_tag_errors(errors):
            result["skipped_documents"] = len(upload_results.get("uploads", []))
            logger.debug("No errors meet severity threshold for tagging")
            return result

        # Get successfully uploaded documents
        uploaded_documents = upload_results.get("uploads", [])
        if not uploaded_documents:
            logger.debug("No uploaded documents to tag")
            return result

        # Apply error tags to documents
        if self.config.paperless_error_batch_tagging:
            return self._apply_batch_error_tags(errors, uploaded_documents)
        else:
            return self._apply_individual_error_tags(errors, uploaded_documents)

    def _should_tag_errors(self, errors: List[Dict[str, Any]]) -> bool:
        """Determine if errors warrant tagging based on severity.

        Args:
            errors: List of detected errors

        Returns:
            bool: True if errors should be tagged
        """
        if not errors:
            return False

        # Check if any errors meet the severity threshold
        severity_levels = self.config.paperless_error_severity_levels
        for error in errors:
            if error.get("severity") in severity_levels:
                return True

        return False

    def _apply_batch_error_tags(
        self, errors: List[Dict[str, Any]], uploaded_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply error tags to all documents in batch.

        Args:
            errors: List of detected errors
            uploaded_documents: List of successfully uploaded documents

        Returns:
            Dict containing batch tagging results
        """
        result = {
            "success": True,
            "tagged_documents": 0,
            "skipped_documents": 0,
            "errors": [],
            "details": [],
        }

        # Collect all document IDs for batch processing
        document_ids = []
        for upload in uploaded_documents:
            if upload.get("success") and upload.get("document_id"):
                document_ids.append(upload["document_id"])

        if not document_ids:
            result["skipped_documents"] = len(uploaded_documents)
            logger.warning("No document IDs available for batch error tagging")
            return result

        # Apply error tags to all documents
        try:
            error_tags = self._generate_error_tags(errors)

            for document_id in document_ids:
                try:
                    tag_result = self.paperless_client.apply_tags_to_document(
                        document_id,
                        error_tags,
                        wait_time=self.config.paperless_tag_wait_time,
                    )

                    if tag_result.get("success"):
                        result["tagged_documents"] += 1
                        result["details"].append(
                            {
                                "document_id": document_id,
                                "tags_applied": tag_result.get("tags_applied", 0),
                                "tags": error_tags,
                            }
                        )
                        logger.info(
                            f"Applied {len(error_tags)} error tags to document {document_id}"
                        )
                    else:
                        result["success"] = False
                        error_msg = tag_result.get("error", "Unknown tagging error")
                        result["errors"].append(
                            f"Failed to tag document {document_id}: {error_msg}"
                        )
                        logger.warning(
                            f"Failed to apply error tags to document {document_id}: {error_msg}"
                        )

                except Exception as e:
                    result["success"] = False
                    result["errors"].append(
                        f"Exception tagging document {document_id}: {str(e)}"
                    )
                    logger.error(
                        f"Exception applying error tags to document {document_id}: {e}"
                    )

        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Batch error tagging failed: {str(e)}")
            logger.error(f"Batch error tagging failed: {e}")

        return result

    def _apply_individual_error_tags(
        self, errors: List[Dict[str, Any]], uploaded_documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply error tags to individual documents based on specific errors.

        Args:
            errors: List of detected errors
            uploaded_documents: List of successfully uploaded documents

        Returns:
            Dict containing individual tagging results
        """
        result = {
            "success": True,
            "tagged_documents": 0,
            "skipped_documents": 0,
            "errors": [],
            "details": [],
        }

        # For individual tagging, we apply the same error tags to all documents
        # since errors are typically workflow-wide issues
        # In the future, this could be enhanced to map specific errors to specific documents

        for upload in uploaded_documents:
            if not upload.get("success") or not upload.get("document_id"):
                result["skipped_documents"] += 1
                continue

            document_id = upload["document_id"]

            try:
                error_tags = self._generate_error_tags(errors)

                tag_result = self.paperless_client.apply_tags_to_document(
                    document_id,
                    error_tags,
                    wait_time=self.config.paperless_tag_wait_time,
                )

                if tag_result.get("success"):
                    result["tagged_documents"] += 1
                    result["details"].append(
                        {
                            "document_id": document_id,
                            "tags_applied": tag_result.get("tags_applied", 0),
                            "tags": error_tags,
                        }
                    )
                    logger.info(
                        f"Applied {len(error_tags)} error tags to document {document_id}"
                    )
                else:
                    result["success"] = False
                    error_msg = tag_result.get("error", "Unknown tagging error")
                    result["errors"].append(
                        f"Failed to tag document {document_id}: {error_msg}"
                    )
                    logger.warning(
                        f"Failed to apply error tags to document {document_id}: {error_msg}"
                    )

            except Exception as e:
                result["success"] = False
                result["errors"].append(
                    f"Exception tagging document {document_id}: {str(e)}"
                )
                logger.error(
                    f"Exception applying error tags to document {document_id}: {e}"
                )

        return result

    def _generate_error_tags(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Generate error tags based on detected errors.

        Args:
            errors: List of detected errors

        Returns:
            List of error tags to apply
        """
        tags = []

        # Always include base error tags from configuration
        if self.config.paperless_error_tags:
            tags.extend(self.config.paperless_error_tags)

        # Add specific error type tags if configured
        error_types = set(error.get("type") for error in errors if error.get("type"))

        # Map error types to additional tags
        error_type_mapping = {
            "llm_analysis_failure": ["error:llm"],
            "low_confidence_boundaries": ["error:confidence"],
            "pdf_processing_error": ["error:pdf"],
            "metadata_extraction_failure": ["error:metadata"],
            "validation_failure": ["error:validation"],
            "file_output_error": ["error:output"],
        }

        for error_type in error_types:
            if error_type in error_type_mapping:
                additional_tags = error_type_mapping[error_type]
                tags.extend(additional_tags)

        # Add severity-based tags using configured severity levels
        severities = set(
            error.get("severity") for error in errors if error.get("severity")
        )
        # Use configured severity levels for tagging, defaulting to ["high", "critical"] if not set
        configured_severities = getattr(
            self.config, "paperless_error_severity_levels", ["high", "critical"]
        )
        for severity in severities:
            if severity in configured_severities:
                tags.append(f"error:severity:{severity}")

        # Remove duplicates while preserving order
        return list(dict.fromkeys(tags))

    def create_error_summary(self, errors: List[Dict[str, Any]]) -> str:
        """Create a human-readable summary of detected errors.

        Args:
            errors: List of detected errors

        Returns:
            String summary of errors
        """
        if not errors:
            return "No errors detected"

        error_counts = {}
        severity_counts = {"low": 0, "medium": 0, "high": 0, "critical": 0}

        for error in errors:
            error_type = error.get("type", "unknown")
            severity = error.get("severity", "unknown")

            error_counts[error_type] = error_counts.get(error_type, 0) + 1
            if severity in severity_counts:
                severity_counts[severity] += 1

        # Build summary
        summary_parts = []

        # Overall count
        summary_parts.append(f"{len(errors)} processing errors detected")

        # Severity breakdown
        severity_parts = [
            f"{count} {severity}"
            for severity, count in severity_counts.items()
            if count > 0
        ]
        if severity_parts:
            summary_parts.append(f"Severity: {', '.join(severity_parts)}")

        # Error types
        if len(error_counts) <= 3:
            type_parts = [
                f"{count} {error_type.replace('_', ' ')}"
                for error_type, count in error_counts.items()
            ]
            summary_parts.append(f"Types: {', '.join(type_parts)}")
        else:
            summary_parts.append(f"Types: {len(error_counts)} different error types")

        return "; ".join(summary_parts)

"""Logging configuration for the application."""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logging(
    log_file: str,
    log_level: str = "INFO",
    max_bytes: int = 10_000_000,
    backup_count: int = 5,
):
    """
    Set up application logging with file rotation and console output.

    Args:
        log_file: Path to the log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
    """
    # Create log directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, log_level.upper()))

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(
        logging.WARNING
    )  # Only show warnings and errors on console

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Set specific loggers to appropriate levels
    logging.getLogger("bank_statement_separator").setLevel(
        getattr(logging, log_level.upper())
    )
    logging.getLogger("langchain").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


class AuditLogger:
    """Special logger for audit trail of document processing activities."""

    def __init__(self, audit_log_file: str):
        """
        Initialize audit logger.

        Args:
            audit_log_file: Path to audit log file
        """
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)

        # Create audit log directory if it doesn't exist
        audit_path = Path(audit_log_file)
        audit_path.parent.mkdir(parents=True, exist_ok=True)

        # Create audit formatter
        audit_formatter = logging.Formatter(
            fmt="%(asctime)s - AUDIT - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Create audit file handler with rotation
        audit_handler = logging.handlers.RotatingFileHandler(
            audit_log_file,
            maxBytes=50_000_000,  # 50MB
            backupCount=10,
        )
        audit_handler.setFormatter(audit_formatter)

        self.logger.addHandler(audit_handler)

    def log_file_access(
        self, file_path: str, operation: str, user: str = "system", success: bool = True
    ):
        """Log file access operations."""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"FILE_ACCESS - {operation} - {file_path} - User: {user} - Status: {status}"
        )

    def log_processing_start(
        self, input_file: str, output_dir: str, config_summary: dict
    ):
        """Log start of document processing."""
        self.logger.info(
            f"PROCESSING_START - Input: {input_file} - Output: {output_dir} - Config: {config_summary}"
        )

    def log_processing_complete(
        self,
        input_file: str,
        statements_found: int,
        files_created: list,
        processing_time: float,
    ):
        """Log completion of document processing."""
        self.logger.info(
            f"PROCESSING_COMPLETE - Input: {input_file} - Statements: {statements_found} - Files: {len(files_created)} - Time: {processing_time:.2f}s"
        )

    def log_processing_error(self, input_file: str, error_message: str, step: str):
        """Log processing errors."""
        self.logger.error(
            f"PROCESSING_ERROR - Input: {input_file} - Step: {step} - Error: {error_message}"
        )

    def log_llm_api_call(
        self, model: str, tokens_used: int, cost_estimate: Optional[float] = None
    ):
        """Log LLM API usage for cost tracking."""
        cost_info = f" - Cost: ${cost_estimate:.4f}" if cost_estimate else ""
        self.logger.info(
            f"LLM_API_CALL - Model: {model} - Tokens: {tokens_used}{cost_info}"
        )

    def log_security_event(self, event_type: str, details: str, severity: str = "INFO"):
        """Log security-related events."""
        self.logger.log(
            getattr(logging, severity.upper()),
            f"SECURITY_EVENT - {event_type} - {details}",
        )

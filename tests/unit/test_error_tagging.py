"""Tests for error detection and automatic tagging functionality."""

from unittest.mock import Mock, patch

import pytest

from src.bank_statement_separator.config import Config


class TestErrorDetection:
    """Test error detection during workflow execution."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration with error tagging enabled."""
        config = Mock(spec=Config)
        config.paperless_enabled = True
        config.paperless_url = "https://paperless.example.com"
        config.paperless_token = "test-token"
        config.paperless_error_tags = ["processing:needs-review"]
        config.paperless_error_tag_threshold = 0.5
        config.paperless_error_detection_enabled = True
        config.paperless_error_severity_levels = ["medium", "high", "critical"]
        return config

    @pytest.fixture
    def error_detector(self, mock_config):
        """Create an error detector instance."""
        from src.bank_statement_separator.utils.error_detector import ErrorDetector

        return ErrorDetector(mock_config)

    def test_detect_llm_analysis_failure(self, error_detector):
        """Test detection of LLM analysis failures."""
        # Simulate workflow state with LLM failure
        workflow_state = {
            "current_step": "statement_detection_error",
            "error_message": "LLM boundary detection failed: API timeout",
            "detected_boundaries": None,
            "confidence_scores": None,
        }

        errors = error_detector.detect_errors(workflow_state)

        assert len(errors) > 0
        assert any(error["type"] == "llm_analysis_failure" for error in errors)
        assert any("API timeout" in error["description"] for error in errors)

    def test_detect_boundary_detection_issues(self, error_detector):
        """Test detection of boundary detection issues."""
        workflow_state = {
            "current_step": "statement_detection_complete",
            "detected_boundaries": [
                {"confidence": 0.3, "start_page": 1, "end_page": 5},
                {"confidence": 0.2, "start_page": 6, "end_page": 10},
            ],
            "confidence_scores": [0.3, 0.2],
        }

        errors = error_detector.detect_errors(workflow_state)

        assert len(errors) > 0
        assert any(error["type"] == "low_confidence_boundaries" for error in errors)

    def test_detect_pdf_processing_errors(self, error_detector):
        """Test detection of PDF processing errors."""
        workflow_state = {
            "current_step": "pdf_generation_error",
            "error_message": "PDF generation failed: corrupted input file",
            "generated_files": [],
            "total_statements_found": 3,
        }

        errors = error_detector.detect_errors(workflow_state)

        assert len(errors) > 0
        assert any(error["type"] == "pdf_processing_error" for error in errors)

    def test_detect_metadata_extraction_problems(self, error_detector):
        """Test detection of metadata extraction problems."""
        workflow_state = {
            "current_step": "metadata_extraction_complete",
            "extracted_metadata": [
                {"account_number": "ACCT0001", "confidence": 0.2},
                {"account_number": "ACCT0002", "confidence": 0.3},
            ],
        }

        errors = error_detector.detect_errors(workflow_state)

        assert len(errors) > 0
        assert any(error["type"] == "metadata_extraction_failure" for error in errors)

    def test_detect_validation_failures(self, error_detector):
        """Test detection of validation failures."""
        workflow_state = {
            "current_step": "output_validation_error",
            "validation_results": {
                "is_valid": False,
                "error_details": ["Page count mismatch", "Content sampling failed"],
                "checks": {
                    "page_count": {"status": "failed"},
                    "content_sampling": {"status": "failed"},
                },
            },
        }

        errors = error_detector.detect_errors(workflow_state)

        assert len(errors) > 0
        assert any(error["type"] == "validation_failure" for error in errors)

    def test_no_errors_detected_for_successful_workflow(self, error_detector):
        """Test that no errors are detected for successful workflow."""
        workflow_state = {
            "current_step": "paperless_upload_complete",
            "error_message": None,
            "processing_complete": True,
            "detected_boundaries": [
                {
                    "confidence": 0.9,
                    "start_page": 1,
                    "end_page": 10,
                    "reasoning": "LLM-based detection",
                }
            ],
            "validation_results": {"is_valid": True},
            "generated_files": ["output1.pdf", "output2.pdf"],
        }

        errors = error_detector.detect_errors(workflow_state)

        assert len(errors) == 0


class TestAutomaticTagging:
    """Test automatic tagging of documents with processing errors."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration with error tagging enabled."""
        config = Mock(spec=Config)
        config.paperless_enabled = True
        config.paperless_url = "https://paperless.example.com"
        config.paperless_token = "test-token"
        config.paperless_error_tags = ["processing:needs-review", "error:detected"]
        config.paperless_error_tag_threshold = 0.5
        config.paperless_error_detection_enabled = True
        config.paperless_error_severity_levels = ["medium", "high", "critical"]
        config.paperless_error_batch_tagging = False
        config.paperless_tag_wait_time = 5
        return config

    @pytest.fixture
    def mock_paperless_client(self, mock_config):
        """Create a mock paperless client."""
        with patch(
            "src.bank_statement_separator.utils.paperless_client.PaperlessClient"
        ) as mock_client_class:
            client = mock_client_class.return_value
            client.is_enabled.return_value = True
            client.apply_tags_to_document.return_value = {
                "success": True,
                "tags_applied": 2,
                "document_id": 123,
            }
            yield client

    @pytest.fixture
    def error_tagger(self, mock_config):
        """Create an error tagger instance."""
        from src.bank_statement_separator.utils.error_tagger import ErrorTagger

        return ErrorTagger(mock_config)

    def test_apply_error_tags_to_documents(self, error_tagger, mock_paperless_client):
        """Test applying error tags to documents with processing issues."""
        errors = [
            {"type": "llm_analysis_failure", "severity": "high"},
            {"type": "low_confidence_boundaries", "severity": "medium"},
        ]

        upload_results = {
            "uploads": [
                {"document_id": 123, "success": True},
                {"document_id": 124, "success": True},
            ]
        }

        with patch.object(error_tagger, "paperless_client", mock_paperless_client):
            result = error_tagger.apply_error_tags(errors, upload_results)

        assert result["success"] is True
        assert result["tagged_documents"] == 2
        mock_paperless_client.apply_tags_to_document.assert_called()

    def test_skip_tagging_for_low_severity_errors(
        self, error_tagger, mock_paperless_client
    ):
        """Test that low severity errors don't trigger tagging."""
        errors = [{"type": "minor_warning", "severity": "low"}]

        upload_results = {"uploads": [{"document_id": 123, "success": True}]}

        with patch.object(error_tagger, "paperless_client", mock_paperless_client):
            result = error_tagger.apply_error_tags(errors, upload_results)

        assert result["tagged_documents"] == 0
        mock_paperless_client.apply_tags_to_document.assert_not_called()

    def test_handle_tagging_failures_gracefully(
        self, error_tagger, mock_paperless_client
    ):
        """Test graceful handling of tagging failures."""
        mock_paperless_client.apply_tags_to_document.side_effect = Exception(
            "API error"
        )

        errors = [{"type": "llm_analysis_failure", "severity": "high"}]
        upload_results = {"uploads": [{"document_id": 123, "success": True}]}

        with patch.object(error_tagger, "paperless_client", mock_paperless_client):
            result = error_tagger.apply_error_tags(errors, upload_results)

        assert result["success"] is False
        assert "API error" in str(result["errors"][0])

    def test_only_tag_documents_with_errors(self, error_tagger, mock_paperless_client):
        """Test that only documents with detected errors are tagged."""
        errors = []  # No errors detected

        upload_results = {"uploads": [{"document_id": 123, "success": True}]}

        with patch.object(error_tagger, "paperless_client", mock_paperless_client):
            result = error_tagger.apply_error_tags(errors, upload_results)

        assert result["tagged_documents"] == 0
        mock_paperless_client.apply_tags_to_document.assert_not_called()


class TestWorkflowIntegration:
    """Test integration of error detection and tagging into the workflow."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration."""
        config = Mock(spec=Config)
        config.paperless_enabled = True
        config.paperless_error_detection_enabled = True
        config.paperless_error_tags = ["processing:needs-review"]
        config.paperless_error_severity_levels = ["medium", "high", "critical"]
        config.quarantine_directory = None
        config.max_retry_attempts = 2
        config.continue_on_validation_warnings = True
        config.auto_quarantine_critical_failures = True
        config.preserve_failed_outputs = True
        config.enable_error_reporting = True
        config.error_report_directory = None
        config.validation_strictness = "normal"
        config.default_output_dir = "./test_output"
        return config

    @pytest.fixture
    def workflow(self, mock_config):
        """Create a workflow instance."""
        from src.bank_statement_separator.workflow import BankStatementWorkflow

        return BankStatementWorkflow(mock_config)

    def test_paperless_upload_node_detects_and_tags_errors(self, workflow):
        """Test that the paperless upload node detects errors and applies tags."""
        state = {
            "current_step": "pdf_generation_error",
            "error_message": "PDF generation failed",
            "generated_files": [],
            "paperless_upload_results": {
                "uploads": [{"document_id": 123, "success": True}]
            },
        }

        with patch.object(workflow, "_detect_and_tag_errors") as mock_detect_tag:
            mock_detect_tag.return_value = {
                "attempted": True,
                "errors_detected": 1,
                "tagged_documents": 1,
                "success": True,
            }

            workflow._detect_and_tag_errors(state, {"enabled": True, "uploads": []})

        mock_detect_tag.assert_called_once()

    def test_error_detection_disabled_skips_tagging(self, workflow):
        """Test that disabled error detection skips tagging."""
        workflow.config.paperless_error_detection_enabled = False

        state = {
            "current_step": "pdf_generation_error",
            "error_message": "PDF generation failed",
        }

        result = workflow._detect_and_tag_errors(state, {"enabled": True})

        assert result["attempted"] is False
        assert result["errors_detected"] == 0

    def test_paperless_disabled_skips_error_tagging(self, workflow):
        """Test that disabled paperless integration skips error tagging."""
        workflow.config.paperless_enabled = False

        state = {"current_step": "output_validation_complete"}

        result = workflow._detect_and_tag_errors(state, {"enabled": False})

        assert result["attempted"] is False


class TestConfigurationOptions:
    """Test configuration options for error detection and tagging."""

    def test_error_detection_configuration_validation(self):
        """Test validation of error detection configuration."""
        # Test valid configuration
        config_data = {
            "paperless_enabled": True,
            "paperless_error_detection_enabled": True,
            "paperless_error_tags": ["processing:needs-review", "error:high"],
            "paperless_error_tag_threshold": 0.5,
        }

        config = Config(**config_data)
        assert config.paperless_error_detection_enabled is True
        assert len(config.paperless_error_tags) == 2

    def test_error_tag_threshold_validation(self):
        """Test validation of error tag threshold."""
        # Test invalid threshold (too high)
        with pytest.raises(ValueError):
            Config(paperless_error_tag_threshold=1.5)

        # Test invalid threshold (negative)
        with pytest.raises(ValueError):
            Config(paperless_error_tag_threshold=-0.1)

        # Test valid threshold
        config = Config(paperless_error_tag_threshold=0.7)
        assert config.paperless_error_tag_threshold == 0.7

    def test_error_tags_list_validation(self):
        """Test validation of error tags list."""
        config = Config(paperless_error_tags=["tag1", "tag2:value", "tag3"])
        assert len(config.paperless_error_tags) == 3
        assert "tag2:value" in config.paperless_error_tags

    def test_default_error_configuration(self):
        """Test default error configuration values."""
        config = Config()
        assert config.paperless_error_detection_enabled is False
        assert config.paperless_error_tags is None
        assert config.paperless_error_tag_threshold == 0.5

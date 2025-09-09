"""Comprehensive tests for paperless-ngx integration with mocked API calls."""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import httpx
from src.bank_statement_separator.config import Config
from src.bank_statement_separator.utils.paperless_client import (
    PaperlessClient,
    PaperlessUploadError,
)
from src.bank_statement_separator.workflow import (
    BankStatementWorkflow,
    WorkflowState,
)


@pytest.mark.unit
@pytest.mark.requires_paperless
@pytest.mark.mock_heavy
class TestPaperlessClient:
    """Test cases for PaperlessClient class."""

    @pytest.fixture
    def paperless_config(self):
        """Create a test configuration with paperless enabled."""
        return Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_tags=["bank-statement", "automated"],
            paperless_correspondent="Bank",
            paperless_document_type="Bank Statement",
            paperless_storage_path="Bank Statements",
        )

    @pytest.fixture
    def disabled_paperless_config(self):
        """Create a test configuration with paperless disabled."""
        return Config(openai_api_key="test-key", paperless_enabled=False)

    @pytest.fixture
    def paperless_client(self, paperless_config):
        """Create a PaperlessClient instance."""
        return PaperlessClient(paperless_config)

    @pytest.fixture
    def test_pdf_file(self, tmp_path):
        """Create a temporary test PDF file."""
        pdf_file = tmp_path / "test_statement.pdf"
        pdf_file.write_bytes(b"%PDF-1.4\n%fake pdf content\n%%EOF")
        return pdf_file

    def test_client_initialization_enabled(self, paperless_config):
        """Test PaperlessClient initialization with enabled configuration."""
        client = PaperlessClient(paperless_config)

        assert client.config == paperless_config
        assert client.base_url == "http://localhost:8000"
        assert client.headers["Authorization"] == "Token test-token-123"
        assert client.headers["Content-Type"] == "application/json"
        assert client.is_enabled() is True

    def test_client_initialization_disabled(self, disabled_paperless_config):
        """Test PaperlessClient initialization with disabled configuration."""
        client = PaperlessClient(disabled_paperless_config)

        assert client.config == disabled_paperless_config
        assert client.base_url is None
        assert client.headers == {}
        assert client.is_enabled() is False

    def test_is_enabled_missing_url(self):
        """Test is_enabled returns False when URL is missing."""
        config = Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_token="test-token",
            # paperless_url is missing
        )
        client = PaperlessClient(config)
        assert client.is_enabled() is False

    def test_is_enabled_missing_token(self):
        """Test is_enabled returns False when token is missing."""
        config = Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            # paperless_token is missing
        )
        client = PaperlessClient(config)
        assert client.is_enabled() is False

    @patch("httpx.Client")
    def test_test_connection_success(self, mock_httpx_client, paperless_client):
        """Test successful connection test."""
        # Mock the HTTP client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        result = paperless_client.test_connection()

        assert result is True
        mock_client.get.assert_called_once_with(
            "http://localhost:8000/api/documents/",
            headers=paperless_client.headers,
            params={"page_size": 1},
        )
        mock_response.raise_for_status.assert_called_once()

    @patch("httpx.Client")
    def test_test_connection_request_error(self, mock_httpx_client, paperless_client):
        """Test connection test with request error."""
        mock_client = Mock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with pytest.raises(
            PaperlessUploadError, match="Failed to connect to paperless-ngx"
        ):
            paperless_client.test_connection()

    @patch("httpx.Client")
    def test_test_connection_http_error(self, mock_httpx_client, paperless_client):
        """Test connection test with HTTP status error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=Mock(), response=mock_response
        )
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with pytest.raises(
            PaperlessUploadError, match="Paperless API returned error 401"
        ):
            paperless_client.test_connection()

    def test_test_connection_disabled(self, disabled_paperless_config):
        """Test connection test when paperless is disabled."""
        client = PaperlessClient(disabled_paperless_config)

        with pytest.raises(
            PaperlessUploadError, match="Paperless integration not enabled"
        ):
            client.test_connection()

    @patch("httpx.Client")
    def test_upload_document_success(
        self, mock_httpx_client, paperless_client, test_pdf_file
    ):
        """Test successful document upload."""
        # Mock the HTTP client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 123, "title": "test_statement"}
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock the resolution methods to return IDs
        with (
            patch.object(paperless_client, "_resolve_tags", return_value=[1, 2]),
            patch.object(paperless_client, "_resolve_correspondent", return_value=10),
            patch.object(paperless_client, "_resolve_document_type", return_value=20),
            patch.object(paperless_client, "_resolve_storage_path", return_value=None),
        ):
            result = paperless_client.upload_document(
                file_path=test_pdf_file,
                title="Test Statement",
                tags=["test-tag"],
                correspondent="Test Bank",
                document_type="Statement",
            )

        assert result["success"] is True
        assert result["document_id"] == 123
        assert result["title"] == "Test Statement"
        assert result["tags"] == ["test-tag"]
        assert result["correspondent"] == "Test Bank"
        assert result["document_type"] == "Statement"

        # Verify the API call
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "http://localhost:8000/api/documents/post_document/"
        assert "document" in call_args[1]["files"]
        assert call_args[1]["data"]["title"] == "Test Statement"

    @patch("httpx.Client")
    def test_upload_document_with_config_defaults(
        self, mock_httpx_client, paperless_client, test_pdf_file
    ):
        """Test document upload using configuration defaults."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 456}
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock the resolution methods to return IDs
        with (
            patch.object(paperless_client, "_resolve_tags", return_value=[1, 2]),
            patch.object(paperless_client, "_resolve_correspondent", return_value=10),
            patch.object(paperless_client, "_resolve_document_type", return_value=20),
            patch.object(paperless_client, "_resolve_storage_path", return_value=30),
        ):
            result = paperless_client.upload_document(file_path=test_pdf_file)

        assert result["success"] is True
        assert result["tags"] == ["bank-statement", "automated"]  # From config
        assert result["correspondent"] == "Bank"  # From config
        assert result["document_type"] == "Bank Statement"  # From config
        assert result["storage_path"] == "Bank Statements"  # From config

    @patch("httpx.Client")
    def test_upload_document_request_error(
        self, mock_httpx_client, paperless_client, test_pdf_file
    ):
        """Test document upload with request error."""
        mock_client = Mock()
        mock_client.post.side_effect = httpx.RequestError("Network error")
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock the resolution methods to return IDs
        with (
            patch.object(paperless_client, "_resolve_tags", return_value=[]),
            patch.object(paperless_client, "_resolve_correspondent", return_value=None),
            patch.object(paperless_client, "_resolve_document_type", return_value=None),
            patch.object(paperless_client, "_resolve_storage_path", return_value=None),
        ):
            with pytest.raises(
                PaperlessUploadError, match="Failed to upload.*to paperless-ngx"
            ):
                paperless_client.upload_document(file_path=test_pdf_file)

    @patch("httpx.Client")
    def test_upload_document_http_error(
        self, mock_httpx_client, paperless_client, test_pdf_file
    ):
        """Test document upload with HTTP status error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad request"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400 Bad Request", request=Mock(), response=mock_response
        )
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock the resolution methods to return IDs
        with (
            patch.object(paperless_client, "_resolve_tags", return_value=[]),
            patch.object(paperless_client, "_resolve_correspondent", return_value=None),
            patch.object(paperless_client, "_resolve_document_type", return_value=None),
            patch.object(paperless_client, "_resolve_storage_path", return_value=None),
        ):
            with pytest.raises(
                PaperlessUploadError, match="Paperless upload failed with status 400"
            ):
                paperless_client.upload_document(file_path=test_pdf_file)

    def test_upload_document_file_not_found(self, paperless_client):
        """Test document upload with non-existent file."""
        non_existent_file = Path("/non/existent/file.pdf")

        with pytest.raises(PaperlessUploadError, match="File not found"):
            paperless_client.upload_document(file_path=non_existent_file)

    def test_upload_document_disabled(self, test_pdf_file):
        """Test document upload when paperless is disabled."""
        config = Config(openai_api_key="test-key", paperless_enabled=False)
        client = PaperlessClient(config)

        with pytest.raises(
            PaperlessUploadError, match="Paperless integration not enabled"
        ):
            client.upload_document(file_path=test_pdf_file)

    @patch("httpx.Client")
    def test_upload_document_with_storage_path(self, mock_httpx_client, test_pdf_file):
        """Test document upload with storage path."""
        # Create a config with storage path
        config = Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token",
            paperless_storage_path="Test Storage",
        )
        client = PaperlessClient(config)

        # Mock the HTTP client
        mock_client = Mock()

        # Mock responses for various API calls
        mock_tag_response = Mock()
        mock_tag_response.raise_for_status.return_value = None
        mock_tag_response.json.return_value = {"results": []}  # No existing tags

        mock_tag_create_response = Mock()
        mock_tag_create_response.raise_for_status.return_value = None
        mock_tag_create_response.json.return_value = {"id": 1, "name": "bank-statement"}

        mock_storage_response = Mock()
        mock_storage_response.raise_for_status.return_value = None
        mock_storage_response.json.return_value = {
            "results": [{"id": 5, "name": "Test Storage"}]
        }

        mock_upload_response = Mock()
        mock_upload_response.raise_for_status.return_value = None
        mock_upload_response.json.return_value = "test-task-id-123"

        # Configure mock to return appropriate responses based on URL
        def side_effect_get(url, **kwargs):
            if "storage_paths" in url:
                return mock_storage_response
            elif "tags" in url:
                return mock_tag_response
            else:
                return mock_tag_response

        def side_effect_post(url, **kwargs):
            if "tags" in url:
                return mock_tag_create_response
            else:
                return mock_upload_response

        mock_client.get.side_effect = side_effect_get
        mock_client.post.side_effect = side_effect_post
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        result = client.upload_document(
            file_path=test_pdf_file, storage_path="Test Storage Path"
        )

        assert result["success"] is True
        assert result["task_id"] == "test-task-id-123"
        assert result["storage_path"] == "Test Storage Path"

    @patch("httpx.Client")
    def test_upload_multiple_documents_success(
        self, mock_httpx_client, paperless_client, tmp_path
    ):
        """Test successful upload of multiple documents."""
        # Create test PDF files
        pdf_files = []
        for i in range(3):
            pdf_file = tmp_path / f"statement_{i}.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\n%fake pdf content\n%%EOF")
            pdf_files.append(pdf_file)

        # Mock successful responses
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 123}
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock the resolution methods to return IDs
        with (
            patch.object(paperless_client, "_resolve_tags", return_value=[1]),
            patch.object(paperless_client, "_resolve_correspondent", return_value=10),
            patch.object(paperless_client, "_resolve_document_type", return_value=None),
            patch.object(paperless_client, "_resolve_storage_path", return_value=None),
        ):
            result = paperless_client.upload_multiple_documents(
                file_paths=pdf_files,
                base_title="Test Statements",
                tags=["test"],
                correspondent="Test Bank",
            )

        assert result["success"] is True
        assert len(result["uploads"]) == 3
        assert len(result["errors"]) == 0

        # Verify all files were uploaded with numbered titles
        for i, upload in enumerate(result["uploads"], 1):
            assert upload["title"] == f"Test Statements - Statement {i}"

        # Verify API calls
        assert mock_client.post.call_count == 3

    @patch("httpx.Client")
    def test_upload_multiple_documents_partial_failure(
        self, mock_httpx_client, paperless_client, tmp_path
    ):
        """Test upload of multiple documents with some failures."""
        # Create test PDF files
        pdf_files = []
        for i in range(3):
            pdf_file = tmp_path / f"statement_{i}.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\n%fake pdf content\n%%EOF")
            pdf_files.append(pdf_file)

        # Mock mixed responses (success, failure, success)
        mock_client = Mock()

        def side_effect(*args, **kwargs):
            if mock_client.post.call_count == 2:  # Second call fails
                raise httpx.RequestError("Network error")
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"id": 123}
            return mock_response

        mock_client.post.side_effect = side_effect
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock the resolution methods to return IDs
        with (
            patch.object(paperless_client, "_resolve_tags", return_value=[]),
            patch.object(paperless_client, "_resolve_correspondent", return_value=None),
            patch.object(paperless_client, "_resolve_document_type", return_value=None),
            patch.object(paperless_client, "_resolve_storage_path", return_value=None),
        ):
            result = paperless_client.upload_multiple_documents(file_paths=pdf_files)

        assert result["success"] is False
        assert len(result["uploads"]) == 2  # First and third succeeded
        assert len(result["errors"]) == 1  # Second failed
        assert "Network error" in result["errors"][0]["error"]

    def test_upload_multiple_documents_empty_list(self, paperless_client):
        """Test upload of empty file list."""
        result = paperless_client.upload_multiple_documents(file_paths=[])

        assert result["success"] is True
        assert len(result["uploads"]) == 0
        assert len(result["errors"]) == 0


@pytest.mark.unit
@pytest.mark.requires_paperless
@pytest.mark.mock_heavy
class TestPaperlessWorkflowIntegration:
    """Test cases for paperless integration within the workflow."""

    @pytest.fixture
    def workflow_config(self):
        """Create a workflow configuration with paperless enabled."""
        return Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_tags=["bank-statement"],
            paperless_correspondent="Bank",
        )

    @pytest.fixture
    def workflow(self, workflow_config):
        """Create a BankStatementWorkflow instance."""
        return BankStatementWorkflow(workflow_config)

    @pytest.fixture
    def mock_workflow_state(self, tmp_path):
        """Create a mock workflow state with generated files."""
        # Create temporary output files
        output_files = []
        for i in range(2):
            output_file = tmp_path / f"statement_{i}.pdf"
            output_file.write_bytes(b"%PDF-1.4\n%fake content\n%%EOF")
            output_files.append(str(output_file))

        return WorkflowState(
            input_file_path="/test/input.pdf",
            output_directory=str(tmp_path),
            pdf_document=None,
            text_chunks=None,
            detected_boundaries=None,
            extracted_metadata=[
                {
                    "statement_index": 0,
                    "bank_name": "Westpac",
                    "account_number": "1234567890",
                },
                {
                    "statement_index": 1,
                    "bank_name": "ANZ",
                    "account_number": "0987654321",
                },
            ],
            generated_files=output_files,
            processed_input_file=None,
            paperless_upload_results=None,
            current_step="output_validation_complete",
            error_message=None,
            processing_complete=True,
            total_pages=10,
            total_statements_found=2,
            processing_time_seconds=None,
            confidence_scores=None,
            validation_results={"is_valid": True},
        )

    def test_paperless_upload_node_success(self, workflow, mock_workflow_state):
        """Test successful paperless upload node execution."""
        # Mock the PaperlessClient class
        with patch(
            "src.bank_statement_separator.utils.paperless_client.PaperlessClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_client.test_connection.return_value = True
            mock_client.upload_document.return_value = {
                "success": True,
                "document_id": 123,
                "title": "Test Statement",
                "file_path": "test.pdf",
            }
            mock_client_class.return_value = mock_client

            result_state = workflow._paperless_upload_node(mock_workflow_state)

        assert result_state["current_step"] == "paperless_upload_complete"
        assert result_state["error_message"] is None
        assert result_state["paperless_upload_results"]["success"] is True
        assert result_state["paperless_upload_results"]["enabled"] is True
        assert len(result_state["paperless_upload_results"]["uploads"]) == 2
        assert len(result_state["paperless_upload_results"]["errors"]) == 0

    def test_paperless_upload_node_connection_failure(
        self, workflow, mock_workflow_state
    ):
        """Test paperless upload node with connection failure."""
        # Mock connection test failure
        from src.bank_statement_separator.utils.paperless_client import (
            PaperlessUploadError,
        )

        with patch(
            "src.bank_statement_separator.utils.paperless_client.PaperlessClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_client.test_connection.side_effect = PaperlessUploadError(
                "Connection refused"
            )
            mock_client_class.return_value = mock_client

            result_state = workflow._paperless_upload_node(mock_workflow_state)

        assert result_state["current_step"] == "paperless_upload_connection_error"
        assert result_state["paperless_upload_results"]["success"] is False
        assert result_state["paperless_upload_results"]["enabled"] is True
        assert (
            "Connection test failed"
            in result_state["paperless_upload_results"]["summary"]
        )
        assert len(result_state["paperless_upload_results"]["errors"]) == 1

    def test_paperless_upload_node_disabled(self, mock_workflow_state):
        """Test paperless upload node when paperless is disabled."""
        # Create workflow with disabled paperless
        disabled_config = Config(openai_api_key="test-key", paperless_enabled=False)
        workflow = BankStatementWorkflow(disabled_config)

        result_state = workflow._paperless_upload_node(mock_workflow_state)

        assert result_state["current_step"] == "paperless_upload_skipped"
        assert result_state["paperless_upload_results"]["success"] is True
        assert result_state["paperless_upload_results"]["enabled"] is False
        assert (
            result_state["paperless_upload_results"]["summary"]
            == "Paperless integration disabled"
        )

    def test_paperless_upload_node_no_files(self, workflow):
        """Test paperless upload node with no generated files."""
        state = WorkflowState(
            input_file_path="/test/input.pdf",
            output_directory="/test/output",
            pdf_document=None,
            text_chunks=None,
            detected_boundaries=None,
            extracted_metadata=None,
            generated_files=[],  # No files
            processed_input_file=None,
            paperless_upload_results=None,
            current_step="output_validation_complete",
            error_message=None,
            processing_complete=True,
            total_pages=0,
            total_statements_found=0,
            processing_time_seconds=None,
            confidence_scores=None,
            validation_results=None,
        )

        # Mock successful connection test
        with patch(
            "src.bank_statement_separator.utils.paperless_client.PaperlessClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_client.test_connection.return_value = True
            mock_client_class.return_value = mock_client

            result_state = workflow._paperless_upload_node(state)

        assert result_state["current_step"] == "paperless_upload_no_files"
        assert result_state["paperless_upload_results"]["success"] is True
        assert (
            result_state["paperless_upload_results"]["summary"] == "No files to upload"
        )

    def test_paperless_upload_node_partial_failure(self, workflow, mock_workflow_state):
        """Test paperless upload node with partial upload failure."""
        # Mock partial upload failure
        with patch(
            "src.bank_statement_separator.utils.paperless_client.PaperlessClient"
        ) as mock_client_class:
            mock_client = Mock()
            mock_client.is_enabled.return_value = True
            mock_client.test_connection.return_value = True

            # First call succeeds, second fails
            def upload_side_effect(*args, **kwargs):
                if mock_client.upload_document.call_count == 1:
                    return {"success": True, "document_id": 123, "title": "Statement 1"}
                else:
                    from src.bank_statement_separator.utils.paperless_client import (
                        PaperlessUploadError,
                    )

                    raise PaperlessUploadError("Network error")

            mock_client.upload_document.side_effect = upload_side_effect
            mock_client_class.return_value = mock_client

            result_state = workflow._paperless_upload_node(mock_workflow_state)

        assert result_state["current_step"] == "paperless_upload_complete"
        assert result_state["paperless_upload_results"]["success"] is False
        assert len(result_state["paperless_upload_results"]["uploads"]) == 1
        assert len(result_state["paperless_upload_results"]["errors"]) == 1
        assert "1/2 files" in result_state["paperless_upload_results"]["summary"]


@pytest.mark.unit
@pytest.mark.validation
class TestPaperlessConfigValidation:
    """Test cases for paperless configuration validation."""

    def test_paperless_config_all_fields(self):
        """Test configuration with all paperless fields."""
        config = Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token",
            paperless_tags=["tag1", "tag2"],
            paperless_correspondent="Bank Name",
            paperless_document_type="Statement",
            paperless_storage_path="Bank Documents",
        )

        assert config.paperless_enabled is True
        assert config.paperless_url == "http://localhost:8000"
        assert config.paperless_token == "test-token"
        assert config.paperless_tags == ["tag1", "tag2"]
        assert config.paperless_correspondent == "Bank Name"
        assert config.paperless_document_type == "Statement"
        assert config.paperless_storage_path == "Bank Documents"

    def test_paperless_config_minimal(self):
        """Test configuration with minimal required fields."""
        config = Config(openai_api_key="test-key")

        assert config.paperless_enabled is False
        assert config.paperless_url is None
        assert config.paperless_token is None
        assert config.paperless_tags is None
        assert config.paperless_correspondent is None
        assert config.paperless_document_type is None
        assert config.paperless_storage_path is None

    def test_paperless_config_defaults(self):
        """Test that paperless configuration uses proper defaults."""
        config = Config(
            openai_api_key="test-key",
            paperless_enabled=False,  # Explicitly set to False
        )

        # Verify defaults
        assert config.paperless_enabled is False
        assert config.paperless_url is None
        assert config.paperless_token is None
        assert config.paperless_tags is None
        assert config.paperless_correspondent is None
        assert config.paperless_document_type is None
        assert config.paperless_storage_path is None


@pytest.mark.integration
class TestPaperlessIntegrationFlow:
    """Integration tests for the complete paperless workflow."""

    @patch("src.bank_statement_separator.utils.paperless_client.httpx.Client")
    @patch(
        "src.bank_statement_separator.workflow.BankStatementWorkflow._output_validation_node"
    )
    def test_full_workflow_with_paperless(
        self, mock_validation_node, mock_httpx_client, tmp_path
    ):
        """Test complete workflow including paperless upload."""
        # Setup config with paperless enabled
        config = Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token",
        )

        # Create workflow
        workflow = BankStatementWorkflow(config)

        # Mock validation node to return successful validation
        mock_validation_node.return_value = {
            "validation_results": {"is_valid": True},
            "current_step": "output_validation_complete",
        }

        # Mock paperless API calls
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"id": 123}
        mock_client.get.return_value = mock_response
        mock_client.post.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Create test state that would come after validation
        test_state = WorkflowState(
            input_file_path="/test/input.pdf",
            output_directory=str(tmp_path),
            pdf_document=None,
            text_chunks=None,
            detected_boundaries=None,
            extracted_metadata=[{"bank_name": "Test Bank", "account_number": "1234"}],
            generated_files=[str(tmp_path / "statement.pdf")],
            processed_input_file=None,
            paperless_upload_results=None,
            current_step="output_validation_complete",
            error_message=None,
            processing_complete=True,
            total_pages=5,
            total_statements_found=1,
            processing_time_seconds=None,
            confidence_scores=None,
            validation_results={"is_valid": True},
        )

        # Create the test file
        (tmp_path / "statement.pdf").write_bytes(b"%PDF-1.4\n%test content\n%%EOF")

        # Test paperless upload node
        result = workflow._paperless_upload_node(test_state)

        # Verify paperless upload occurred
        assert result["paperless_upload_results"]["success"] is True
        assert result["paperless_upload_results"]["enabled"] is True
        assert len(result["paperless_upload_results"]["uploads"]) == 1
        assert result["current_step"] == "paperless_upload_complete"

        # Verify API calls were made
        mock_client.get.assert_called_once()  # Connection test
        mock_client.post.assert_called_once()  # Upload


@pytest.mark.unit
@pytest.mark.requires_paperless
@pytest.mark.validation
class TestPaperlessFilenameConsistency:
    """Test cases for ensuring paperless document titles match output filenames."""

    @pytest.fixture
    def workflow_with_paperless(self, tmp_path):
        """Create a workflow instance with paperless enabled."""
        config = Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_tags=["bank-statement", "automated"],
            paperless_correspondent="Bank",
            paperless_document_type="Bank Statement",
            paperless_storage_path="Bank Statements",
            default_output_dir=str(tmp_path),
        )
        return BankStatementWorkflow(config)

    @patch("httpx.Client")
    @patch("src.bank_statement_separator.utils.paperless_client.PaperlessClient")
    def test_paperless_title_matches_filename_exactly(
        self, mock_client_class, mock_httpx, tmp_path, workflow_with_paperless
    ):
        """Test that paperless document title matches the output filename exactly."""
        workflow = workflow_with_paperless

        # Create test output files with PRD-compliant names
        test_files = [
            "westpac-2440-2023-01-31.pdf",
            "cba-9876-2023-02-28.pdf",
            "nab-5555-2023-03-15.pdf",
        ]

        # Create actual test files
        output_files = []
        for filename in test_files:
            file_path = tmp_path / filename
            file_path.write_bytes(b"%PDF-1.4\n%test content\n%%EOF")
            output_files.append(str(file_path))

        # Mock paperless client
        mock_client = Mock()
        mock_client.is_enabled.return_value = True
        mock_client.test_connection.return_value = True

        # Track upload calls to verify titles
        upload_calls = []

        def mock_upload(*args, **kwargs):
            upload_calls.append(kwargs)
            return {
                "success": True,
                "document_id": len(upload_calls),
                "title": kwargs.get("title", "Unknown"),
            }

        mock_client.upload_document.side_effect = mock_upload
        mock_client_class.return_value = mock_client

        # Create workflow state with the test files
        test_state = {
            "input_file_path": str(tmp_path / "original_input.pdf"),
            "generated_files": output_files,
            "extracted_metadata": [{}, {}, {}],  # Mock metadata for 3 files
            "current_step": "output_validation_complete",
            "processing_complete": True,
        }

        # Execute paperless upload
        result = workflow._paperless_upload_node(test_state)

        # Verify upload was successful
        assert result["paperless_upload_results"]["success"] is True
        assert len(result["paperless_upload_results"]["uploads"]) == 3

        # Critical Test: Verify that each paperless document title matches filename exactly
        expected_titles = [
            "westpac-2440-2023-01-31",  # filename without .pdf extension
            "cba-9876-2023-02-28",
            "nab-5555-2023-03-15",
        ]

        for i, call in enumerate(upload_calls):
            expected_title = expected_titles[i]
            actual_title = call["title"]

            assert actual_title == expected_title, (
                f"Paperless title mismatch for file {i + 1}: "
                f"expected '{expected_title}', got '{actual_title}'"
            )

        # Verify the upload results contain the correct titles
        for i, upload_result in enumerate(
            result["paperless_upload_results"]["uploads"]
        ):
            expected_title = expected_titles[i]
            assert upload_result["title"] == expected_title, (
                f"Upload result title mismatch: expected '{expected_title}', "
                f"got '{upload_result['title']}'"
            )

    @patch("httpx.Client")
    @patch("src.bank_statement_separator.utils.paperless_client.PaperlessClient")
    def test_paperless_title_handles_special_characters(
        self, mock_client_class, mock_httpx, tmp_path, workflow_with_paperless
    ):
        """Test that paperless titles handle special characters in filenames correctly."""
        workflow = workflow_with_paperless

        # Create test files with special characters that might appear in bank names
        test_files = [
            "wells-fargo-1234-2023-01-31.pdf",
            "bank-of-america-9999-2023-02-28.pdf",
            "td-canada-trust-5678-2023-03-15.pdf",
        ]

        # Create actual test files
        output_files = []
        for filename in test_files:
            file_path = tmp_path / filename
            file_path.write_bytes(b"%PDF-1.4\n%test content\n%%EOF")
            output_files.append(str(file_path))

        # Mock paperless client
        mock_client = Mock()
        mock_client.is_enabled.return_value = True
        mock_client.test_connection.return_value = True

        # Track upload calls
        upload_calls = []

        def mock_upload(*args, **kwargs):
            upload_calls.append(kwargs)
            return {
                "success": True,
                "document_id": len(upload_calls),
                "title": kwargs.get("title", "Unknown"),
            }

        mock_client.upload_document.side_effect = mock_upload
        mock_client_class.return_value = mock_client

        # Create workflow state
        test_state = {
            "input_file_path": str(tmp_path / "original_input.pdf"),
            "generated_files": output_files,
            "extracted_metadata": [{}, {}, {}],
            "current_step": "output_validation_complete",
            "processing_complete": True,
        }

        # Execute paperless upload
        result = workflow._paperless_upload_node(test_state)

        # Verify success
        assert result["paperless_upload_results"]["success"] is True
        assert len(result["paperless_upload_results"]["uploads"]) == 3

        # Verify exact filename matching for special character filenames
        expected_titles = [
            "wells-fargo-1234-2023-01-31",
            "bank-of-america-9999-2023-02-28",
            "td-canada-trust-5678-2023-03-15",
        ]

        for i, call in enumerate(upload_calls):
            expected_title = expected_titles[i]
            actual_title = call["title"]

            assert actual_title == expected_title, (
                f"Special character filename title mismatch: "
                f"expected '{expected_title}', got '{actual_title}'"
            )

    @patch("httpx.Client")
    @patch("src.bank_statement_separator.utils.paperless_client.PaperlessClient")
    def test_paperless_title_single_file(
        self, mock_client_class, mock_httpx, tmp_path, workflow_with_paperless
    ):
        """Test paperless title consistency for single file upload."""
        workflow = workflow_with_paperless

        # Create single test file
        filename = "single-statement-acct-1234-2023-12-31.pdf"
        file_path = tmp_path / filename
        file_path.write_bytes(b"%PDF-1.4\n%test content\n%%EOF")

        # Mock paperless client
        mock_client = Mock()
        mock_client.is_enabled.return_value = True
        mock_client.test_connection.return_value = True

        upload_call = None

        def mock_upload(*args, **kwargs):
            nonlocal upload_call
            upload_call = kwargs
            return {
                "success": True,
                "document_id": 123,
                "title": kwargs.get("title", "Unknown"),
            }

        mock_client.upload_document.side_effect = mock_upload
        mock_client_class.return_value = mock_client

        # Create workflow state
        test_state = {
            "input_file_path": str(tmp_path / "original.pdf"),
            "generated_files": [str(file_path)],
            "extracted_metadata": [{}],
            "current_step": "output_validation_complete",
            "processing_complete": True,
        }

        # Execute paperless upload
        result = workflow._paperless_upload_node(test_state)

        # Verify upload success
        assert result["paperless_upload_results"]["success"] is True
        assert len(result["paperless_upload_results"]["uploads"]) == 1

        # Critical verification: title must exactly match filename without extension
        expected_title = "single-statement-acct-1234-2023-12-31"
        actual_title = upload_call["title"]

        assert (
            actual_title == expected_title
        ), f"Single file title mismatch: expected '{expected_title}', got '{actual_title}'"

        # Also verify in upload results
        assert (
            result["paperless_upload_results"]["uploads"][0]["title"] == expected_title
        )

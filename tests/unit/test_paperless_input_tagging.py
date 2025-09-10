"""Test suite for paperless-ngx input document tagging functionality."""

from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from src.bank_statement_separator.config import Config
from src.bank_statement_separator.utils.paperless_client import (
    PaperlessClient,
    PaperlessUploadError,
)


@pytest.mark.unit
@pytest.mark.requires_paperless
@pytest.mark.mock_heavy
class TestPaperlessInputDocumentTagging:
    """Test cases for paperless-ngx input document tagging functionality."""

    @pytest.fixture
    def paperless_config_add_tag(self) -> Config:
        """Create a test configuration with add processed tag enabled."""
        return Config(
            openai_api_key="test-key",  # pragma: allowlist secret
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_input_processed_tag="processed",
            paperless_input_tagging_enabled=True,
        )

    @pytest.fixture
    def paperless_config_remove_tag(self) -> Config:
        """Create a test configuration with remove unprocessed tag enabled."""
        return Config(
            openai_api_key="test-key",  # pragma: allowlist secret
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_input_remove_unprocessed_tag=True,
            paperless_input_tagging_enabled=True,
        )

    @pytest.fixture
    def paperless_config_custom_tag(self) -> Config:
        """Create a test configuration with custom processing tag enabled."""
        return Config(
            openai_api_key="test-key",  # pragma: allowlist secret
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_input_processing_tag="bank-statement-processed",
            paperless_input_tagging_enabled=True,
        )

    @pytest.fixture
    def paperless_config_disabled(self) -> Config:
        """Create a test configuration with input tagging disabled."""
        return Config(
            openai_api_key="test-key",  # pragma: allowlist secret
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_input_processed_tag="processed",
            paperless_input_tagging_enabled=False,
        )

    @pytest.fixture
    def mock_document_response(self) -> Dict[str, Any]:
        """Mock response for a single document API call."""
        return {
            "id": 101,
            "title": "Bank Statement Jan 2024",
            "tags": [1, 2],  # unprocessed, bank-statement-raw
            "correspondent": 10,
            "document_type": 20,
        }

    def test_config_validation_add_processed_tag(
        self, paperless_config_add_tag: Config
    ) -> None:
        """Test configuration validation for add processed tag option."""
        assert paperless_config_add_tag.paperless_input_processed_tag == "processed"
        assert paperless_config_add_tag.paperless_input_tagging_enabled is True
        assert paperless_config_add_tag.paperless_input_remove_unprocessed_tag is False
        assert paperless_config_add_tag.paperless_input_processing_tag is None

    def test_config_validation_remove_unprocessed_tag(
        self, paperless_config_remove_tag: Config
    ) -> None:
        """Test configuration validation for remove unprocessed tag option."""
        assert (
            paperless_config_remove_tag.paperless_input_remove_unprocessed_tag is True
        )
        assert paperless_config_remove_tag.paperless_input_tagging_enabled is True
        assert paperless_config_remove_tag.paperless_input_processed_tag is None
        assert paperless_config_remove_tag.paperless_input_processing_tag is None

    def test_config_validation_custom_processing_tag(
        self, paperless_config_custom_tag: Config
    ) -> None:
        """Test configuration validation for custom processing tag option."""
        assert (
            paperless_config_custom_tag.paperless_input_processing_tag
            == "bank-statement-processed"
        )
        assert paperless_config_custom_tag.paperless_input_tagging_enabled is True
        assert paperless_config_custom_tag.paperless_input_processed_tag is None
        assert (
            paperless_config_custom_tag.paperless_input_remove_unprocessed_tag is False
        )

    @patch("httpx.Client")
    def test_mark_input_document_processed_add_tag_success(
        self, mock_httpx_client: Mock, paperless_config_add_tag: Config
    ) -> None:
        """Test successful marking of input document as processed by adding tag."""
        # Mock HTTP client responses
        mock_client = Mock()
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock tag resolution
        mock_resolve_tag = Mock(return_value=3)  # processed tag ID

        # Mock document GET (to retrieve current tags)
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {
            "id": 101,
            "tags": [1, 2],
        }  # Current tags

        # Mock document PATCH (to update tags)
        mock_patch_response = Mock()
        mock_patch_response.raise_for_status.return_value = None
        mock_patch_response.json.return_value = {"id": 101, "tags": [1, 2, 3]}

        mock_client.get.return_value = mock_get_response
        mock_client.patch.return_value = mock_patch_response

        client = PaperlessClient(paperless_config_add_tag)

        with patch.object(client, "_resolve_tag", mock_resolve_tag):
            result = client.mark_input_document_processed(document_id=101)

        assert result["success"] is True
        assert result["document_id"] == 101
        assert result["action"] == "add_tag"
        assert result["tag_name"] == "processed"
        assert result["tag_id"] == 3

        # Verify API calls
        mock_client.get.assert_called_once()
        mock_client.patch.assert_called_once()

        # Verify GET call
        get_call_args = mock_client.get.call_args
        assert "/api/documents/101/" in get_call_args[0][0]

        # Verify PATCH call
        patch_call_args = mock_client.patch.call_args
        assert "/api/documents/101/" in patch_call_args[0][0]
        assert patch_call_args[1]["json"]["tags"] == [1, 2, 3]  # Original + new tag

    @patch("httpx.Client")
    def test_mark_input_document_processed_remove_tag_success(
        self, mock_httpx_client: Mock, paperless_config_remove_tag: Config
    ) -> None:
        """Test successful marking by removing unprocessed tag."""
        # Mock HTTP client responses
        mock_client = Mock()
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock tag resolution
        mock_resolve_tag = Mock(return_value=1)  # unprocessed tag ID

        # Mock document GET (to retrieve current tags)
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {
            "id": 101,
            "tags": [1, 2],  # includes unprocessed tag (ID 1)
        }

        # Mock document PATCH (to update tags)
        mock_patch_response = Mock()
        mock_patch_response.raise_for_status.return_value = None
        mock_patch_response.json.return_value = {"id": 101, "tags": [2]}

        mock_client.get.return_value = mock_get_response
        mock_client.patch.return_value = mock_patch_response

        client = PaperlessClient(paperless_config_remove_tag)

        with patch.object(client, "_resolve_tag", mock_resolve_tag):
            result = client.mark_input_document_processed(document_id=101)

        assert result["success"] is True
        assert result["document_id"] == 101
        assert result["action"] == "remove_tag"
        assert result["tag_name"] == "unprocessed"
        assert result["tag_id"] == 1

        # Verify API calls
        mock_client.get.assert_called_once()
        mock_client.patch.assert_called_once()

        # Verify GET call
        get_call_args = mock_client.get.call_args
        assert "/api/documents/101/" in get_call_args[0][0]

        # Verify PATCH call
        patch_call_args = mock_client.patch.call_args
        assert "/api/documents/101/" in patch_call_args[0][0]
        assert patch_call_args[1]["json"]["tags"] == [2]  # Tag removed

    @patch("httpx.Client")
    def test_mark_input_document_processed_custom_tag_success(
        self, mock_httpx_client: Mock, paperless_config_custom_tag: Config
    ) -> None:
        """Test successful marking with custom processing tag."""
        # Mock HTTP client responses
        mock_client = Mock()
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock tag resolution
        mock_resolve_tag = Mock(return_value=5)  # custom tag ID

        # Mock document GET (to retrieve current tags)
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {
            "id": 101,
            "tags": [1, 2],
        }  # Current tags

        # Mock document PATCH (to update tags)
        mock_patch_response = Mock()
        mock_patch_response.raise_for_status.return_value = None
        mock_patch_response.json.return_value = {"id": 101, "tags": [1, 2, 5]}

        mock_client.get.return_value = mock_get_response
        mock_client.patch.return_value = mock_patch_response

        client = PaperlessClient(paperless_config_custom_tag)

        with patch.object(client, "_resolve_tag", mock_resolve_tag):
            result = client.mark_input_document_processed(document_id=101)

        assert result["success"] is True
        assert result["document_id"] == 101
        assert result["action"] == "add_tag"
        assert result["tag_name"] == "bank-statement-processed"
        assert result["tag_id"] == 5

        # Verify API calls
        mock_client.get.assert_called_once()
        mock_client.patch.assert_called_once()

        # Verify GET call
        get_call_args = mock_client.get.call_args
        assert "/api/documents/101/" in get_call_args[0][0]

        # Verify PATCH call
        patch_call_args = mock_client.patch.call_args
        assert "/api/documents/101/" in patch_call_args[0][0]
        assert patch_call_args[1]["json"]["tags"] == [1, 2, 5]  # Original + new tag

    def test_mark_input_document_processed_disabled(
        self, paperless_config_disabled: Config
    ) -> None:
        """Test that marking is skipped when tagging is disabled."""
        client = PaperlessClient(paperless_config_disabled)

        result = client.mark_input_document_processed(document_id=101)

        assert result["success"] is True
        assert result["document_id"] == 101
        assert result["action"] == "disabled"
        assert "message" in result
        assert "disabled" in result["message"].lower()

    def test_mark_input_document_processed_no_config(self) -> None:
        """Test that marking fails gracefully when no tagging config is set."""
        config = Config(
            openai_api_key="test-key",  # pragma: allowlist secret
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_input_tagging_enabled=True,
            # No tagging configuration
        )

        client = PaperlessClient(config)

        result = client.mark_input_document_processed(document_id=101)

        assert result["success"] is False
        assert result["document_id"] == 101
        assert "error" in result
        assert "configuration" in result["error"].lower()

    @patch("httpx.Client")
    def test_mark_input_document_processed_tag_not_found(
        self, mock_httpx_client: Mock, paperless_config_add_tag: Config
    ) -> None:
        """Test handling when specified tag doesn't exist."""
        # Mock HTTP client responses
        mock_client = Mock()
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock tag resolution failure
        mock_resolve_tag = Mock(return_value=None)

        client = PaperlessClient(paperless_config_add_tag)

        with patch.object(client, "_resolve_tag", mock_resolve_tag):
            result = client.mark_input_document_processed(document_id=101)

        assert result["success"] is False
        assert result["document_id"] == 101
        assert "error" in result
        assert "not found" in result["error"].lower()

    @patch("httpx.Client")
    def test_mark_input_document_processed_api_error(
        self, mock_httpx_client: Mock, paperless_config_add_tag: Config
    ) -> None:
        """Test handling of API errors during tagging."""
        # Mock HTTP client responses
        mock_client = Mock()
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock tag resolution
        mock_resolve_tag = Mock(return_value=3)

        # Mock successful GET but failed PATCH
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {"id": 101, "tags": [1, 2]}

        mock_patch_response = Mock()
        mock_patch_response.status_code = 404
        mock_patch_response.text = "Document not found"
        mock_patch_response.raise_for_status.side_effect = Exception("API Error")

        mock_client.get.return_value = mock_get_response
        mock_client.patch.return_value = mock_patch_response

        client = PaperlessClient(paperless_config_add_tag)

        with patch.object(client, "_resolve_tag", mock_resolve_tag):
            result = client.mark_input_document_processed(document_id=101)

        assert result["success"] is False
        assert result["document_id"] == 101
        assert "error" in result
        assert "API Error" in result["error"]

    def test_mark_input_document_processed_paperless_disabled(self) -> None:
        """Test that method fails when paperless integration is disabled."""
        config = Config(
            openai_api_key="test-key",  # pragma: allowlist secret
            paperless_enabled=False,  # Disabled
        )

        client = PaperlessClient(config)

        with pytest.raises(PaperlessUploadError, match="not enabled"):
            client.mark_input_document_processed(document_id=101)

    @patch("httpx.Client")
    def test_mark_multiple_input_documents_processed_success(
        self, mock_httpx_client: Mock, paperless_config_add_tag: Config
    ) -> None:
        """Test successful marking of multiple input documents as processed."""
        # Mock HTTP client responses
        mock_client = Mock()
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock tag resolution
        mock_resolve_tag = Mock(return_value=3)  # processed tag ID

        # Mock document GET (to retrieve current tags)
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {"tags": [1, 2]}

        # Mock document PATCH (to update tags)
        mock_patch_response = Mock()
        mock_patch_response.raise_for_status.return_value = None
        mock_patch_response.json.return_value = {"tags": [1, 2, 3]}

        mock_client.get.return_value = mock_get_response
        mock_client.patch.return_value = mock_patch_response

        client = PaperlessClient(paperless_config_add_tag)
        document_ids = [101, 102, 103]

        with patch.object(client, "_resolve_tag", mock_resolve_tag):
            result = client.mark_multiple_input_documents_processed(document_ids)

        assert result["success"] is True
        assert len(result["processed"]) == 3
        assert len(result["errors"]) == 0

        # Verify API calls - GET and PATCH for each document
        assert mock_client.get.call_count == 3
        assert mock_client.patch.call_count == 3

    @patch("httpx.Client")
    def test_mark_multiple_input_documents_processed_partial_failure(
        self, mock_httpx_client: Mock, paperless_config_add_tag: Config
    ) -> None:
        """Test handling of partial failures when marking multiple documents."""
        # Mock HTTP client responses
        mock_client = Mock()
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock tag resolution
        mock_resolve_tag = Mock(return_value=3)

        # Mock successful GET responses for all documents
        mock_get_response = Mock()
        mock_get_response.raise_for_status.return_value = None
        mock_get_response.json.return_value = {"tags": [1, 2]}
        mock_client.get.return_value = mock_get_response

        # Mock PATCH responses: first succeeds, second fails, third succeeds
        def patch_side_effect(*args, **kwargs):
            if "102" in args[0]:  # Second document fails
                raise Exception("Network error")

            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"tags": [1, 2, 3]}
            return mock_response

        mock_client.patch.side_effect = patch_side_effect

        client = PaperlessClient(paperless_config_add_tag)
        document_ids = [101, 102, 103]

        with patch.object(client, "_resolve_tag", mock_resolve_tag):
            result = client.mark_multiple_input_documents_processed(document_ids)

        assert result["success"] is False  # At least one failure
        assert len(result["processed"]) == 2  # Two succeeded
        assert len(result["errors"]) == 1  # One failed

        # Verify error details
        error = result["errors"][0]
        assert error["document_id"] == 102
        assert "Network error" in error["error"]

    def test_mark_multiple_input_documents_processed_empty_list(
        self, paperless_config_add_tag: Config
    ) -> None:
        """Test handling of empty document list."""
        client = PaperlessClient(paperless_config_add_tag)

        result = client.mark_multiple_input_documents_processed([])

        assert result["success"] is True
        assert len(result["processed"]) == 0
        assert len(result["errors"]) == 0

    @patch("httpx.Client")
    def test_should_mark_input_document_processed_true(
        self, mock_httpx_client: Mock, paperless_config_add_tag: Config
    ) -> None:
        """Test helper method returns True when input tagging should proceed."""
        client = PaperlessClient(paperless_config_add_tag)

        assert client.should_mark_input_document_processed() is True

    def test_should_mark_input_document_processed_false_disabled(
        self, paperless_config_disabled: Config
    ) -> None:
        """Test helper method returns False when input tagging is disabled."""
        client = PaperlessClient(paperless_config_disabled)

        assert client.should_mark_input_document_processed() is False

    def test_should_mark_input_document_processed_false_no_config(self) -> None:
        """Test helper method returns False when no tagging config is set."""
        config = Config(
            openai_api_key="test-key",  # pragma: allowlist secret
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_input_tagging_enabled=True,
            # No tagging configuration
        )

        client = PaperlessClient(config)

        assert client.should_mark_input_document_processed() is False


@pytest.mark.unit
@pytest.mark.requires_paperless
class TestPaperlessInputTaggingConfiguration:
    """Test cases for input tagging configuration validation."""

    def test_config_defaults(self) -> None:
        """Test that configuration defaults are correct."""
        config = Config(openai_api_key="test-key")

        assert config.paperless_input_processed_tag is None
        assert config.paperless_input_remove_unprocessed_tag is False
        assert config.paperless_input_processing_tag is None
        assert config.paperless_input_tagging_enabled is True

    def test_config_environment_variable_mapping(self) -> None:
        """Test that environment variables map to config fields correctly."""
        import os

        from src.bank_statement_separator.config import load_config

        # Set test environment variables
        test_env = {
            "OPENAI_API_KEY": "test-key",  # pragma: allowlist secret
            "PAPERLESS_INPUT_PROCESSED_TAG": "processed-by-separator",
            "PAPERLESS_INPUT_REMOVE_UNPROCESSED_TAG": "true",
            "PAPERLESS_INPUT_PROCESSING_TAG": "separator-processed",
            "PAPERLESS_INPUT_TAGGING_ENABLED": "false",
        }

        with patch.dict(os.environ, test_env):
            config = load_config()

            assert config.paperless_input_processed_tag == "processed-by-separator"
            assert config.paperless_input_remove_unprocessed_tag is True
            assert config.paperless_input_processing_tag == "separator-processed"
            assert config.paperless_input_tagging_enabled is False

    def test_config_mutually_exclusive_options(self) -> None:
        """Test that multiple tagging options can coexist (precedence handled in code)."""
        config = Config(
            openai_api_key="test-key",  # pragma: allowlist secret
            paperless_input_processed_tag="processed",
            paperless_input_remove_unprocessed_tag=True,
            paperless_input_processing_tag="custom-processed",
        )

        # All options can be set - precedence is handled in the client logic
        assert config.paperless_input_processed_tag == "processed"
        assert config.paperless_input_remove_unprocessed_tag is True
        assert config.paperless_input_processing_tag == "custom-processed"

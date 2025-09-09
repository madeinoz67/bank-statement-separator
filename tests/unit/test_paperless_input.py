"""Test suite for paperless-ngx input functionality (document query and download)."""

import pytest
from unittest.mock import Mock, patch
import httpx
from src.bank_statement_separator.config import Config
from src.bank_statement_separator.utils.paperless_client import (
    PaperlessClient,
    PaperlessUploadError,
)


@pytest.mark.unit
@pytest.mark.requires_paperless
@pytest.mark.mock_heavy
class TestPaperlessDocumentQuery:
    """Test cases for paperless-ngx document query functionality."""

    @pytest.fixture
    def paperless_config(self):
        """Create a test configuration with paperless input features enabled."""
        return Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_input_tags=["unprocessed", "bank-statement-raw"],
            paperless_input_correspondent="Bank",
            paperless_input_document_type="Raw Statement",
            paperless_max_documents=50,
            paperless_query_timeout=30,
        )

    @pytest.fixture
    def paperless_client(self, paperless_config):
        """Create a PaperlessClient instance with input functionality."""
        return PaperlessClient(paperless_config)

    @pytest.fixture
    def mock_documents_response(self):
        """Mock response for documents API call."""
        return {
            "count": 3,
            "results": [
                {
                    "id": 101,
                    "title": "Bank Statement Jan 2024",
                    "created": "2024-01-15T10:00:00Z",
                    "original_file_name": "statement_jan_2024.pdf",
                    "content_type": "application/pdf",
                    "tags": [1, 2],  # unprocessed, bank-statement-raw
                    "correspondent": 10,
                    "document_type": 20,
                    "storage_path": 30,
                    "download_url": "/api/documents/101/download/",
                },
                {
                    "id": 102,
                    "title": "Bank Statement Feb 2024",
                    "created": "2024-02-15T10:00:00Z",
                    "original_file_name": "statement_feb_2024.pdf",
                    "content_type": "application/pdf",
                    "tags": [1, 2],
                    "correspondent": 10,
                    "document_type": 20,
                    "storage_path": 30,
                    "download_url": "/api/documents/102/download/",
                },
                {
                    "id": 103,
                    "title": "Bank Statement Mar 2024",
                    "created": "2024-03-15T10:00:00Z",
                    "original_file_name": "statement_mar_2024.pdf",
                    "content_type": "application/pdf",
                    "tags": [1, 2],
                    "correspondent": 10,
                    "document_type": 20,
                    "storage_path": 30,
                    "download_url": "/api/documents/103/download/",
                },
            ],
        }

    @patch("httpx.Client")
    def test_query_documents_by_tags_success(
        self, mock_httpx_client, paperless_client, mock_documents_response
    ):
        """Test successful document query by tags."""
        # Mock the HTTP client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_documents_response
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock tag resolution
        with patch.object(paperless_client, "_resolve_tags", return_value=[1, 2]):
            result = paperless_client.query_documents_by_tags(
                ["unprocessed", "bank-statement-raw"]
            )

        assert result["success"] is True
        assert result["count"] == 3
        assert len(result["documents"]) == 3

        # Verify first document structure
        doc = result["documents"][0]
        assert doc["id"] == 101
        assert doc["title"] == "Bank Statement Jan 2024"
        assert doc["original_file_name"] == "statement_jan_2024.pdf"
        assert doc["download_url"] == "/api/documents/101/download/"

        # Verify API call
        mock_client.get.assert_called_once()
        call_args = mock_client.get.call_args
        assert "/api/documents/" in call_args[0][0]
        assert "tags__id__in" in call_args[1]["params"]
        assert call_args[1]["params"]["tags__id__in"] == "1,2"

    @patch("httpx.Client")
    def test_query_documents_by_tags_with_limit(
        self, mock_httpx_client, paperless_client, mock_documents_response
    ):
        """Test document query with page size limit."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_documents_response
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with patch.object(paperless_client, "_resolve_tags", return_value=[1]):
            result = paperless_client.query_documents_by_tags(
                tags=["unprocessed"], page_size=25
            )

        assert result["success"] is True

        # Verify page_size parameter was passed
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["page_size"] == 25

    @patch("httpx.Client")
    def test_query_documents_by_tags_empty_result(
        self, mock_httpx_client, paperless_client
    ):
        """Test document query with no matching documents."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"count": 0, "results": []}
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with patch.object(paperless_client, "_resolve_tags", return_value=[999]):
            result = paperless_client.query_documents_by_tags(["nonexistent-tag"])

        assert result["success"] is True
        assert result["count"] == 0
        assert len(result["documents"]) == 0

    @patch("httpx.Client")
    def test_query_documents_by_tags_connection_error(
        self, mock_httpx_client, paperless_client
    ):
        """Test document query with connection error."""
        mock_client = Mock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with patch.object(paperless_client, "_resolve_tags", return_value=[1]):
            with pytest.raises(PaperlessUploadError, match="Failed to query documents"):
                paperless_client.query_documents_by_tags(["unprocessed"])

    @patch("httpx.Client")
    def test_query_documents_by_tags_http_error(
        self, mock_httpx_client, paperless_client
    ):
        """Test document query with HTTP error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized", request=Mock(), response=mock_response
        )
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with patch.object(paperless_client, "_resolve_tags", return_value=[1]):
            with pytest.raises(
                PaperlessUploadError, match="Document query failed with status 401"
            ):
                paperless_client.query_documents_by_tags(["unprocessed"])

    def test_query_documents_disabled(self):
        """Test document query when paperless is disabled."""
        config = Config(openai_api_key="test-key", paperless_enabled=False)
        client = PaperlessClient(config)

        with pytest.raises(
            PaperlessUploadError, match="Paperless integration not enabled"
        ):
            client.query_documents_by_tags(["any-tag"])

    @patch("httpx.Client")
    def test_query_documents_by_correspondent(
        self, mock_httpx_client, paperless_client, mock_documents_response
    ):
        """Test document query by correspondent."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_documents_response
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with patch.object(paperless_client, "_resolve_correspondent", return_value=10):
            result = paperless_client.query_documents_by_correspondent("Test Bank")

        assert result["success"] is True
        assert result["count"] == 3

        # Verify API call
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["correspondent"] == 10

    @patch("httpx.Client")
    def test_query_documents_by_document_type(
        self, mock_httpx_client, paperless_client, mock_documents_response
    ):
        """Test document query by document type."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_documents_response
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with patch.object(paperless_client, "_resolve_document_type", return_value=20):
            result = paperless_client.query_documents_by_document_type("Bank Statement")

        assert result["success"] is True
        assert result["count"] == 3

        # Verify API call
        call_args = mock_client.get.call_args
        assert call_args[1]["params"]["document_type"] == 20

    @patch("httpx.Client")
    def test_query_documents_combined_filters(
        self, mock_httpx_client, paperless_client, mock_documents_response
    ):
        """Test document query with combined filters."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_documents_response
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Mock resolution methods
        with (
            patch.object(paperless_client, "_resolve_tags", return_value=[1, 2]),
            patch.object(paperless_client, "_resolve_correspondent", return_value=10),
            patch.object(paperless_client, "_resolve_document_type", return_value=20),
        ):
            result = paperless_client.query_documents(
                tags=["unprocessed", "bank-statement"],
                correspondent="Test Bank",
                document_type="Bank Statement",
                page_size=10,
            )

        assert result["success"] is True
        assert result["count"] == 3

        # Verify combined parameters
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["tags__id__in"] == "1,2"
        assert params["correspondent"] == 10
        assert params["document_type"] == 20
        assert params["page_size"] == 10

    @patch("httpx.Client")
    def test_query_documents_with_date_range(
        self, mock_httpx_client, paperless_client, mock_documents_response
    ):
        """Test document query with date range filter."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_documents_response
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        from datetime import date

        start_date = date(2024, 1, 1)
        end_date = date(2024, 3, 31)

        with patch.object(paperless_client, "_resolve_tags", return_value=[1]):
            result = paperless_client.query_documents(
                tags=["unprocessed"], created_after=start_date, created_before=end_date
            )

        assert result["success"] is True

        # Verify date parameters
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert params["created__date__gte"] == "2024-01-01"
        assert params["created__date__lte"] == "2024-03-31"


@pytest.mark.unit
@pytest.mark.requires_paperless
@pytest.mark.mock_heavy
class TestPaperlessDocumentDownload:
    """Test cases for paperless-ngx document download functionality."""

    @pytest.fixture
    def paperless_config(self):
        """Create a test configuration with paperless enabled."""
        return Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_query_timeout=30,
        )

    @pytest.fixture
    def paperless_client(self, paperless_config):
        """Create a PaperlessClient instance."""
        return PaperlessClient(paperless_config)

    @pytest.fixture
    def mock_pdf_content(self):
        """Mock PDF file content."""
        return b"%PDF-1.4\n%mock pdf content for testing\n%%EOF"

    @patch("httpx.Client")
    def test_download_document_success(
        self, mock_httpx_client, paperless_client, mock_pdf_content, tmp_path
    ):
        """Test successful document download."""
        # Mock the HTTP client
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = mock_pdf_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        # Download document
        document_id = 101
        output_file = tmp_path / "downloaded_statement.pdf"

        result = paperless_client.download_document(
            document_id=document_id, output_path=output_file
        )

        assert result["success"] is True
        assert result["document_id"] == document_id
        assert result["output_path"] == str(output_file)
        assert result["file_size"] > 0

        # Verify file was created with correct content
        assert output_file.exists()
        assert output_file.read_bytes() == mock_pdf_content

        # Verify API call
        mock_client.get.assert_called_once_with(
            "http://localhost:8000/api/documents/101/download/",
            headers=paperless_client.headers,
        )

    @patch("httpx.Client")
    def test_download_document_auto_filename(
        self, mock_httpx_client, paperless_client, mock_pdf_content, tmp_path
    ):
        """Test document download with auto-generated filename."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = mock_pdf_content
        mock_response.headers = {
            "content-type": "application/pdf",
            "content-disposition": 'attachment; filename="bank_statement_jan.pdf"',
        }
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        result = paperless_client.download_document(
            document_id=101, output_directory=tmp_path
        )

        assert result["success"] is True
        expected_file = tmp_path / "document_101.pdf"  # Default naming pattern
        assert result["output_path"] == str(expected_file)
        assert expected_file.exists()

    @patch("httpx.Client")
    def test_download_document_connection_error(
        self, mock_httpx_client, paperless_client, tmp_path
    ):
        """Test document download with connection error."""
        mock_client = Mock()
        mock_client.get.side_effect = httpx.RequestError("Connection failed")
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        output_file = tmp_path / "test.pdf"

        with pytest.raises(
            PaperlessUploadError, match="Failed to download document 101"
        ):
            paperless_client.download_document(document_id=101, output_path=output_file)

    @patch("httpx.Client")
    def test_download_document_http_error(
        self, mock_httpx_client, paperless_client, tmp_path
    ):
        """Test document download with HTTP error."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Document not found"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "404 Not Found", request=Mock(), response=mock_response
        )
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        output_file = tmp_path / "test.pdf"

        with pytest.raises(
            PaperlessUploadError, match="Document download failed with status 404"
        ):
            paperless_client.download_document(document_id=101, output_path=output_file)

    def test_download_document_disabled(self, tmp_path):
        """Test document download when paperless is disabled."""
        config = Config(openai_api_key="test-key", paperless_enabled=False)
        client = PaperlessClient(config)

        output_file = tmp_path / "test.pdf"

        with pytest.raises(
            PaperlessUploadError, match="Paperless integration not enabled"
        ):
            client.download_document(document_id=101, output_path=output_file)

    @patch("httpx.Client")
    def test_download_multiple_documents_success(
        self, mock_httpx_client, paperless_client, mock_pdf_content, tmp_path
    ):
        """Test successful download of multiple documents."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = mock_pdf_content
        mock_response.headers = {"content-type": "application/pdf"}
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        document_ids = [101, 102, 103]
        result = paperless_client.download_multiple_documents(
            document_ids=document_ids, output_directory=tmp_path
        )

        assert result["success"] is True
        assert len(result["downloads"]) == 3
        assert len(result["errors"]) == 0

        # Verify all files were created
        for i, doc_id in enumerate(document_ids):
            expected_file = tmp_path / f"document_{doc_id}.pdf"
            assert expected_file.exists()
            assert result["downloads"][i]["document_id"] == doc_id
            assert result["downloads"][i]["output_path"] == str(expected_file)

        # Verify API calls
        assert mock_client.get.call_count == 3

    @patch("httpx.Client")
    def test_download_multiple_documents_partial_failure(
        self, mock_httpx_client, paperless_client, mock_pdf_content, tmp_path
    ):
        """Test download of multiple documents with some failures."""
        mock_client = Mock()

        def side_effect(url, **kwargs):
            if "102" in url:  # Second document fails
                raise httpx.RequestError("Network error")

            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = mock_pdf_content
            mock_response.headers = {"content-type": "application/pdf"}
            return mock_response

        mock_client.get.side_effect = side_effect
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        document_ids = [101, 102, 103]
        result = paperless_client.download_multiple_documents(
            document_ids=document_ids, output_directory=tmp_path
        )

        assert result["success"] is False  # At least one failure
        assert len(result["downloads"]) == 2  # First and third succeeded
        assert len(result["errors"]) == 1  # Second failed

        # Verify successful downloads
        assert (tmp_path / "document_101.pdf").exists()
        assert (tmp_path / "document_103.pdf").exists()
        assert not (tmp_path / "document_102.pdf").exists()  # Failed download

        # Verify error details
        error = result["errors"][0]
        assert error["document_id"] == 102
        assert "Network error" in error["error"]

    def test_download_multiple_documents_empty_list(self, paperless_client, tmp_path):
        """Test download of empty document list."""
        result = paperless_client.download_multiple_documents(
            document_ids=[], output_directory=tmp_path
        )

        assert result["success"] is True
        assert len(result["downloads"]) == 0
        assert len(result["errors"]) == 0

    @patch("httpx.Client")
    def test_download_document_invalid_content_type(
        self, mock_httpx_client, paperless_client, tmp_path
    ):
        """Test document download with non-PDF content type should fail."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.content = b"<html>Not a PDF</html>"
        mock_response.headers = {"content-type": "text/html"}  # Unexpected type
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        output_file = tmp_path / "test.pdf"

        # Should fail for non-PDF content types
        with pytest.raises(
            PaperlessUploadError, match="Document 101 is not a PDF file"
        ):
            paperless_client.download_document(document_id=101, output_path=output_file)

        # File should not be created
        assert not output_file.exists()


@pytest.mark.unit
@pytest.mark.requires_paperless
@pytest.mark.mock_heavy
class TestPaperlessDocumentValidation:
    """Test cases for paperless-ngx document type validation (PDF-only)."""

    @pytest.fixture
    def paperless_config(self):
        """Create a test configuration with paperless enabled."""
        return Config(
            openai_api_key="test-key",
            paperless_enabled=True,
            paperless_url="http://localhost:8000",
            paperless_token="test-token-123",
            paperless_input_tags=["unprocessed", "bank-statement-raw"],
        )

    @pytest.fixture
    def paperless_client(self, paperless_config):
        """Create a PaperlessClient instance."""
        return PaperlessClient(paperless_config)

    @pytest.fixture
    def mock_mixed_documents_response(self):
        """Mock response with mixed document types (PDF and non-PDF)."""
        return {
            "count": 4,
            "results": [
                {
                    "id": 101,
                    "title": "Bank Statement Jan 2024",
                    "original_file_name": "statement_jan_2024.pdf",
                    "content_type": "application/pdf",
                    "tags": [1, 2],
                    "download_url": "/api/documents/101/download/",
                },
                {
                    "id": 102,
                    "title": "Bank Statement Feb 2024",
                    "original_file_name": "statement_feb_2024.docx",
                    "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "tags": [1, 2],
                    "download_url": "/api/documents/102/download/",
                },
                {
                    "id": 103,
                    "title": "Bank Statement Mar 2024",
                    "original_file_name": "statement_mar_2024.pdf",
                    "content_type": "application/pdf",
                    "tags": [1, 2],
                    "download_url": "/api/documents/103/download/",
                },
                {
                    "id": 104,
                    "title": "Bank Receipt Apr 2024",
                    "original_file_name": "receipt_apr_2024.jpg",
                    "content_type": "image/jpeg",
                    "tags": [1, 2],
                    "download_url": "/api/documents/104/download/",
                },
            ],
        }

    @patch("httpx.Client")
    def test_query_documents_filters_pdf_only(
        self, mock_httpx_client, paperless_client, mock_mixed_documents_response
    ):
        """Test that document queries automatically filter for PDF files only."""
        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mock_mixed_documents_response
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with patch.object(paperless_client, "_resolve_tags", return_value=[1, 2]):
            result = paperless_client.query_documents_by_tags(
                ["unprocessed", "bank-statement-raw"]
            )

        assert result["success"] is True
        # Should only return 2 PDF documents out of 4 total
        assert result["count"] == 2
        assert len(result["documents"]) == 2

        # Verify only PDF documents are included
        for doc in result["documents"]:
            assert doc["content_type"] == "application/pdf"
            assert doc["original_file_name"].endswith(".pdf")

        # Verify specific PDF documents are included
        doc_ids = [doc["id"] for doc in result["documents"]]
        assert 101 in doc_ids  # PDF document
        assert 103 in doc_ids  # PDF document
        assert 102 not in doc_ids  # DOCX document (filtered out)
        assert 104 not in doc_ids  # JPEG document (filtered out)

        # Verify API call includes PDF content type filter
        call_args = mock_client.get.call_args
        params = call_args[1]["params"]
        assert "mime_type" in params
        assert params["mime_type"] == "application/pdf"

    def test_validate_document_type_pdf_valid(self, paperless_client):
        """Test document type validation for valid PDF documents."""
        # Valid PDF documents
        valid_docs = [
            {"content_type": "application/pdf", "original_file_name": "doc.pdf"},
            {"mime_type": "application/pdf", "original_file_name": "statement.pdf"},
            {"content_type": "application/pdf", "original_file_name": "STATEMENT.PDF"},
        ]

        for doc in valid_docs:
            assert paperless_client._is_pdf_document(doc) is True

    def test_validate_document_type_non_pdf_invalid(self, paperless_client):
        """Test document type validation for non-PDF documents."""
        # Invalid non-PDF documents
        invalid_docs = [
            {"content_type": "application/msword", "original_file_name": "doc.doc"},
            {"content_type": "image/jpeg", "original_file_name": "image.jpg"},
            {"content_type": "text/plain", "original_file_name": "text.txt"},
            {
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "original_file_name": "doc.docx",
            },
            {"content_type": "image/png", "original_file_name": "screenshot.png"},
            {"content_type": "application/zip", "original_file_name": "archive.zip"},
        ]

        for doc in invalid_docs:
            assert paperless_client._is_pdf_document(doc) is False

    def test_validate_document_type_missing_fields(self, paperless_client):
        """Test document type validation with missing metadata fields."""
        # Documents with missing content type info - should be rejected
        incomplete_docs = [
            {"original_file_name": "unknown.pdf"},  # Missing content_type
            {},  # Missing both fields
            {"title": "Some Document"},  # Different fields entirely
        ]

        for doc in incomplete_docs:
            assert paperless_client._is_pdf_document(doc) is False

        # Document with valid content type should still pass even without filename
        valid_doc = {"content_type": "application/pdf"}
        assert paperless_client._is_pdf_document(valid_doc) is True

    def test_validate_document_type_edge_cases(self, paperless_client):
        """Test document type validation edge cases."""
        # Edge cases that should be handled correctly
        edge_cases = [
            # Case insensitive content type
            {"content_type": "APPLICATION/PDF", "original_file_name": "doc.pdf"},
            # PDF with additional parameters
            {
                "content_type": "application/pdf; charset=utf-8",
                "original_file_name": "doc.pdf",
            },
            # Mixed case filename extension
            {"content_type": "application/pdf", "original_file_name": "doc.PDF"},
            {"content_type": "application/pdf", "original_file_name": "doc.Pdf"},
        ]

        for doc in edge_cases:
            assert paperless_client._is_pdf_document(doc) is True

    @patch("httpx.Client")
    def test_download_document_validates_pdf_content_type(
        self, mock_httpx_client, paperless_client, tmp_path
    ):
        """Test that document download validates PDF content type in response headers."""
        mock_client = Mock()

        # Test various content types
        test_cases = [
            ("application/pdf", True, "Valid PDF content type should succeed"),
            (
                "APPLICATION/PDF",
                True,
                "Case insensitive PDF content type should succeed",
            ),
            (
                "application/pdf; charset=utf-8",
                True,
                "PDF with parameters should succeed",
            ),
            ("text/html", False, "HTML content type should fail"),
            ("image/jpeg", False, "JPEG content type should fail"),
            ("application/msword", False, "Word document content type should fail"),
            ("application/json", False, "JSON content type should fail"),
        ]

        for content_type, should_succeed, description in test_cases:
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            mock_response.content = (
                b"%PDF-1.4\ntest content\n%%EOF"
                if should_succeed
                else b"not pdf content"
            )
            mock_response.headers = {"content-type": content_type}
            mock_client.get.return_value = mock_response
            mock_httpx_client.return_value.__enter__.return_value = mock_client

            output_file = tmp_path / f"test_{content_type.replace('/', '_')}.pdf"

            if should_succeed:
                result = paperless_client.download_document(
                    document_id=101, output_path=output_file
                )
                assert result["success"] is True, description
                assert output_file.exists(), f"File should be created: {description}"
            else:
                with pytest.raises(
                    PaperlessUploadError, match="Document 101 is not a PDF file"
                ):
                    paperless_client.download_document(
                        document_id=101, output_path=output_file
                    )
                assert (
                    not output_file.exists()
                ), f"File should not be created: {description}"

    @patch("httpx.Client")
    def test_filter_pdf_documents_from_query_results(
        self, mock_httpx_client, paperless_client
    ):
        """Test filtering of PDF documents from mixed query results."""
        # Mock response with mixed document types
        mixed_response = {
            "count": 5,
            "results": [
                {
                    "id": 1,
                    "content_type": "application/pdf",
                    "original_file_name": "doc1.pdf",
                },
                {
                    "id": 2,
                    "content_type": "image/jpeg",
                    "original_file_name": "img1.jpg",
                },
                {
                    "id": 3,
                    "content_type": "application/pdf",
                    "original_file_name": "doc2.pdf",
                },
                {
                    "id": 4,
                    "content_type": "text/plain",
                    "original_file_name": "text1.txt",
                },
                {
                    "id": 5,
                    "content_type": "application/pdf",
                    "original_file_name": "doc3.pdf",
                },
            ],
        }

        mock_client = Mock()
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = mixed_response
        mock_client.get.return_value = mock_response
        mock_httpx_client.return_value.__enter__.return_value = mock_client

        with patch.object(paperless_client, "_resolve_tags", return_value=[1]):
            result = paperless_client.query_documents_by_tags(["test-tag"])

        # Should filter to only PDF documents
        assert result["success"] is True
        assert result["count"] == 3  # Only 3 PDF documents

        pdf_ids = [doc["id"] for doc in result["documents"]]
        assert pdf_ids == [1, 3, 5]  # Only PDF document IDs

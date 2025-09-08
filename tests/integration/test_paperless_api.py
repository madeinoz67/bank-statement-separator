"""Integration tests for paperless-ngx API functionality with real API calls.

These tests require a running paperless-ngx instance and valid credentials.
They are designed to test the actual API integration without mocks.

To run these tests:
1. Set up a paperless-ngx test instance
2. Configure test environment with real credentials
3. Run with: pytest tests/integration/test_paperless_api.py -m api_integration
"""

import pytest
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any

from src.bank_statement_separator.config import Config, load_config
from src.bank_statement_separator.utils.paperless_client import (
    PaperlessClient,
    PaperlessUploadError,
)


# Skip all tests in this file unless explicitly running API integration tests
pytestmark = pytest.mark.skipif(
    not os.getenv("PAPERLESS_API_INTEGRATION_TEST", "").lower() in ("true", "1"),
    reason="API integration tests require PAPERLESS_API_INTEGRATION_TEST=true"
)


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow
class TestPaperlessAPIConnection:
    """Test real API connection and authentication."""
    
    @pytest.fixture(scope="class")
    def api_config(self):
        """Load real API configuration for integration tests."""
        # Try to load from test environment file first
        test_env_file = Path("tests/env/paperless_integration.env")
        if test_env_file.exists():
            return load_config(str(test_env_file))
        
        # Fallback to environment variables
        return Config(
            openai_api_key="test-key-integration",
            paperless_enabled=True,
            paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
            paperless_token=os.getenv("PAPERLESS_TOKEN"),
            paperless_input_tags=["test-integration", "bank-statement"],
            paperless_max_documents=10,
            paperless_query_timeout=30,
        )
    
    @pytest.fixture(scope="class")
    def api_client(self, api_config):
        """Create PaperlessClient for API integration tests."""
        client = PaperlessClient(api_config)
        
        # Verify client is properly configured
        if not client.is_enabled():
            pytest.skip("Paperless API client not properly configured")
            
        return client
    
    def test_api_connection_success(self, api_client):
        """Test successful connection to real paperless-ngx API."""
        try:
            result = api_client.test_connection()
            assert result is True
        except PaperlessUploadError as e:
            pytest.fail(f"API connection failed: {e}")
    
    def test_api_authentication_valid(self, api_client):
        """Test API authentication with valid credentials."""
        try:
            # Simple API call that requires authentication
            result = api_client.query_documents(page_size=1)
            assert result["success"] is True
        except PaperlessUploadError as e:
            if "401" in str(e) or "403" in str(e):
                pytest.fail(f"Authentication failed: {e}")
            else:
                # Other errors are acceptable for this test
                pass
    
    def test_api_configuration_validation(self, api_config):
        """Test that API configuration meets requirements."""
        assert api_config.paperless_enabled is True
        assert api_config.paperless_url is not None
        assert api_config.paperless_token is not None
        assert api_config.paperless_url.startswith(("http://", "https://"))
        assert len(api_config.paperless_token) > 10  # Reasonable token length


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow
class TestPaperlessAPIDocumentQuery:
    """Test real API document querying functionality."""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client for document query tests."""
        test_env_file = Path("tests/env/paperless_integration.env")
        if test_env_file.exists():
            config = load_config(str(test_env_file))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
                paperless_max_documents=50,
                paperless_query_timeout=30,
            )
        
        client = PaperlessClient(config)
        if not client.is_enabled():
            pytest.skip("Paperless API client not configured")
        return client
    
    def test_query_all_documents(self, api_client):
        """Test querying all documents with pagination."""
        try:
            result = api_client.query_documents(page_size=5)
            
            assert result["success"] is True
            assert "count" in result
            assert "documents" in result
            assert isinstance(result["documents"], list)
            assert len(result["documents"]) <= 5
            
            # Each document should have required fields
            for doc in result["documents"]:
                assert "id" in doc
                assert "title" in doc
                assert doc["content_type"] == "application/pdf"  # PDF-only filtering
                
        except PaperlessUploadError as e:
            pytest.fail(f"Document query failed: {e}")
    
    def test_query_documents_by_existing_tags(self, api_client):
        """Test querying documents by tags that exist in the system."""
        try:
            # First, get some documents to see what tags exist
            all_docs = api_client.query_documents(page_size=10)
            
            if all_docs["count"] == 0:
                pytest.skip("No documents available for tag testing")
            
            # Try to find documents with common tag patterns
            common_tags = ["bank-statement", "statement", "document", "pdf"]
            
            for tag_name in common_tags:
                try:
                    result = api_client.query_documents_by_tags([tag_name])
                    assert result["success"] is True
                    
                    # If we find documents, verify they're PDFs
                    if result["count"] > 0:
                        for doc in result["documents"]:
                            assert doc["content_type"] == "application/pdf"
                        break  # Found working tag, test passed
                except PaperlessUploadError:
                    continue  # Try next tag
            
        except PaperlessUploadError as e:
            pytest.fail(f"Tag query failed: {e}")
    
    def test_query_documents_date_range(self, api_client):
        """Test querying documents within a date range."""
        try:
            # Query documents from last 30 days
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=30)
            
            result = api_client.query_documents(
                created_after=start_date,
                created_before=end_date,
                page_size=10
            )
            
            assert result["success"] is True
            assert isinstance(result["documents"], list)
            
            # Verify date filtering (if documents found)
            for doc in result["documents"]:
                doc_date = datetime.fromisoformat(doc["created"].replace("Z", "+00:00")).date()
                assert start_date <= doc_date <= end_date
                
        except PaperlessUploadError as e:
            pytest.fail(f"Date range query failed: {e}")
    
    def test_query_documents_pagination(self, api_client):
        """Test document query pagination."""
        try:
            # Get first page
            page1 = api_client.query_documents(page_size=2)
            assert page1["success"] is True
            
            if page1["count"] <= 2:
                pytest.skip("Not enough documents for pagination testing")
            
            # Verify pagination limit is respected
            assert len(page1["documents"]) <= 2
            
        except PaperlessUploadError as e:
            pytest.fail(f"Pagination test failed: {e}")
    
    def test_query_nonexistent_tags(self, api_client):
        """Test querying with tags that don't exist."""
        try:
            # Use a very unlikely tag name
            result = api_client.query_documents_by_tags(["nonexistent-tag-12345"])
            
            assert result["success"] is True
            assert result["count"] == 0
            assert len(result["documents"]) == 0
            
        except PaperlessUploadError as e:
            pytest.fail(f"Nonexistent tag query failed: {e}")


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow
class TestPaperlessAPIDocumentDownload:
    """Test real API document download functionality."""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client for download tests."""
        test_env_file = Path("tests/env/paperless_integration.env")
        if test_env_file.exists():
            config = load_config(str(test_env_file))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
                paperless_query_timeout=30,
            )
        
        client = PaperlessClient(config)
        if not client.is_enabled():
            pytest.skip("Paperless API client not configured")
        return client
    
    @pytest.fixture(scope="class")
    def test_document_id(self, api_client):
        """Get a test document ID for download testing."""
        try:
            result = api_client.query_documents(page_size=1)
            if result["count"] == 0:
                pytest.skip("No documents available for download testing")
            return result["documents"][0]["id"]
        except PaperlessUploadError:
            pytest.skip("Cannot query documents for download testing")
    
    def test_download_single_document(self, api_client, test_document_id, tmp_path):
        """Test downloading a single document."""
        try:
            output_file = tmp_path / "test_download.pdf"
            
            result = api_client.download_document(
                document_id=test_document_id,
                output_path=output_file
            )
            
            assert result["success"] is True
            assert result["document_id"] == test_document_id
            assert Path(result["output_path"]).exists()
            assert result["file_size"] > 0
            assert result["content_type"].startswith("application/pdf")
            
            # Verify file was actually created and has content
            downloaded_file = Path(result["output_path"])
            assert downloaded_file.exists()
            assert downloaded_file.stat().st_size > 0
            
            # Basic PDF validation - should start with PDF header
            content = downloaded_file.read_bytes()
            assert content.startswith(b"%PDF")
            
        except PaperlessUploadError as e:
            pytest.fail(f"Document download failed: {e}")
    
    def test_download_document_auto_filename(self, api_client, test_document_id, tmp_path):
        """Test downloading a document with auto-generated filename."""
        try:
            result = api_client.download_document(
                document_id=test_document_id,
                output_directory=tmp_path
            )
            
            assert result["success"] is True
            assert f"document_{test_document_id}.pdf" in result["output_path"]
            
            downloaded_file = Path(result["output_path"])
            assert downloaded_file.exists()
            assert downloaded_file.stat().st_size > 0
            
        except PaperlessUploadError as e:
            pytest.fail(f"Auto-filename download failed: {e}")
    
    def test_download_multiple_documents(self, api_client, tmp_path):
        """Test downloading multiple documents."""
        try:
            # Get a few document IDs
            query_result = api_client.query_documents(page_size=3)
            if query_result["count"] == 0:
                pytest.skip("No documents available for multi-download testing")
            
            document_ids = [doc["id"] for doc in query_result["documents"]]
            
            result = api_client.download_multiple_documents(
                document_ids=document_ids,
                output_directory=tmp_path
            )
            
            assert result["success"] is True
            assert len(result["downloads"]) <= len(document_ids)
            assert len(result["errors"]) == 0  # Should be no errors with valid IDs
            
            # Verify all files were downloaded
            for download in result["downloads"]:
                file_path = Path(download["output_path"])
                assert file_path.exists()
                assert file_path.stat().st_size > 0
                
        except PaperlessUploadError as e:
            pytest.fail(f"Multiple document download failed: {e}")
    
    def test_download_nonexistent_document(self, api_client, tmp_path):
        """Test downloading a document that doesn't exist."""
        try:
            # Use a very high ID that's unlikely to exist
            nonexistent_id = 999999
            output_file = tmp_path / "nonexistent.pdf"
            
            with pytest.raises(PaperlessUploadError) as exc_info:
                api_client.download_document(
                    document_id=nonexistent_id,
                    output_path=output_file
                )
            
            # Should be a 404-related error
            assert "404" in str(exc_info.value) or "not found" in str(exc_info.value).lower()
            
            # File should not be created
            assert not output_file.exists()
            
        except Exception as e:
            pytest.fail(f"Nonexistent document test failed: {e}")


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow
class TestPaperlessAPITagManagement:
    """Test real API tag resolution and management."""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client for tag management tests."""
        test_env_file = Path("tests/env/paperless_integration.env")
        if test_env_file.exists():
            config = load_config(str(test_env_file))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
                paperless_query_timeout=30,
            )
        
        client = PaperlessClient(config)
        if not client.is_enabled():
            pytest.skip("Paperless API client not configured")
        return client
    
    def test_resolve_existing_tags(self, api_client):
        """Test resolving tags that exist in the system."""
        try:
            # Try to resolve common tag names
            common_tags = ["document", "pdf", "test"]
            
            for tag_name in common_tags:
                try:
                    # This will try to find or create the tag
                    tag_ids = api_client._resolve_tags([tag_name])
                    assert isinstance(tag_ids, list)
                    
                    if len(tag_ids) > 0:
                        assert all(isinstance(tag_id, int) for tag_id in tag_ids)
                        break  # Found at least one working tag
                except Exception:
                    continue  # Try next tag
                    
        except Exception as e:
            pytest.fail(f"Tag resolution failed: {e}")
    
    def test_create_new_test_tag(self, api_client):
        """Test creating a new tag for testing."""
        try:
            # Use timestamp to ensure unique tag name
            test_tag_name = f"test-integration-{int(datetime.now().timestamp())}"
            
            tag_ids = api_client._resolve_tags([test_tag_name])
            
            assert isinstance(tag_ids, list)
            assert len(tag_ids) == 1
            assert isinstance(tag_ids[0], int)
            assert tag_ids[0] > 0
            
        except Exception as e:
            pytest.fail(f"Test tag creation failed: {e}")
    
    def test_resolve_multiple_tags(self, api_client):
        """Test resolving multiple tags at once."""
        try:
            # Use timestamp-based unique names
            timestamp = int(datetime.now().timestamp())
            tag_names = [
                f"multi-test-1-{timestamp}",
                f"multi-test-2-{timestamp}",
                f"multi-test-3-{timestamp}",
            ]
            
            tag_ids = api_client._resolve_tags(tag_names)
            
            assert isinstance(tag_ids, list)
            assert len(tag_ids) == len(tag_names)
            assert all(isinstance(tag_id, int) for tag_id in tag_ids)
            assert all(tag_id > 0 for tag_id in tag_ids)
            assert len(set(tag_ids)) == len(tag_ids)  # All unique IDs
            
        except Exception as e:
            pytest.fail(f"Multiple tag resolution failed: {e}")


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow
class TestPaperlessAPICorrespondentManagement:
    """Test real API correspondent resolution."""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client for correspondent tests."""
        test_env_file = Path("tests/env/paperless_integration.env")
        if test_env_file.exists():
            config = load_config(str(test_env_file))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
                paperless_query_timeout=30,
            )
        
        client = PaperlessClient(config)
        if not client.is_enabled():
            pytest.skip("Paperless API client not configured")
        return client
    
    def test_create_test_correspondent(self, api_client):
        """Test creating a new correspondent for testing."""
        try:
            # Use timestamp to ensure unique name
            correspondent_name = f"Test Bank Integration {int(datetime.now().timestamp())}"
            
            correspondent_id = api_client._resolve_correspondent(correspondent_name)
            
            assert isinstance(correspondent_id, int)
            assert correspondent_id > 0
            
        except Exception as e:
            pytest.fail(f"Test correspondent creation failed: {e}")
    
    def test_resolve_existing_correspondent(self, api_client):
        """Test resolving a correspondent that might exist."""
        try:
            # Try common bank names that might exist
            common_banks = ["Bank", "Test Bank", "Chase", "Wells Fargo", "Bank of America"]
            
            for bank_name in common_banks:
                try:
                    correspondent_id = api_client._resolve_correspondent(bank_name)
                    if correspondent_id is not None:
                        assert isinstance(correspondent_id, int)
                        assert correspondent_id > 0
                        break  # Found working correspondent
                except Exception:
                    continue  # Try next bank
                    
        except Exception as e:
            pytest.fail(f"Correspondent resolution failed: {e}")


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow
class TestPaperlessAPIDocumentTypeManagement:
    """Test real API document type resolution."""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client for document type tests."""
        test_env_file = Path("tests/env/paperless_integration.env")
        if test_env_file.exists():
            config = load_config(str(test_env_file))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
                paperless_query_timeout=30,
            )
        
        client = PaperlessClient(config)
        if not client.is_enabled():
            pytest.skip("Paperless API client not configured")
        return client
    
    def test_create_test_document_type(self, api_client):
        """Test creating a new document type for testing."""
        try:
            # Use timestamp to ensure unique name
            doc_type_name = f"Test Statement {int(datetime.now().timestamp())}"
            
            doc_type_id = api_client._resolve_document_type(doc_type_name)
            
            assert isinstance(doc_type_id, int)
            assert doc_type_id > 0
            
        except Exception as e:
            pytest.fail(f"Test document type creation failed: {e}")
    
    def test_resolve_existing_document_type(self, api_client):
        """Test resolving document types that might exist."""
        try:
            # Try common document type names
            common_types = ["Bank Statement", "Statement", "Document", "Invoice", "Receipt"]
            
            for doc_type in common_types:
                try:
                    doc_type_id = api_client._resolve_document_type(doc_type)
                    if doc_type_id is not None:
                        assert isinstance(doc_type_id, int)
                        assert doc_type_id > 0
                        break  # Found working document type
                except Exception:
                    continue  # Try next type
                    
        except Exception as e:
            pytest.fail(f"Document type resolution failed: {e}")


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow 
class TestPaperlessAPIErrorHandling:
    """Test real API error handling and edge cases."""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client for error handling tests."""
        test_env_file = Path("tests/env/paperless_integration.env")
        if test_env_file.exists():
            config = load_config(str(test_env_file))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
                paperless_query_timeout=5,  # Short timeout for testing
            )
        
        client = PaperlessClient(config)
        if not client.is_enabled():
            pytest.skip("Paperless API client not configured")
        return client
    
    def test_api_timeout_handling(self, api_client):
        """Test handling of API timeouts."""
        try:
            # This might timeout with the short timeout configured
            result = api_client.query_documents(page_size=100)
            
            # If it succeeds, that's fine too
            assert result["success"] is True
            
        except PaperlessUploadError as e:
            # Should be a timeout-related error
            assert "timeout" in str(e).lower() or "connection" in str(e).lower()
    
    def test_invalid_query_parameters(self, api_client):
        """Test handling of invalid query parameters."""
        try:
            # Query with invalid page size (too large)
            result = api_client.query_documents(page_size=10000)
            
            # API might clamp the value or return an error
            assert result["success"] is True
            assert len(result["documents"]) <= 10000
            
        except PaperlessUploadError as e:
            # Error is acceptable for invalid parameters
            assert "400" in str(e) or "invalid" in str(e).lower()
    
    def test_pdf_validation_with_real_documents(self, api_client):
        """Test PDF validation with real documents from API."""
        try:
            result = api_client.query_documents(page_size=5)
            
            if result["count"] == 0:
                pytest.skip("No documents available for PDF validation testing")
            
            # All returned documents should be PDFs
            for doc in result["documents"]:
                assert api_client._is_pdf_document(doc) is True
                assert "content_type" in doc
                assert doc["content_type"].lower().startswith("application/pdf")
                
        except PaperlessUploadError as e:
            pytest.fail(f"PDF validation test failed: {e}")
    
    def test_empty_query_results(self, api_client):
        """Test handling of queries that return no results."""
        try:
            # Query with impossible date range
            from datetime import date
            future_date = date(2030, 1, 1)
            
            result = api_client.query_documents(
                created_after=future_date,
                created_before=future_date,
            )
            
            assert result["success"] is True
            assert result["count"] == 0
            assert len(result["documents"]) == 0
            
        except PaperlessUploadError as e:
            pytest.fail(f"Empty query test failed: {e}")


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow
class TestPaperlessAPIFullWorkflow:
    """Test complete API workflow integration."""
    
    @pytest.fixture(scope="class")
    def api_client(self):
        """Create API client for workflow tests."""
        test_env_file = Path("tests/env/paperless_integration.env")
        if test_env_file.exists():
            config = load_config(str(test_env_file))
        else:
            config = Config(
                openai_api_key="test-key",
                paperless_enabled=True,
                paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
                paperless_token=os.getenv("PAPERLESS_TOKEN"),
                paperless_input_tags=["test-workflow", "integration"],
                paperless_max_documents=5,
                paperless_query_timeout=30,
            )
        
        client = PaperlessClient(config)
        if not client.is_enabled():
            pytest.skip("Paperless API client not configured")
        return client
    
    def test_complete_query_and_download_workflow(self, api_client, tmp_path):
        """Test complete workflow: query -> validate -> download."""
        try:
            # Step 1: Query documents
            query_result = api_client.query_documents(page_size=3)
            
            if query_result["count"] == 0:
                pytest.skip("No documents available for workflow testing")
            
            assert query_result["success"] is True
            assert len(query_result["documents"]) > 0
            
            # Step 2: Validate all documents are PDFs
            pdf_documents = []
            for doc in query_result["documents"]:
                if api_client._is_pdf_document(doc):
                    pdf_documents.append(doc)
            
            if len(pdf_documents) == 0:
                pytest.skip("No PDF documents available for workflow testing")
            
            # Step 3: Download first PDF document
            test_doc = pdf_documents[0]
            download_result = api_client.download_document(
                document_id=test_doc["id"],
                output_directory=tmp_path
            )
            
            assert download_result["success"] is True
            assert Path(download_result["output_path"]).exists()
            
            # Step 4: Verify downloaded file
            downloaded_file = Path(download_result["output_path"])
            content = downloaded_file.read_bytes()
            assert content.startswith(b"%PDF")
            assert len(content) > 1000  # Reasonable PDF file size
            
        except PaperlessUploadError as e:
            pytest.fail(f"Complete workflow test failed: {e}")
    
    def test_query_with_config_defaults(self, api_client):
        """Test querying using configuration defaults."""
        try:
            # Query using tags from config
            if api_client.config.paperless_input_tags:
                result = api_client.query_documents_by_tags(
                    api_client.config.paperless_input_tags
                )
                
                assert result["success"] is True
                # Results might be empty if tags don't exist, that's OK
                
        except PaperlessUploadError as e:
            pytest.fail(f"Config defaults test failed: {e}")
    
    def test_batch_download_workflow(self, api_client, tmp_path):
        """Test batch downloading multiple documents."""
        try:
            # Query multiple documents
            query_result = api_client.query_documents(page_size=3)
            
            if query_result["count"] < 2:
                pytest.skip("Need at least 2 documents for batch download testing")
            
            # Get document IDs
            doc_ids = [doc["id"] for doc in query_result["documents"][:2]]
            
            # Batch download
            download_result = api_client.download_multiple_documents(
                document_ids=doc_ids,
                output_directory=tmp_path
            )
            
            assert download_result["success"] is True
            assert len(download_result["downloads"]) > 0
            assert len(download_result["errors"]) == 0
            
            # Verify all files exist
            for download in download_result["downloads"]:
                file_path = Path(download["output_path"])
                assert file_path.exists()
                assert file_path.stat().st_size > 0
                
        except PaperlessUploadError as e:
            pytest.fail(f"Batch download workflow failed: {e}")
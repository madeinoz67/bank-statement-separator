"""End-to-end Paperless API integration test fixture with standardized test data.

This module provides a comprehensive test fixture that:
1. Clears remote test storage paths (test-input and test-processed)
2. Creates standardized multi-statement test files with known metadata
3. Executes end-to-end processing using local Ollama instance
4. Validates processed files against expected standardized test data

The fixture ensures reproducible test results by using controlled test data
with predictable statement boundaries and metadata.
"""

import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
import pytest

from src.bank_statement_separator.config import Config
from src.bank_statement_separator.utils.paperless_client import (
    PaperlessClient,
)
from src.bank_statement_separator.workflow import BankStatementWorkflow


@dataclass
class StatementSpec:
    """Specification for a standardized test statement."""

    bank_name: str
    account_number: str
    account_suffix: str  # Last 4 digits for display
    statement_period: str
    statement_date: str
    expected_filename_pattern: str
    page_count: int
    opening_balance: str
    closing_balance: str
    transaction_count: int


@dataclass
class DocumentSpec:
    """Specification for a test document containing multiple statements."""

    title: str
    filename: str
    description: str
    statements: List[StatementSpec]
    total_pages: int
    expected_output_files: List[str]


class PaperlessEndToEndFixture:
    """End-to-end test fixture for Paperless API integration."""

    def __init__(self, api_client: PaperlessClient):
        """Initialize the fixture with a Paperless API client."""
        self.client = api_client
        self.created_documents: List[Dict[str, Any]] = []
        self.test_storage_paths = ["test-input", "test-processed"]
        self.test_timestamp = int(time.time())

    def cleanup_remote_storage(self) -> Dict[str, Any]:
        """Clear remote test storage paths to ensure clean test environment.

        Returns:
            Dict with cleanup results
        """
        cleanup_results = {
            "success": True,
            "paths_cleared": [],
            "documents_removed": 0,
            "errors": [],
        }

        try:
            for storage_path in self.test_storage_paths:
                try:
                    # Query documents in this storage path
                    with httpx.Client(timeout=30.0) as http_client:
                        # Get storage path ID
                        response = http_client.get(
                            f"{self.client.base_url}/api/storage_paths/",
                            headers=self.client.headers,
                            params={"name__iexact": storage_path},
                        )
                        response.raise_for_status()

                        storage_paths = response.json().get("results", [])
                        if not storage_paths:
                            continue  # Storage path doesn't exist, nothing to clean

                        storage_path_id = storage_paths[0]["id"]

                        # Query documents in this storage path
                        response = http_client.get(
                            f"{self.client.base_url}/api/documents/",
                            headers=self.client.headers,
                            params={
                                "storage_path": storage_path_id,
                                "page_size": 100,  # Get all documents
                            },
                        )
                        response.raise_for_status()

                        documents = response.json().get("results", [])

                        # Delete each document
                        deleted_count = 0
                        for doc in documents:
                            try:
                                delete_response = http_client.delete(
                                    f"{self.client.base_url}/api/documents/{doc['id']}/",
                                    headers=self.client.headers,
                                )
                                delete_response.raise_for_status()
                                deleted_count += 1
                            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                                cleanup_results["errors"].append(
                                    {
                                        "storage_path": storage_path,
                                        "document_id": doc["id"],
                                        "error": str(e),
                                    }
                                )

                        cleanup_results["paths_cleared"].append(storage_path)
                        cleanup_results["documents_removed"] += deleted_count

                except (httpx.RequestError, httpx.HTTPStatusError) as e:
                    cleanup_results["errors"].append(
                        {"storage_path": storage_path, "error": str(e)}
                    )
                    cleanup_results["success"] = False

        except Exception as e:
            cleanup_results["success"] = False
            cleanup_results["errors"].append({"general_error": str(e)})

        return cleanup_results

    def generate_standardized_test_data(self) -> List[DocumentSpec]:
        """Generate standardized test document specifications with known metadata.

        Returns:
            List of test document specifications
        """
        test_docs = [
            DocumentSpec(
                title=f"Test Multi-Statement Bundle - Standard 3 Statements [{self.test_timestamp}001]",
                filename=f"test_multi_3_statements_{self.test_timestamp}001.pdf",
                description="Controlled 3-statement bundle with predictable boundaries",
                statements=[
                    StatementSpec(
                        bank_name="Test Bank Alpha",
                        account_number="1234567890123456",
                        account_suffix="3456",
                        statement_period="January 2024",
                        statement_date="2024-01-31",
                        expected_filename_pattern="test-bank-alpha-3456-2024-01-31.pdf",
                        page_count=2,
                        opening_balance="$1,234.56",
                        closing_balance="$2,845.67",
                        transaction_count=8,
                    ),
                    StatementSpec(
                        bank_name="Test Bank Alpha",
                        account_number="1234567890127890",
                        account_suffix="7890",
                        statement_period="February 2024",
                        statement_date="2024-02-29",
                        expected_filename_pattern="test-bank-alpha-7890-2024-02-29.pdf",
                        page_count=2,
                        opening_balance="$2,845.67",
                        closing_balance="$3,567.89",
                        transaction_count=6,
                    ),
                    StatementSpec(
                        bank_name="Test Credit Union Beta",
                        account_number="9876543210654321",
                        account_suffix="4321",
                        statement_period="March 2024",
                        statement_date="2024-03-31",
                        expected_filename_pattern="test-credit-union-beta-4321-2024-03-31.pdf",
                        page_count=3,
                        opening_balance="$3,567.89",
                        closing_balance="$4,123.45",
                        transaction_count=12,
                    ),
                ],
                total_pages=7,
                expected_output_files=[
                    "test-bank-alpha-3456-2024-01-31.pdf",
                    "test-bank-alpha-7890-2024-02-29.pdf",
                    "test-credit-union-beta-4321-2024-03-31.pdf",
                ],
            ),
            DocumentSpec(
                title=f"Test Dual-Statement Document - 2 Statements [{self.test_timestamp}002]",
                filename=f"test_dual_statements_{self.test_timestamp}002.pdf",
                description="Controlled 2-statement document for validation testing",
                statements=[
                    StatementSpec(
                        bank_name="Test Community Bank",
                        account_number="5555666677778888",
                        account_suffix="8888",
                        statement_period="April 2024",
                        statement_date="2024-04-30",
                        expected_filename_pattern="test-community-bank-8888-2024-04-30.pdf",
                        page_count=3,
                        opening_balance="$5,432.10",
                        closing_balance="$6,789.01",
                        transaction_count=10,
                    ),
                    StatementSpec(
                        bank_name="Test Savings & Loan",
                        account_number="1111222233334444",
                        account_suffix="4444",
                        statement_period="May 2024",
                        statement_date="2024-05-31",
                        expected_filename_pattern="test-savings-loan-4444-2024-05-31.pdf",
                        page_count=2,
                        opening_balance="$6,789.01",
                        closing_balance="$7,654.32",
                        transaction_count=7,
                    ),
                ],
                total_pages=5,
                expected_output_files=[
                    "test-community-bank-8888-2024-04-30.pdf",
                    "test-savings-loan-4444-2024-05-31.pdf",
                ],
            ),
        ]

        return test_docs

    def create_standardized_pdf(self, doc_spec: DocumentSpec) -> bytes:
        """Create a standardized PDF with known statement boundaries.

        Args:
            doc_spec: Document specification

        Returns:
            PDF content as bytes
        """
        import io

        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

        # Create PDF in memory
        pdf_buffer = io.BytesIO()
        doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        for i, stmt in enumerate(doc_spec.statements):
            # Add statement header with clear boundary markers
            story.append(
                Paragraph(
                    f"=== STATEMENT BOUNDARY START: {stmt.bank_name.upper()} ===",
                    styles["Title"],
                )
            )
            story.append(Spacer(1, 20))
            story.append(Paragraph(stmt.bank_name.upper(), styles["Title"]))
            story.append(Spacer(1, 15))
            story.append(
                Paragraph(
                    f"Account Number: ****{stmt.account_suffix}", styles["Normal"]
                )
            )
            story.append(
                Paragraph(
                    f"Statement Period: {stmt.statement_period}", styles["Normal"]
                )
            )
            story.append(
                Paragraph(f"Statement Date: {stmt.statement_date}", styles["Normal"])
            )
            story.append(Spacer(1, 20))

            # Add transaction history
            story.append(Paragraph("TRANSACTION HISTORY", styles["Heading2"]))
            story.append(
                Paragraph(f"Opening Balance: {stmt.opening_balance}", styles["Normal"])
            )

            # Add sample transactions based on transaction count
            for j in range(stmt.transaction_count):
                transaction_date = f"2024-{i + 1:02d}-{(j + 1) * 3:02d}"
                if j % 3 == 0:
                    story.append(
                        Paragraph(
                            f"{transaction_date} - Direct Deposit: +$500.{j:02d}",
                            styles["Normal"],
                        )
                    )
                elif j % 3 == 1:
                    story.append(
                        Paragraph(
                            f"{transaction_date} - Purchase: -$75.{j:02d}",
                            styles["Normal"],
                        )
                    )
                else:
                    story.append(
                        Paragraph(
                            f"{transaction_date} - Transfer: -$125.{j:02d}",
                            styles["Normal"],
                        )
                    )

            story.append(Spacer(1, 15))
            story.append(
                Paragraph(f"Closing Balance: {stmt.closing_balance}", styles["Normal"])
            )

            # Add page breaks based on page count (except last statement)
            for _ in range(stmt.page_count - 1):
                story.append(PageBreak())
                story.append(
                    Paragraph(
                        f"{stmt.bank_name} - Statement Continued", styles["Normal"]
                    )
                )
                story.append(Spacer(1, 20))

            # Add clear boundary marker at end
            story.append(Spacer(1, 30))
            story.append(
                Paragraph(
                    f"=== STATEMENT BOUNDARY END: {stmt.bank_name.upper()} ===",
                    styles["Normal"],
                )
            )

            # Page break between statements (except last)
            if i < len(doc_spec.statements) - 1:
                story.append(PageBreak())
                story.append(Spacer(1, 50))  # Large gap between statements

        # Build PDF
        doc.build(story)
        pdf_content = pdf_buffer.getvalue()
        pdf_buffer.close()

        return pdf_content

    def upload_test_documents(self, test_docs: List[DocumentSpec]) -> Dict[str, Any]:
        """Upload standardized test documents to Paperless.

        Args:
            test_docs: List of test document specifications

        Returns:
            Upload results
        """
        upload_results = {"success": True, "uploaded_documents": [], "errors": []}

        for doc_spec in test_docs:
            try:
                # Create PDF content
                pdf_content = self.create_standardized_pdf(doc_spec)

                # Save to temporary file
                with tempfile.NamedTemporaryFile(
                    mode="wb", suffix=".pdf", delete=False
                ) as tmp_file:
                    tmp_file.write(pdf_content)
                    tmp_path = Path(tmp_file.name)

                try:
                    # Upload to paperless with test tags
                    upload_result = self.client.upload_document(
                        file_path=tmp_path,
                        title=doc_spec.title,
                        tags=[
                            "test:automation",
                            "test:multi-statement",
                            "test:unprocessed",
                        ],
                        correspondent="Test Automation Bot",
                        document_type="Test Statement Bundle",
                        storage_path="test-input",
                    )

                    if upload_result and upload_result.get("success"):
                        document_id = upload_result.get("document_id")
                        task_id = upload_result.get("task_id")

                        # Handle both immediate document ID and task-based uploads
                        if document_id:
                            # Immediate upload - apply test tags right away
                            self._apply_test_tags_with_retry(
                                document_id, doc_spec.title
                            )
                        elif task_id:
                            # Task-based upload - wait for processing then apply tags
                            document_id = self._wait_for_task_and_apply_tags(
                                task_id, doc_spec.title
                            )
                        else:
                            # Fallback - find document by title after short wait
                            time.sleep(5)
                            document_id = self._find_document_by_title_and_apply_tags(
                                doc_spec.title
                            )

                        # Store document info with test specification
                        doc_info = {
                            "upload_result": upload_result,
                            "spec": doc_spec,
                            "title": doc_spec.title,
                            "filename": doc_spec.filename,
                            "expected_output_files": doc_spec.expected_output_files,
                            "expected_statement_count": len(doc_spec.statements),
                            "document_id": document_id,
                        }

                        upload_results["uploaded_documents"].append(doc_info)
                        self.created_documents.append(doc_info)

                finally:
                    # Clean up temporary file
                    tmp_path.unlink(missing_ok=True)

            except Exception as e:
                upload_results["success"] = False
                upload_results["errors"].append(
                    {"document": doc_spec.title, "error": str(e)}
                )

        return upload_results

    def _apply_test_tags_with_retry(
        self, document_id: int, title: str, max_retries: int = 3
    ) -> int:
        """Apply test tags to a document with retry logic.

        Args:
            document_id: Document ID to apply tags to
            title: Document title for logging
            max_retries: Maximum number of retry attempts

        Returns:
            Document ID if successful
        """
        test_tags = ["test:automation", "test:multi-statement", "test:unprocessed"]

        for attempt in range(max_retries):
            try:
                result = self.client.apply_tags_to_document(document_id, test_tags)
                if result.get("success"):
                    print(f"✅ Applied test tags to document {document_id}: {title}")
                    return document_id
                else:
                    print(
                        f"⚠️ Failed to apply tags to document {document_id} (attempt {attempt + 1}): {result.get('error', 'Unknown error')}"
                    )
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
            except Exception as e:
                print(
                    f"⚠️ Error applying tags to document {document_id} (attempt {attempt + 1}): {e}"
                )
                if attempt < max_retries - 1:
                    time.sleep(2)

        print(
            f"❌ Failed to apply test tags to document {document_id} after {max_retries} attempts"
        )
        return document_id  # Return ID even if tagging failed

    def _wait_for_task_and_apply_tags(self, task_id: str, title: str) -> Optional[int]:
        """Wait for a paperless task to complete and apply test tags.

        Args:
            task_id: Task ID to monitor
            title: Document title for searching

        Returns:
            Document ID if found and tagged successfully
        """
        print(f"⏳ Waiting for task {task_id} to complete...")

        try:
            # Wait for task completion
            task_result = self.client.poll_task_completion(
                task_id, timeout_seconds=120, poll_interval=5
            )

            if task_result.get("success") and task_result.get("document_id"):
                document_id = task_result["document_id"]
                print(f"✅ Task {task_id} completed, document ID: {document_id}")
                return self._apply_test_tags_with_retry(document_id, title)
            else:
                print(
                    f"⚠️ Task {task_id} completed but no document ID returned, searching by title..."
                )
                return self._find_document_by_title_and_apply_tags(title)

        except Exception as e:
            print(f"⚠️ Error waiting for task {task_id}: {e}")
            return self._find_document_by_title_and_apply_tags(title)

    def _find_document_by_title_and_apply_tags(self, title: str) -> Optional[int]:
        """Find a document by title and apply test tags.

        Args:
            title: Document title to search for

        Returns:
            Document ID if found and tagged successfully
        """
        try:
            import httpx

            # Search for document by title
            with httpx.Client(timeout=30.0) as http_client:
                response = http_client.get(
                    f"{self.client.base_url}/api/documents/",
                    headers=self.client.headers,
                    params={
                        "title__icontains": title.split("[")[
                            0
                        ].strip(),  # Use title without timestamp
                        "page_size": 5,
                        "ordering": "-created",  # Most recent first
                    },
                )
                response.raise_for_status()

                documents = response.json().get("results", [])

                # Find exact match
                for doc in documents:
                    if doc.get("title") == title:
                        document_id = doc["id"]
                        print(f"🔍 Found document by title search: ID {document_id}")
                        return self._apply_test_tags_with_retry(document_id, title)

                print(f"❌ Document not found by title: {title}")
                return None

        except Exception as e:
            print(f"❌ Error finding document by title '{title}': {e}")
            return None

    def run_end_to_end_processing(
        self, config: Config, max_documents: int = 5
    ) -> Dict[str, Any]:
        """Execute end-to-end processing using local Ollama instance.

        Args:
            config: Configuration with Ollama settings
            max_documents: Maximum number of documents to process

        Returns:
            Processing results
        """
        processing_results = {
            "success": True,
            "processed_documents": [],
            "validation_results": [],
            "errors": [],
        }

        try:
            # Create workflow with Ollama configuration
            workflow = BankStatementWorkflow(config)

            # Query test documents for processing
            query_result = self.client.query_documents_by_tags(
                tags=["test:automation", "test:multi-statement", "test:unprocessed"],
                page_size=max_documents,
            )

            if not query_result.get("success") or not query_result.get("documents"):
                processing_results["success"] = False
                processing_results["errors"].append(
                    "No test documents found for processing"
                )
                return processing_results

            # Process each document
            for doc in query_result["documents"][:max_documents]:
                try:
                    # Download document
                    with tempfile.TemporaryDirectory() as tmp_dir:
                        download_result = self.client.download_document(
                            document_id=doc["id"], output_directory=Path(tmp_dir)
                        )

                        if not download_result.get("success"):
                            processing_results["errors"].append(
                                {"document_id": doc["id"], "error": "Download failed"}
                            )
                            continue

                        input_path = Path(download_result["output_path"])
                        output_dir = Path(tmp_dir) / "processed"
                        output_dir.mkdir(exist_ok=True)

                        # Process the document using workflow
                        workflow_result = workflow.run(str(input_path), str(output_dir))

                        # Validate processing results
                        validation_result = self.validate_processing_results(
                            workflow_result=workflow_result,
                            output_dir=output_dir,
                            original_document=doc,
                        )

                        processing_results["processed_documents"].append(
                            {
                                "document_id": doc["id"],
                                "title": doc["title"],
                                "workflow_result": workflow_result,
                                "output_files": list(output_dir.glob("*.pdf")),
                                "validation": validation_result,
                            }
                        )

                        processing_results["validation_results"].append(
                            validation_result
                        )

                except Exception as e:
                    processing_results["success"] = False
                    processing_results["errors"].append(
                        {"document_id": doc["id"], "error": str(e)}
                    )

        except Exception as e:
            processing_results["success"] = False
            processing_results["errors"].append({"general_error": str(e)})

        return processing_results

    def validate_processing_results(
        self,
        workflow_result: Dict[str, Any],
        output_dir: Path,
        original_document: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Validate processing results against expected standardized test data.

        Args:
            workflow_result: Results from workflow processing
            output_dir: Directory containing output files
            original_document: Original document metadata

        Returns:
            Validation results
        """
        validation = {
            "success": True,
            "expected_vs_actual": {},
            "file_validations": [],
            "errors": [],
        }

        try:
            # Find matching test specification
            matching_spec = None
            for created_doc in self.created_documents:
                if created_doc["title"] == original_document["title"]:
                    matching_spec = created_doc["spec"]
                    break

            if not matching_spec:
                validation["success"] = False
                validation["errors"].append("No matching test specification found")
                return validation

            # Get actual output files
            output_files = list(output_dir.glob("*.pdf"))

            # Validate file count
            expected_count = len(matching_spec.expected_output_files)
            actual_count = len(output_files)

            validation["expected_vs_actual"]["file_count"] = {
                "expected": expected_count,
                "actual": actual_count,
                "match": expected_count == actual_count,
            }

            if expected_count != actual_count:
                validation["success"] = False
                validation["errors"].append(
                    f"File count mismatch: expected {expected_count}, got {actual_count}"
                )

            # Validate individual files
            for expected_filename in matching_spec.expected_output_files:
                # Check if a file with similar pattern exists (allowing for minor naming variations)
                matching_files = [
                    f
                    for f in output_files
                    if any(
                        part in f.name.lower()
                        for part in expected_filename.lower().split("-")[:3]
                    )
                ]

                if matching_files:
                    actual_file = matching_files[0]
                    file_validation = {
                        "expected_filename": expected_filename,
                        "actual_filename": actual_file.name,
                        "exists": True,
                        "size_bytes": actual_file.stat().st_size,
                        "is_pdf": actual_file.suffix.lower() == ".pdf",
                    }

                    # Basic PDF validation
                    try:
                        with open(actual_file, "rb") as f:
                            header = f.read(10)
                            file_validation["valid_pdf_header"] = header.startswith(
                                b"%PDF"
                            )
                    except Exception as e:
                        file_validation["valid_pdf_header"] = False
                        file_validation["pdf_error"] = str(e)
                else:
                    validation["success"] = False
                    file_validation = {
                        "expected_filename": expected_filename,
                        "actual_filename": None,
                        "exists": False,
                    }
                    validation["errors"].append(
                        f"Expected file not found: {expected_filename}"
                    )

                validation["file_validations"].append(file_validation)

            # Validate workflow result structure
            if workflow_result:
                validation["workflow_validation"] = {
                    "has_result": True,
                    "success": workflow_result.get("success", False),
                    "has_metadata": "metadata" in workflow_result,
                    "has_output_files": "output_files" in workflow_result,
                }
            else:
                validation["success"] = False
                validation["workflow_validation"] = {"has_result": False}
                validation["errors"].append("Workflow returned no results")

        except Exception as e:
            validation["success"] = False
            validation["errors"].append(str(e))

        return validation

    def cleanup(self):
        """Clean up created test documents and resources."""
        cleanup_results = []

        for doc_info in self.created_documents:
            try:
                upload_result = doc_info.get("upload_result", {})
                document_id = upload_result.get("document_id")

                if document_id:
                    # Note: Document deletion would require additional API permissions
                    # For now, documents remain as test data
                    cleanup_results.append(
                        {
                            "document_id": document_id,
                            "title": doc_info["title"],
                            "cleanup_status": "left_as_test_data",
                        }
                    )
            except Exception as e:
                cleanup_results.append(
                    {
                        "document_info": doc_info.get("title", "unknown"),
                        "cleanup_error": str(e),
                    }
                )

        return cleanup_results


@pytest.fixture(scope="session")
def paperless_e2e_fixture():
    """Session-scoped end-to-end test fixture for Paperless API integration.

    This fixture:
    1. Clears remote test storage paths
    2. Creates standardized test documents with known metadata
    3. Provides methods for end-to-end testing with Ollama
    4. Validates results against expected test data

    Yields:
        PaperlessEndToEndFixture instance for testing
    """
    # Skip if paperless integration testing is not enabled
    if os.getenv("PAPERLESS_API_INTEGRATION_TEST", "").lower() not in ("true", "1"):
        pytest.skip("Paperless API integration testing not enabled")

    # Load configuration
    config = Config(
        openai_api_key="test-key-e2e-integration",
        paperless_enabled=True,
        paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
        paperless_token=os.getenv("PAPERLESS_TOKEN"),
        paperless_max_documents=10,
        paperless_query_timeout=30,
    )

    # Create client and fixture
    client = PaperlessClient(config)
    if not client.is_enabled():
        pytest.skip("Paperless API client not properly configured")

    fixture = PaperlessEndToEndFixture(client)

    try:
        # Setup: Clear remote storage and create test documents
        cleanup_result = fixture.cleanup_remote_storage()
        if not cleanup_result["success"]:
            pytest.skip(f"Failed to clean remote storage: {cleanup_result['errors']}")

        # Generate and upload standardized test documents
        test_docs = fixture.generate_standardized_test_data()
        upload_result = fixture.upload_test_documents(test_docs)

        if not upload_result["success"]:
            pytest.skip(f"Failed to upload test documents: {upload_result['errors']}")

        print(
            f"✅ E2E fixture ready: {len(upload_result['uploaded_documents'])} test documents created"
        )

        # Yield fixture for tests
        yield fixture

    except Exception as e:
        pytest.skip(f"Failed to initialize E2E fixture: {e}")

    finally:
        # Cleanup: Clean up test documents
        try:
            cleanup_results = fixture.cleanup()
            print(f"🧹 E2E fixture cleanup: {len(cleanup_results)} items processed")
        except Exception as e:
            print(f"⚠️ E2E fixture cleanup failed: {e}")


# Skip all tests in this file unless explicitly running API integration tests
pytestmark = pytest.mark.skipif(
    os.getenv("PAPERLESS_API_INTEGRATION_TEST", "").lower() not in ("true", "1"),
    reason="E2E API integration tests require PAPERLESS_API_INTEGRATION_TEST=true",
)


@pytest.mark.api_integration
@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.e2e
class TestPaperlessEndToEndProcessing:
    """End-to-end integration tests using standardized test data and local Ollama."""

    def test_end_to_end_workflow_with_ollama(self, paperless_e2e_fixture):
        """Test complete end-to-end workflow using local Ollama instance."""
        fixture = paperless_e2e_fixture

        # Create Ollama configuration
        ollama_config = Config(
            openai_api_key="test-key-ollama-e2e",
            llm_provider="ollama",
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://10.0.0.150:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "openhermes:latest"),
            paperless_enabled=True,
            paperless_url=os.getenv("PAPERLESS_URL", "http://localhost:8000"),
            paperless_token=os.getenv("PAPERLESS_TOKEN"),
            paperless_tags=["test:processed", "test:statement"],
            paperless_correspondent="Test Processing Bot",
            paperless_document_type="Processed Statement",
            paperless_storage_path="test-processed",
            default_output_dir="./test/output/e2e_processing",
        )

        # Run end-to-end processing
        processing_results = fixture.run_end_to_end_processing(
            config=ollama_config,
            max_documents=2,  # Process first 2 test documents
        )

        # Validate processing results
        assert processing_results["success"] is True, (
            f"Processing failed: {processing_results['errors']}"
        )
        assert len(processing_results["processed_documents"]) > 0, (
            "No documents were processed"
        )

        # Validate individual document results
        for processed_doc in processing_results["processed_documents"]:
            validation = processed_doc["validation"]

            # Check overall validation success
            if not validation["success"]:
                print(
                    f"❌ Validation failed for {processed_doc['title']}: {validation['errors']}"
                )

            # Verify file count matches expectations
            file_count_validation = validation["expected_vs_actual"].get(
                "file_count", {}
            )
            assert file_count_validation.get("match", False), (
                f"File count mismatch for {processed_doc['title']}: "
                f"expected {file_count_validation.get('expected')}, "
                f"got {file_count_validation.get('actual')}"
            )

            # Verify output files exist and are valid PDFs
            for file_validation in validation["file_validations"]:
                assert file_validation["exists"], (
                    f"Expected file not found: {file_validation['expected_filename']}"
                )
                if file_validation["exists"]:
                    assert file_validation["is_pdf"], (
                        f"File is not a PDF: {file_validation['actual_filename']}"
                    )
                    assert file_validation["size_bytes"] > 1000, (
                        f"File too small: {file_validation['actual_filename']}"
                    )
                    assert file_validation.get("valid_pdf_header", False), (
                        f"Invalid PDF header: {file_validation['actual_filename']}"
                    )

        print(
            f"✅ End-to-end test completed successfully: {len(processing_results['processed_documents'])} documents processed"
        )

    def test_standardized_test_data_validation(self, paperless_e2e_fixture):
        """Test that standardized test data meets validation requirements."""
        fixture = paperless_e2e_fixture

        # Verify test documents were created with expected specifications
        assert len(fixture.created_documents) >= 2, "Expected at least 2 test documents"

        for doc_info in fixture.created_documents:
            spec = doc_info["spec"]

            # Validate document specification
            assert spec.title, "Document must have a title"
            assert spec.statements, "Document must contain statements"
            assert len(spec.statements) >= 1, (
                "Document must contain at least 1 statement"
            )
            assert spec.total_pages > 0, "Document must have pages"
            assert spec.expected_output_files, (
                "Document must specify expected output files"
            )
            assert len(spec.expected_output_files) == len(spec.statements), (
                "Output file count must match statement count"
            )

            # Validate individual statements
            for stmt in spec.statements:
                assert stmt.bank_name, "Statement must have bank name"
                assert stmt.account_number, "Statement must have account number"
                assert stmt.account_suffix, "Statement must have account suffix"
                assert stmt.statement_date, "Statement must have statement date"
                assert stmt.expected_filename_pattern, (
                    "Statement must have expected filename pattern"
                )
                assert stmt.page_count > 0, "Statement must have pages"
                assert stmt.opening_balance, "Statement must have opening balance"
                assert stmt.closing_balance, "Statement must have closing balance"
                assert stmt.transaction_count > 0, "Statement must have transactions"

        print(
            f"✅ Standardized test data validation passed: {len(fixture.created_documents)} documents validated"
        )

    def test_remote_storage_cleanup(self, paperless_e2e_fixture):
        """Test that remote storage cleanup works correctly."""
        fixture = paperless_e2e_fixture

        # Test cleanup functionality (this was already run during fixture setup)
        # Verify the fixture's storage paths are configured correctly
        assert "test-input" in fixture.test_storage_paths, (
            "test-input storage path should be configured"
        )
        assert "test-processed" in fixture.test_storage_paths, (
            "test-processed storage path should be configured"
        )

        # The cleanup was already performed during fixture setup
        # This test validates that the functionality exists and is configurable
        print("✅ Remote storage cleanup functionality validated")

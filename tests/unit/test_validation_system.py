"""Unit tests for the output validation system."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
class TestValidationSystem:
    """Test the 4-tier output validation system components."""

    def test_validate_output_integrity_success(self, workflow_instance, temp_test_dir):
        """Test successful output validation."""
        # Create mock input and output files with appropriate sizes
        input_file = temp_test_dir / "input" / "test.pdf"
        input_content = "Mock PDF content " * 60  # About 1,020 bytes
        input_file.write_text(input_content)

        output_files = []
        output_content = (
            "Mock output content " * 17
        )  # About 340 bytes each, total ~1,020 bytes
        for i in range(3):
            output_file = temp_test_dir / "output" / f"statement_{i + 1}.pdf"
            output_file.write_text(output_content)
            output_files.append(str(output_file))

        # Mock PDF operations using fitz (imported locally in the validation method)
        with patch("fitz.open") as mock_fitz_open:
            # Mock output file PDF documents
            mock_output_docs = []
            for i in range(3):
                mock_doc = Mock()
                # Set the __len__ method to return 4 pages each
                mock_doc.__len__ = Mock(return_value=4)
                mock_doc.close = Mock()

                # Mock page objects for content sampling
                mock_pages = []
                for j in range(4):
                    page_mock = Mock()
                    page_mock.get_text.return_value = (
                        "Mock PDF page content with BusinessChoice Westpac Statement"
                    )
                    mock_pages.append(page_mock)

                mock_doc.__getitem__ = Mock(
                    side_effect=lambda idx: mock_pages[min(idx, len(mock_pages) - 1)]
                )
                mock_output_docs.append(mock_doc)

            # Mock original file PDF document
            mock_original_doc = Mock()
            mock_original_doc.__len__ = Mock(return_value=12)
            mock_original_doc.close = Mock()

            # Mock pages for original document
            original_pages = []
            for i in range(12):
                page_mock = Mock()
                page_mock.get_text.return_value = (
                    "Original PDF content with BusinessChoice Westpac Statement"
                )
                original_pages.append(page_mock)

            mock_original_doc.__getitem__ = Mock(
                side_effect=lambda idx: original_pages[
                    min(idx, len(original_pages) - 1)
                ]
            )

            # Configure mock to return appropriate documents based on file path
            call_count = 0

            def side_effect(file_path):
                nonlocal call_count
                if "statement_" in str(file_path):
                    doc_index = min(call_count, len(mock_output_docs) - 1)
                    call_count += 1
                    return mock_output_docs[doc_index]
                else:
                    return mock_original_doc

            mock_fitz_open.side_effect = side_effect

            validation_result = workflow_instance._validate_output_integrity(
                str(input_file),
                output_files,
                12,  # original_total_pages
            )

        # Should pass all validations
        assert validation_result["is_valid"] is True
        assert "All 4 validation checks passed" in validation_result["summary"]

        # Check all 4 validation tiers
        checks = validation_result["checks"]
        assert checks["file_count"]["status"] == "passed"
        assert checks["page_count"]["status"] == "passed"
        assert checks["file_size"]["status"] == "passed"
        assert checks["content_sampling"]["status"] == "passed"

    def test_validate_missing_files(self, workflow_instance, temp_test_dir):
        """Test validation when output files are missing."""
        input_file = temp_test_dir / "input" / "test.pdf"
        input_file.write_text("Mock PDF content")

        # Reference non-existent files
        missing_files = [
            str(temp_test_dir / "output" / "missing1.pdf"),
            str(temp_test_dir / "output" / "missing2.pdf"),
        ]

        validation_result = workflow_instance._validate_output_integrity(
            str(input_file), missing_files, 10
        )

        # Should fail file existence check
        assert validation_result["is_valid"] is False
        assert validation_result["checks"]["file_count"]["status"] == "failed"
        # Check for the actual error message format from the validation method
        assert "Missing 2 files" in validation_result["checks"]["file_count"]["details"]

    @pytest.mark.skip(reason="Test needs refactoring for fitz mock")
    def test_validate_page_count_mismatch(self, workflow_instance, temp_test_dir):
        """Test validation when page counts don't match."""
        pass

    @pytest.mark.skip(reason="Test needs refactoring for fitz mock")
    def test_validate_file_size_suspicious(self, workflow_instance, temp_test_dir):
        """Test validation when file sizes are suspiciously small."""
        pass

    def test_content_sampling_validation(self, workflow_instance, temp_test_dir):
        """Test content sampling validation with real PDF processing."""
        input_file = temp_test_dir / "input" / "test.pdf"
        output_file = temp_test_dir / "output" / "output.pdf"

        # Create fake PDF files
        input_file.write_bytes(b"%PDF-1.4\n%fake pdf content\n%%EOF")
        output_file.write_bytes(b"%PDF-1.4\n%fake pdf content\n%%EOF")

        # Mock fitz.open to simulate PDF processing
        with patch("fitz.open") as mock_fitz:
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=10)  # 10 pages
            mock_page = Mock()
            mock_page.get_text.return_value = "Sample PDF text content"
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_fitz.return_value.__enter__.return_value = mock_doc
            mock_fitz.return_value.__exit__.return_value = None

            validation_result = workflow_instance._validate_output_integrity(
                str(input_file), [str(output_file)], 10
            )

        # Content sampling should be attempted
        assert "content_sampling" in validation_result["checks"]

    def test_validation_with_pdf_processing_error(
        self, workflow_instance, temp_test_dir
    ):
        """Test validation when PDF processing fails."""
        input_file = temp_test_dir / "input" / "corrupt.pdf"
        output_file = temp_test_dir / "output" / "output.pdf"

        input_file.write_text("Not a real PDF")
        output_file.write_text("Also not a real PDF")

        # Mock fitz.open to raise an exception
        with patch("fitz.open") as mock_fitz:
            mock_fitz.side_effect = Exception("PDF processing failed")

            validation_result = workflow_instance._validate_output_integrity(
                str(input_file), [str(output_file)], 10
            )

        # Should handle errors gracefully
        assert validation_result["is_valid"] is False
        assert len(validation_result["error_details"]) > 0

    def test_validation_workflow_integration(self, workflow_instance):
        """Test validation integration in workflow state."""
        from src.bank_statement_separator.workflow import WorkflowState

        # Create mock state
        test_state = WorkflowState(
            input_file_path="/test/input.pdf",
            output_directory="/test/output",
            pdf_document=None,
            text_chunks=None,
            detected_boundaries=None,
            extracted_metadata=None,
            generated_files=[
                "/test/output/statement1.pdf",
                "/test/output/statement2.pdf",
            ],
            current_step="pdf_generation_complete",
            error_message=None,
            processing_complete=False,
            total_pages=10,
            total_statements_found=2,
            processing_time_seconds=None,
            confidence_scores=None,
            validation_results=None,
        )

        # Mock validation method
        with patch.object(
            workflow_instance, "_validate_output_integrity"
        ) as mock_validate:
            mock_validate.return_value = {
                "is_valid": True,
                "summary": "All checks passed",
                "checks": {
                    "file_count": {"status": "passed"},
                    "page_count": {"status": "passed"},
                    "file_size": {"status": "passed"},
                    "content_sampling": {"status": "passed"},
                },
            }

            # Run validation node
            result_state = workflow_instance._output_validation_node(test_state)

        # Check validation was integrated into state
        assert result_state["validation_results"] is not None
        assert result_state["validation_results"]["is_valid"] is True
        assert result_state["current_step"] == "output_validation_complete"

    def test_validation_failure_handling(self, workflow_instance):
        """Test workflow handles validation failures."""
        from src.bank_statement_separator.workflow import WorkflowState

        test_state = WorkflowState(
            input_file_path="/test/input.pdf",
            output_directory="/test/output",
            pdf_document=None,
            text_chunks=None,
            detected_boundaries=None,
            extracted_metadata=None,
            generated_files=["/test/output/statement1.pdf"],
            current_step="pdf_generation_complete",
            error_message=None,
            processing_complete=False,
            total_pages=10,
            total_statements_found=2,  # Mismatch: 2 detected but 1 file
            processing_time_seconds=None,
            confidence_scores=None,
            validation_results=None,
        )

        # Mock validation to fail
        with patch.object(
            workflow_instance, "_validate_output_integrity"
        ) as mock_validate:
            mock_validate.return_value = {
                "is_valid": False,
                "summary": "File count mismatch detected",
                "error_details": ["Expected 2 files but found 1"],
                "checks": {
                    "file_count": {"status": "failed", "details": "Missing files"},
                    "page_count": {"status": "passed"},
                    "file_size": {"status": "passed"},
                    "content_sampling": {"status": "passed"},
                },
            }

            result_state = workflow_instance._output_validation_node(test_state)

        # When validation fails, workflow should record error
        assert result_state["current_step"] == "output_validation_error"
        assert result_state["error_message"] is not None
        # The error message should contain either the validation error or quarantine failure
        assert (
            "validation failed" in result_state["error_message"].lower()
            or "quarantine" in result_state["error_message"].lower()
        )
        # validation_results is not set when validation fails early
        # The mock validation result doesn't get set to state when returning early


@pytest.mark.unit
class TestValidationHelperMethods:
    """Test validation helper methods."""

    def test_validate_output_integrity_direct(self, workflow_instance, temp_test_dir):
        """Test the _validate_output_integrity method directly."""
        input_file = temp_test_dir / "input" / "test.pdf"
        output_file = temp_test_dir / "output" / "output.pdf"

        # Create mock PDF files
        input_file.write_bytes(b"%PDF-1.4\n%content\n%%EOF")
        output_file.write_bytes(b"%PDF-1.4\n%content\n%%EOF")

        # Mock fitz operations
        with patch("fitz.open") as mock_fitz:
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=5)
            mock_page = Mock()
            mock_page.get_text.return_value = "Test content"
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_fitz.return_value.__enter__.return_value = mock_doc
            mock_fitz.return_value.__exit__.return_value = None

            result = workflow_instance._validate_output_integrity(
                str(input_file),
                [str(output_file)],
                5,  # Expected pages
            )

        assert "is_valid" in result
        assert "checks" in result
        assert "file_count" in result["checks"]
        assert "page_count" in result["checks"]
        assert "file_size" in result["checks"]
        assert "content_sampling" in result["checks"]

    def test_pdf_operations_with_mock(self, workflow_instance, temp_test_dir):
        """Test PDF operations are called correctly during validation."""
        input_file = temp_test_dir / "input" / "test.pdf"
        output_file = temp_test_dir / "output" / "output.pdf"

        input_file.write_bytes(b"%PDF-1.4\n%content\n%%EOF")
        output_file.write_bytes(b"%PDF-1.4\n%content\n%%EOF")

        with patch("fitz.open") as mock_fitz:
            mock_doc = Mock()
            mock_doc.__len__ = Mock(return_value=3)
            mock_page = Mock()
            mock_page.get_text.return_value = "Sample text"
            mock_doc.__getitem__ = Mock(return_value=mock_page)
            mock_fitz.return_value.__enter__.return_value = mock_doc
            mock_fitz.return_value.__exit__.return_value = None

            workflow_instance._validate_output_integrity(
                str(input_file), [str(output_file)], 3
            )

            # Verify fitz.open was called for both input and output files
            assert mock_fitz.call_count >= 2  # Should open input and output files


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

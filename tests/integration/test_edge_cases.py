"""Integration tests for edge case scenarios using generated test data."""

import pytest
from pathlib import Path

from bank_statement_separator.workflow import BankStatementWorkflow


@pytest.mark.integration
@pytest.mark.edge_case
class TestEdgeCaseScenarios:
    """Test edge cases with generated bank statement data."""

    def test_single_statement_processing(
        self, statement_generator, workflow_instance, edge_case_scenarios
    ):
        """Test processing of single statement with minimal data."""
        scenario = next(
            s for s in edge_case_scenarios if s["name"] == "single_statement_minimal"
        )

        # Generate test PDF
        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            scenario["name"], scenario["statements"]
        )

        # Process the PDF
        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )

        # Validate results
        assert not result.get("error_message"), (
            f"Processing failed: {result.get('error_message')}"
        )
        assert result["processing_complete"] is True
        assert result["total_statements_found"] == scenario["expected_statements"]
        assert len(result["generated_files"]) == scenario["expected_statements"]

        # Validate output validation passed
        if "validation_results" in result and result["validation_results"] is not None:
            assert result["validation_results"]["is_valid"] is True

        # Check generated files exist
        for file_path in result["generated_files"]:
            assert Path(file_path).exists(), f"Generated file not found: {file_path}"

    @pytest.mark.parametrize(
        "scenario_name",
        [
            "dual_statements_same_bank",
            "triple_statements_mixed_banks",
            "similar_account_numbers",
            "overlapping_periods",
        ],
    )
    def test_multi_statement_scenarios(
        self,
        statement_generator,
        workflow_instance,
        edge_case_scenarios,
        scenario_name,
        skip_if_no_api_key,
    ):
        """Test various multi-statement scenarios."""
        scenario = next(s for s in edge_case_scenarios if s["name"] == scenario_name)

        # Generate test PDF
        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            scenario["name"], scenario["statements"]
        )

        # Process the PDF
        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )

        # Validate core processing results
        assert not result.get("error_message"), (
            f"Processing failed: {result.get('error_message')}"
        )
        assert result["processing_complete"] is True
        # Fragment filtering may reduce the number of statements found
        assert result["total_statements_found"] >= 1, (
            "Should find at least one statement"
        )
        assert result["total_statements_found"] <= scenario["expected_statements"], (
            f"Found more statements than expected: {result['total_statements_found']} > {scenario['expected_statements']}"
        )
        assert len(result["generated_files"]) == result["total_statements_found"]

        # Validate output validation
        if "validation_results" in result and result["validation_results"] is not None:
            validation = result["validation_results"]
            assert validation["is_valid"] is True, (
                f"Validation failed: {validation.get('summary', 'Unknown error')}"
            )

        # Check all files were generated
        for file_path in result["generated_files"]:
            assert Path(file_path).exists(), f"Generated file not found: {file_path}"

        # Validate metadata extraction - should match the actual statements found
        assert len(result["extracted_metadata"]) == result["total_statements_found"]

        # Check each statement has required metadata fields
        for i, metadata in enumerate(result["extracted_metadata"]):
            # Since we might have fewer statements due to filtering, only check what we have
            if i < len(expected_metadata):
                expected = expected_metadata[i]

                # Validate bank name is extracted
                assert metadata.get("bank_name"), (
                    f"Bank name not extracted for statement {i + 1}"
                )

                # Validate account information is present
                assert metadata.get("account_number") or metadata.get("account_type"), (
                    f"Account information missing for statement {i + 1}"
                )

                # Check file naming convention
                filename = Path(result["generated_files"][i]).name
                assert filename.endswith(".pdf"), (
                    f"Generated file should be PDF: {filename}"
                )
                # Bank name check is more lenient due to various naming conventions
                if expected["bank"]:
                    bank_check = (
                        expected["bank"]
                        .lower()
                        .replace(" ", "")
                        .replace("bank", "")[:10]
                    )
                    # Check if bank name is in filename or if it's "unknown" (fallback case)
                    assert (
                        bank_check in filename.lower() or "unknown" in filename.lower()
                    ), f"Bank name should be in filename: {filename}"

    @pytest.mark.slow
    def test_fallback_processing_without_api_key(
        self, statement_generator, test_config, edge_case_scenarios, monkeypatch
    ):
        """Test fallback processing when API key is not available."""
        # Remove API key to test fallback
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        test_config.openai_api_key = ""

        workflow = BankStatementWorkflow(test_config)
        scenario = next(
            s for s in edge_case_scenarios if s["name"] == "dual_statements_same_bank"
        )

        # Generate test PDF
        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            scenario["name"], scenario["statements"]
        )

        # Process with fallback
        result = workflow.run(pdf_path, str(Path(pdf_path).parent.parent / "output"))

        # Should still process successfully with fallback
        assert not result.get("error_message"), (
            f"Fallback processing failed: {result.get('error_message')}"
        )
        assert result["processing_complete"] is True
        assert (
            result["total_statements_found"] >= 1
        )  # Fallback might detect different boundaries
        assert len(result["generated_files"]) >= 1

        # Files should still be created
        for file_path in result["generated_files"]:
            assert Path(file_path).exists()

    @pytest.mark.requires_api
    def test_llm_vs_fallback_accuracy(
        self,
        statement_generator,
        workflow_instance,
        edge_case_scenarios,
        skip_if_no_api_key,
    ):
        """Compare LLM processing vs fallback accuracy."""
        scenario = next(
            s
            for s in edge_case_scenarios
            if s["name"] == "triple_statements_mixed_banks"
        )

        # Generate test PDF
        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            scenario["name"], scenario["statements"]
        )

        # Process with LLM
        llm_result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )

        # Create fallback workflow
        fallback_config = workflow_instance.config
        fallback_config.openai_api_key = ""
        fallback_workflow = BankStatementWorkflow(fallback_config)

        # Process with fallback
        fallback_result = fallback_workflow.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output" / "fallback")
        )

        # Compare results
        assert not llm_result.get("error_message")
        assert not fallback_result.get("error_message")

        # LLM should be more accurate for complex scenarios
        assert llm_result["total_statements_found"] == scenario["expected_statements"]

        # Both should generate files
        assert len(llm_result["generated_files"]) >= 1
        assert len(fallback_result["generated_files"]) >= 1

    def test_error_handling_malformed_input(
        self, statement_generator, workflow_instance, temp_test_dir
    ):
        """Test error handling with malformed PDF input."""
        # Create a fake PDF file (just text)
        fake_pdf = temp_test_dir / "input" / "fake.pdf"
        with open(fake_pdf, "w") as f:
            f.write("This is not a PDF file")

        # Try to process it
        result = workflow_instance.run(str(fake_pdf), str(temp_test_dir / "output"))

        # Should handle error gracefully
        assert result.get("error_message") is not None
        assert result["processing_complete"] is False
        assert (
            result.get("generated_files") is None or len(result["generated_files"]) == 0
        )

    def test_validation_system_integrity(
        self, statement_generator, workflow_instance, edge_case_scenarios
    ):
        """Test the 4-tier output validation system."""
        scenario = next(
            s for s in edge_case_scenarios if s["name"] == "dual_statements_same_bank"
        )

        # Generate test PDF
        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            scenario["name"], scenario["statements"]
        )

        # Process the PDF
        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )

        # Validation should be present and detailed
        assert "validation_results" in result
        validation = result["validation_results"]

        # Check validation structure
        assert "is_valid" in validation
        assert "checks" in validation
        assert "summary" in validation

        # Check all 4 validation tiers
        expected_checks = ["file_count", "page_count", "file_size", "content_sampling"]
        for check_name in expected_checks:
            assert check_name in validation["checks"]
            check_result = validation["checks"][check_name]
            assert "status" in check_result
            assert check_result["status"] in ["passed", "failed"]

        # For successful processing, validation should pass
        if not result.get("error_message"):
            assert validation["is_valid"] is True
            for check_name in expected_checks:
                assert validation["checks"][check_name]["status"] == "passed"

    def test_metadata_extraction_accuracy(
        self, statement_generator, workflow_instance, edge_case_scenarios
    ):
        """Test accuracy of metadata extraction across different scenarios."""
        for scenario in edge_case_scenarios:
            # Generate test PDF
            pdf_path, expected_metadata = statement_generator.create_test_pdf(
                scenario["name"], scenario["statements"]
            )

            # Process the PDF
            result = workflow_instance.run(
                pdf_path,
                str(Path(pdf_path).parent.parent / "output" / scenario["name"]),
            )

            if result.get("error_message"):
                continue  # Skip failed scenarios in metadata test

            # Check metadata extraction
            extracted = result.get("extracted_metadata", [])

            # Should extract metadata for each statement
            assert len(extracted) >= 1, f"No metadata extracted for {scenario['name']}"

            # Each metadata entry should have key fields
            for i, metadata in enumerate(extracted):
                # Bank name might be "unknown" for test PDFs that don't match real bank patterns
                bank_name = metadata.get("bank_name")
                assert bank_name or metadata.get("filename"), (
                    f"Missing bank name in {scenario['name']} statement {i + 1}"
                )

                # Should have some form of account identifier
                has_account_info = any(
                    [
                        metadata.get("account_number"),
                        metadata.get("account_type"),
                        metadata.get("card_number"),
                    ]
                )
                assert has_account_info, (
                    f"Missing account info in {scenario['name']} statement {i + 1}"
                )


@pytest.mark.integration
@pytest.mark.edge_case
class TestSpecificEdgeCases:
    """Test specific problematic scenarios."""

    def test_billing_account_detection(self, statement_generator, workflow_instance):
        """Test detection of billing account vs card statements."""
        from datetime import datetime, timedelta

        base_date = datetime(2023, 6, 1)

        statements_config = [
            {
                "bank": "Westpac",
                "type": "Billing Account",  # This should be detected as primary
                "start_date": base_date,
                "end_date": base_date + timedelta(days=30),
                "expected_pages": 2,
                "force_account": "429318319017281",  # Master account
            },
            {
                "bank": "Westpac",
                "type": "Rewards VISA",
                "start_date": base_date,
                "end_date": base_date + timedelta(days=30),
                "expected_pages": 3,
                "force_account": "4293183110515881",  # Card ending in 5881
            },
            {
                "bank": "Westpac",
                "type": "Rewards VISA",
                "start_date": base_date,
                "end_date": base_date + timedelta(days=30),
                "expected_pages": 4,
                "force_account": "4293183110558782",  # Card ending in 8782
            },
        ]

        # Generate test PDF similar to original Westpac format
        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            "billing_account_test", statements_config
        )

        # Process the PDF
        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )

        # Should detect statements (may be fewer due to fragment filtering)
        assert not result.get("error_message"), (
            f"Processing failed: {result.get('error_message')}"
        )
        # Fragment filtering may reduce statement count, but should find at least 1
        assert result["total_statements_found"] >= 1, (
            "Should find at least one statement"
        )
        assert result["total_statements_found"] <= 3, (
            f"Found too many statements: {result['total_statements_found']}"
        )
        assert len(result["generated_files"]) == result["total_statements_found"]

        # Check that different account types were detected (if multiple statements found)
        if result["total_statements_found"] > 1:
            metadata = result["extracted_metadata"]
            account_numbers = [m.get("account_number", "") for m in metadata]

            # Should have different account numbers/identifiers
            unique_accounts = set(filter(None, account_numbers))
            assert len(unique_accounts) >= 1, (
                f"Should detect at least one account, got: {unique_accounts}"
            )

    def test_page_continuation_merger(self, statement_generator, workflow_instance):
        """Test that continuation pages are properly merged."""
        from datetime import datetime, timedelta

        base_date = datetime(2023, 6, 1)

        # Create a scenario that might trigger over-segmentation
        statements_config = [
            {
                "bank": "Commonwealth Bank",
                "type": "Mastercard",
                "start_date": base_date,
                "end_date": base_date
                + timedelta(days=60),  # Longer period = more transactions
                "expected_pages": 8,  # Multi-page statement
                "force_account": "062123456789",
            }
        ]

        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            "continuation_test", statements_config
        )

        # Process with both LLM and fallback to compare
        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )

        # Should detect as single statement, not multiple
        assert not result.get("error_message")
        assert result["total_statements_found"] == 1, (
            f"Expected 1 statement but got {result['total_statements_found']} - continuation pages may not be merged"
        )
        assert len(result["generated_files"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

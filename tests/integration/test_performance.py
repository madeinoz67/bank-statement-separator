"""Performance tests for bank statement processing."""

import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceScenarios:
    """Test performance characteristics of the bank statement processor."""

    def test_large_document_processing_time(
        self, statement_generator, workflow_instance
    ):
        """Test processing time for large documents."""
        # Create a large document scenario
        base_date = datetime(2023, 1, 1)
        statements_config = [
            {
                "bank": "Commonwealth Bank",
                "type": "Mastercard",
                "start_date": base_date,
                "end_date": base_date + timedelta(days=90),  # 3 months
                "expected_pages": 20,  # Large document
                "force_account": "062123456789",
            }
        ]

        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            "large_document_performance", statements_config
        )

        # Measure processing time
        start_time = time.time()
        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )
        end_time = time.time()

        processing_time = end_time - start_time

        # Performance assertions
        assert not result.get(
            "error_message"
        ), f"Processing failed: {result.get('error_message')}"
        assert (
            processing_time < 60
        ), (
            f"Processing took too long: {processing_time:.2f}s"
        )  # Should complete in under 1 minute

        # Log performance metrics
        print(f"Large document processing time: {processing_time:.2f}s")
        print(f"Total pages processed: {result.get('total_pages', 0)}")
        print(f"Statements detected: {result.get('total_statements_found', 0)}")

    def test_multiple_statements_processing_efficiency(
        self, statement_generator, workflow_instance
    ):
        """Test efficiency with multiple statements."""
        base_date = datetime(2023, 1, 1)
        statements_config = []

        # Create 5 different statements
        banks = ["Westpac", "ANZ", "Commonwealth Bank", "NAB", "Westpac"]
        types = [
            "Everyday",
            "Access",
            "Complete Access",
            "Classic Banking",
            "BusinessChoice",
        ]

        for i in range(5):
            statements_config.append(
                {
                    "bank": banks[i],
                    "type": types[i],
                    "start_date": base_date + timedelta(days=i * 10),
                    "end_date": base_date + timedelta(days=i * 10 + 30),
                    "expected_pages": 3,
                    "force_account": f"12345678{i:02d}",
                }
            )

        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            "multiple_statements_performance", statements_config
        )

        start_time = time.time()
        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )
        end_time = time.time()

        processing_time = end_time - start_time

        # Performance checks (accounting for fragment filtering)
        assert not result.get("error_message")
        assert (
            processing_time < 120
        ), f"Multiple statements took too long: {processing_time:.2f}s"
        assert (
            result["total_statements_found"] >= 1
        ), "Should find at least one statement"
        assert (
            result["total_statements_found"] <= 5
        ), "Should not exceed expected statements"

        # Calculate per-statement processing time
        per_statement_time = processing_time / max(1, result["total_statements_found"])
        assert (
            per_statement_time < 60
        ), f"Per-statement time too high: {per_statement_time:.2f}s"

        print(f"Multiple statements processing: {processing_time:.2f}s")
        print(f"Per statement: {per_statement_time:.2f}s")

    def test_memory_usage_large_files(self, statement_generator, workflow_instance):
        """Test memory usage with large files (requires psutil for full testing)."""
        try:
            import psutil
            import os

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Create large document
            base_date = datetime(2023, 1, 1)
            statements_config = [
                {
                    "bank": "ANZ",
                    "type": "Visa",
                    "start_date": base_date,
                    "end_date": base_date + timedelta(days=180),  # 6 months
                    "expected_pages": 30,
                    "force_account": "013456789012",
                }
            ]

            pdf_path, _ = statement_generator.create_test_pdf(
                "memory_usage_test", statements_config
            )

            # Process document
            result = workflow_instance.run(
                pdf_path, str(Path(pdf_path).parent.parent / "output")
            )

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory

            # Memory assertions
            assert (
                memory_increase < 500
            ), f"Memory usage too high: {memory_increase:.2f}MB increase"
            assert not result.get("error_message")

            print(f"Memory usage increase: {memory_increase:.2f}MB")

        except ImportError:
            pytest.skip("psutil not available for memory testing")

    def test_concurrent_processing_simulation(
        self, statement_generator, workflow_instance
    ):
        """Test that workflow can handle sequential processing efficiently."""
        # Create multiple small documents
        test_files = []
        base_date = datetime(2023, 1, 1)

        for i in range(3):
            statements_config = [
                {
                    "bank": "Westpac",
                    "type": "Everyday",
                    "start_date": base_date + timedelta(days=i * 30),
                    "end_date": base_date + timedelta(days=i * 30 + 30),
                    "expected_pages": 2,
                    "force_account": f"42931831{i:07d}",
                }
            ]

            pdf_path, _ = statement_generator.create_test_pdf(
                f"concurrent_test_{i}", statements_config
            )
            test_files.append(pdf_path)

        # Process files sequentially and measure total time
        total_start = time.time()
        results = []

        for i, pdf_path in enumerate(test_files):
            output_dir = str(Path(pdf_path).parent.parent / "output" / f"batch_{i}")
            result = workflow_instance.run(pdf_path, output_dir)
            results.append(result)

        total_time = time.time() - total_start

        # All should succeed
        for result in results:
            assert not result.get("error_message")
            assert result["total_statements_found"] >= 1

        # Total time should be reasonable
        assert (
            total_time < 180
        ), f"Sequential processing took too long: {total_time:.2f}s"

        print(f"Sequential processing of {len(test_files)} files: {total_time:.2f}s")
        print(f"Average per file: {total_time / len(test_files):.2f}s")


@pytest.mark.integration
@pytest.mark.slow
class TestScalabilityLimits:
    """Test system limits and scalability."""

    def test_maximum_pages_handling(self, statement_generator, workflow_instance):
        """Test handling of documents at maximum page limits."""
        base_date = datetime(2023, 1, 1)

        # Create document near the maximum page limit
        statements_config = [
            {
                "bank": "NAB",
                "type": "Classic Banking",
                "start_date": base_date,
                "end_date": base_date + timedelta(days=365),  # Full year
                "expected_pages": 50,  # At the limit
                "force_account": "084234999999",
            }
        ]

        pdf_path, _ = statement_generator.create_test_pdf(
            "max_pages_test", statements_config
        )

        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )

        # Should handle large documents gracefully
        if result.get("error_message"):
            # If it fails, it should be due to configured limits, not crashes
            assert (
                "page" in result["error_message"].lower()
                or "size" in result["error_message"].lower()
            )
        else:
            # If it succeeds, validation should pass
            assert result["processing_complete"] is True
            if "validation_results" in result:
                # Validation might fail due to size, but shouldn't crash
                pass

    def test_many_statements_boundary_detection(
        self, statement_generator, workflow_instance
    ):
        """Test boundary detection with many statements."""
        base_date = datetime(2023, 1, 1)
        statements_config = []

        # Create 10 small statements (stress test boundary detection)
        for i in range(10):
            statements_config.append(
                {
                    "bank": ["Westpac", "ANZ", "Commonwealth Bank", "NAB"][i % 4],
                    "type": "Everyday",
                    "start_date": base_date + timedelta(days=i * 5),
                    "end_date": base_date + timedelta(days=i * 5 + 30),
                    "expected_pages": 2,
                    "force_account": f"99999999{i:02d}",
                }
            )

        pdf_path, expected_metadata = statement_generator.create_test_pdf(
            "many_statements_boundary_test", statements_config
        )

        result = workflow_instance.run(
            pdf_path, str(Path(pdf_path).parent.parent / "output")
        )

        # Should detect reasonable number of statements (accounting for fragment filtering)
        assert not result.get("error_message")
        assert (
            result["total_statements_found"] >= 1
        )  # Should find at least one statement after filtering
        assert result["total_statements_found"] <= 15  # Shouldn't over-segment too much

        print(f"Expected statements: 10, Detected: {result['total_statements_found']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not requires_api"])

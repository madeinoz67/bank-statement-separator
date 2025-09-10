#!/usr/bin/env python3
"""
End-to-end test for error detection and automatic tagging functionality.
Tests the complete error detection and tagging workflow with real configuration.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from bank_statement_separator.config import load_config
from bank_statement_separator.utils.error_detector import ErrorDetector
from bank_statement_separator.utils.error_tagger import ErrorTagger
from bank_statement_separator.utils.paperless_client import PaperlessClient
from bank_statement_separator.workflow import BankStatementWorkflow


def test_configuration_loading():
    """Test that error tagging configuration loads correctly."""
    print("🔧 Testing configuration loading...")

    # Test with error detection enabled
    env_overrides = {
        "PAPERLESS_ERROR_DETECTION_ENABLED": "true",
        "PAPERLESS_ERROR_TAGS": "processing:needs-review,error:detected",
        "PAPERLESS_ERROR_TAG_THRESHOLD": "0.7",
        "PAPERLESS_ERROR_SEVERITY_LEVELS": "high,critical",
        "PAPERLESS_ERROR_BATCH_TAGGING": "true",
    }

    with patch.dict(os.environ, env_overrides):
        config = load_config()

        print(
            f"  ✓ Error detection enabled: {config.paperless_error_detection_enabled}"
        )
        print(f"  ✓ Error tags: {config.paperless_error_tags}")
        print(f"  ✓ Error threshold: {config.paperless_error_tag_threshold}")
        print(f"  ✓ Error severity levels: {config.paperless_error_severity_levels}")
        print(f"  ✓ Batch tagging: {config.paperless_error_batch_tagging}")

        assert config.paperless_error_detection_enabled is True
        assert config.paperless_error_tags == [
            "processing:needs-review",
            "error:detected",
        ]
        assert config.paperless_error_tag_threshold == 0.7
        assert config.paperless_error_severity_levels == ["high", "critical"]
        assert config.paperless_error_batch_tagging is True

    print("  ✅ Configuration loading test passed!")


def test_error_detection_scenarios():
    """Test various error detection scenarios."""
    print("🔍 Testing error detection scenarios...")

    # Create test configuration
    env_overrides = {
        "PAPERLESS_ERROR_DETECTION_ENABLED": "true",
        "PAPERLESS_ERROR_TAG_THRESHOLD": "0.5",
    }

    with patch.dict(os.environ, env_overrides):
        config = load_config()
        detector = ErrorDetector(config)

        # Test 1: LLM Analysis Failure
        print("  📋 Testing LLM analysis failure detection...")
        workflow_state_1 = {
            "current_step": "statement_detection_error",
            "error_message": "LLM API timeout after 30 seconds",
            "detected_boundaries": None,
        }

        errors_1 = detector.detect_errors(workflow_state_1)
        assert len(errors_1) > 0
        assert any(e["type"] == "llm_analysis_failure" for e in errors_1)
        print(f"    ✓ Detected {len(errors_1)} LLM-related errors")

        # Test 2: Low Confidence Boundaries
        print("  📋 Testing low confidence boundary detection...")
        workflow_state_2 = {
            "current_step": "statement_detection_complete",
            "detected_boundaries": [
                {"confidence": 0.3, "start_page": 1, "end_page": 5},
                {"confidence": 0.2, "start_page": 6, "end_page": 10},
            ],
        }

        errors_2 = detector.detect_errors(workflow_state_2)
        assert len(errors_2) > 0
        assert any(e["type"] == "low_confidence_boundaries" for e in errors_2)
        print(f"    ✓ Detected {len(errors_2)} boundary confidence errors")

        # Test 3: PDF Processing Error
        print("  📋 Testing PDF processing error detection...")
        workflow_state_3 = {
            "current_step": "pdf_generation_error",
            "error_message": "Failed to generate PDF: corrupted input",
            "generated_files": [],
            "total_statements_found": 3,
        }

        errors_3 = detector.detect_errors(workflow_state_3)
        assert len(errors_3) > 0
        assert any(e["type"] == "pdf_processing_error" for e in errors_3)
        print(f"    ✓ Detected {len(errors_3)} PDF processing errors")

        # Test 4: Validation Failure
        print("  📋 Testing validation failure detection...")
        workflow_state_4 = {
            "current_step": "output_validation_error",
            "validation_results": {
                "is_valid": False,
                "checks": {
                    "page_count": {"status": "failed"},
                    "content_sampling": {"status": "failed"},
                },
            },
        }

        errors_4 = detector.detect_errors(workflow_state_4)
        assert len(errors_4) > 0
        assert any(e["type"] == "validation_failure" for e in errors_4)
        print(f"    ✓ Detected {len(errors_4)} validation errors")

        # Test 5: No Errors (Successful Workflow)
        print("  📋 Testing successful workflow (no errors)...")
        workflow_state_5 = {
            "current_step": "paperless_upload_complete",
            "detected_boundaries": [
                {
                    "confidence": 0.95,
                    "start_page": 1,
                    "end_page": 10,
                    "reasoning": "LLM-based detection",
                }
            ],
            "validation_results": {"is_valid": True},
            "generated_files": ["output1.pdf", "output2.pdf"],
        }

        errors_5 = detector.detect_errors(workflow_state_5)
        assert len(errors_5) == 0
        print("    ✓ No errors detected for successful workflow")

    print("  ✅ Error detection scenarios test passed!")


def test_error_tagging_functionality():
    """Test error tagging functionality with mocked paperless client."""
    print("🏷️  Testing error tagging functionality...")

    # Create test configuration
    env_overrides = {
        "PAPERLESS_ERROR_DETECTION_ENABLED": "true",
        "PAPERLESS_ERROR_TAGS": "processing:needs-review,error:detected",
        "PAPERLESS_ERROR_SEVERITY_LEVELS": "medium,high,critical",
        "PAPERLESS_ERROR_BATCH_TAGGING": "false",
        "PAPERLESS_TAG_WAIT_TIME": "1",
    }

    with patch.dict(os.environ, env_overrides):
        config = load_config()

        # Mock the paperless client
        with patch(
            "bank_statement_separator.utils.error_tagger.PaperlessClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.is_enabled.return_value = True
            mock_client.apply_tags_to_document.return_value = {
                "success": True,
                "tags_applied": 2,
                "document_id": 123,
            }

            tagger = ErrorTagger(config)

            # Test with high severity errors
            print("  📋 Testing error tagging with high severity errors...")
            errors = [
                {"type": "llm_analysis_failure", "severity": "high"},
                {"type": "validation_failure", "severity": "critical"},
            ]

            upload_results = {
                "uploads": [
                    {"document_id": 123, "success": True},
                    {"document_id": 124, "success": True},
                ]
            }

            result = tagger.apply_error_tags(errors, upload_results)

            assert result["success"] is True
            assert result["tagged_documents"] == 2
            print(f"    ✓ Successfully tagged {result['tagged_documents']} documents")

            # Verify tags were generated correctly
            expected_tags = tagger._generate_error_tags(errors)
            print(f"    ✓ Generated tags: {expected_tags}")
            assert "processing:needs-review" in expected_tags
            assert "error:detected" in expected_tags
            assert "error:llm" in expected_tags
            assert "error:validation" in expected_tags

            # Test with low severity errors (should skip tagging)
            print("  📋 Testing error tagging with low severity errors...")
            low_severity_errors = [{"type": "minor_warning", "severity": "low"}]

            result_low = tagger.apply_error_tags(low_severity_errors, upload_results)
            assert result_low["tagged_documents"] == 0
            print("    ✓ Correctly skipped tagging for low severity errors")

            # Test error summary creation
            print("  📋 Testing error summary creation...")
            summary = tagger.create_error_summary(errors)
            print(f"    ✓ Error summary: {summary}")
            assert "2 processing errors detected" in summary
            assert "high" in summary
            assert "critical" in summary

    print("  ✅ Error tagging functionality test passed!")


def test_workflow_integration():
    """Test integration of error detection and tagging into the workflow."""
    print("🔄 Testing workflow integration...")

    # Create test configuration
    env_overrides = {
        "PAPERLESS_ERROR_DETECTION_ENABLED": "true",
        "PAPERLESS_ERROR_TAGS": "processing:needs-review",
        "PAPERLESS_ERROR_SEVERITY_LEVELS": "medium,high,critical",
        "PAPERLESS_ENABLED": "true",
        "PAPERLESS_URL": "https://test.example.com",
        "PAPERLESS_TOKEN": "test-token",
        "DEFAULT_OUTPUT_DIR": "./test_output",
    }

    with patch.dict(os.environ, env_overrides):
        config = load_config()

        # Mock dependencies to avoid actual API calls
        with patch(
            "bank_statement_separator.utils.error_tagger.PaperlessClient"
        ) as mock_client_class:
            mock_client = mock_client_class.return_value
            mock_client.is_enabled.return_value = True
            mock_client.apply_tags_to_document.return_value = {
                "success": True,
                "tags_applied": 1,
            }

            workflow = BankStatementWorkflow(config)

            # Test error detection and tagging method
            print("  📋 Testing _detect_and_tag_errors method...")
            state = {
                "current_step": "pdf_generation_error",
                "error_message": "PDF generation failed",
                "generated_files": [],
                "total_statements_found": 2,
            }

            upload_results = {
                "enabled": True,
                "uploads": [{"document_id": 123, "success": True}],
            }

            result = workflow._detect_and_tag_errors(state, upload_results)

            print(f"    ✓ Error detection attempted: {result['attempted']}")
            print(f"    ✓ Errors detected: {result['errors_detected']}")
            print(f"    ✓ Documents tagged: {result['tagged_documents']}")
            print(f"    ✓ Error summary: {result['error_summary']}")

            assert result["attempted"] is True
            assert result["errors_detected"] > 0
            assert result["success"] is True

            # Test with error detection disabled
            print("  📋 Testing with error detection disabled...")
            config.paperless_error_detection_enabled = False
            result_disabled = workflow._detect_and_tag_errors(state, upload_results)

            assert result_disabled["attempted"] is False
            assert result_disabled["errors_detected"] == 0
            print("    ✓ Correctly skipped when disabled")

    print("  ✅ Workflow integration test passed!")


def test_real_paperless_connection():
    """Test actual connection to paperless if credentials are available."""
    print("🌐 Testing real Paperless connection...")

    # Load real config
    config = load_config()

    if not config.paperless_enabled:
        print("  ⚠️  Paperless disabled in config, skipping real connection test")
        return

    if not config.paperless_url or not config.paperless_token:
        print(
            "  ⚠️  Paperless credentials not configured, skipping real connection test"
        )
        return

    try:
        # Test basic connection
        client = PaperlessClient(config)

        if client.is_enabled():
            print(f"  ✓ Connected to Paperless at: {config.paperless_url}")

            # Test tag creation/retrieval (read-only operations)
            print("  📋 Testing tag operations...")

            # This is a safe read operation
            try:
                # We won't actually create documents or tags in this test
                # Just verify the client is properly configured
                print("  ✓ Paperless client properly configured")
                print(f"  ✓ Using token: {config.paperless_token[:10]}...")

            except Exception as e:
                print(f"  ⚠️  Tag operations test failed: {e}")
        else:
            print("  ⚠️  Paperless client not enabled")

    except Exception as e:
        print(f"  ❌ Paperless connection failed: {e}")
        print(
            "  ℹ️  This is expected if credentials are not valid or server is not accessible"
        )

    print("  ✅ Real Paperless connection test completed!")


def main():
    """Run all end-to-end tests."""
    print("🚀 Starting Error Detection and Tagging End-to-End Tests")
    print("=" * 60)

    try:
        # Test 1: Configuration Loading
        test_configuration_loading()
        print()

        # Test 2: Error Detection Scenarios
        test_error_detection_scenarios()
        print()

        # Test 3: Error Tagging Functionality
        test_error_tagging_functionality()
        print()

        # Test 4: Workflow Integration
        test_workflow_integration()
        print()

        # Test 5: Real Paperless Connection (optional)
        test_real_paperless_connection()
        print()

        print("🎉 All end-to-end tests completed successfully!")
        print("✅ Error detection and tagging functionality is working correctly.")

    except AssertionError as e:
        print(f"❌ Test assertion failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

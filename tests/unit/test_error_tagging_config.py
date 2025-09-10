"""Tests for error tagging configuration."""

import os
from unittest.mock import patch

import pytest

from src.bank_statement_separator.config import Config, load_config


class TestErrorTaggingConfig:
    """Test error tagging configuration options."""

    def test_error_detection_enabled_config(self):
        """Test error detection enabled configuration."""
        config = Config(paperless_error_detection_enabled=True)
        assert config.paperless_error_detection_enabled is True

        config = Config(paperless_error_detection_enabled=False)
        assert config.paperless_error_detection_enabled is False

    def test_error_tags_config(self):
        """Test error tags configuration."""
        tags = ["processing:needs-review", "error:detected", "manual:check"]
        config = Config(paperless_error_tags=tags)
        assert config.paperless_error_tags == tags
        assert len(config.paperless_error_tags) == 3

    def test_error_tag_threshold_config(self):
        """Test error tag threshold configuration."""
        config = Config(paperless_error_tag_threshold=0.3)
        assert config.paperless_error_tag_threshold == 0.3

        config = Config(paperless_error_tag_threshold=0.8)
        assert config.paperless_error_tag_threshold == 0.8

    def test_error_tag_threshold_validation(self):
        """Test error tag threshold validation."""
        # Valid thresholds
        Config(paperless_error_tag_threshold=0.0)  # Should not raise
        Config(paperless_error_tag_threshold=0.5)  # Should not raise
        Config(paperless_error_tag_threshold=1.0)  # Should not raise

        # Invalid thresholds
        with pytest.raises(ValueError):
            Config(paperless_error_tag_threshold=-0.1)

        with pytest.raises(ValueError):
            Config(paperless_error_tag_threshold=1.1)

    def test_error_severity_levels_config(self):
        """Test error severity levels configuration."""
        levels = ["low", "medium", "high", "critical"]
        config = Config(paperless_error_severity_levels=levels)
        assert config.paperless_error_severity_levels == levels

    def test_default_error_config_values(self):
        """Test default error configuration values."""
        config = Config()
        assert config.paperless_error_detection_enabled is False
        assert config.paperless_error_tags is None
        assert config.paperless_error_tag_threshold == 0.5
        assert config.paperless_error_severity_levels == ["medium", "high", "critical"]

    def test_environment_variable_loading(self):
        """Test loading error configuration from environment variables."""
        env_vars = {
            "PAPERLESS_ERROR_DETECTION_ENABLED": "true",
            "PAPERLESS_ERROR_TAGS": "processing:needs-review,error:detected",
            "PAPERLESS_ERROR_TAG_THRESHOLD": "0.7",
            "PAPERLESS_ERROR_SEVERITY_LEVELS": "high,critical",
        }

        with patch.dict(os.environ, env_vars):
            config = load_config()

        assert config.paperless_error_detection_enabled is True
        assert config.paperless_error_tags == [
            "processing:needs-review",
            "error:detected",
        ]
        assert config.paperless_error_tag_threshold == 0.7
        assert config.paperless_error_severity_levels == ["high", "critical"]

    def test_error_config_with_paperless_disabled(self):
        """Test error configuration when paperless is disabled."""
        config = Config(
            paperless_enabled=False,
            paperless_error_detection_enabled=True,
            paperless_error_tags=["processing:needs-review"],
        )

        # Configuration should be valid even if paperless is disabled
        assert config.paperless_enabled is False
        assert config.paperless_error_detection_enabled is True
        assert config.paperless_error_tags == ["processing:needs-review"]

    def test_empty_error_tags_list(self):
        """Test handling of empty error tags list."""
        config = Config(paperless_error_tags=[])
        assert config.paperless_error_tags == []

        config = Config(paperless_error_tags=None)
        assert config.paperless_error_tags is None

    def test_error_batch_tagging_config(self):
        """Test batch vs individual error tagging configuration."""
        config = Config(paperless_error_batch_tagging=True)
        assert config.paperless_error_batch_tagging is True

        config = Config(paperless_error_batch_tagging=False)
        assert config.paperless_error_batch_tagging is False

    def test_config_field_descriptions(self):
        """Test that configuration fields have proper descriptions."""
        # Check that error-related fields are documented
        field_info = Config.model_fields

        assert "paperless_error_detection_enabled" in field_info
        assert "paperless_error_tags" in field_info
        assert "paperless_error_tag_threshold" in field_info

        # Verify descriptions exist
        assert field_info["paperless_error_detection_enabled"].description is not None
        assert field_info["paperless_error_tags"].description is not None
        assert field_info["paperless_error_tag_threshold"].description is not None

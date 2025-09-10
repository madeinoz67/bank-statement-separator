"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest

from src.bank_statement_separator.config import Config, load_config, validate_env_file


class TestValidateEnvFile:
    """Test validate_env_file function."""

    def test_validate_existing_readable_file(self, tmp_path):
        """Test validation succeeds for existing readable file."""
        env_file = tmp_path / "test.env"
        env_file.write_text("TEST_VAR=value")

        assert validate_env_file(str(env_file)) is True

    def test_validate_nonexistent_file(self, tmp_path):
        """Test validation fails for nonexistent file."""
        env_file = tmp_path / "nonexistent.env"

        with pytest.raises(FileNotFoundError, match="Environment file not found"):
            validate_env_file(str(env_file))

    def test_validate_directory_path(self, tmp_path):
        """Test validation fails for directory path."""
        with pytest.raises(ValueError, match="Environment path is not a file"):
            validate_env_file(str(tmp_path))

    def test_validate_unreadable_file(self, tmp_path):
        """Test validation fails for unreadable file."""
        env_file = tmp_path / "unreadable.env"
        env_file.write_text("TEST_VAR=value")
        env_file.chmod(0o000)

        try:
            with pytest.raises(PermissionError, match="Cannot read environment file"):
                validate_env_file(str(env_file))
        finally:
            # Restore permissions for cleanup
            env_file.chmod(0o644)


class TestLoadConfig:
    """Test load_config function."""

    def test_load_config_default(self):
        """Test loading config without custom env file."""
        # Clear specific environment variables that might interfere
        env_vars_to_clear = [
            "OPENAI_API_KEY",
            "LLM_PROVIDER",
            "OPENAI_MODEL",
            "DEFAULT_OUTPUT_DIR",
            "LOG_LEVEL",
        ]

        # Create a clean environment by removing these variables completely
        cleared_env = {
            k: v for k, v in os.environ.items() if k not in env_vars_to_clear
        }

        with patch.dict(os.environ, cleared_env, clear=True):
            config = load_config()

            # Should use defaults or values from default .env file
            assert config.llm_provider in [
                "openai",
                "ollama",
                "auto",
            ]  # Could be default or from .env
            assert config.openai_model == "gpt-4o-mini"
            assert config.default_output_dir == "./separated_statements"
            assert config.log_level == "INFO"

    def test_load_config_custom_env_file(self, tmp_path):
        """Test loading config with custom env file."""
        # Create custom env file
        custom_env = tmp_path / "custom.env"
        custom_env.write_text("""
LLM_PROVIDER=ollama
OPENAI_MODEL=gpt-4o
DEFAULT_OUTPUT_DIR=/custom/output
LOG_LEVEL=DEBUG
OPENAI_API_KEY=test-key-123
MAX_FILE_SIZE_MB=200
ENABLE_AUDIT_LOGGING=false
""")

        config = load_config(str(custom_env))

        # Should use custom values
        assert config.llm_provider == "ollama"
        assert config.openai_model == "gpt-4o"
        assert config.default_output_dir == "/custom/output"
        assert config.log_level == "DEBUG"
        assert config.openai_api_key == "test-key-123"
        assert config.max_file_size_mb == 200
        assert config.enable_audit_logging is False

    def test_load_config_override_behavior(self, tmp_path):
        """Test that custom env file overrides existing environment variables."""
        # Set environment variable
        with patch.dict(os.environ, {"LOG_LEVEL": "ERROR"}):
            # Create custom env file with different value
            custom_env = tmp_path / "override.env"
            custom_env.write_text("LOG_LEVEL=DEBUG\nOPENAI_API_KEY=test-override")

            config = load_config(str(custom_env))

            # Should use custom env file value, not environment variable
            assert config.log_level == "DEBUG"
            assert config.openai_api_key == "test-override"

    def test_load_config_list_values(self, tmp_path):
        """Test loading config with list-type values."""
        custom_env = tmp_path / "lists.env"
        custom_env.write_text("""
ALLOWED_INPUT_DIRS=/path1,/path2,/path3
PAPERLESS_TAGS=bank,statement,financial
ALLOWED_FILE_EXTENSIONS=.pdf,.doc
OPENAI_API_KEY=test-list-key
""")

        config = load_config(str(custom_env))

        assert config.allowed_input_dirs == ["/path1", "/path2", "/path3"]
        assert config.paperless_tags == ["bank", "statement", "financial"]
        assert config.allowed_file_extensions == [".pdf", ".doc"]

    def test_load_config_boolean_values(self, tmp_path):
        """Test loading config with boolean values."""
        custom_env = tmp_path / "booleans.env"
        custom_env.write_text("""
ENABLE_AUDIT_LOGGING=true
PAPERLESS_ENABLED=1
INCLUDE_BANK_IN_FILENAME=yes
ENABLE_FALLBACK_PROCESSING=on
OPENAI_API_KEY=test-bool-key
""")

        config = load_config(str(custom_env))

        assert config.enable_audit_logging is True
        assert config.paperless_enabled is True
        assert config.include_bank_in_filename is True
        assert config.enable_fallback_processing is True

    def test_load_config_numeric_values(self, tmp_path):
        """Test loading config with numeric values."""
        custom_env = tmp_path / "numbers.env"
        custom_env.write_text("""
LLM_TEMPERATURE=0.5
CHUNK_SIZE=8000
MAX_FILE_SIZE_MB=150
OPENAI_API_KEY=test-numeric-key
""")

        config = load_config(str(custom_env))

        assert config.llm_temperature == 0.5
        assert config.chunk_size == 8000
        assert config.max_file_size_mb == 150

    def test_load_config_nonexistent_file(self, tmp_path):
        """Test loading config with nonexistent env file raises error."""
        nonexistent_file = tmp_path / "nonexistent.env"

        with pytest.raises(FileNotFoundError, match="Environment file not found"):
            load_config(str(nonexistent_file))

    def test_load_config_unreadable_file(self, tmp_path):
        """Test loading config with unreadable file raises error."""
        unreadable_file = tmp_path / "unreadable.env"
        unreadable_file.write_text("TEST=value")
        unreadable_file.chmod(0o000)

        try:
            # The load_config function now re-raises PermissionError directly
            with pytest.raises(PermissionError, match="Cannot read environment file"):
                load_config(str(unreadable_file))
        finally:
            # Restore permissions for cleanup
            unreadable_file.chmod(0o644)

    def test_load_config_directory_path(self, tmp_path):
        """Test loading config with directory path raises error."""
        with pytest.raises(ValueError, match="Environment path is not a file"):
            load_config(str(tmp_path))


class TestConfigValidation:
    """Test Config model validation."""

    def test_invalid_log_level(self):
        """Test that invalid log level raises validation error."""
        with pytest.raises(ValueError, match="Log level must be one of"):
            Config(log_level="INVALID", openai_api_key="test-key")

    def test_invalid_openai_model(self):
        """Test that invalid OpenAI model raises validation error."""
        with pytest.raises(ValueError, match="OpenAI model must be one of"):
            Config(openai_model="invalid-model", openai_api_key="test-key")

    def test_invalid_llm_provider(self):
        """Test that invalid LLM provider raises validation error."""
        with pytest.raises(ValueError, match="LLM provider must be one of"):
            Config(llm_provider="invalid-provider", openai_api_key="test-key")

    def test_chunk_overlap_validation(self):
        """Test chunk overlap cannot exceed chunk size."""
        with pytest.raises(
            ValueError, match="Chunk overlap must be less than chunk size"
        ):
            Config(chunk_size=1000, chunk_overlap=1500, openai_api_key="test-key")

    def test_openai_api_key_validation_production(self):
        """Test OpenAI API key validation works for valid production keys."""
        # Test that a valid production key works
        config = Config(openai_api_key="sk-test1234567890abcdef1234567890abcdef")
        assert config.openai_api_key == "sk-test1234567890abcdef1234567890abcdef"

    def test_openai_api_key_validation_test_env(self):
        """Test OpenAI API key validation allows test keys in test environment."""
        # Test keys should be allowed
        test_keys = ["test-key", "invalid-key", "mock-key", "fake-key", "dummy-key", ""]

        for test_key in test_keys:
            # Should not raise validation error for test keys
            config = Config(openai_api_key=test_key)
            assert config.openai_api_key == test_key


class TestConfigEnvironmentIntegration:
    """Test integration with different environment configurations."""

    def test_development_config(self, tmp_path):
        """Test loading development configuration."""
        dev_env = tmp_path / ".env.dev"
        dev_env.write_text("""
# Development Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=test-dev-key
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=DEBUG
DEFAULT_OUTPUT_DIR=./dev_output
ENABLE_AUDIT_LOGGING=true
""")

        config = load_config(str(dev_env))

        assert config.llm_provider == "openai"
        assert config.log_level == "DEBUG"
        assert config.default_output_dir == "./dev_output"
        assert config.enable_audit_logging is True

    def test_production_config(self, tmp_path):
        """Test loading production configuration."""
        prod_env = tmp_path / ".env.prod"
        prod_env.write_text("""
# Production Configuration
LLM_PROVIDER=openai
OPENAI_API_KEY=test-prod-key
OPENAI_MODEL=gpt-4o
LOG_LEVEL=WARNING
DEFAULT_OUTPUT_DIR=/var/app/output
MAX_FILE_SIZE_MB=50
ENABLE_AUDIT_LOGGING=true
ALLOWED_INPUT_DIRS=/secure/input
ALLOWED_OUTPUT_DIRS=/secure/output
""")

        config = load_config(str(prod_env))

        assert config.llm_provider == "openai"
        assert config.openai_model == "gpt-4o"
        assert config.log_level == "WARNING"
        assert config.default_output_dir == "/var/app/output"
        assert config.max_file_size_mb == 50
        assert config.allowed_input_dirs == ["/secure/input"]
        assert config.allowed_output_dirs == ["/secure/output"]

    def test_testing_config(self, tmp_path):
        """Test loading testing configuration."""
        test_env = tmp_path / ".env.test"
        test_env.write_text("""
# Testing Configuration
LLM_PROVIDER=auto
OPENAI_API_KEY=test-key
OPENAI_MODEL=gpt-4o-mini
LOG_LEVEL=ERROR
DEFAULT_OUTPUT_DIR=./test_output
MAX_FILE_SIZE_MB=10
ENABLE_FALLBACK_PROCESSING=false
""")

        config = load_config(str(test_env))

        assert config.llm_provider == "auto"
        assert config.log_level == "ERROR"
        assert config.default_output_dir == "./test_output"
        assert config.max_file_size_mb == 10
        assert config.enable_fallback_processing is False

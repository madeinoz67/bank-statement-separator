"""Unit tests for CLI functionality."""

from click.testing import CliRunner

from src.bank_statement_separator.main import main


class TestEnvHelpCommand:
    """Test the env-help command functionality."""

    def test_env_help_all_categories(self):
        """Test env-help command displays all categories by default."""
        runner = CliRunner()
        result = runner.invoke(main, ["env-help"])

        assert result.exit_code == 0
        assert "Environment Variable Documentation" in result.output
        assert "🤖 LLM Provider Configuration" in result.output
        assert "⚙️ Processing Configuration" in result.output
        assert "🔒 Security & Logging" in result.output
        assert "📄 Paperless-ngx Integration" in result.output
        assert "🚨 Error Handling & Quarantine" in result.output
        assert "✅ Document Validation" in result.output

    def test_env_help_llm_category(self):
        """Test env-help command with LLM category filter."""
        runner = CliRunner()
        result = runner.invoke(main, ["env-help", "--category", "llm"])

        assert result.exit_code == 0
        assert "🤖 LLM Provider Configuration" in result.output
        assert "OPENAI_API_KEY" in result.output
        assert "OLLAMA_BASE_URL" in result.output
        # Should not contain other categories when filtered
        assert "📄 Paperless-ngx Integration" not in result.output

    def test_env_help_processing_category(self):
        """Test env-help command with processing category filter."""
        runner = CliRunner()
        result = runner.invoke(main, ["env-help", "--category", "processing"])

        assert result.exit_code == 0
        assert "⚙️ Processing Configuration" in result.output
        assert "CHUNK_SIZE" in result.output
        assert "DEFAULT_OUTPUT_DIR" in result.output
        assert "MAX_FILE_SIZE_MB" in result.output

    def test_env_help_paperless_category(self):
        """Test env-help command with paperless category filter."""
        runner = CliRunner()
        result = runner.invoke(main, ["env-help", "--category", "paperless"])

        assert result.exit_code == 0
        assert "📄 Paperless-ngx Integration" in result.output
        assert "PAPERLESS_ENABLED" in result.output
        assert "PAPERLESS_URL" in result.output
        assert "PAPERLESS_TOKEN" in result.output

    def test_env_help_invalid_category(self):
        """Test env-help command with invalid category."""
        runner = CliRunner()
        result = runner.invoke(main, ["env-help", "--category", "invalid"])

        # Click validates choices and exits with code 2 for invalid options
        assert result.exit_code == 2
        assert "Invalid value for '--category'" in result.output

    def test_env_help_contains_documentation_links(self):
        """Test that env-help includes documentation links."""
        runner = CliRunner()
        result = runner.invoke(main, ["env-help"])

        assert result.exit_code == 0
        assert "https://madeinoz67.github.io/bank-statement-separator/" in result.output
        assert "Configuration Guide" in result.output
        assert "Environment Variables Reference" in result.output


class TestVersionCommand:
    """Test the version command enhancements."""

    def test_version_contains_repository_link(self):
        """Test that version command includes repository link."""
        runner = CliRunner()
        result = runner.invoke(main, ["version"])

        assert result.exit_code == 0
        assert "https://github.com/madeinoz67/bank-statement-separator" in result.output

    def test_version_contains_documentation_links(self):
        """Test that version command includes documentation and issue links."""
        runner = CliRunner()
        result = runner.invoke(main, ["version"])

        assert result.exit_code == 0
        assert (
            "Documentation: https://madeinoz67.github.io/bank-statement-separator/"
            in result.output
        )
        assert (
            "Issues: https://github.com/madeinoz67/bank-statement-separator/issues"
            in result.output
        )

    def test_version_contains_basic_info(self):
        """Test that version command contains expected information."""
        runner = CliRunner()
        result = runner.invoke(main, ["version"])

        assert result.exit_code == 0
        assert "Bank Statement Separator" in result.output
        assert "Version Information" in result.output
        assert "Stephen Eaton" in result.output
        assert "MIT" in result.output


class TestCommandHelpEnhancements:
    """Test that individual commands include environment variable help."""

    def test_process_command_help_includes_env_vars(self):
        """Test that process command help includes environment variables."""
        runner = CliRunner()
        result = runner.invoke(main, ["process", "--help"])

        assert result.exit_code == 0
        assert "COMMON ENVIRONMENT VARIABLES" in result.output
        assert "OPENAI_API_KEY" in result.output
        assert "DEFAULT_OUTPUT_DIR" in result.output
        assert "env-help" in result.output

    def test_process_paperless_help_includes_env_vars(self):
        """Test that process-paperless command help includes environment variables."""
        runner = CliRunner()
        result = runner.invoke(main, ["process-paperless", "--help"])

        assert result.exit_code == 0
        assert "REQUIRED ENVIRONMENT VARIABLES" in result.output
        assert "PAPERLESS_ENABLED" in result.output
        assert "PAPERLESS_URL" in result.output
        assert "PAPERLESS_TOKEN" in result.output

    def test_batch_process_help_includes_env_vars(self):
        """Test that batch-process command help includes environment variables."""
        runner = CliRunner()
        result = runner.invoke(main, ["batch-process", "--help"])

        assert result.exit_code == 0
        assert "BATCH PROCESSING ENVIRONMENT VARIABLES" in result.output
        assert "ERROR HANDLING VARIABLES" in result.output
        assert "QUARANTINE_DIRECTORY" in result.output
        assert "MAX_RETRY_ATTEMPTS" in result.output

    def test_quarantine_status_help_includes_env_vars(self):
        """Test that quarantine-status command help includes environment variables."""
        runner = CliRunner()
        result = runner.invoke(main, ["quarantine-status", "--help"])

        assert result.exit_code == 0
        assert "RELEVANT ENVIRONMENT VARIABLES" in result.output
        assert "QUARANTINE_DIRECTORY" in result.output
        assert "ENABLE_ERROR_REPORTING" in result.output

    def test_quarantine_clean_help_includes_env_vars(self):
        """Test that quarantine-clean command help includes environment variables."""
        runner = CliRunner()
        result = runner.invoke(main, ["quarantine-clean", "--help"])

        assert result.exit_code == 0
        assert "RELEVANT ENVIRONMENT VARIABLES" in result.output
        assert "QUARANTINE_DIRECTORY" in result.output
        assert "ERROR_REPORT_DIRECTORY" in result.output


class TestCliIntegration:
    """Test CLI integration with the help system."""

    def test_main_help_lists_env_help_command(self):
        """Test that main CLI help lists the env-help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])

        assert result.exit_code == 0
        assert "env-help" in result.output
        assert "Display comprehensive environment variable" in result.output

    def test_env_help_command_exists_in_main_group(self):
        """Test that env-help command is properly registered."""
        runner = CliRunner()
        # This should not produce a "No such command" error
        result = runner.invoke(main, ["env-help", "--help"])

        assert result.exit_code == 0
        assert (
            "Display comprehensive environment variable documentation" in result.output
        )
        assert "--category" in result.output

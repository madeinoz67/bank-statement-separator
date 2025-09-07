"""Integration tests for Ollama provider with factory and workflow."""

import pytest
from unittest.mock import Mock, patch
import json

from src.bank_statement_separator.llm import LLMProviderFactory, OllamaProvider
from src.bank_statement_separator.llm.base import LLMProviderError


@pytest.mark.unit
class TestOllamaFactoryIntegration:
    """Test Ollama provider integration with factory."""

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_factory_creates_ollama_provider(self, mock_chat_ollama):
        """Test factory creates Ollama provider correctly."""
        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        config = {
            "base_url": "http://localhost:11434",
            "model": "llama3.2",
            "temperature": 0.1,
            "max_tokens": 4000,
        }

        provider = LLMProviderFactory.create_provider("ollama", config)

        assert isinstance(provider, OllamaProvider)
        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "llama3.2"
        assert provider.temperature == 0.1
        assert provider.max_tokens == 4000

        # Verify ChatOllama was called with correct parameters
        mock_chat_ollama.assert_called_once_with(
            base_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.1,
            num_predict=4000,
        )

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_factory_creates_from_app_config(self, mock_chat_ollama):
        """Test factory creates Ollama provider from app config."""
        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        # Mock app config
        app_config = Mock()
        app_config.llm_provider = "ollama"
        app_config.ollama_base_url = "http://custom:8080"
        app_config.ollama_model = "custom-model"
        app_config.llm_temperature = 0.2
        app_config.llm_max_tokens = 5000

        provider = LLMProviderFactory.create_from_config(app_config)

        assert isinstance(provider, OllamaProvider)
        assert provider.base_url == "http://custom:8080"
        assert provider.model == "custom-model"
        assert provider.temperature == 0.2
        assert provider.max_tokens == 5000

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_factory_with_default_config(self, mock_chat_ollama):
        """Test factory with default Ollama configuration."""
        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        # Mock app config with defaults
        app_config = Mock()
        app_config.llm_provider = "ollama"
        # Set defaults explicitly since getattr with mock objects returns mocks
        app_config.ollama_base_url = "http://localhost:11434"
        app_config.ollama_model = "llama3.2"
        app_config.llm_temperature = 0.1
        app_config.llm_max_tokens = 4000

        provider = LLMProviderFactory.create_from_config(app_config)

        assert isinstance(provider, OllamaProvider)
        assert provider.base_url == "http://localhost:11434"  # Default
        assert provider.model == "llama3.2"  # Default

    def test_factory_lists_ollama_as_available(self):
        """Test that factory includes Ollama in available providers."""
        providers = LLMProviderFactory._providers

        assert "ollama" in providers
        assert providers["ollama"] == OllamaProvider

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_factory_handles_ollama_creation_error(self, mock_chat_ollama):
        """Test factory handles Ollama creation errors."""
        mock_chat_ollama.side_effect = Exception("Ollama server not available")

        with pytest.raises(LLMProviderError, match="Failed to create ollama provider"):
            LLMProviderFactory.create_provider("ollama", {})


@pytest.mark.unit
class TestOllamaWorkflowIntegration:
    """Test Ollama provider integration with workflow components."""

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_ollama_boundary_detection_workflow(self, mock_chat_ollama):
        """Test complete boundary detection workflow with Ollama."""
        # Setup Ollama provider
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "total_statements": 2,
                "boundaries": [
                    {"start_page": 1, "end_page": 3, "account_number": "123456"},
                    {"start_page": 4, "end_page": 6, "account_number": "789012"},
                ],
                "confidence": 0.9,
            }
        )
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama.return_value = mock_llm

        # Create provider through factory
        provider = LLMProviderFactory.create_provider(
            "ollama", {"base_url": "http://localhost:11434", "model": "llama3.2"}
        )

        # Test boundary detection
        document_text = "Bank Statement 1 content...\n---\nBank Statement 2 content..."
        result = provider.analyze_boundaries(document_text, total_pages=6)

        # Verify results
        assert len(result.boundaries) == 2
        assert result.boundaries[0]["start_page"] == 1
        assert result.boundaries[0]["end_page"] == 3
        assert result.boundaries[1]["start_page"] == 4
        assert result.boundaries[1]["end_page"] == 6
        assert result.confidence == 0.9

        # Verify LLM was called
        mock_llm.invoke.assert_called_once()
        call_args = mock_llm.invoke.call_args[0][0]
        assert len(call_args) == 1  # Should be a list with one HumanMessage
        assert document_text in call_args[0].content

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_ollama_metadata_extraction_workflow(self, mock_chat_ollama):
        """Test complete metadata extraction workflow with Ollama."""
        # Setup Ollama provider
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "bank_name": "Chase Bank",
                "account_number": "****1234",
                "account_type": "Credit Card",
                "statement_period": "Jan 2023",
                "customer_name": "John Doe",
                "confidence": 0.85,
            }
        )
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama.return_value = mock_llm

        # Create provider
        provider = LLMProviderFactory.create_provider("ollama", {})

        # Test metadata extraction
        statement_text = "Chase Bank Statement for John Doe..."
        result = provider.extract_metadata(statement_text, 1, 3)

        # Verify results
        assert result.metadata["bank_name"] == "Chase Bank"
        assert result.metadata["account_number"] == "****1234"
        assert result.metadata["account_type"] == "Credit Card"
        assert result.metadata["statement_period"] == "Jan 2023"
        assert result.metadata["customer_name"] == "John Doe"
        assert result.confidence == 0.85

        # Verify LLM was called
        mock_llm.invoke.assert_called_once()
        call_args = mock_llm.invoke.call_args[0][0]
        assert statement_text in call_args[0].content
        assert "pages 1-3" in call_args[0].content

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_ollama_availability_check(self, mock_chat_ollama):
        """Test Ollama availability checking."""
        # Setup successful availability check
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "OK"
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama.return_value = mock_llm

        provider = LLMProviderFactory.create_provider("ollama", {})

        # Test availability
        assert provider.is_available() is True

        # Verify test call was made
        mock_llm.invoke.assert_called_once()
        test_call_args = mock_llm.invoke.call_args[0][0]
        assert "Hello, respond with just 'OK'" in test_call_args[0].content

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_ollama_unavailable_handling(self, mock_chat_ollama):
        """Test handling when Ollama is unavailable."""
        # Setup connection failure
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("Connection refused")
        mock_chat_ollama.return_value = mock_llm

        provider = LLMProviderFactory.create_provider("ollama", {})

        # Test availability
        assert provider.is_available() is False

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_ollama_provider_info(self, mock_chat_ollama):
        """Test Ollama provider information."""
        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        provider = LLMProviderFactory.create_provider(
            "ollama", {"base_url": "http://test:1234", "model": "test-model"}
        )

        info = provider.get_info()

        assert info["name"] == "ollama"
        assert info["type"] == "OllamaProvider"
        assert info["model"] == "test-model"
        assert info["base_url"] == "http://test:1234"
        assert info["privacy"] == "high"
        assert info["cost"] == "free"
        assert "local_processing" in info["features"]


@pytest.mark.unit
class TestOllamaErrorHandling:
    """Test Ollama provider error handling scenarios."""

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_ollama_json_parsing_error(self, mock_chat_ollama):
        """Test handling of invalid JSON responses."""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "This is not valid JSON"
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama.return_value = mock_llm

        provider = LLMProviderFactory.create_provider("ollama", {})

        with pytest.raises(LLMProviderError, match="Invalid boundary response format"):
            provider.analyze_boundaries("test text")

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_ollama_network_error(self, mock_chat_ollama):
        """Test handling of network errors."""
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("Network timeout")
        mock_chat_ollama.return_value = mock_llm

        provider = LLMProviderFactory.create_provider("ollama", {})

        with pytest.raises(LLMProviderError, match="Boundary analysis failed"):
            provider.analyze_boundaries("test text")

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_ollama_malformed_boundary_response(self, mock_chat_ollama):
        """Test handling of malformed boundary responses."""
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = json.dumps(
            {
                "boundaries": [
                    {"start_page": 1}  # Missing end_page
                ]
            }
        )
        mock_llm.invoke.return_value = mock_response
        mock_chat_ollama.return_value = mock_llm

        provider = LLMProviderFactory.create_provider("ollama", {})

        with pytest.raises(LLMProviderError, match="missing start_page or end_page"):
            provider.analyze_boundaries("test text")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

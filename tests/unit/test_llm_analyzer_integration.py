"""Integration tests for LLM analyzer with provider abstraction."""

from unittest.mock import Mock, patch

import pytest

from src.bank_statement_separator.llm import (
    LLMProviderFactory,
    OllamaProvider,
    OpenAIProvider,
)
from src.bank_statement_separator.llm.base import (
    BoundaryResult,
    MetadataResult,
)
from src.bank_statement_separator.nodes.llm_analyzer import (
    BoundaryDetectionResult,
    LLMAnalyzer,
    StatementMetadata,
)


@pytest.mark.unit
class TestLLMAnalyzerIntegration:
    """Test integration between analyzer and provider abstraction."""

    def test_analyzer_with_openai_provider(self):
        """Test analyzer using OpenAI provider."""
        # Create mock config
        config = Mock()
        config.llm_provider = "openai"
        config.openai_api_key = "test-key"
        config.openai_model = "gpt-4o-mini"
        config.llm_temperature = 0.1

        # Create analyzer
        analyzer = LLMAnalyzer(config)

        # Should have created OpenAI provider
        assert analyzer.provider is not None
        assert isinstance(analyzer.provider, OpenAIProvider)
        assert analyzer.provider.api_key == "test-key"

    def test_analyzer_with_ollama_provider(self):
        """Test analyzer using Ollama provider."""
        # Create mock config
        config = Mock()
        config.llm_provider = "ollama"
        config.ollama_base_url = "http://localhost:11434"
        config.ollama_model = "llama3.2"
        config.llm_temperature = 0.1
        config.llm_max_tokens = 4000

        # Create analyzer
        with patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama"):
            analyzer = LLMAnalyzer(config)

        # Should have created Ollama provider
        assert analyzer.provider is not None
        assert isinstance(analyzer.provider, OllamaProvider)
        assert analyzer.provider.base_url == "http://localhost:11434"
        assert analyzer.provider.model == "llama3.2"

    def test_analyzer_without_provider(self):
        """Test analyzer when provider creation fails."""
        config = Mock()
        config.llm_provider = "invalid"

        # The factory should raise LLMProviderError for invalid provider
        from src.bank_statement_separator.llm.base import LLMProviderError

        with patch.object(LLMProviderFactory, "create_from_config") as mock_create:
            mock_create.side_effect = LLMProviderError("Invalid provider type")

            analyzer = LLMAnalyzer(config)

            # Should handle failure gracefully
            assert analyzer.provider is None

    @patch("src.bank_statement_separator.llm.openai_provider.ChatOpenAI")
    def test_boundary_detection_with_provider(self, mock_chat):
        """Test boundary detection using provider."""
        # Setup config and analyzer
        config = Mock()
        config.llm_provider = "openai"
        config.openai_api_key = "test-key"
        config.openai_model = "gpt-4o-mini"
        config.llm_temperature = 0.1

        # Mock the ChatOpenAI response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = '{"total_statements": 2, "boundaries": [{"start_page": 1, "end_page": 3}, {"start_page": 4, "end_page": 6}]}'
        mock_llm.invoke.return_value = mock_response
        mock_chat.return_value = mock_llm

        analyzer = LLMAnalyzer(config)

        # Test boundary detection
        text_chunks = ["Page 1 content", "Page 2 content", "Page 3 content"]
        result = analyzer.detect_statement_boundaries(text_chunks, total_pages=6)

        # Should get results from provider
        assert isinstance(result, BoundaryDetectionResult)
        assert result.total_statements == 2
        assert len(result.boundaries) == 2
        assert result.boundaries[0].start_page == 1
        assert result.boundaries[0].end_page == 3

    def test_boundary_detection_fallback(self):
        """Test boundary detection fallback when provider fails."""
        config = Mock()
        config.llm_provider = "openai"
        config.openai_api_key = None  # No API key

        analyzer = LLMAnalyzer(config)

        # Should use fallback
        text_chunks = ["Page 1 content", "Page 2 content"]
        result = analyzer.detect_statement_boundaries(text_chunks, total_pages=2)

        assert isinstance(result, BoundaryDetectionResult)
        assert result.total_statements == 1
        assert len(result.boundaries) == 1
        assert "fallback" in result.analysis_notes.lower()

    @patch("src.bank_statement_separator.llm.openai_provider.ChatOpenAI")
    def test_metadata_extraction_with_provider(self, mock_chat):
        """Test metadata extraction using provider."""
        # Setup config and analyzer
        config = Mock()
        config.llm_provider = "openai"
        config.openai_api_key = "test-key"
        config.openai_model = "gpt-4o-mini"
        config.llm_temperature = 0.1

        # Mock the ChatOpenAI response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "bank_name": "Test Bank",
            "account_number": "123456",
            "account_type": "Checking",
            "confidence": 0.9
        }"""
        mock_llm.invoke.return_value = mock_response
        mock_chat.return_value = mock_llm

        analyzer = LLMAnalyzer(config)

        # Test metadata extraction
        result = analyzer.extract_metadata("Statement text", 1, 3)

        # Should get results from provider
        assert isinstance(result, StatementMetadata)
        assert result.bank_name == "Test Bank"
        assert result.account_number == "123456"
        assert result.confidence == 0.9

    def test_metadata_extraction_fallback(self):
        """Test metadata extraction fallback when provider fails."""
        config = Mock()
        config.llm_provider = "openai"
        config.openai_api_key = None  # No API key

        analyzer = LLMAnalyzer(config)

        # Should use fallback
        result = analyzer.extract_metadata("Statement text", 1, 3)

        assert isinstance(result, StatementMetadata)
        assert result.bank_name == "Unknown"
        assert result.confidence == 0.3

    def test_provider_conversion_boundary_result(self):
        """Test conversion of provider boundary result."""
        config = Mock()
        analyzer = LLMAnalyzer(config, provider=None)

        # Mock provider result
        provider_result = BoundaryResult(
            boundaries=[
                {"start_page": 1, "end_page": 5, "account_number": "123"},
                {"start_page": 6, "end_page": 10, "account_number": "456"},
            ],
            confidence=0.9,
            analysis_notes="Provider detected 2 statements",
        )

        # Convert result
        result = analyzer._convert_provider_boundaries(provider_result, total_pages=10)

        assert isinstance(result, BoundaryDetectionResult)
        assert result.total_statements == 2
        assert len(result.boundaries) == 2
        assert result.boundaries[0].account_number == "123"
        assert result.boundaries[1].account_number == "456"
        assert result.analysis_notes == "Provider detected 2 statements"

    def test_provider_conversion_metadata_result(self):
        """Test conversion of provider metadata result."""
        config = Mock()
        analyzer = LLMAnalyzer(config, provider=None)

        # Mock provider result
        provider_result = MetadataResult(
            metadata={
                "bank_name": "Test Bank",
                "account_number": "123456",
                "account_type": "Savings",
                "statement_period": "Jan 2023",
            },
            confidence=0.85,
        )

        # Convert result
        result = analyzer._convert_provider_metadata(provider_result)

        assert isinstance(result, StatementMetadata)
        assert result.bank_name == "Test Bank"
        assert result.account_number == "123456"
        assert result.account_type == "Savings"
        assert result.statement_period == "Jan 2023"
        assert result.confidence == 0.85


@pytest.mark.unit
class TestLLMAnalyzerWithFactory:
    """Test analyzer using factory to create providers."""

    def test_create_analyzer_from_config(self):
        """Test creating analyzer with different provider configs."""
        # OpenAI config
        openai_config = Mock()
        openai_config.llm_provider = "openai"
        openai_config.openai_api_key = "test-key"
        openai_config.openai_model = "gpt-4o-mini"
        openai_config.llm_temperature = 0.1

        analyzer = LLMAnalyzer(openai_config)

        assert analyzer.provider is not None
        assert isinstance(analyzer.provider, OpenAIProvider)

    def test_create_analyzer_with_ollama_config(self):
        """Test creating analyzer with Ollama config."""
        # Ollama config
        ollama_config = Mock()
        ollama_config.llm_provider = "ollama"
        ollama_config.ollama_base_url = "http://localhost:11434"
        ollama_config.ollama_model = "llama3.2"
        ollama_config.llm_temperature = 0.1
        ollama_config.llm_max_tokens = 4000

        with patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama"):
            analyzer = LLMAnalyzer(ollama_config)

        assert analyzer.provider is not None
        assert isinstance(analyzer.provider, OllamaProvider)

    def test_analyzer_provider_info(self):
        """Test getting provider information."""
        config = Mock()
        config.llm_provider = "openai"
        config.openai_api_key = "test-key"
        config.openai_model = "gpt-4o-mini"
        config.llm_temperature = 0.1

        analyzer = LLMAnalyzer(config)

        # Get provider info
        if analyzer.provider:
            info = analyzer.provider.get_info()
            assert info["name"] == "openai"
            assert info["type"] == "OpenAIProvider"
            assert "available" in info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

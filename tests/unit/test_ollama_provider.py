"""Unit tests for Ollama LLM provider."""

import json
from unittest.mock import Mock, patch

import pytest

from src.bank_statement_separator.llm import LLMProviderError, OllamaProvider
from src.bank_statement_separator.llm.base import (
    BoundaryResult,
    MetadataResult,
)


@pytest.fixture
def ollama_provider():
    """Create OllamaProvider instance for testing."""
    with patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama"):
        return OllamaProvider(
            base_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.1,
            max_tokens=4000,
        )


@pytest.fixture
def mock_ollama_response():
    """Mock response from Ollama."""
    response = Mock()
    response.content = ""
    return response


@pytest.mark.unit
@pytest.mark.llm
@pytest.mark.requires_ollama
class TestOllamaProviderInitialization:
    """Test Ollama provider initialization."""

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_initialization_success(self, mock_chat_ollama):
        """Test successful provider initialization."""
        mock_llm = Mock()
        mock_chat_ollama.return_value = mock_llm

        provider = OllamaProvider(
            base_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.2,
            max_tokens=5000,
        )

        # Verify initialization
        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "llama3.2"
        assert provider.temperature == 0.2
        assert provider.max_tokens == 5000
        assert provider.llm == mock_llm

        # Verify ChatOllama was called correctly
        mock_chat_ollama.assert_called_once_with(
            base_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.2,
            num_predict=5000,
        )

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_initialization_with_defaults(self, mock_chat_ollama):
        """Test initialization with default parameters."""
        provider = OllamaProvider()

        assert provider.base_url == "http://localhost:11434"
        assert provider.model == "llama3.2"
        assert provider.temperature == 0.1
        assert provider.max_tokens == 4000

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_initialization_failure(self, mock_chat_ollama):
        """Test initialization failure handling."""
        mock_chat_ollama.side_effect = Exception("Connection failed")

        with pytest.raises(LLMProviderError, match="Ollama initialization failed"):
            OllamaProvider()

    @patch("src.bank_statement_separator.llm.ollama_provider.ChatOllama")
    def test_initialization_with_kwargs(self, mock_chat_ollama):
        """Test initialization with additional kwargs."""
        OllamaProvider(timeout=30, num_ctx=2048)

        # Verify additional kwargs were passed
        mock_chat_ollama.assert_called_once_with(
            base_url="http://localhost:11434",
            model="llama3.2",
            temperature=0.1,
            num_predict=4000,
            timeout=30,
            num_ctx=2048,
        )


@pytest.mark.unit
@pytest.mark.llm
@pytest.mark.requires_ollama
class TestOllamaBoundaryAnalysis:
    """Test boundary analysis functionality."""

    def test_analyze_boundaries_success(self, ollama_provider, mock_ollama_response):
        """Test successful boundary analysis."""
        # Mock successful response
        mock_ollama_response.content = json.dumps(
            {
                "total_statements": 2,
                "boundaries": [
                    {"start_page": 1, "end_page": 3, "account_number": "123456"},
                    {"start_page": 4, "end_page": 6, "account_number": "789012"},
                ],
                "confidence": 0.9,
            }
        )

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        # Test boundary analysis
        result = ollama_provider.analyze_boundaries("Test document text", total_pages=6)

        # Verify result
        assert isinstance(result, BoundaryResult)
        assert len(result.boundaries) == 2
        assert result.boundaries[0]["start_page"] == 1
        assert result.boundaries[0]["end_page"] == 3
        assert result.boundaries[0]["account_number"] == "123456"
        assert result.boundaries[1]["start_page"] == 4
        assert result.boundaries[1]["end_page"] == 6
        assert result.confidence == 0.9
        assert "Ollama detected 2 statement boundaries" in result.analysis_notes

    def test_analyze_boundaries_with_markdown(
        self, ollama_provider, mock_ollama_response
    ):
        """Test boundary analysis with markdown-formatted response."""
        # Mock response with markdown formatting
        mock_ollama_response.content = """```json
{
    "total_statements": 1,
    "boundaries": [
        {"start_page": 1, "end_page": 5, "account_number": "999888"}
    ],
    "confidence": 0.85
}
```"""

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        result = ollama_provider.analyze_boundaries("Test text")

        assert isinstance(result, BoundaryResult)
        assert len(result.boundaries) == 1
        assert result.boundaries[0]["account_number"] == "999888"
        assert result.confidence == 0.85

    def test_analyze_boundaries_missing_confidence(
        self, ollama_provider, mock_ollama_response
    ):
        """Test boundary analysis with missing confidence field."""
        mock_ollama_response.content = json.dumps(
            {"boundaries": [{"start_page": 1, "end_page": 2, "account_number": "123"}]}
        )

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        result = ollama_provider.analyze_boundaries("Test text")

        assert isinstance(result, BoundaryResult)
        assert result.confidence == 0.8  # Default value

    def test_analyze_boundaries_invalid_json(
        self, ollama_provider, mock_ollama_response
    ):
        """Test boundary analysis with invalid JSON response."""
        mock_ollama_response.content = "Invalid JSON response"

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        with pytest.raises(LLMProviderError, match="Invalid boundary response format"):
            ollama_provider.analyze_boundaries("Test text")

    def test_analyze_boundaries_missing_boundaries(
        self, ollama_provider, mock_ollama_response
    ):
        """Test boundary analysis with missing boundaries field."""
        mock_ollama_response.content = json.dumps(
            {"total_statements": 1, "confidence": 0.9}
        )

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        with pytest.raises(LLMProviderError, match="Missing 'boundaries' field"):
            ollama_provider.analyze_boundaries("Test text")

    def test_analyze_boundaries_invalid_boundary_format(
        self, ollama_provider, mock_ollama_response
    ):
        """Test boundary analysis with invalid boundary format."""
        mock_ollama_response.content = json.dumps(
            {
                "boundaries": [
                    {"start_page": 1}  # Missing end_page
                ]
            }
        )

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        with pytest.raises(LLMProviderError, match="missing start_page or end_page"):
            ollama_provider.analyze_boundaries("Test text")

    def test_analyze_boundaries_llm_error(self, ollama_provider):
        """Test boundary analysis with LLM invocation error."""
        ollama_provider.llm.invoke.side_effect = Exception("Network error")

        with pytest.raises(LLMProviderError, match="Boundary analysis failed"):
            ollama_provider.analyze_boundaries("Test text")


@pytest.mark.unit
@pytest.mark.llm
@pytest.mark.requires_ollama
class TestOllamaMetadataExtraction:
    """Test metadata extraction functionality."""

    def test_extract_metadata_success(self, ollama_provider, mock_ollama_response):
        """Test successful metadata extraction."""
        mock_ollama_response.content = json.dumps(
            {
                "bank_name": "Test Bank",
                "account_number": "123456789",
                "account_type": "Checking",
                "statement_period": "Jan 2023",
                "customer_name": "John Doe",
                "confidence": 0.95,
            }
        )

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        result = ollama_provider.extract_metadata("Statement text", 1, 3)

        assert isinstance(result, MetadataResult)
        assert result.metadata["bank_name"] == "Test Bank"
        assert result.metadata["account_number"] == "123456789"
        assert result.metadata["account_type"] == "Checking"
        assert result.metadata["statement_period"] == "Jan 2023"
        assert result.metadata["customer_name"] == "John Doe"
        assert result.confidence == 0.95

    def test_extract_metadata_with_markdown(
        self, ollama_provider, mock_ollama_response
    ):
        """Test metadata extraction with markdown-formatted response."""
        mock_ollama_response.content = """```json
{
    "bank_name": "Chase Bank",
    "account_number": "****1234",
    "account_type": "Credit Card",
    "confidence": 0.8
}
```"""

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        result = ollama_provider.extract_metadata("Statement text", 2, 4)

        assert isinstance(result, MetadataResult)
        assert result.metadata["bank_name"] == "Chase Bank"
        assert result.metadata["account_number"] == "****1234"
        assert result.metadata["account_type"] == "Credit Card"
        assert result.confidence == 0.8

    def test_extract_metadata_with_empty_fields(
        self, ollama_provider, mock_ollama_response
    ):
        """Test metadata extraction with empty fields."""
        mock_ollama_response.content = json.dumps(
            {
                "bank_name": "Wells Fargo",
                "account_number": "",
                "account_type": "Savings",
                "statement_period": "",
                "customer_name": "",
                "confidence": 0.6,
            }
        )

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        result = ollama_provider.extract_metadata("Statement text", 1, 2)

        # Empty fields should be filtered out
        assert "bank_name" in result.metadata
        assert "account_type" in result.metadata
        assert "account_number" not in result.metadata  # Empty string filtered out
        assert "statement_period" not in result.metadata
        assert "customer_name" not in result.metadata

    def test_extract_metadata_missing_fields(
        self, ollama_provider, mock_ollama_response
    ):
        """Test metadata extraction with missing fields."""
        mock_ollama_response.content = json.dumps({"bank_name": "Bank of America"})

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        result = ollama_provider.extract_metadata("Statement text", 1, 1)

        assert isinstance(result, MetadataResult)
        assert result.metadata["bank_name"] == "Bank of America"
        assert result.confidence == 0.7  # Default confidence

    def test_extract_metadata_defaults_unknown_bank(
        self, ollama_provider, mock_ollama_response
    ):
        """Test metadata extraction with all defaults."""
        mock_ollama_response.content = json.dumps({})

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        result = ollama_provider.extract_metadata("Statement text", 1, 1)

        # Should get Unknown bank name when nothing found
        assert result.metadata.get("bank_name") == "Unknown"
        assert result.confidence == 0.7

    def test_extract_metadata_invalid_json(self, ollama_provider, mock_ollama_response):
        """Test metadata extraction with invalid JSON."""
        mock_ollama_response.content = "Not valid JSON"

        ollama_provider.llm.invoke.return_value = mock_ollama_response

        with pytest.raises(LLMProviderError, match="Invalid metadata response format"):
            ollama_provider.extract_metadata("Statement text", 1, 1)

    def test_extract_metadata_llm_error(self, ollama_provider):
        """Test metadata extraction with LLM error."""
        ollama_provider.llm.invoke.side_effect = Exception("Connection timeout")

        with pytest.raises(LLMProviderError, match="Metadata extraction failed"):
            ollama_provider.extract_metadata("Statement text", 1, 1)


@pytest.mark.unit
@pytest.mark.llm
@pytest.mark.requires_ollama
class TestOllamaProviderInfo:
    """Test provider information methods."""

    def test_get_info(self, ollama_provider):
        """Test get_info method."""
        info = ollama_provider.get_info()

        assert info["name"] == "ollama"
        assert info["type"] == "OllamaProvider"
        assert info["model"] == "llama3.2"
        assert info["base_url"] == "http://localhost:11434"
        assert "available" in info
        assert info["features"] == [
            "boundary_analysis",
            "metadata_extraction",
            "local_processing",
        ]
        assert info["version"] == "1.0.0"
        assert info["privacy"] == "high"
        assert info["cost"] == "free"

    def test_get_info_custom_model(self, ollama_provider):
        """Test get_info with custom model."""
        ollama_provider.model = "custom-model"
        ollama_provider.base_url = "http://custom:8080"

        info = ollama_provider.get_info()

        assert info["model"] == "custom-model"
        assert info["base_url"] == "http://custom:8080"


@pytest.mark.unit
@pytest.mark.llm
@pytest.mark.requires_ollama
class TestOllamaAvailability:
    """Test provider availability checking."""

    def test_is_available_success(self, ollama_provider):
        """Test successful availability check."""
        mock_response = Mock()
        mock_response.content = "OK"
        ollama_provider.llm.invoke.return_value = mock_response

        assert ollama_provider.is_available() is True

    def test_is_available_connection_error(self, ollama_provider):
        """Test availability check with connection error."""
        ollama_provider.llm.invoke.side_effect = Exception("Connection refused")

        assert ollama_provider.is_available() is False

    def test_is_available_no_response(self, ollama_provider):
        """Test availability check with no response."""
        ollama_provider.llm.invoke.return_value = None

        assert ollama_provider.is_available() is False

    def test_is_available_invalid_response(self, ollama_provider):
        """Test availability check with invalid response."""
        mock_response = Mock()
        del mock_response.content  # Remove content attribute
        ollama_provider.llm.invoke.return_value = mock_response

        assert ollama_provider.is_available() is False


@pytest.mark.unit
@pytest.mark.llm
@pytest.mark.requires_ollama
class TestOllamaPromptGeneration:
    """Test prompt generation methods."""

    def test_create_boundary_prompt(self, ollama_provider):
        """Test boundary analysis prompt generation."""
        text = "Sample document text with multiple pages"
        prompt = ollama_provider._create_boundary_prompt(text, total_pages=10)

        assert "bank statement analyzer" in prompt.lower()
        assert "10 pages" in prompt
        assert text in prompt
        assert "start_page" in prompt
        assert "end_page" in prompt
        assert "JSON" in prompt

    def test_create_boundary_prompt_default_pages(self, ollama_provider):
        """Test boundary prompt with default page calculation."""
        text = "Page 1\n---\nPage 2\n---\nPage 3"
        prompt = ollama_provider._create_boundary_prompt(text)

        # Should calculate pages from text splits
        assert "3 pages" in prompt or text in prompt

    def test_create_metadata_prompt(self, ollama_provider):
        """Test metadata extraction prompt generation."""
        text = "Statement text with account info"
        start_page = 2
        end_page = 5

        prompt = ollama_provider._create_metadata_prompt(text, start_page, end_page)

        assert "bank statement analyzer" in prompt.lower()
        assert f"pages {start_page}-{end_page}" in prompt
        assert text in prompt
        assert "bank_name" in prompt
        assert "account_number" in prompt
        assert "JSON" in prompt


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

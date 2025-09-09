"""Unit tests for LLM provider abstraction."""

import time
from unittest.mock import Mock, patch

import pytest

from src.bank_statement_separator.llm import (
    LLMProvider,
    LLMProviderError,
    LLMProviderFactory,
    OpenAIProvider,
)
from src.bank_statement_separator.llm.base import (
    BoundaryResult,
    MetadataResult,
)
from src.bank_statement_separator.utils.rate_limiter import (
    BackoffStrategy,
    RateLimitConfig,
    RateLimiter,
    load_rate_limit_config_from_env,
)


@pytest.mark.unit
class TestLLMProviderBase:
    """Test base LLM provider functionality."""

    def test_provider_interface(self):
        """Test that LLMProvider defines required interface."""
        # Provider should be abstract
        with pytest.raises(TypeError):
            LLMProvider("test")

    def test_boundary_result_dataclass(self):
        """Test BoundaryResult dataclass."""
        result = BoundaryResult(
            boundaries=[{"start": 1, "end": 3}],
            confidence=0.9,
            analysis_notes="Test analysis",
            provider="test",
        )

        assert result.boundaries == [{"start": 1, "end": 3}]
        assert result.confidence == 0.9
        assert result.analysis_notes == "Test analysis"
        assert result.provider == "test"

    def test_metadata_result_dataclass(self):
        """Test MetadataResult dataclass."""
        result = MetadataResult(
            metadata={"bank": "Test Bank"}, confidence=0.8, provider="test"
        )

        assert result.metadata == {"bank": "Test Bank"}
        assert result.confidence == 0.8
        assert result.provider == "test"


@pytest.mark.unit
class TestOpenAIProvider:
    """Test OpenAI provider implementation."""

    def test_initialization_with_api_key(self):
        """Test OpenAI provider initialization with API key."""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")

        assert provider.name == "openai"
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"
        assert provider.is_available() is True

    def test_initialization_without_api_key(self):
        """Test OpenAI provider without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = OpenAIProvider()

            assert provider.api_key is None
            assert provider.is_available() is False

    def test_initialization_from_env(self):
        """Test OpenAI provider gets API key from environment."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            provider = OpenAIProvider()

            assert provider.api_key == "env-key"
            assert provider.is_available() is True

    @patch("src.bank_statement_separator.llm.openai_provider.ChatOpenAI")
    def test_analyze_boundaries_success(self, mock_chat):
        """Test successful boundary analysis with mock PDF content."""
        # Setup mock
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = '{"total_statements": 2, "boundaries": [{"start": 1, "end": 3}, {"start": 4, "end": 6}]}'
        mock_llm.invoke.return_value = mock_response
        mock_chat.return_value = mock_llm

        # Create mock PDF content with 6 pages (3 statements x 2 pages each)
        # This simulates extracted text from a real PDF with multiple bank statements
        pdf_pages = []

        # Statement 1: Pages 1-2
        pdf_pages.append("""
        WESTPAC BANKING CORPORATION
        Account Number: 4293 1831 9017 1234
        Statement Period: 01 Apr 2024 to 30 Apr 2024

        TRANSACTION HISTORY
        01 APR 2024 - Opening Balance: $1,250.00
        05 APR 2024 - Direct Deposit: $3,500.00
        10 APR 2024 - ATM Withdrawal: -$100.00
        15 APR 2024 - Online Purchase: -$89.99
        20 APR 2024 - Bill Payment: -$450.00
        30 APR 2024 - Closing Balance: $4,110.01
        """)

        pdf_pages.append("""
        WESTPAC BANKING CORPORATION - Continued
        Additional transactions and summary information for account ending in 1234.
        Interest earned: $5.67
        Fees charged: -$2.50
        Final balance: $4,113.18
        """)

        # Statement 2: Pages 3-4
        pdf_pages.append("""
        WESTPAC BANKING CORPORATION
        Account Number: 4293 1831 9017 5678
        Statement Period: 01 May 2024 to 31 May 2024

        TRANSACTION HISTORY
        01 MAY 2024 - Opening Balance: $2,340.00
        03 MAY 2024 - Direct Deposit: $4,200.00
        08 MAY 2024 - Grocery Store: -$156.78
        12 MAY 2024 - Gas Station: -$75.50
        18 MAY 2024 - Online Transfer: -$1,200.00
        25 MAY 2024 - Interest Earned: $12.45
        31 MAY 2024 - Closing Balance: $5,120.17
        """)

        pdf_pages.append("""
        WESTPAC BANKING CORPORATION - Continued
        Additional transactions for account ending in 5678.
        ATM fees: -$3.00
        Online banking charges: -$1.50
        Final balance with adjustments: $5,115.67
        """)

        # Statement 3: Pages 5-6
        pdf_pages.append("""
        COMMONWEALTH BANK OF AUSTRALIA
        Account Number: 0623 1045 8901 9012
        Statement Period: 01 Jun 2024 to 30 Jun 2024

        TRANSACTION HISTORY
        01 JUN 2024 - Opening Balance: $5,780.00
        04 JUN 2024 - Salary Deposit: $6,500.00
        07 JUN 2024 - Rent Payment: -$1,800.00
        11 JUN 2024 - Utilities: -$234.56
        15 JUN 2024 - Shopping: -$298.44
        22 JUN 2024 - Restaurant: -$87.90
        30 JUN 2024 - Closing Balance: $9,859.10
        """)

        pdf_pages.append("""
        COMMONWEALTH BANK OF AUSTRALIA - Continued
        Final statement summary for account ending in 9012.
        Total credits: $6,500.00
        Total debits: -$2,421.90
        Net movement: $4,078.10
        End balance: $9,859.10
        """)

        # Combine all pages with page separators (simulating PDF text extraction)
        document_text = "\n--- PAGE BREAK ---\n".join(pdf_pages)

        provider = OpenAIProvider(api_key="test-key")
        result = provider.analyze_boundaries(document_text, total_pages=6)

        assert isinstance(result, BoundaryResult)
        assert len(result.boundaries) == 2
        assert result.confidence == 0.9
        assert result.provider == "openai"
        assert "detected 2 statements" in result.analysis_notes

    @patch("src.bank_statement_separator.llm.openai_provider.ChatOpenAI")
    def test_analyze_boundaries_parse_error(self, mock_chat):
        """Test boundary analysis with parse error."""
        # Setup mock with invalid response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Invalid JSON response"
        mock_llm.invoke.return_value = mock_response
        mock_chat.return_value = mock_llm

        provider = OpenAIProvider(api_key="test-key")
        result = provider.analyze_boundaries("Test document text")

        # Should return fallback result
        assert isinstance(result, BoundaryResult)
        assert len(result.boundaries) == 1
        assert result.confidence == 0.5
        assert "Failed to parse" in result.analysis_notes

    def test_analyze_boundaries_no_api_key(self):
        """Test boundary analysis without API key."""
        with patch.dict("os.environ", {}, clear=True):
            provider = OpenAIProvider()

            with pytest.raises(LLMProviderError, match="not available"):
                provider.analyze_boundaries("Test text")

    @patch("src.bank_statement_separator.llm.openai_provider.ChatOpenAI")
    def test_extract_metadata_success(self, mock_chat):
        """Test successful metadata extraction."""
        # Setup mock
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = """{
            "bank_name": "Test Bank",
            "account_number": "123456789",
            "account_type": "Checking",
            "statement_period": "Jan 2023",
            "start_date": "2023-01-01",
            "end_date": "2023-01-31",
            "confidence": 0.95
        }"""
        mock_llm.invoke.return_value = mock_response
        mock_chat.return_value = mock_llm

        provider = OpenAIProvider(api_key="test-key")
        result = provider.extract_metadata("Test statement text", 1, 3)

        assert isinstance(result, MetadataResult)
        assert result.metadata["bank_name"] == "Test Bank"
        assert result.metadata["account_number"] == "123456789"
        assert result.confidence == 0.95
        assert result.provider == "openai"

    @patch("src.bank_statement_separator.llm.openai_provider.ChatOpenAI")
    def test_rate_limit_error(self, mock_chat):
        """Test handling of rate limit errors."""
        from openai import RateLimitError

        mock_llm = Mock()
        mock_llm.invoke.side_effect = RateLimitError(
            message="Rate limit exceeded", response=Mock(status_code=429), body={}
        )
        mock_chat.return_value = mock_llm

        provider = OpenAIProvider(api_key="test-key")

        with pytest.raises(LLMProviderError, match="rate limit"):
            provider.analyze_boundaries("Test text")

    def test_get_info(self):
        """Test provider info method."""
        provider = OpenAIProvider(api_key="test-key")
        info = provider.get_info()

        assert info["name"] == "openai"
        assert info["available"] is True
        assert info["type"] == "OpenAIProvider"


@pytest.mark.unit
class TestLLMProviderFactory:
    """Test LLM provider factory."""

    def test_create_openai_provider(self):
        """Test creating OpenAI provider through factory."""
        config = {"api_key": "test-key", "model": "gpt-4"}
        provider = LLMProviderFactory.create_provider("openai", config)

        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"

    def test_create_unknown_provider(self):
        """Test creating unknown provider type."""
        with pytest.raises(LLMProviderError, match="Unknown provider type"):
            LLMProviderFactory.create_provider("unknown", {})

    def test_register_provider(self):
        """Test registering a new provider type."""

        # Create mock provider class
        class MockProvider(LLMProvider):
            def is_available(self):
                return True

            def analyze_boundaries(self, text, **kwargs):
                return BoundaryResult([], 1.0)

            def extract_metadata(self, text, start, end, **kwargs):
                return MetadataResult({}, 1.0)

        # Register it
        LLMProviderFactory.register_provider("mock", MockProvider)

        # Should be able to create it
        provider = LLMProviderFactory.create_provider("mock", {"name": "test"})
        assert isinstance(provider, MockProvider)

    def test_create_from_config(self):
        """Test creating provider from app config."""
        # Mock config object
        mock_config = Mock()
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "config-key"
        mock_config.openai_model = "gpt-3.5-turbo"
        mock_config.llm_temperature = 0.2

        provider = LLMProviderFactory.create_from_config(mock_config)

        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "config-key"
        assert provider.model == "gpt-3.5-turbo"
        assert provider.temperature == 0.2

    def test_create_from_config_defaults(self):
        """Test creating provider with default config."""
        # Mock config with minimal settings
        mock_config = Mock()
        mock_config.llm_provider = "openai"
        mock_config.openai_api_key = "key"

        # Should use defaults for missing attributes
        delattr(mock_config, "openai_model")
        delattr(mock_config, "llm_temperature")

        provider = LLMProviderFactory.create_from_config(mock_config)

        assert provider.model == "gpt-4o-mini"  # default
        assert provider.temperature == 0.1  # default

    @patch(
        "src.bank_statement_separator.llm.factory.LLMProviderFactory.create_provider"
    )
    def test_get_available_providers(self, mock_create):
        """Test getting availability status of providers."""
        # Mock provider instances
        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_create.return_value = mock_provider

        status = LLMProviderFactory.get_available_providers()

        assert "openai" in status
        assert status["openai"] is True


@pytest.mark.unit
class TestProviderIntegration:
    """Test provider integration scenarios."""

    @patch("src.bank_statement_separator.llm.openai_provider.ChatOpenAI")
    def test_full_workflow(self, mock_chat):
        """Test complete workflow with provider."""
        # Setup mock
        mock_llm = Mock()

        # Mock boundary response
        boundary_response = Mock()
        boundary_response.content = (
            '{"total_statements": 1, "boundaries": [{"start": 1, "end": 5}]}'
        )

        # Mock metadata response
        metadata_response = Mock()
        metadata_response.content = (
            '{"bank_name": "Test Bank", "account_number": "12345", "confidence": 0.9}'
        )

        mock_llm.invoke.side_effect = [boundary_response, metadata_response]
        mock_chat.return_value = mock_llm

        # Create provider
        provider = LLMProviderFactory.create_provider("openai", {"api_key": "test"})

        # Analyze boundaries
        boundaries = provider.analyze_boundaries("Document text")
        assert len(boundaries.boundaries) == 1

        # Extract metadata
        metadata = provider.extract_metadata("Statement text", 1, 5)
        assert metadata.metadata["bank_name"] == "Test Bank"


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiter functionality."""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initialization."""
        config = RateLimitConfig(requests_per_minute=10, burst_limit=5)
        limiter = RateLimiter(config)

        assert limiter.config.requests_per_minute == 10
        assert limiter.config.burst_limit == 5

    def test_rate_limiter_acquire_within_limit(self):
        """Test acquiring requests within rate limit."""
        config = RateLimitConfig(requests_per_minute=10)
        limiter = RateLimiter(config)

        # Should allow requests within limit
        for _ in range(5):
            assert limiter.acquire() is True

    def test_rate_limiter_burst_limit(self):
        """Test burst limit functionality."""
        config = RateLimitConfig(requests_per_minute=10, burst_limit=3)
        limiter = RateLimiter(config)

        # Should allow burst requests
        for _ in range(3):
            assert limiter.acquire() is True

        # Should deny after burst limit
        assert limiter.acquire() is False

    def test_rate_limiter_stats(self):
        """Test rate limiter statistics."""
        config = RateLimitConfig(requests_per_minute=10)
        limiter = RateLimiter(config)

        # Make some requests
        for _ in range(3):
            limiter.acquire()

        stats = limiter.get_stats()
        assert stats["requests_last_minute"] == 3
        assert stats["limit_per_minute"] == 10
        assert stats["burst_tokens_remaining"] <= 10


@pytest.mark.unit
class TestBackoffStrategy:
    """Test backoff strategy functionality."""

    def test_calculate_backoff_delay(self):
        """Test backoff delay calculation."""
        # Test multiple times to account for jitter
        delays = [BackoffStrategy.calculate_backoff_delay(attempt=0) for _ in range(10)]
        assert all(0.1 <= d <= 2.0 for d in delays)  # Base delay with jitter

        delays = [BackoffStrategy.calculate_backoff_delay(attempt=2) for _ in range(10)]
        # For attempt=2, base delay is 4.0, with jitter it can be 0.4 to 8.0
        assert all(0.4 <= d <= 8.0 for d in delays)

    def test_execute_with_backoff_success(self):
        """Test successful execution with backoff."""

        def mock_func():
            return "success"

        result = BackoffStrategy.execute_with_backoff(
            mock_func, max_attempts=3, base_delay=0.1
        )
        assert result == "success"

    def test_execute_with_backoff_rate_limit(self):
        """Test backoff with rate limit errors."""
        from openai import RateLimitError

        call_count = 0

        def mock_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RateLimitError(
                    "Rate limit", response=Mock(status_code=429), body={}
                )
            return "success"

        start_time = time.time()
        result = BackoffStrategy.execute_with_backoff(
            mock_func, max_attempts=5, base_delay=0.5
        )
        end_time = time.time()

        assert result == "success"
        assert call_count == 3
        # Should have taken some time due to backoff (accounting for jitter)
        assert end_time - start_time >= 0.1  # Minimum expected with jitter


@pytest.mark.unit
class TestOpenAIProviderWithRateLimiting:
    """Test OpenAI provider with rate limiting enabled."""

    def test_provider_initialization_with_rate_limiting(self):
        """Test provider initialization with rate limiting."""
        config = RateLimitConfig(requests_per_minute=25)
        provider = OpenAIProvider(api_key="test-key", rate_limit_config=config)

        assert provider.rate_limiter is not None
        assert provider.rate_limit_config.requests_per_minute == 25

    def test_provider_rate_limit_config_loading(self):
        """Test loading rate limit config from environment."""
        with patch.dict(
            "os.environ",
            {"OPENAI_REQUESTS_PER_MINUTE": "30", "OPENAI_BURST_LIMIT": "5"},
        ):
            config = load_rate_limit_config_from_env()
            assert config.requests_per_minute == 30
            assert config.burst_limit == 5

    @patch("src.bank_statement_separator.llm.openai_provider.ChatOpenAI")
    def test_provider_rate_limiting_integration(self, mock_chat):
        """Test full integration with rate limiting."""
        # Setup mock
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = (
            '{"total_statements": 1, "boundaries": [{"start": 1, "end": 3}]}'
        )
        mock_llm.invoke.return_value = mock_response
        mock_chat.return_value = mock_llm

        # Create provider with rate limiting
        config = RateLimitConfig(requests_per_minute=100)  # High limit for test
        provider = OpenAIProvider(api_key="test-key", rate_limit_config=config)

        # Test boundary analysis
        result = provider.analyze_boundaries("Test text", total_pages=3)

        assert isinstance(result, BoundaryResult)
        assert len(result.boundaries) == 1
        # Verify rate limiter was used
        assert provider.rate_limiter is not None

    def test_provider_rate_limit_exceeded(self):
        """Test provider behavior when rate limit is exceeded."""
        # Create provider with very low limit
        config = RateLimitConfig(requests_per_minute=1, burst_limit=0)
        provider = OpenAIProvider(api_key="test-key", rate_limit_config=config)

        # Exhaust the rate limit
        provider.rate_limiter.acquire()  # Use the burst token
        provider.rate_limiter.acquire()  # This should fail

        # Try to make a request - should fail with rate limit error
        with pytest.raises(LLMProviderError, match="rate limit exceeded"):
            provider.analyze_boundaries("Test text")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

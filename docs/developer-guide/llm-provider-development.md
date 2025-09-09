# LLM Provider Development Guide

This guide explains how to develop new LLM providers for the bank statement separator system.

## Overview

The LLM provider architecture enables support for multiple AI providers through a unified interface. This guide covers creating new providers, testing, and integration.

## Provider Architecture

### Base Provider Interface

All providers must implement the `LLMProvider` abstract base class:

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class BoundaryResult:
    boundaries: List[Dict[str, Any]]
    confidence: float
    analysis_notes: Optional[str] = None

@dataclass
class MetadataResult:
    metadata: Dict[str, Any]
    confidence: float

class LLMProvider(ABC):
    @abstractmethod
    def analyze_boundaries(self, text: str, **kwargs) -> BoundaryResult:
        """Analyze document text to detect statement boundaries."""
        pass

    @abstractmethod
    def extract_metadata(self, text: str, start_page: int, end_page: int, **kwargs) -> MetadataResult:
        """Extract metadata from a statement section."""
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get provider information and status."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        pass
```

## Creating a New Provider

### Step 1: Provider Implementation

Create a new file in `src/bank_statement_separator/llm/`:

```python
# src/bank_statement_separator/llm/my_provider.py
import logging
from typing import Dict, Any, List, Optional
from .base import LLMProvider, BoundaryResult, MetadataResult, LLMProviderError

logger = logging.getLogger(__name__)

class MyProvider(LLMProvider):
    """Custom LLM provider implementation."""

    def __init__(self, api_key: Optional[str] = None, model: str = "default-model", **kwargs):
        """Initialize provider with configuration."""
        self.api_key = api_key
        self.model = model
        self.base_url = kwargs.get('base_url', 'https://api.myprovider.com')
        self.temperature = kwargs.get('temperature', 0.1)
        self.max_tokens = kwargs.get('max_tokens', 4000)

        # Initialize provider client
        try:
            self.client = self._create_client()
        except Exception as e:
            raise LLMProviderError(f"Failed to initialize MyProvider: {e}")

    def _create_client(self):
        """Create and configure the provider client."""
        # Implementation specific to your provider
        # e.g., return MyProviderClient(api_key=self.api_key, base_url=self.base_url)
        pass

    def analyze_boundaries(self, text: str, **kwargs) -> BoundaryResult:
        """Analyze document text to detect statement boundaries."""
        try:
            # Prepare the prompt for boundary analysis
            prompt = self._create_boundary_prompt(text, **kwargs)

            # Call your provider's API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Parse response
            return self._parse_boundary_response(response)

        except Exception as e:
            logger.error(f"MyProvider boundary analysis failed: {e}")
            raise LLMProviderError(f"Boundary analysis failed: {e}")

    def extract_metadata(self, text: str, start_page: int, end_page: int, **kwargs) -> MetadataResult:
        """Extract metadata from a statement section."""
        try:
            # Prepare the prompt for metadata extraction
            prompt = self._create_metadata_prompt(text, start_page, end_page, **kwargs)

            # Call your provider's API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            # Parse response
            return self._parse_metadata_response(response)

        except Exception as e:
            logger.error(f"MyProvider metadata extraction failed: {e}")
            raise LLMProviderError(f"Metadata extraction failed: {e}")

    def get_info(self) -> Dict[str, Any]:
        """Get provider information and status."""
        return {
            "name": "myprovider",
            "type": "MyProvider",
            "model": self.model,
            "base_url": self.base_url,
            "available": self.is_available(),
            "features": ["boundary_analysis", "metadata_extraction"],
            "version": "1.0.0"
        }

    def is_available(self) -> bool:
        """Check if provider is available and configured."""
        try:
            # Test basic connectivity/configuration
            return bool(self.api_key and self.client)
        except:
            return False

    def _create_boundary_prompt(self, text: str, **kwargs) -> str:
        """Create prompt for boundary analysis."""
        total_pages = kwargs.get('total_pages', len(text.split('\\n---\\n')))

        return f"""
        Analyze this bank statement document and identify individual statement boundaries.

        Document text ({total_pages} pages):
        {text}

        Return JSON with:
        - total_statements: number of statements found
        - boundaries: array of {{"start_page": X, "end_page": Y, "account_number": "..."}}

        Look for:
        - Statement periods and dates
        - Account numbers and bank names
        - Page breaks and new statement headers
        """

    def _create_metadata_prompt(self, text: str, start_page: int, end_page: int, **kwargs) -> str:
        """Create prompt for metadata extraction."""
        return f"""
        Extract metadata from this bank statement (pages {start_page}-{end_page}):

        {text}

        Return JSON with:
        - bank_name: string
        - account_number: string
        - account_type: string
        - statement_period: string
        - customer_name: string (if available)
        - confidence: float (0.0-1.0)
        """

    def _parse_boundary_response(self, response) -> BoundaryResult:
        """Parse boundary analysis response."""
        try:
            import json
            content = response.choices[0].message.content
            data = json.loads(content)

            return BoundaryResult(
                boundaries=data.get('boundaries', []),
                confidence=data.get('confidence', 0.8),
                analysis_notes=f"MyProvider detected {len(data.get('boundaries', []))} boundaries"
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to parse boundary response: {e}")

    def _parse_metadata_response(self, response) -> MetadataResult:
        """Parse metadata extraction response."""
        try:
            import json
            content = response.choices[0].message.content
            data = json.loads(content)

            return MetadataResult(
                metadata={
                    "bank_name": data.get('bank_name', 'Unknown'),
                    "account_number": data.get('account_number', ''),
                    "account_type": data.get('account_type', ''),
                    "statement_period": data.get('statement_period', ''),
                    "customer_name": data.get('customer_name', '')
                },
                confidence=data.get('confidence', 0.7)
            )
        except Exception as e:
            raise LLMProviderError(f"Failed to parse metadata response: {e}")
```

### Step 2: Factory Registration

Register your provider in the factory:

```python
# src/bank_statement_separator/llm/factory.py
from .my_provider import MyProvider

class LLMProviderFactory:
    _PROVIDERS = {
        "openai": OpenAIProvider,
        "myprovider": MyProvider,  # Add your provider
        # ... other providers
    }

    @classmethod
    def create_from_config(cls, app_config: Any) -> LLMProvider:
        """Create provider instance from configuration."""
        provider_type = getattr(app_config, "llm_provider", "openai").lower()

        if provider_type == "myprovider":
            return cls._create_my_provider(app_config)
        # ... existing provider creation logic

    @classmethod
    def _create_my_provider(cls, config: Any) -> MyProvider:
        """Create MyProvider instance."""
        return MyProvider(
            api_key=getattr(config, "myprovider_api_key", None),
            model=getattr(config, "myprovider_model", "default-model"),
            base_url=getattr(config, "myprovider_base_url", "https://api.myprovider.com"),
            temperature=getattr(config, "llm_temperature", 0.1),
            max_tokens=getattr(config, "llm_max_tokens", 4000)
        )
```

### Step 3: Configuration Support

Add configuration fields for your provider:

```python
# src/bank_statement_separator/config.py
class ProcessingConfig(BaseModel):
    # ... existing fields

    # MyProvider Configuration
    myprovider_api_key: Optional[str] = Field(
        default=None, description="MyProvider API key"
    )
    myprovider_model: str = Field(
        default="default-model", description="MyProvider model name"
    )
    myprovider_base_url: str = Field(
        default="https://api.myprovider.com", description="MyProvider API base URL"
    )
```

### Step 4: Environment Variables

Update `.env.example`:

```bash
# MyProvider Configuration
MYPROVIDER_API_KEY=your-api-key-here
MYPROVIDER_MODEL=default-model
MYPROVIDER_BASE_URL=https://api.myprovider.com
```

## Testing Your Provider

### Unit Tests

Create comprehensive tests for your provider:

```python
# tests/unit/test_my_provider.py
import pytest
from unittest.mock import Mock, patch
from src.bank_statement_separator.llm import MyProvider, LLMProviderError
from src.bank_statement_separator.llm.base import BoundaryResult, MetadataResult

@pytest.fixture
def provider():
    return MyProvider(api_key="test-key", model="test-model")

class TestMyProvider:
    def test_initialization_success(self):
        provider = MyProvider(api_key="test-key", model="test-model")
        assert provider.api_key == "test-key"
        assert provider.model == "test-model"

    def test_initialization_failure(self):
        with patch.object(MyProvider, '_create_client') as mock_create:
            mock_create.side_effect = Exception("Connection failed")

            with pytest.raises(LLMProviderError):
                MyProvider(api_key="test-key")

    @patch('src.bank_statement_separator.llm.my_provider.MyProviderClient')
    def test_analyze_boundaries_success(self, mock_client_class, provider):
        # Mock response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices[0].message.content = '''
        {
            "total_statements": 2,
            "boundaries": [
                {"start_page": 1, "end_page": 3, "account_number": "123456"},
                {"start_page": 4, "end_page": 6, "account_number": "789012"}
            ]
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        provider.client = mock_client

        # Test boundary analysis
        result = provider.analyze_boundaries("Test document text", total_pages=6)

        # Assertions
        assert isinstance(result, BoundaryResult)
        assert len(result.boundaries) == 2
        assert result.boundaries[0]["start_page"] == 1
        assert result.boundaries[0]["end_page"] == 3

    def test_analyze_boundaries_failure(self, provider):
        provider.client = Mock()
        provider.client.chat.completions.create.side_effect = Exception("API Error")

        with pytest.raises(LLMProviderError):
            provider.analyze_boundaries("Test text")

    @patch('src.bank_statement_separator.llm.my_provider.MyProviderClient')
    def test_extract_metadata_success(self, mock_client_class, provider):
        # Mock response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices[0].message.content = '''
        {
            "bank_name": "Test Bank",
            "account_number": "123456789",
            "account_type": "Checking",
            "statement_period": "Jan 2023",
            "confidence": 0.9
        }
        '''
        mock_client.chat.completions.create.return_value = mock_response
        provider.client = mock_client

        # Test metadata extraction
        result = provider.extract_metadata("Statement text", 1, 3)

        # Assertions
        assert isinstance(result, MetadataResult)
        assert result.metadata["bank_name"] == "Test Bank"
        assert result.metadata["account_number"] == "123456789"
        assert result.confidence == 0.9

    def test_get_info(self, provider):
        info = provider.get_info()

        assert info["name"] == "myprovider"
        assert info["type"] == "MyProvider"
        assert info["model"] == "test-model"
        assert "available" in info
        assert "features" in info

    def test_is_available_true(self, provider):
        provider.client = Mock()
        assert provider.is_available() is True

    def test_is_available_false(self):
        provider = MyProvider(api_key=None)
        assert provider.is_available() is False
```

### Integration Tests

Test your provider with the analyzer:

```python
# tests/unit/test_my_provider_integration.py
import pytest
from unittest.mock import Mock
from src.bank_statement_separator.nodes.llm_analyzer_new import LLMAnalyzerNew
from src.bank_statement_separator.llm import MyProvider

@pytest.fixture
def mock_config():
    config = Mock()
    config.llm_provider = "myprovider"
    config.myprovider_api_key = "test-key"
    config.myprovider_model = "test-model"
    return config

class TestMyProviderIntegration:
    def test_analyzer_with_my_provider(self, mock_config):
        with patch('src.bank_statement_separator.llm.factory.MyProvider') as mock_provider_class:
            mock_provider = Mock(spec=MyProvider)
            mock_provider_class.return_value = mock_provider

            analyzer = LLMAnalyzerNew(mock_config)

            assert analyzer.provider is not None
            assert isinstance(analyzer.provider, Mock)  # Mock of MyProvider
```

## Integration with Existing System

### Configuration Loading

Your provider will be automatically available once registered in the factory. Users can select it via:

```bash
LLM_PROVIDER=myprovider
```

### Error Handling

Implement robust error handling:

```python
def analyze_boundaries(self, text: str, **kwargs) -> BoundaryResult:
    try:
        # Provider implementation
        pass
    except ProviderAPIError as e:
        logger.error(f"MyProvider API error: {e}")
        raise LLMProviderError(f"API request failed: {e}")
    except json.JSONDecodeError as e:
        logger.error(f"MyProvider response parsing failed: {e}")
        raise LLMProviderError(f"Invalid response format: {e}")
    except Exception as e:
        logger.error(f"MyProvider unexpected error: {e}")
        raise LLMProviderError(f"Unexpected error: {e}")
```

### Logging

Use consistent logging patterns:

```python
import logging

logger = logging.getLogger(__name__)

class MyProvider(LLMProvider):
    def analyze_boundaries(self, text: str, **kwargs) -> BoundaryResult:
        logger.debug(f"MyProvider analyzing {len(text)} characters")

        try:
            result = self._perform_analysis(text, **kwargs)
            logger.info(f"MyProvider found {len(result.boundaries)} boundaries")
            return result
        except Exception as e:
            logger.error(f"MyProvider boundary analysis failed: {e}")
            raise
```

## Provider-Specific Considerations

### OpenAI-Compatible Providers

For OpenAI-compatible APIs:

```python
from langchain_openai import ChatOpenAI

class OpenAICompatibleProvider(LLMProvider):
    def __init__(self, api_key: str, base_url: str, model: str):
        self.llm = ChatOpenAI(
            api_key=api_key,
            base_url=base_url,  # Custom endpoint
            model=model,
            temperature=0.1
        )
```

### Local Model Providers

For local models (like Ollama):

```python
from langchain_community.llms import Ollama

class LocalProvider(LLMProvider):
    def __init__(self, base_url: str, model: str):
        self.llm = Ollama(
            base_url=base_url,
            model=model
        )

    def is_available(self) -> bool:
        try:
            # Test model availability
            self.llm.invoke("test")
            return True
        except:
            return False
```

## Best Practices

### Performance

1. **Connection Pooling**: Reuse connections where possible
2. **Timeout Handling**: Implement appropriate timeouts
3. **Rate Limiting**: Respect provider rate limits
4. **Caching**: Cache responses for repeated queries

```python
class MyProvider(LLMProvider):
    def __init__(self, **kwargs):
        self.session = requests.Session()  # Connection pooling
        self.session.timeout = 30  # Timeout
        self.rate_limiter = RateLimiter()  # Custom rate limiting
        self._cache = {}  # Simple caching
```

### Security

1. **API Key Handling**: Never log API keys
2. **Input Validation**: Validate all inputs
3. **Output Sanitization**: Clean responses
4. **SSL Verification**: Always verify SSL certificates

```python
def _make_request(self, data):
    # Never log API keys
    logger.debug("Making request to provider (API key redacted)")

    # Validate inputs
    if not isinstance(data, dict):
        raise ValueError("Invalid request data")

    # SSL verification
    response = self.session.post(
        self.base_url,
        json=data,
        verify=True  # SSL verification
    )

    return response
```

### Error Recovery

1. **Retry Logic**: Implement exponential backoff
2. **Circuit Breaker**: Prevent cascade failures
3. **Graceful Degradation**: Fall back to alternatives

```python
from tenacity import retry, stop_after_attempt, wait_exponential

class MyProvider(LLMProvider):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def _make_api_call(self, data):
        return self.client.request(data)
```

## Documentation and Examples

### Provider Documentation

Document your provider's capabilities:

```python
class MyProvider(LLMProvider):
    """
    MyProvider LLM integration for bank statement analysis.

    Features:
    - High accuracy boundary detection
    - Comprehensive metadata extraction
    - Multi-language support

    Configuration:
    - MYPROVIDER_API_KEY: Required API key
    - MYPROVIDER_MODEL: Model name (default: default-model)
    - MYPROVIDER_BASE_URL: API endpoint

    Example:
        provider = MyProvider(
            api_key="your-key",
            model="advanced-model"
        )

        boundaries = provider.analyze_boundaries(document_text)
        metadata = provider.extract_metadata(statement_text, 1, 5)
    """
```

### Usage Examples

Provide clear usage examples in documentation:

````markdown
## MyProvider Usage

### Configuration

```bash
LLM_PROVIDER=myprovider
MYPROVIDER_API_KEY=your-api-key
MYPROVIDER_MODEL=advanced-model
```
````

### Features

- Accuracy: ~92% boundary detection
- Speed: ~2s per document
- Languages: English, Spanish, French
- Models: basic-model, advanced-model, premium-model

````

## Testing and Validation

### Continuous Integration

Add your provider to CI tests:

```yaml
# .github/workflows/test.yml
- name: Test MyProvider
  env:
    MYPROVIDER_API_KEY: ${{ secrets.MYPROVIDER_TEST_KEY }}
  run: uv run pytest tests/unit/test_my_provider.py -v
````

### Performance Testing

Include performance benchmarks:

```python
def test_my_provider_performance(benchmark):
    provider = MyProvider(api_key="test-key")

    def analyze_document():
        return provider.analyze_boundaries(SAMPLE_DOCUMENT)

    result = benchmark(analyze_document)
    assert len(result.boundaries) > 0
```

This guide provides a comprehensive foundation for developing new LLM providers. Follow the patterns established by existing providers and maintain consistency with the overall system architecture.

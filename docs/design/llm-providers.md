# LLM Provider Architecture

This document describes the LLM provider abstraction layer that enables support for multiple Language Learning Model providers in the bank statement separator.

## Overview

The LLM provider architecture allows the system to work with different AI providers (OpenAI, Ollama, etc.) through a unified interface. This provides flexibility in deployment scenarios, cost optimization, and privacy requirements.

## Architecture Components

### Provider Abstraction

The system uses an abstract base class `LLMProvider` that defines the contract for all AI providers:

```python
class LLMProvider(ABC):
    @abstractmethod
    def analyze_boundaries(self, text: str, **kwargs) -> BoundaryResult:
        """Analyze document text to detect statement boundaries."""
        
    @abstractmethod
    def extract_metadata(self, text: str, start_page: int, end_page: int, **kwargs) -> MetadataResult:
        """Extract metadata from a statement section."""
        
    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Get provider information and status."""
        
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured."""
```

### Factory Pattern

The `LLMProviderFactory` handles provider instantiation and configuration:

```python
class LLMProviderFactory:
    @classmethod
    def create_from_config(cls, app_config: Any) -> LLMProvider:
        """Create provider instance from application configuration."""
        
    @classmethod
    def get_available_providers(cls) -> List[str]:
        """Get list of available provider types."""
```

### Data Structures

**BoundaryResult**: Structured response for boundary detection
```python
@dataclass
class BoundaryResult:
    boundaries: List[Dict[str, Any]]
    confidence: float
    analysis_notes: Optional[str] = None
```

**MetadataResult**: Structured response for metadata extraction
```python
@dataclass
class MetadataResult:
    metadata: Dict[str, Any]
    confidence: float
```

## Current Providers

### OpenAI Provider

- **Implementation**: `OpenAIProvider`
- **Models**: GPT-4o, GPT-4o-mini, GPT-3.5-turbo
- **Features**: High accuracy, robust error handling, rate limiting
- **Configuration**: Requires `OPENAI_API_KEY`

### Future Providers

The architecture is designed to support additional providers:

- **Ollama**: Local LLM processing for privacy and cost savings
- **Anthropic**: Claude models for alternative AI capabilities
- **Azure OpenAI**: Enterprise-grade OpenAI hosting

## Configuration

Provider selection is controlled via environment variables:

```bash
# Provider Selection
LLM_PROVIDER=openai          # openai, ollama, auto
LLM_FALLBACK_ENABLED=true    # Enable fallback to pattern matching

# OpenAI Configuration
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

# Ollama Configuration (future)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# General LLM Settings
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=4000
```

## Integration Points

### Analyzer Integration

The `LLMAnalyzerNew` class integrates with providers:

```python
class LLMAnalyzerNew:
    def __init__(self, config: Any, provider: Optional[LLMProvider] = None):
        if provider:
            self.provider = provider
        else:
            try:
                self.provider = LLMProviderFactory.create_from_config(config)
            except LLMProviderError:
                self.provider = None  # Use fallback methods
```

### Workflow Integration

The main workflow uses the analyzer with provider abstraction:

```python
# Provider is created automatically from configuration
analyzer = LLMAnalyzerNew(config)

# Boundary detection with provider fallback
boundaries = analyzer.detect_statement_boundaries(text_chunks, total_pages)

# Metadata extraction with provider fallback
metadata = analyzer.extract_metadata(statement_text, start_page, end_page)
```

## Error Handling

The system implements graceful error handling:

1. **Provider Creation Errors**: Fall back to pattern matching
2. **API Errors**: Retry with exponential backoff
3. **Response Parsing Errors**: Use fallback methods
4. **Network Errors**: Automatic fallback to offline processing

## Benefits

### Cost Optimization
- Use local models (Ollama) for development
- Switch to cloud models (OpenAI) for production
- Reduce API costs through intelligent provider selection

### Privacy & Security
- Local processing keeps documents private
- No data sent to external services when using Ollama
- Configurable for different security requirements

### Reliability
- Automatic fallback to pattern matching
- Multiple provider options reduce single points of failure
- Graceful degradation maintains functionality

### Flexibility
- Easy to add new providers
- Runtime provider switching
- Environment-specific configurations

## Testing

The provider architecture includes comprehensive test coverage:

- **Unit Tests**: Provider-specific functionality
- **Integration Tests**: End-to-end workflow testing
- **Mock Tests**: API interaction testing
- **Error Scenarios**: Failure handling verification

## Performance Considerations

### Provider Selection Strategy
- **Auto Mode**: Automatically selects best available provider
- **Explicit Mode**: Use specific provider for predictable behavior
- **Fallback Chain**: OpenAI → Ollama → Pattern Matching

### Caching
- Response caching for repeated document processing
- Provider availability caching to avoid repeated checks
- Configuration caching for performance

### Resource Management
- Connection pooling for API providers
- Memory management for local models
- Request rate limiting and throttling

## Future Enhancements

### Multi-Provider Processing
- Consensus-based analysis using multiple providers
- Quality scoring and provider ranking
- Load balancing across providers

### Advanced Fallback Logic
- Provider health monitoring
- Automatic provider switching based on performance
- Custom fallback chains per document type

### Provider Plugins
- Dynamic provider loading
- Third-party provider support
- Custom provider development framework
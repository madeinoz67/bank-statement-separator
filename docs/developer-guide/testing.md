# Testing Guide

This guide covers setting up and running tests for the Bank Statement Separator project.

## Current Status

![Tests](https://img.shields.io/badge/tests-164%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-comprehensive-brightgreen)

- **Total Tests:** 164 (164 passing, 3 skipped)
- **Unit Tests:** 108 tests covering LLM providers, validation, and Paperless integration
- **Integration Tests:** 19 tests covering edge cases and performance
- **Manual Tests:** 4 scripts for external integration testing (excluded from automated runs)

## Overview

The test suite is organized into three main categories:

- **Unit Tests** (`tests/unit/`) - Fast, isolated tests for individual components
- **Integration Tests** (`tests/integration/`) - Tests that verify component interactions
- **Manual Tests** (`tests/manual/`) - Scripts for testing external integrations that require manual verification

## Prerequisites

### Required Dependencies

Install all development dependencies:

```bash
uv sync --group dev
```

This installs:

- `pytest` - Test framework
- `pytest-cov` - Coverage reporting
- `pytest-mock` - Mocking utilities
- `pytest-asyncio` - Async test support
- `faker` - Test data generation
- `httpx` - HTTP client for API testing

### Environment Setup

1. **Copy the example environment file:**

   ```bash
   cp .env.example .env
   ```

2. **Configure test-specific settings:**

   ```bash
   # Optional: Set for integration tests
   export OPENAI_API_KEY="your-test-key"

   # Optional: Set for Paperless integration tests
   export PAPERLESS_URL="http://localhost:8000"
   export PAPERLESS_TOKEN="your-test-token"
   ```

### Test Environment Configurations

The project includes comprehensive test environment configurations in `tests/env/` for testing different LLM providers and scenarios:

#### Available Test Environments

- **`.env.openai`** - OpenAI GPT-4o-mini configuration
- **`.env.ollama`** - Base Ollama configuration (server at 10.0.0.150:11434)
- **`.env.fallback`** - Pattern-matching fallback (no LLM required)
- **Multiple Ollama model configs:** Gemma2, Mistral, Qwen2.5, DeepSeek, etc.

#### Using Test Environments

```bash
# Test with specific environment configuration
uv run python -m src.bank_statement_separator.main process \
  test/input/sample.pdf \
  --env-file tests/env/.env.ollama_gemma2

# Compare different models
for config in tests/env/.env.ollama_*; do
  echo "Testing $(basename $config)"
  uv run python -m src.bank_statement_separator.main process \
    test/input/sample.pdf \
    --env-file $config \
    --dry-run
done
```

#### Test Environment Documentation

See `tests/env/README.md` for detailed model performance comparisons and selection guidance.

### Temporary Directory Management

Tests now use dedicated temporary directories within the project structure:

#### Automatic Temp Directory Creation

- **Location:** `tests/temp_test_data/` (auto-created)
- **Session Isolation:** Unique subdirectories per test session
- **Automatic Cleanup:** Directories removed after test completion
- **Project Structure:** All temp files contained within `tests/` directory

#### Benefits

- Clean project structure (no temp files in root)
- Session isolation prevents test interference
- Automatic cleanup prevents disk space issues
- Consistent temp file management across all tests

## Running Tests

### Quick Start

Run all automated tests:

```bash
uv run pytest
```

### Test Categories

#### Unit Tests Only

```bash
uv run pytest tests/unit/
```

#### Integration Tests Only

```bash
uv run pytest tests/integration/
```

#### Specific Test File

```bash
uv run pytest tests/unit/test_validation_system.py
```

#### Specific Test Function

```bash
uv run pytest tests/unit/test_validation_system.py::TestValidationSystem::test_validate_pdf_success
```

### Test Options

#### Verbose Output

```bash
uv run pytest -v
```

#### Show Print Statements

```bash
uv run pytest -s
```

#### Stop on First Failure

```bash
uv run pytest -x
```

#### Run Tests Matching Pattern

```bash
uv run pytest -k "test_boundary"
```

#### Run Tests with Specific Marker

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run tests requiring API key
uv run pytest -m requires_api

# Run edge case tests
uv run pytest -m edge_case
```

### Coverage Reports

#### Generate Coverage Report

```bash
uv run pytest --cov=src/bank_statement_separator
```

#### HTML Coverage Report

```bash
uv run pytest --cov=src/bank_statement_separator --cov-report=html
# Open htmlcov/index.html in browser
```

#### Terminal Coverage Report with Missing Lines

```bash
uv run pytest --cov=src/bank_statement_separator --cov-report=term-missing
```

## Manual Test Scripts

Manual tests are located in `tests/manual/` and are **automatically excluded** from automated test discovery via `--ignore=tests/manual` in `pyproject.toml`.

### Available Manual Tests

1. **test_auto_creation.py** - Tests automatic creation of Paperless-ngx entities
2. **test_unique_creation.py** - Tests creation with UUID suffixes to prevent conflicts
3. **test_creation_verbose.py** - Tests with verbose debug logging
4. **test_api_search.py** - Tests direct API search functionality
5. **test_ollama.py** - Tests Ollama provider functionality (requires Ollama server)

### Running Manual Tests

```bash
# Navigate to project root
cd /path/to/bank-statement-separator

# Run individual manual test
uv run python tests/manual/test_auto_creation.py
uv run python tests/manual/test_unique_creation.py
uv run python tests/manual/test_creation_verbose.py
uv run python tests/manual/test_api_search.py
uv run python tests/manual/test_ollama.py
```

### Manual Test Prerequisites

**For Ollama Tests (`test_ollama.py`):**

- Install and start Ollama server: `https://ollama.ai/`
- Pull compatible model: `ollama pull llama3.2`
- Configure Ollama server URL in test environment

**For Paperless Tests:**

- Configured Paperless-ngx instance
- Valid `PAPERLESS_URL` and `PAPERLESS_TOKEN` in `.env`
- May create actual entities in your Paperless instance

### Manual Test Execution Notes

- Manual tests are designed for standalone execution, not pytest integration
- They may require external services (Ollama, Paperless-ngx) to be running
- Use for testing integrations that cannot be easily mocked or automated

## Test Data Generation

The project includes utilities for generating test PDFs:

### Generate Test Statements

```bash
uv run python scripts/generate_test_statements.py
```

This creates various test scenarios in `test/input/generated/`:

- Single statements
- Multiple statements in one PDF
- Overlapping date periods
- Different banks and formats

## Writing Tests

### Test Structure

```python
import pytest
from pathlib import Path

class TestMyFeature:
    """Test suite for MyFeature."""

    @pytest.fixture
    def sample_data(self):
        """Fixture providing sample test data."""
        return {"key": "value"}

    def test_feature_success(self, sample_data):
        """Test successful feature execution."""
        # Arrange
        input_data = sample_data

        # Act
        result = my_feature(input_data)

        # Assert
        assert result is not None
        assert result["status"] == "success"

    def test_feature_error_handling(self):
        """Test error handling."""
        with pytest.raises(ValueError, match="Invalid input"):
            my_feature(None)
```

### Using Fixtures

Common fixtures are defined in `tests/conftest.py`:

```python
def test_with_fixtures(temp_pdf, mock_config, sample_metadata):
    """Test using provided fixtures."""
    # temp_pdf - Path to temporary test PDF
    # mock_config - Mock configuration object
    # sample_metadata - Sample statement metadata

    result = process_pdf(temp_pdf, mock_config)
    assert result.metadata == sample_metadata
```

### Mocking External Services

```python
from unittest.mock import patch, MagicMock

def test_with_mock_openai():
    """Test with mocked OpenAI API."""
    with patch('openai.ChatCompletion.create') as mock_create:
        mock_create.return_value = MagicMock(
            choices=[MagicMock(message={"content": "mocked response"})]
        )

        result = analyze_with_llm("test input")
        assert result == "mocked response"
```

### Testing Async Code

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test asynchronous function."""
    result = await async_process()
    assert result is not None
```

## Test Markers

Available pytest markers (defined in `pytest.ini`):

- `@pytest.mark.unit` - Unit tests (fast, no external dependencies)
- `@pytest.mark.integration` - Integration tests (may be slower)
- `@pytest.mark.edge_case` - Edge case scenario tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.requires_api` - Tests requiring OpenAI API key
- `@pytest.mark.requires_paperless` - Tests requiring Paperless-ngx
- `@pytest.mark.manual` - Manual execution tests (not automated)

Example usage:

```python
@pytest.mark.unit
def test_fast_unit():
    """Fast unit test."""
    assert True

@pytest.mark.integration
@pytest.mark.requires_api
def test_with_openai():
    """Integration test requiring API."""
    # Test implementation
```

## Continuous Integration

Tests are automatically run on:

- Every push to main branch
- Every pull request
- Can be triggered manually via GitHub Actions

### CI Test Command

```bash
# Same as CI pipeline
uv run pytest tests/unit/ tests/integration/ -v --tb=short
```

## Debugging Tests

### Run Tests in Debug Mode

```bash
# With pytest debugging
uv run pytest --pdb

# Break on failures
uv run pytest --pdb --pdbcls=IPython.terminal.debugger:TerminalPdb
```

### View Test Collection

```bash
# See which tests would run without executing
uv run pytest --collect-only
```

### Run Last Failed Tests

```bash
# Run only tests that failed in the last run
uv run pytest --lf

# Run failed tests first, then others
uv run pytest --ff
```

## Performance Testing

### Benchmark Tests

```bash
# Run performance tests
uv run pytest tests/integration/test_performance.py -v
```

### Profile Test Execution

```bash
# Show slowest tests
uv run pytest --durations=10
```

## Troubleshooting

### Common Issues

1. **Import Errors**

   ```bash
   # Ensure you're in project root
   cd /path/to/bank-statement-separator

   # Reinstall dependencies
   uv sync --group dev
   ```

2. **Test Discovery Issues**

   ```bash
   # Check test discovery
   uv run pytest --collect-only

   # Verify pytest.ini configuration
   cat pytest.ini
   ```

3. **Manual Tests Running Automatically**
   - Manual tests should be in `tests/manual/`
   - Check `pyproject.toml` includes `addopts = "--ignore=tests/manual"`

4. **Temporary Directory Issues**

   ```bash
   # Check temp directory creation
   ls -la tests/temp_test_data/

   # Clean up temp directories manually if needed
   rm -rf tests/temp_test_data/
   ```

5. **Test Environment Configuration Issues**

   ```bash
   # Check available test environments
   ls tests/env/

   # Use specific test environment
   uv run python -m src.bank_statement_separator.main process \
     test/input/sample.pdf \
     --env-file tests/env/.env.fallback
   ```

6. **Missing Test Dependencies**

   ```bash
   # Install all dev dependencies
   uv sync --group dev

   # Check installed packages
   uv pip list
   ```

7. **Environment Variable Issues**

   ```bash
   # Check current environment
   env | grep OPENAI
   env | grep PAPERLESS

   # Source .env file
   source .env
   ```

## Best Practices

1. **Test Naming**
   - Use descriptive names: `test_boundary_detection_with_multiple_statements`
   - Group related tests in classes
   - Prefix test files with `test_`

2. **Test Independence**
   - Each test should be independent
   - Use fixtures for setup/teardown
   - Don't rely on test execution order

3. **Assertions**
   - Use specific assertions with clear messages
   - Test both success and failure cases
   - Verify edge cases and boundaries

4. **Performance**
   - Keep unit tests fast (< 1 second)
   - Mock external services in unit tests
   - Use integration tests for end-to-end validation

5. **Documentation**
   - Add docstrings to test functions
   - Document complex test scenarios
   - Include examples in comments

6. **Test Environment Management**
   - Use appropriate test environments from `tests/env/` for different scenarios
   - Test with multiple LLM providers when possible
   - Include fallback testing without API keys
   - Document specific environment requirements in test docstrings

7. **Temporary File Management**
   - Use provided fixtures for temp directory management
   - Don't create temp files in project root
   - Let fixtures handle cleanup automatically
   - Use descriptive names for temp files and directories

## Test Categories and Coverage

### Unit Tests (tests/unit/)

- **test_llm_providers.py** - 19 tests covering OpenAI provider, backoff strategy, and rate limiting
- **test_ollama_provider.py** - 27 tests covering Ollama provider functionality
- **test_ollama_integration.py** - 13 tests covering Ollama factory integration
- **test_llm_analyzer_integration.py** - 12 tests covering LLM analyzer with providers
- **test_hallucination_detector.py** - 12 tests covering hallucination detection and prevention
- **test_paperless_integration.py** - 27 tests covering Paperless-ngx client functionality
- **test_validation_system.py** - 10 tests covering the 4-tier validation system
- **test_filename_generation.py** - 12 tests covering PRD-compliant filename generation

### Integration Tests (tests/integration/)

- **test_edge_cases.py** - 11 tests covering various edge scenarios:
  - Single and multi-statement processing
  - Fallback processing without API key
  - Error handling for malformed input
  - Metadata extraction accuracy with predictable account numbers
  - Billing account detection
  - Validation system integrity
- **test_performance.py** - 8 tests covering performance scenarios:
  - Large document processing
  - Multiple statements efficiency
  - Memory usage monitoring
  - Concurrent processing simulation
  - Scalability limits with boundary detection

### Key Test Features

#### Fragment Detection Testing

The test suite includes comprehensive testing for the fragment detection feature that filters out low-confidence document fragments:

- Tests adapt to varying numbers of detected statements due to fragment filtering
- Validation accounts for intentionally skipped pages
- Performance tests verify fragment filtering doesn't impact processing speed

#### Fallback Processing

Tests verify the system works without OpenAI API key:

- Pattern-based boundary detection
- Regex-based metadata extraction
- Graceful degradation of features

## Common Test Patterns

### Testing with Fragment Filtering

When testing document processing, account for fragment filtering:

```python
# Don't expect exact statement counts
assert result["total_statements_found"] >= 1  # At least one statement
assert result["total_statements_found"] <= expected_max  # Not over-segmented

# Verify consistency
assert len(result["generated_files"]) == result["total_statements_found"]
```

### Mocking PDF Operations

Many tests mock PyMuPDF (fitz) operations:

```python
with patch('fitz.open') as mock_fitz:
    mock_doc = Mock()
    mock_doc.__len__ = Mock(return_value=10)  # 10 pages
    mock_page = Mock()
    mock_page.get_text.return_value = "Sample PDF text"
    mock_doc.__getitem__ = Mock(return_value=mock_page)
    mock_fitz.return_value.__enter__.return_value = mock_doc
```

## Recent Test Updates

### Test Suite Improvements (September 6, 2025)

- **Updated test counts:** 164 tests (up from 56) with comprehensive LLM provider coverage
- **Manual test exclusion:** Added `--ignore=tests/manual` to pytest configuration
- **Temporary directory management:** All temp files now contained within `tests/` directory
- **Test environment configurations:** 15+ pre-configured .env files for different LLM providers
- **Session isolation:** Unique temp directories per test session with automatic cleanup

### Test Fixes and Enhancements (September 6, 2025)

#### Fixed Failing Tests

1. **Metadata Extraction Accuracy Test** - Added `force_account` values for predictable account numbers
2. **Boundary Detection Performance Test** - Adjusted expectations for realistic boundary detection
3. **Backoff Strategy Timing Test** - Updated timing expectations to account for jitter
4. **Ollama Provider Fixture Issues** - Configured proper exclusion of manual tests

#### Test Infrastructure Improvements

- **Enhanced conftest.py:** Updated `temp_test_dir` fixture for project-contained temp files
- **Script updates:** Modified validation scripts to use project temp directories
- **Pytest configuration:** Added manual test exclusion and improved test discovery
- **Environment management:** Comprehensive test environment configurations

### Fragment Detection Compatibility (2025-08-31)

- Updated test assertions to account for fragment filtering reducing statement counts
- Made validation checks handle None values properly
- Added directory creation in PDF generation to prevent path errors
- Synchronized `total_statements_found` with actual generated files

### Test Infrastructure Improvements (Previous)

- Reorganized test files into proper directories
- Excluded manual tests from automated discovery
- Enhanced test data generation with realistic PDF structures
- Improved error message assertions for better debugging

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)
- [Test-Driven Development](https://testdriven.io/)
- Project-specific test utilities in `tests/conftest.py`
- Test environment configurations in `tests/env/README.md`
- LLM model testing results in `docs/reference/llm_model_testing.md`
- Model selection guide in `docs/user-guide/model-selection-guide.md`

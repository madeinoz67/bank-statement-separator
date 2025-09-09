# Pytest Marks Guide

This guide explains the comprehensive pytest marks system implemented in the bank-statement-separator project. The marks system enables efficient test organization, selective test execution, and optimized CI/CD pipelines.

## Available Marks

### Core Test Categories

#### `@pytest.mark.unit`

- **Description**: Fast, isolated tests for individual components
- **Characteristics**: No external dependencies, typically run in < 1 second
- **Usage**: Applied to all unit test classes and functions
- **Example**:

```python
@pytest.mark.unit
class TestFilenameGeneration:
    """Test filename generation methods."""
```

#### `@pytest.mark.integration`

- **Description**: Tests that verify component interactions
- **Characteristics**: May involve multiple components, file I/O, or mocked external services
- **Usage**: Applied to integration test scenarios
- **Example**:

```python
@pytest.mark.integration
@pytest.mark.edge_case
class TestEdgeCaseScenarios:
    """Test edge case scenarios with full workflow."""
```

### Performance Marks

#### `@pytest.mark.slow`

- **Description**: Tests that take more than 5 seconds to execute
- **Characteristics**: Long-running tests, performance benchmarks
- **Usage**: Applied to performance and scalability tests
- **Example**:

```python
@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceScenarios:
    """Test performance with large documents."""
```

#### `@pytest.mark.performance`

- **Description**: Performance and scalability tests
- **Characteristics**: Memory usage monitoring, concurrent processing tests
- **Usage**: Applied to tests that measure performance metrics

### External Dependency Marks

#### `@pytest.mark.requires_api`

- **Description**: Tests that require OpenAI API keys
- **Characteristics**: Makes actual API calls, requires valid API credentials
- **Usage**: Applied to tests using OpenAI services
- **CI Behavior**: Only runs on main branch or with [api-test] commit message

#### `@pytest.mark.requires_ollama`

- **Description**: Tests that require Ollama to be running
- **Characteristics**: Requires local Ollama server at localhost:11434
- **Usage**: Applied to Ollama provider tests

#### `@pytest.mark.requires_paperless`

- **Description**: Tests that require Paperless-ngx to be running
- **Characteristics**: Requires Paperless-ngx instance with valid API token
- **Usage**: Applied to Paperless integration tests

### Test Type Marks

#### `@pytest.mark.edge_case`

- **Description**: Edge case scenario tests
- **Characteristics**: Tests unusual or boundary conditions
- **Usage**: Applied to tests covering edge cases

#### `@pytest.mark.smoke`

- **Description**: Critical functionality that should always work
- **Characteristics**: Core features, basic sanity checks
- **Usage**: Applied to essential tests for quick validation

#### `@pytest.mark.validation`

- **Description**: Tests for validation and error handling
- **Characteristics**: Input validation, error recovery, data integrity
- **Usage**: Applied to validation system tests

#### `@pytest.mark.mock_heavy`

- **Description**: Tests that use extensive mocking
- **Characteristics**: Heavy use of unittest.mock or pytest-mock
- **Usage**: Applied to tests with complex mocking scenarios

#### `@pytest.mark.pdf_processing`

- **Description**: Tests involving PDF file operations
- **Characteristics**: PDF creation, manipulation, or parsing
- **Usage**: Applied to PDF-related tests

#### `@pytest.mark.llm`

- **Description**: Tests involving LLM providers and operations
- **Characteristics**: LLM provider tests, prompt generation, response parsing
- **Usage**: Applied to LLM-related functionality

#### `@pytest.mark.manual`

- **Description**: Manual execution tests (excluded from automated runs)
- **Characteristics**: Requires manual verification or setup
- **Usage**: Applied to tests in tests/manual/ directory

## Running Tests with Marks

### Basic Mark Selection

```bash
# Run only unit tests
uv run pytest -m unit

# Run only integration tests
uv run pytest -m integration

# Run only slow tests
uv run pytest -m slow

# Run tests requiring API
uv run pytest -m requires_api
```

### Combining Marks

```bash
# Run unit tests that don't require external services
uv run pytest -m "unit and not requires_api and not requires_ollama"

# Run fast integration tests
uv run pytest -m "integration and not slow"

# Run all tests except those requiring external services
uv run pytest -m "not requires_api and not requires_ollama and not requires_paperless"

# Run smoke tests for quick validation
uv run pytest -m smoke
```

### Excluding Marks

```bash
# Run all tests except slow ones
uv run pytest -m "not slow"

# Run all tests except manual ones (default behavior)
uv run pytest  # manual tests are excluded by default

# Run unit tests excluding mock-heavy ones
uv run pytest -m "unit and not mock_heavy"
```

## CI/CD Pipeline Usage

### Standard CI Pipeline

The CI pipeline uses marks to optimize test execution:

1. **Unit Tests**: `pytest -m unit`

   - Runs on all commits
   - Fast feedback loop
   - No external dependencies

2. **Integration Tests (No API)**: `pytest -m "integration and not requires_api and not requires_ollama and not requires_paperless"`

   - Runs on all commits
   - Tests component integration
   - Uses mocks for external services

3. **API Tests**: `pytest -m requires_api`

   - Only runs on main branch
   - Requires OPENAI_API_KEY secret
   - Can be triggered with [api-test] in commit message

4. **Coverage Report**: `pytest -m "unit or (integration and not slow)"`
   - Excludes slow tests from coverage
   - Provides quick coverage metrics

### Release Pipeline

```bash
# Quick validation before release
uv run pytest -m "smoke and unit"

# Full test suite for release validation
uv run pytest -m "not manual"
```

## Best Practices

### 1. Mark Application Guidelines

- Apply marks at the class level when all methods share the same characteristics
- Use multiple marks when tests fit multiple categories
- Always mark tests that require external services

### 2. Mark Combinations

```python
@pytest.mark.unit
@pytest.mark.validation
@pytest.mark.smoke
class TestCriticalValidation:
    """Critical validation that should always work."""
```

### 3. Performance Optimization

- Use marks to create test suites for different scenarios:
  - **Quick feedback**: `pytest -m "unit and smoke"`
  - **Pre-commit**: `pytest -m "unit and not slow"`
  - **Full validation**: `pytest -m "not manual"`
  - **Performance testing**: `pytest -m "performance or slow"`

### 4. External Service Testing

When testing with external services:

```bash
# Test with Ollama
docker run -d -p 11434:11434 ollama/ollama
uv run pytest -m requires_ollama

# Test with Paperless
# Start Paperless-ngx container
uv run pytest -m requires_paperless

# Test with OpenAI API
export OPENAI_API_KEY="your-key"
uv run pytest -m requires_api
```

## Adding New Marks

To add a new mark:

1. **Register in pyproject.toml**:

```toml
[tool.pytest.ini_options]
markers = [
    # ... existing marks ...
    "new_mark: Description of the new mark",
]
```

2. **Apply to tests**:

```python
@pytest.mark.new_mark
def test_something():
    """Test with new mark."""
    pass
```

3. **Update CI/CD if needed**:

```yaml
- name: Run new mark tests
  run: uv run pytest -m new_mark
```

4. **Document in this guide**

## Troubleshooting

### Unknown Mark Warnings

If you see warnings about unknown marks:

1. Ensure the mark is registered in `pyproject.toml`
2. Check for typos in mark names
3. Run with `--strict-markers` to enforce mark registration

### Mark Not Working

If marks aren't filtering tests correctly:

1. Verify mark syntax: `@pytest.mark.markname`
2. Check mark combinations use proper boolean operators
3. Use `--collect-only` to see which tests would run:
   ```bash
   uv run pytest -m "unit" --collect-only
   ```

### Performance Issues

If test suite is slow:

1. Use marks to run subsets: `pytest -m "unit and not slow"`
2. Parallelize with pytest-xdist: `pytest -n auto -m unit`
3. Profile slow tests: `pytest --durations=10`

## Examples

### Development Workflow

```bash
# During development - quick feedback
uv run pytest -m "unit and smoke"

# Before commit - thorough but fast
uv run pytest -m "not slow and not requires_api"

# Before PR - comprehensive
uv run pytest -m "not manual"
```

### Debugging Workflow

```bash
# Test specific functionality
uv run pytest -m "llm and unit"

# Test validation system
uv run pytest -m validation

# Test PDF processing
uv run pytest -m pdf_processing
```

### CI/CD Workflow

```yaml
# GitHub Actions example
- name: Quick validation
  run: uv run pytest -m "smoke"

- name: Unit tests
  run: uv run pytest -m "unit"

- name: Integration tests
  run: uv run pytest -m "integration and not slow"

- name: Full test suite
  if: github.ref == 'refs/heads/main'
  run: uv run pytest -m "not manual"
```

## Summary

The pytest marks system provides:

- **Organized test structure**: Clear categorization of test types
- **Flexible execution**: Run specific test subsets as needed
- **Optimized CI/CD**: Different test strategies for different pipeline stages
- **Clear dependencies**: Explicit marking of external requirements
- **Performance control**: Separate slow tests from fast feedback loops

Use marks to create efficient testing workflows that match your development needs while maintaining comprehensive test coverage.

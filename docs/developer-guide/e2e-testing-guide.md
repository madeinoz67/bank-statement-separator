# End-to-End Testing Guide

This guide explains how to use the comprehensive end-to-end test fixture for validating the bank statement separator with Paperless integration.

## Overview

The end-to-end (E2E) test fixture provides:

1. **Remote Storage Cleanup**: Clears test storage paths (`test-input` and `test-processed`)
2. **Standardized Test Data**: Creates multi-statement PDFs with known metadata and boundaries
3. **Ollama Integration**: Tests with local Ollama instance using recommended models
4. **Result Validation**: Compares processed output against expected test data specifications

## Prerequisites

### Required Services

1. **Paperless-ngx Instance**: Running and accessible
2. **Ollama Instance**: Local or remote Ollama with recommended model
3. **Python Environment**: Project dependencies installed

### Environment Configuration

Create a test environment file or export these variables:

```bash
# Paperless Configuration
export PAPERLESS_URL="https://your-paperless-instance.com"
export PAPERLESS_TOKEN="your-api-token-here"
export PAPERLESS_API_INTEGRATION_TEST="true"

# Ollama Configuration
export OLLAMA_BASE_URL="http://10.0.0.150:11434"
export OLLAMA_MODEL="openhermes:latest"

# Optional: Output directories
export DEFAULT_OUTPUT_DIR="./test/output/e2e"
export ALLOWED_OUTPUT_DIRS="./"
```

### Recommended Ollama Model

Based on testing, the recommended model is:

- **openhermes:latest** - Provides good balance of accuracy and performance for statement separation

Other tested models available in `tests/env/.env.ollama_*` files.

## Usage

### Method 1: Demo Script (Recommended for First-Time Users)

The demo script provides a complete walkthrough:

```bash
# Set environment variables first
export PAPERLESS_URL="https://your-paperless.com"
export PAPERLESS_TOKEN="your-token"

# Run the demo
uv run python tests/manual/test_paperless_e2e_demo.py
```

**Demo Steps:**

1. ✅ Tests Paperless connection
2. 🧹 Cleans remote test storage paths
3. 📄 Generates standardized test documents
4. 📤 Uploads test documents to Paperless
5. 🤖 Configures Ollama processing
6. ⚡ Runs end-to-end processing
7. 📊 Validates results against expected data

### Method 2: Pytest Integration

Use the fixture in pytest tests:

```python
import pytest
from tests.integration.test_paperless_end_to_end_fixture import paperless_e2e_fixture

@pytest.mark.api_integration
@pytest.mark.e2e
def test_my_e2e_workflow(paperless_e2e_fixture):
    fixture = paperless_e2e_fixture

    # Your test code here
    config = create_ollama_config()
    results = fixture.run_end_to_end_processing(config)

    # Validate results
    assert results["success"]
    for doc_result in results["processed_documents"]:
        assert doc_result["validation"]["success"]
```

Run E2E tests:

```bash
# Run all E2E tests
PAPERLESS_API_INTEGRATION_TEST=true uv run pytest tests/integration/test_paperless_end_to_end_fixture.py -v -m e2e

# Run with specific environment
uv run pytest tests/integration/test_paperless_end_to_end_fixture.py -v -m e2e --env-file=tests/env/paperless_integration.env
```

### Method 3: Direct Fixture Usage

Use the fixture class directly in custom scripts:

```python
from src.bank_statement_separator.config import Config
from src.bank_statement_separator.utils.paperless_client import PaperlessClient
from tests.integration.test_paperless_end_to_end_fixture import PaperlessEndToEndFixture

# Initialize
config = Config(...)  # Your configuration
client = PaperlessClient(config)
fixture = PaperlessEndToEndFixture(client)

# Use fixture methods
cleanup_result = fixture.cleanup_remote_storage()
test_docs = fixture.generate_standardized_test_data()
upload_result = fixture.upload_test_documents(test_docs)
processing_result = fixture.run_end_to_end_processing(ollama_config)
```

## Test Data Specifications

### Standardized Documents

The fixture creates documents with **known, predictable content**:

#### Document 1: Multi-Statement Bundle (3 statements)

- **Test Bank Alpha Account 3456** - January 2024 (2 pages)
  - 8 transactions, $1,234.56 → $2,845.67
- **Test Bank Alpha Account 7890** - February 2024 (2 pages)
  - 6 transactions, $2,845.67 → $3,567.89
- **Test Credit Union Beta Account 4321** - March 2024 (3 pages)
  - 12 transactions, $3,567.89 → $4,123.45

#### Document 2: Dual-Statement Document (2 statements)

- **Test Community Bank Account 8888** - April 2024 (3 pages)
  - 10 transactions, $5,432.10 → $6,789.01
- **Test Savings & Loan Account 4444** - May 2024 (2 pages)
  - 7 transactions, $6,789.01 → $7,654.32

### Expected Outputs

Each document should produce separate PDF files matching these patterns:

- `test-bank-alpha-3456-2024-01-31.pdf`
- `test-bank-alpha-7890-2024-02-29.pdf`
- `test-credit-union-beta-4321-2024-03-31.pdf`
- `test-community-bank-8888-2024-04-30.pdf`
- `test-savings-loan-4444-2024-05-31.pdf`

## Validation Criteria

### File-Level Validation

- ✅ Correct number of output files generated
- ✅ Each file is a valid PDF with proper header
- ✅ File sizes are reasonable (> 1KB)
- ✅ Filenames match expected patterns

### Content Validation

- ✅ Statement boundaries correctly identified
- ✅ Account numbers properly extracted
- ✅ Bank names accurately identified
- ✅ Statement dates correctly parsed
- ✅ No content mixing between statements

### Workflow Validation

- ✅ Processing completes without errors
- ✅ Ollama integration works correctly
- ✅ Output files are properly generated
- ✅ Paperless upload/download cycle works

## Remote Storage Management

### Test Storage Paths

- **test-input**: Where test documents are uploaded
- **test-processed**: Where processed results are stored

### Cleanup Process

The fixture automatically:

1. Queries documents in test storage paths
2. Deletes existing test documents to ensure clean state
3. Creates new standardized test documents
4. Tracks created documents for later cleanup

## Troubleshooting

### Common Issues

**Connection Errors**

```
❌ Paperless connection failed: Connection refused
```

- Verify `PAPERLESS_URL` is correct and accessible
- Check `PAPERLESS_TOKEN` is valid and has sufficient permissions
- Ensure Paperless instance is running

**Ollama Errors**

```
❌ Failed to connect to Ollama
```

- Verify `OLLAMA_BASE_URL` is correct
- Ensure Ollama is running and has the specified model
- Check model name with `ollama list`

**Processing Failures**

```
❌ Statement separation failed
```

- Check Ollama model performance with simpler documents
- Review LLM temperature and token settings
- Examine processing logs for specific errors

**Validation Failures**

```
❌ File count mismatch: expected 3, got 2
```

- Review Ollama model's statement boundary detection
- Check if test documents have clear boundary markers
- Verify LLM prompt engineering is appropriate

### Debug Mode

Enable verbose logging:

```bash
export LOG_LEVEL="DEBUG"
uv run python tests/manual/test_paperless_e2e_demo.py
```

Check output directories:

```bash
ls -la ./test/output/demo_processing/
```

Examine generated PDFs:

```bash
# Check file sizes and content
file ./test/output/demo_processing/*.pdf
pdfinfo ./test/output/demo_processing/statement_1.pdf
```

### Performance Tuning

**Ollama Settings:**

- Use local Ollama instance for faster processing
- Ensure sufficient RAM/GPU for model
- Consider smaller models for testing (phi3, gemma2)

**Processing Settings:**

- Reduce `max_documents` for faster iteration
- Adjust `chunk_size` and `chunk_overlap` for model
- Set appropriate `llm_temperature` (0 for deterministic results)

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    services:
      paperless:
        image: paperlessngx/paperless-ngx:latest
        env:
          PAPERLESS_SECRET_KEY: test-secret
        ports:
          - 8000:8000

    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.12"

      - name: Install Ollama
        run: |
          curl -fsSL https://ollama.ai/install.sh | sh
          ollama serve &
          ollama pull openhermes:latest

      - name: Run E2E Tests
        env:
          PAPERLESS_URL: http://localhost:8000
          PAPERLESS_TOKEN: test-token
          OLLAMA_BASE_URL: http://localhost:11434
          PAPERLESS_API_INTEGRATION_TEST: true
        run: |
          uv run pytest tests/integration/test_paperless_end_to_end_fixture.py -v -m e2e
```

## Best Practices

### Test Isolation

- Always clean remote storage before tests
- Use unique timestamps in test document names
- Separate test storage paths from production

### Reproducible Results

- Use `temperature=0` for deterministic LLM output
- Test with consistent, known input documents
- Validate against specific expected outputs

### Resource Management

- Clean up test documents after testing
- Monitor Ollama resource usage
- Use appropriate timeouts for API calls

### Monitoring

- Track processing times and success rates
- Log validation failures for analysis
- Monitor API rate limits and quotas

## Example Test Scenarios

### Scenario 1: Basic Statement Separation

```python
def test_basic_separation(paperless_e2e_fixture):
    fixture = paperless_e2e_fixture

    config = create_basic_ollama_config()
    results = fixture.run_end_to_end_processing(config, max_documents=1)

    assert results["success"]
    doc = results["processed_documents"][0]
    assert doc["validation"]["success"]
    assert doc["validation"]["expected_vs_actual"]["file_count"]["match"]
```

### Scenario 2: Multi-Document Batch Processing

```python
def test_batch_processing(paperless_e2e_fixture):
    fixture = paperless_e2e_fixture

    config = create_batch_ollama_config()
    results = fixture.run_end_to_end_processing(config, max_documents=5)

    assert results["success"]
    assert len(results["processed_documents"]) >= 2

    for doc_result in results["processed_documents"]:
        assert doc_result["validation"]["success"]
```

### Scenario 3: Error Recovery Testing

```python
def test_error_recovery(paperless_e2e_fixture):
    fixture = paperless_e2e_fixture

    # Test with intentionally problematic configuration
    config = create_limited_ollama_config()  # Low token limit
    results = fixture.run_end_to_end_processing(config)

    # Should handle errors gracefully
    assert "errors" in results
    assert len(results.get("processed_documents", [])) >= 0
```

This comprehensive E2E testing approach ensures reliable validation of the bank statement separator's core functionality with real-world Paperless integration and Ollama processing.

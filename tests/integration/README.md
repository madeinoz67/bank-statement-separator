# Paperless-ngx API Integration Tests

This directory contains comprehensive integration tests for the paperless-ngx API functionality. These tests are designed to work against a real paperless-ngx instance to validate actual API interactions.

## 🔧 Test Overview

### Test Categories

1. **API Connection Tests** (`TestPaperlessAPIConnection`)
   - Connection validation and authentication
   - Configuration validation
   - Error handling for connection issues

2. **Document Query Tests** (`TestPaperlessAPIDocumentQuery`)
   - Document querying by tags, correspondent, document type
   - Date range filtering and pagination
   - PDF-only document filtering
   - Empty result handling

3. **Document Download Tests** (`TestPaperlessAPIDocumentDownload`)
   - Single document downloads with PDF validation
   - Auto-generated filename handling
   - Batch document downloads
   - Error handling for nonexistent documents

4. **Tag Management Tests** (`TestPaperlessAPITagManagement`)
   - Tag resolution and creation
   - Multiple tag handling
   - Tag ID validation

5. **Correspondent Management Tests** (`TestPaperlessAPICorrespondentManagement`)
   - Correspondent resolution and creation
   - Bank name handling

6. **Document Type Management Tests** (`TestPaperlessAPIDocumentTypeManagement`)
   - Document type resolution and creation
   - Type validation

7. **Error Handling Tests** (`TestPaperlessAPIErrorHandling`)
   - API timeout handling
   - Invalid parameter handling
   - PDF validation with real documents

8. **Complete Workflow Tests** (`TestPaperlessAPIFullWorkflow`)
   - End-to-end query → download → validate workflows
   - Configuration-based testing
   - Batch processing workflows

## 🚀 Running API Integration Tests

### Prerequisites

1. **Running paperless-ngx instance** (local or remote)
2. **Valid API credentials** (URL and token)
3. **Network access** to the paperless-ngx server
4. **Test documents** in paperless-ngx (optional, tests can handle empty systems)

### Quick Start

1. **Configure Test Environment**:
   ```bash
   # Copy and edit the integration environment file
   cp tests/env/paperless_integration.env.example tests/env/paperless_integration.env
   
   # Edit with your real credentials
   vim tests/env/paperless_integration.env
   ```

2. **Set Required Variables**:
   ```bash
   export PAPERLESS_URL="http://localhost:8000"
   export PAPERLESS_TOKEN="your-api-token-here" 
   export PAPERLESS_API_INTEGRATION_TEST="true"
   ```

3. **Run Setup and Validation**:
   ```bash
   python tests/manual/test_paperless_api_integration.py --setup --validate
   ```

4. **Run All API Integration Tests**:
   ```bash
   # Enable API integration tests and run them
   export PAPERLESS_API_INTEGRATION_TEST=true
   uv run pytest tests/integration/test_paperless_api.py -m api_integration -v
   ```

### Using the Helper Script

The `tests/manual/test_paperless_api_integration.py` script provides utilities for managing API integration tests:

```bash
# Setup test environment
python tests/manual/test_paperless_api_integration.py --setup

# Validate API connection
python tests/manual/test_paperless_api_integration.py --validate

# Create test data (tags, correspondents, etc.)
python tests/manual/test_paperless_api_integration.py --create-data

# Run all API integration tests
python tests/manual/test_paperless_api_integration.py --run-tests

# Run specific test categories
python tests/manual/test_paperless_api_integration.py --run-tests --test-pattern "connection"
python tests/manual/test_paperless_api_integration.py --run-tests --test-pattern "download"

# Clean up test data
python tests/manual/test_paperless_api_integration.py --cleanup

# Get detailed help
python tests/manual/test_paperless_api_integration.py --help-detailed
```

## ⚙️ Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PAPERLESS_URL` | Yes | Paperless-ngx server URL (e.g., `http://localhost:8000`) |
| `PAPERLESS_TOKEN` | Yes | API authentication token |
| `PAPERLESS_API_INTEGRATION_TEST` | Yes | Must be `"true"` to enable API tests |
| `PAPERLESS_INPUT_TAGS` | No | Default tags for testing (comma-separated) |
| `PAPERLESS_MAX_DOCUMENTS` | No | Document query limit (default: 10) |
| `PAPERLESS_QUERY_TIMEOUT` | No | API request timeout in seconds (default: 30) |

### Test Environment File

Create `tests/env/paperless_integration.env` with real credentials:

```bash
# API Integration Test Configuration
PAPERLESS_ENABLED=true
PAPERLESS_URL=http://localhost:8000
PAPERLESS_TOKEN=your-real-api-token-here
PAPERLESS_API_INTEGRATION_TEST=true

# Test-specific settings  
PAPERLESS_INPUT_TAGS=test-integration,bank-statement
PAPERLESS_MAX_DOCUMENTS=10
PAPERLESS_QUERY_TIMEOUT=30
```

## 🔐 Security Considerations

### ⚠️ Important Security Notes

1. **Never commit real credentials** to version control
2. **Use test/development instances** only - never production
3. **API tests will create/modify data** in your paperless-ngx instance:
   - Tags: `test-integration`, `api-test`, `bank-statement`
   - Correspondents: `Test Bank API Integration`
   - Document Types: `Test Statement Integration`
4. **Network access required** - tests make real HTTP requests
5. **Clean up test data** after testing to avoid clutter

### Test Data Impact

These tests will create the following entities in your paperless-ngx instance:
- **Tags**: For filtering and categorization testing
- **Correspondents**: For bank/organization testing
- **Document Types**: For statement categorization testing
- **No documents are uploaded** - tests only query/download existing documents

## 🧪 Test Execution Modes

### 1. Individual Test Categories

```bash
# Connection and authentication only
uv run pytest tests/integration/test_paperless_api.py::TestPaperlessAPIConnection -v

# Document query functionality
uv run pytest tests/integration/test_paperless_api.py::TestPaperlessAPIDocumentQuery -v

# Document download functionality  
uv run pytest tests/integration/test_paperless_api.py::TestPaperlessAPIDocumentDownload -v

# Complete workflow testing
uv run pytest tests/integration/test_paperless_api.py::TestPaperlessAPIFullWorkflow -v
```

### 2. Pattern-Based Testing

```bash
# All connection-related tests
uv run pytest tests/integration/test_paperless_api.py -k "connection" -v

# All query-related tests
uv run pytest tests/integration/test_paperless_api.py -k "query" -v

# All download-related tests
uv run pytest tests/integration/test_paperless_api.py -k "download" -v

# All workflow tests
uv run pytest tests/integration/test_paperless_api.py -k "workflow" -v
```

### 3. Marker-Based Testing

```bash
# All API integration tests
uv run pytest -m "api_integration" -v

# API integration tests (slow ones only)
uv run pytest -m "api_integration and slow" -v

# Integration tests excluding API
uv run pytest -m "integration and not api_integration" -v
```

## 📊 Expected Test Results

### Successful Test Run

```
tests/integration/test_paperless_api.py::TestPaperlessAPIConnection::test_api_connection_success PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIConnection::test_api_authentication_valid PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIDocumentQuery::test_query_all_documents PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIDocumentDownload::test_download_single_document PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIFullWorkflow::test_complete_query_and_download_workflow PASSED

========================= 45 passed in 12.34s =========================
```

### Common Skip Reasons

- `PAPERLESS_API_INTEGRATION_TEST=true not set` - API integration tests are disabled by default
- `Paperless API client not configured` - Missing URL or token
- `No documents available for testing` - Empty paperless-ngx instance (some tests will skip)
- `Not enough documents for pagination testing` - Need multiple documents for some tests

## 🐛 Troubleshooting

### Connection Issues

```bash
# Test basic connectivity
curl -H "Authorization: Token YOUR-TOKEN-HERE" http://localhost:8000/api/documents/?page_size=1

# Validate token format
echo "Your token should be 40+ characters: ${#PAPERLESS_TOKEN}"
```

### Common Errors

1. **401 Unauthorized**: Invalid or missing API token
2. **403 Forbidden**: Valid token but insufficient permissions  
3. **404 Not Found**: Incorrect paperless-ngx URL or endpoint
4. **Connection refused**: paperless-ngx not running or wrong port
5. **Timeout errors**: paperless-ngx overloaded or network issues

### Debug Mode

Enable detailed logging for troubleshooting:

```bash
export LOG_LEVEL=DEBUG
uv run pytest tests/integration/test_paperless_api.py -v -s --log-cli-level=DEBUG
```

## 📈 Performance Considerations

- **Test duration**: 10-30 seconds depending on paperless-ngx response time
- **Network dependency**: Tests require stable network connection
- **API rate limits**: Some paperless-ngx instances may have rate limiting
- **Document count**: Tests with more documents available will be more comprehensive

## 🔄 Continuous Integration

To run API integration tests in CI environments:

```yaml
# GitHub Actions example
- name: Run API Integration Tests
  env:
    PAPERLESS_URL: ${{ secrets.PAPERLESS_URL }}
    PAPERLESS_TOKEN: ${{ secrets.PAPERLESS_TOKEN }}
    PAPERLESS_API_INTEGRATION_TEST: "true"
  run: |
    uv run pytest tests/integration/test_paperless_api.py -m api_integration -v
```

**Note**: Only run in CI with dedicated test instances, never against production paperless-ngx.
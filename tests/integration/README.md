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

8. **Test Document Setup** (`TestPaperlessTestDocumentSetup`)

   - Creates realistic multi-page bank statement test documents
   - Uploads test documents with unique identifiers to prevent duplicates
   - Validates test document creation and availability
   - Uses `test:` prefixed tags to avoid system rule conflicts

9. **Complete Workflow Tests** (`TestPaperlessAPIFullWorkflow`)
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

### Creating Test Documents for Processing

The test suite includes a fixture that creates realistic bank statement test documents in paperless-ngx. This is useful for testing the complete workflow from document upload to processing:

```bash
# Create test documents in paperless-ngx (with real API credentials)
PAPERLESS_API_INTEGRATION_TEST=true \
PAPERLESS_ENABLED=true \
PAPERLESS_URL=https://your-paperless-instance.com \
PAPERLESS_TOKEN=your-api-token \
uv run pytest tests/integration/test_paperless_api.py::TestPaperlessTestDocumentSetup::test_fixture_creates_test_documents -v -s
```

This will create 5 realistic multi-page bank statement PDFs with:

- **Unique identifiers** to prevent duplicate detection
- **Test-prefixed tags** (`test:automation`, `test:multi-statement`, `test:unprocessed`) to avoid system rule conflicts
- **Varying page counts** (6-15 pages each) to simulate real multi-statement documents
- **Realistic content** including bank names, account numbers, transactions, and proper PDF structure

**Note**: Test documents use timestamp-based unique identifiers to prevent paperless-ngx from rejecting them as duplicates. Each run creates new documents with fresh timestamps.

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

| Variable                         | Required | Description                                              |
| -------------------------------- | -------- | -------------------------------------------------------- |
| `PAPERLESS_URL`                  | Yes      | Paperless-ngx server URL (e.g., `http://localhost:8000`) |
| `PAPERLESS_TOKEN`                | Yes      | API authentication token                                 |
| `PAPERLESS_API_INTEGRATION_TEST` | Yes      | Must be `"true"` to enable API tests                     |
| `PAPERLESS_INPUT_TAGS`           | No       | Default tags for testing (comma-separated)               |
| `PAPERLESS_MAX_DOCUMENTS`        | No       | Document query limit (default: 10)                       |
| `PAPERLESS_QUERY_TIMEOUT`        | No       | API request timeout in seconds (default: 30)             |

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

### 4. Testing Complete Paperless Workflow

After creating test documents, you can test the complete workflow from paperless-ngx document retrieval to statement processing:

```bash
# Test the complete paperless workflow with dry-run (safe to test)
PAPERLESS_ENABLED=true \
PAPERLESS_URL=https://your-paperless-instance.com \
PAPERLESS_TOKEN=your-api-token \
PAPERLESS_INPUT_TAGS=test:automation,test:multi-statement,test:unprocessed \
ALLOWED_OUTPUT_DIRS=./ \
uv run python -m src.bank_statement_separator.main process-paperless \
  --tags test:automation,test:multi-statement,test:unprocessed \
  --max-documents 5 \
  --dry-run -v -y

# Test with actual processing (will create output files)
PAPERLESS_ENABLED=true \
PAPERLESS_URL=https://your-paperless-instance.com \
PAPERLESS_TOKEN=your-api-token \
ALLOWED_OUTPUT_DIRS=./ \
uv run python -m src.bank_statement_separator.main process-paperless \
  --tags test:automation,test:multi-statement,test:unprocessed \
  --max-documents 3 \
  -o ./test/output/paperless_processing_test \
  -v -y
```

**Important Notes:**

- Use `--dry-run` first to verify document detection without processing
- The `ALLOWED_OUTPUT_DIRS` environment variable is required for security
- Test documents may have different tags due to paperless-ngx system rules overriding custom tags
- This is expected behavior and demonstrates proper tag-based filtering

## 📊 Expected Test Results

### Successful Test Run

```
tests/integration/test_paperless_api.py::TestPaperlessAPIConnection::test_api_connection_success PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIConnection::test_api_authentication_valid PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIConnection::test_api_configuration_validation PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIDocumentQuery::test_query_all_documents PASSED
tests/integration/test_paperless_api.py::TestPaperlessTestDocumentSetup::test_fixture_creates_test_documents PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIDocumentDownload::test_download_single_document PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPITagManagement::test_resolve_existing_tags PASSED
tests/integration/test_paperless_api.py::TestPaperlessAPIFullWorkflow::test_complete_query_and_download_workflow PASSED

========================= 26 passed, 3 skipped in 5.14s =========================
```

### Test Document Creation Results

When running the test document creation fixture, you should see output like:

```
✅ Created 5 realistic bank statement test documents in paperless-ngx
📊 Document types: ['Chase Bank Multi-Statement Bundle - January 2024 [1757330218001]',
                   'Wells Fargo Statement Collection - Q1 2024 [1757330218002]',
                   'Bank of America Combined Statements - Feb-Mar 2024 [1757330218003]',
                   'Citibank Business Account Statements - 2024 [1757330218004]',
                   'Credit Union Mixed Statement Bundle [1757330218005]']
PASSED
🧹 Cleaning up 5 test documents...
```

The unique identifiers (e.g., `[1757330218001]`) prevent duplicate detection and ensure each test run creates fresh documents.

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

### Test-Specific Issues

#### Duplicate Document Detection

If you see errors like `"Not consuming tmp059qtinl.pdf: It is a duplicate of Test Multi-Statement Bank Document 1"`:

- **Expected behavior**: Paperless-ngx prevents duplicate documents by content hash
- **Solution**: Test fixtures use timestamp-based unique identifiers to prevent duplicates
- **Manual fix**: Delete existing test documents or wait for timestamp to change

#### Tag Application Issues

If test documents don't have the expected tags (`test:automation`, etc.):

- **Expected behavior**: Paperless-ngx system rules may override custom tags
- **Result**: Documents get different system-assigned tags (e.g., [66, 568, 1, 582])
- **Impact**: Workflow tests won't find documents with `test:` prefixed tags
- **Solution**: Use the actual tags assigned by the system or configure paperless-ngx rules

#### No Documents Found for Processing

If `process-paperless` shows "No PDF documents found matching the criteria":

- **Check default tags**: System uses `unprocessed,bank-statement-raw` by default
- **Tag mismatch**: Test documents may have different tags due to system rules
- **Solution**: Query actual document tags and adjust filter criteria accordingly

```bash
# Check what tags your test documents actually have
uv run python test_paperless_documents.py
```

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

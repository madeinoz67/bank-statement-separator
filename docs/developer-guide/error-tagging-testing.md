# Error Tagging Testing Guide

Comprehensive testing guide for the error detection and tagging system that automatically tags Paperless-ngx documents with processing errors.

## Overview

The error tagging system identifies 6 types of processing errors and automatically applies configurable tags to affected documents in Paperless-ngx for manual review. This guide covers testing strategies and manual verification procedures.

## Testing Components

### Core Components

1. **ErrorDetector** (`src/bank_statement_separator/utils/error_detector.py`)
   - Detects processing errors from workflow state
   - Evaluates error severity levels
   - Applies threshold filtering

2. **ErrorTagger** (`src/bank_statement_separator/utils/error_tagger.py`)
   - Applies error tags to Paperless documents
   - Supports batch and individual tagging modes
   - Handles API errors gracefully

3. **Workflow Integration** (`src/bank_statement_separator/workflow.py`)
   - Integrates error detection into processing pipeline
   - Triggers tagging during Paperless upload

## Unit Testing

### Running Unit Tests

```bash
# Run all error tagging tests
uv run pytest tests/unit/test_error_tagging.py -v

# Run configuration tests
uv run pytest tests/unit/test_error_tagging_config.py -v

# Run with coverage
uv run pytest tests/unit/test_error_tagging*.py --cov=src/bank_statement_separator/utils/error_detector --cov=src/bank_statement_separator/utils/error_tagger --cov-report=html
```

### Test Coverage

The unit tests cover 28 test cases across:

- **Error Detection (10 tests)**
  - All 6 error types detection
  - Threshold filtering
  - Severity level evaluation
  - Configuration validation

- **Automatic Tagging (12 tests)**
  - Document tagging with mock Paperless client
  - Batch vs individual tagging modes
  - Error handling and graceful degradation
  - Tag application verification

- **Workflow Integration (6 tests)**
  - End-to-end workflow with error detection
  - Upload results with error tagging
  - Configuration scenarios

### Key Test Scenarios

```python
# Example test cases from the test suite

def test_detect_llm_analysis_error():
    """Test LLM analysis error detection."""

def test_detect_low_confidence_boundaries():
    """Test boundary detection with low confidence."""

def test_apply_error_tags_success():
    """Test successful error tag application."""

def test_workflow_integration_with_errors():
    """Test full workflow with error detection enabled."""
```

## Manual Integration Testing

### Test Environment Setup

1. **Configure Test Environment**

   ```bash
   # .env.testing
   PAPERLESS_ENABLED=true
   PAPERLESS_URL=https://your-paperless-instance.com
   PAPERLESS_TOKEN=your-test-api-token

   # Error detection configuration
   PAPERLESS_ERROR_DETECTION_ENABLED=true
   PAPERLESS_ERROR_TAGS=test:error-detection,test:automated-tagging
   PAPERLESS_ERROR_TAG_THRESHOLD=0.0
   PAPERLESS_ERROR_SEVERITY_LEVELS=low,medium,high,critical
   PAPERLESS_ERROR_BATCH_TAGGING=false
   ```

2. **Create Required Tags in Paperless**
   - Go to Paperless Settings → Tags
   - Create test tags: `test:error-detection`, `test:automated-tagging`
   - Create error type tags: `error:llm`, `error:confidence`, `error:pdf`, etc.
   - Create severity tags: `error:severity:high`, `error:severity:critical`

### Manual Test Scripts

The repository includes manual test scripts in `tests/manual/`:

#### 1. Storage Path Verification

```bash
# Check available storage paths
uv run python tests/manual/test_storage_paths.py
```

#### 2. Complete Integration Test

```bash
# Full end-to-end test with document creation
uv run python tests/manual/test_final_complete_integration.py
```

#### 3. Error Tagging with Existing Documents

```bash
# Test error tagging on existing documents
uv run python tests/manual/test_with_existing_documents.py
```

#### 4. Results Verification

```bash
# Verify final results and tag application
uv run python tests/manual/verify_final_results.py
```

### Expected Test Results

Successful integration tests should show:

```bash
🎉 COMPLETE SUCCESS!
✅ All documents are in 'test' storage path with error tags applied!
✅ Error detection and tagging system is fully operational!

FINAL RESULTS SUMMARY:
  • Total documents found: 2
  • Successfully configured: 2
  • Success rate: 100.0%
```

## Error Types Testing

### 1. LLM Analysis Failures

Test by simulating API failures or invalid responses:

```python
# Test scenario: LLM analysis timeout
workflow_state = {
    "current_step": "llm_analysis_error",
    "error_message": "OpenAI API timeout after 60 seconds",
    "llm_responses": [],
    "api_calls_made": 3,
    "total_api_failures": 3
}
```

### 2. Low Confidence Boundaries

Test boundary detection with low confidence scores:

```python
# Test scenario: Poor boundary detection
workflow_state = {
    "current_step": "boundary_detection",
    "detected_boundaries": [
        {"confidence": 0.2, "start_page": 1, "end_page": 5},
        {"confidence": 0.3, "start_page": 6, "end_page": 10}
    ]
}
```

### 3. PDF Processing Errors

Test PDF generation failures:

```python
# Test scenario: PDF generation failure
workflow_state = {
    "current_step": "pdf_generation_error",
    "error_message": "PDF generation failed: memory limit exceeded",
    "generated_files": [],
    "expected_files": ["statement1.pdf", "statement2.pdf"]
}
```

### 4. Metadata Extraction Issues

Test metadata extraction failures:

```python
# Test scenario: Metadata extraction failure
workflow_state = {
    "current_step": "metadata_extraction",
    "extracted_metadata": {},
    "metadata_extraction_errors": ["Failed to extract bank name", "No account number found"]
}
```

### 5. File Output Problems

Test file system issues:

```python
# Test scenario: File output failure
workflow_state = {
    "current_step": "file_output_error",
    "generated_files": [],
    "expected_files": ["statement1.pdf", "statement2.pdf"],
    "file_system_errors": ["Disk space full", "Permission denied"]
}
```

### 6. Validation Failures

Test output validation issues:

```python
# Test scenario: Validation failure
workflow_state = {
    "current_step": "validation",
    "validation_results": {
        "is_valid": False,
        "checks": {
            "page_count": {"status": "failed", "expected": 10, "actual": 8},
            "content_sampling": {"status": "failed", "error": "No readable text"}
        }
    }
}
```

## Configuration Testing

### Threshold Testing

Test different threshold values:

```bash
# High threshold (0.8) - only critical errors trigger tagging
PAPERLESS_ERROR_TAG_THRESHOLD=0.8

# Medium threshold (0.5) - medium and above trigger tagging
PAPERLESS_ERROR_TAG_THRESHOLD=0.5

# Low threshold (0.0) - all errors trigger tagging
PAPERLESS_ERROR_TAG_THRESHOLD=0.0
```

### Severity Level Testing

Test different severity configurations:

```bash
# Only critical errors
PAPERLESS_ERROR_SEVERITY_LEVELS=critical

# High and critical errors
PAPERLESS_ERROR_SEVERITY_LEVELS=high,critical

# All error levels
PAPERLESS_ERROR_SEVERITY_LEVELS=low,medium,high,critical
```

## Performance Testing

### Batch vs Individual Tagging

Test performance differences:

```bash
# Individual tagging mode (default)
PAPERLESS_ERROR_BATCH_TAGGING=false

# Batch tagging mode (better for high volume)
PAPERLESS_ERROR_BATCH_TAGGING=true
```

### High Volume Testing

Test with multiple documents:

1. Create 10+ test documents with processing errors
2. Measure tagging performance
3. Verify all documents are tagged correctly
4. Check for API rate limiting issues

## Troubleshooting Tests

### Permission Testing

Test API token permissions:

```bash
# Test tag creation permission
curl -X POST \
  -H "Authorization: Token $PAPERLESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-permission-check"}' \
  "$PAPERLESS_URL/api/tags/"
```

### Network Error Simulation

Test error handling for network issues:

1. Temporarily block network access
2. Run error tagging tests
3. Verify graceful degradation
4. Check error logging

### Tag Existence Testing

Test behavior when tags don't exist:

1. Remove error tags from Paperless
2. Run error detection tests
3. Verify tag creation attempts
4. Check fallback behavior

## Continuous Integration Testing

### GitHub Actions Integration

The error tagging tests run in CI/CD:

```yaml
# Example CI test configuration
- name: Test Error Tagging
  run: |
    uv run pytest tests/unit/test_error_tagging.py --cov=src --cov-report=xml

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Automated Testing Strategy

1. **Unit Tests**: Run on every commit
2. **Integration Tests**: Run on PR to main
3. **Manual Tests**: Run before release
4. **Performance Tests**: Run weekly

## Monitoring and Observability

### Log Analysis

Monitor error tagging in logs:

```bash
# Check error detection results
grep "Detected.*processing errors" logs/statement_processing.log

# Monitor tagging success rates
grep "Error Tagging Results" logs/statement_processing.log | \
  awk '{success+=$0} END{print "Success rate: " success/NR}'

# Check for tagging failures
grep "Failed to apply error tags" logs/statement_processing.log
```

### Metrics Collection

Key metrics to track:

- Error detection rate by type
- Tag application success rate
- Processing time impact
- API error rates

### Dashboard Queries

Example monitoring queries:

```bash
# Error detection by type
grep "error_type" logs/statement_processing.log | \
  sort | uniq -c | sort -nr

# Tagging success rate by hour
grep "tagged_documents" logs/statement_processing.log | \
  grep "$(date +%Y-%m-%d)" | \
  awk '{hour=substr($2,1,2); success[hour]+=$NF} END{for(h in success) print h":00 " success[h]}'
```

## Best Practices

### Testing Best Practices

1. **Test with Real Data**: Use actual bank statement PDFs when possible
2. **Test Error Scenarios**: Don't just test success cases
3. **Verify Cleanup**: Ensure test documents are properly tagged/removed
4. **Performance Testing**: Test with realistic document volumes
5. **Security Testing**: Verify proper permission handling

### Documentation Best Practices

1. **Document Test Cases**: Keep test documentation up-to-date
2. **Error Scenarios**: Document how to reproduce each error type
3. **Expected Outcomes**: Clearly define success criteria
4. **Troubleshooting**: Document common issues and solutions

### Development Best Practices

1. **Test-Driven Development**: Write tests before implementing features
2. **Mock External Dependencies**: Use mocks for Paperless API in unit tests
3. **Integration Testing**: Test with real Paperless instances
4. **Error Handling**: Test all error paths thoroughly
5. **Performance Monitoring**: Track performance impact of error detection

This testing guide ensures comprehensive validation of the error detection and tagging system across all scenarios and environments.

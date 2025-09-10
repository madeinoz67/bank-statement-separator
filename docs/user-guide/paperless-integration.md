# Paperless-ngx Integration Guide

Complete guide to integrating the Workflow Bank Statement Separator with Paperless-ngx document management system.

## Overview

Paperless-ngx integration enables automatic upload and organization of separated bank statements into your document management system. The integration includes:

- **Automatic Upload**: Processed statements uploaded after successful separation
- **Smart Organization**: Auto-creation of tags, correspondents, and document types
- **Metadata Management**: Automatic extraction and application of document metadata
- **Error Handling**: Robust handling of upload failures with retry logic
- **Error Detection & Tagging**: Automatic tagging of documents with processing errors for manual review

!!! tip "Production Ready"
The Paperless integration has been live-tested with actual paperless-ngx instances and includes comprehensive error handling with 27 unit tests covering all functionality.

## Prerequisites

### Paperless-ngx Setup

Ensure you have:

- **Paperless-ngx instance**: Running version 1.9.0 or higher
- **API Access**: Admin account with API token
- **Network Access**: System can reach Paperless-ngx server

### Authentication

Generate an API token in Paperless-ngx:

1. Log into your Paperless-ngx admin interface
2. Navigate to **Settings** → **API Tokens**
3. Click **Add Token** and give it a descriptive name
4. Copy the generated token for configuration

## Configuration

### Basic Setup

Configure Paperless integration in your `.env` file:

```bash
# Enable Paperless integration
PAPERLESS_ENABLED=true

# Connection settings
PAPERLESS_URL=http://localhost:8000
PAPERLESS_TOKEN=your-api-token-here

# Optional: Connection timeout
PAPERLESS_TIMEOUT_SECONDS=30
```

### Document Organization

Configure how documents are organized in Paperless:

```bash
# Auto-applied tags (comma-separated)
PAPERLESS_TAGS=bank-statement,automated

# Default correspondent name
PAPERLESS_CORRESPONDENT=Bank

# Document type
PAPERLESS_DOCUMENT_TYPE=Bank Statement

# Storage path for organization
PAPERLESS_STORAGE_PATH=Bank Statements

# Tag application timing (seconds)
PAPERLESS_TAG_WAIT_TIME=5
```

!!! info "Tag Wait Time"
`PAPERLESS_TAG_WAIT_TIME` controls how long the system waits (in seconds) before applying tags to uploaded documents. Paperless-ngx needs time to process documents before tags can be successfully applied. Adjust this value based on your Paperless instance speed:

    - **Fast instances**: 3-5 seconds (default: 5)
    - **Slower instances**: 8-10 seconds
    - **Testing/immediate**: 0 seconds (may cause tag failures)

### Advanced Options

```bash
# Upload behavior
PAPERLESS_AUTO_UPLOAD=true                    # Auto-upload after processing
PAPERLESS_DELETE_AFTER_UPLOAD=false          # Keep local files after upload
PAPERLESS_RETRY_UPLOADS=true                 # Retry failed uploads
PAPERLESS_BATCH_SIZE=5                       # Max documents per batch

# Backoff configuration for uploads
PAPERLESS_BACKOFF_MIN=2.0                    # Minimum backoff delay
PAPERLESS_BACKOFF_MAX=30.0                   # Maximum backoff delay
PAPERLESS_MAX_RETRIES=3                      # Maximum retry attempts
```

## Input Document Processing Tracking

When processing documents that **originate from Paperless-ngx** (using the `source_document_id` parameter), the system can automatically tag the original input documents as "processed" after successful processing. This prevents re-processing of the same documents in future runs.

### Configuration Options

Configure **one** of these input document tagging options:

```bash
# Option 1: Add a "processed" tag to input documents
PAPERLESS_INPUT_PROCESSED_TAG=processed

# Option 2: Remove "unprocessed" tag from input documents
PAPERLESS_INPUT_REMOVE_UNPROCESSED_TAG=true

# Option 3: Use a custom processing tag
PAPERLESS_INPUT_PROCESSING_TAG=bank-statement-processed

# Global enable/disable (default: true)
PAPERLESS_INPUT_TAGGING_ENABLED=true
```

### How It Works

1. **Document Processing**: Process bank statements from Paperless using `source_document_id`
2. **Output Processing**: Create separated statements and upload them to Paperless
3. **Input Tagging**: After successful upload, tag the original input document as processed
4. **Re-processing Prevention**: Tagged documents can be filtered out in future processing runs

### Usage Example

```bash
# Process a document from Paperless with ID 123
uv run python -c "
from src.bank_statement_separator.workflow import BankStatementWorkflow
from src.bank_statement_separator.config import load_config

config = load_config()
workflow = BankStatementWorkflow(config)

# source_document_id=123 tells the system this came from Paperless
result = workflow.run(
    input_file_path='/path/to/downloaded/statement.pdf',
    output_directory='/output',
    source_document_id=123
)

# After successful processing:
# - Output documents uploaded to Paperless with configured tags
# - Input document (ID 123) tagged as processed to prevent re-processing
"
```

### Configuration Precedence

Only **one** input tagging option should be configured. The system checks in this order:

1. `PAPERLESS_INPUT_PROCESSED_TAG` (if set, adds this tag)
2. `PAPERLESS_INPUT_REMOVE_UNPROCESSED_TAG` (if true, removes 'unprocessed' tag)
3. `PAPERLESS_INPUT_PROCESSING_TAG` (if set, adds this custom tag)

### Error Handling

Input document tagging failures are handled gracefully:

- **Non-blocking**: Tagging failures don't stop the workflow
- **Detailed Logging**: All tagging attempts and results are logged
- **Graceful Degradation**: Missing tags or API errors are handled without stopping processing

### Monitoring Input Document Processing

Check input document tagging results in logs:

```bash
# View input document tagging results
grep "input document.*processed" logs/statement_processing.log

# Check for tagging failures
grep "Failed to mark input document" logs/statement_processing.log

# View full workflow results including input tagging
grep "upload_results.*input_tagging" logs/statement_processing.log
```

## Error Detection and Tagging

The system automatically detects processing errors during bank statement separation and applies configurable tags to uploaded documents in Paperless-ngx for manual review. This feature helps identify documents that may need human attention or reprocessing.

### Overview

When processing errors occur, the system:

1. **Detects Processing Issues**: Identifies 6 types of processing errors during workflow execution
2. **Applies Error Tags**: Automatically tags affected documents in Paperless with configurable error tags
3. **Enables Manual Review**: Tagged documents can be easily filtered for manual review and correction
4. **Maintains Audit Trail**: Detailed logging of all error detection and tagging activities

### Configuration

Enable error detection and tagging in your `.env` file:

```bash
# Enable error detection and tagging
PAPERLESS_ERROR_DETECTION_ENABLED=true

# Tags to apply to documents with processing errors (comma-separated)
PAPERLESS_ERROR_TAGS=processing:needs-review,error:automated-detection

# Severity threshold (0.0-1.0) - only errors above this threshold trigger tagging
PAPERLESS_ERROR_TAG_THRESHOLD=0.5

# Severity levels that trigger tagging (comma-separated)
PAPERLESS_ERROR_SEVERITY_LEVELS=medium,high,critical

# Tagging mode: false=individual requests, true=batch requests
PAPERLESS_ERROR_BATCH_TAGGING=false
```

### Error Types Detected

The system detects these processing error categories:

| Error Type                     | Severity    | Description                                          | Example Scenarios                                   |
| ------------------------------ | ----------- | ---------------------------------------------------- | --------------------------------------------------- |
| **LLM Analysis Failures**      | High        | AI model fails to analyze document content           | API timeouts, invalid responses, model errors       |
| **Low Confidence Boundaries**  | Medium-High | Statement boundaries detected with low confidence    | Ambiguous page breaks, unclear statement separators |
| **PDF Processing Errors**      | High        | PDF generation or manipulation failures              | Memory limits, corruption, format issues            |
| **Metadata Extraction Issues** | Medium      | Failed to extract bank names, dates, account numbers | Unrecognized formats, OCR failures                  |
| **File Output Problems**       | Critical    | Generated files missing or corrupted                 | Disk space, permissions, write failures             |
| **Validation Failures**        | High        | Output validation checks failed                      | Page counts, content sampling, format verification  |

### How It Works

#### 1. Error Detection During Processing

```python
# Error detection happens automatically during workflow execution
from bank_statement_separator.workflow import BankStatementWorkflow

workflow = BankStatementWorkflow(config)
result = workflow.run(
    input_file_path='statements.pdf',
    output_directory='./output'
)

# If errors are detected during processing, they are automatically
# identified and prepared for tagging
```

#### 2. Automatic Tagging of Uploaded Documents

When documents are uploaded to Paperless, the system:

1. Checks if any processing errors were detected
2. Evaluates error severity against the configured threshold
3. Applies configured error tags to affected documents
4. Logs detailed tagging results for audit purposes

#### 3. Error Tag Application

```bash
# Example: Document with PDF processing errors gets these tags applied:
processing:needs-review        # From PAPERLESS_ERROR_TAGS
error:automated-detection      # From PAPERLESS_ERROR_TAGS
error:pdf                     # Specific error type tag
error:severity:high           # Severity level tag
```

### Configuration Examples

#### Basic Error Tagging

```bash
# Simple setup - tag documents needing review
PAPERLESS_ERROR_DETECTION_ENABLED=true
PAPERLESS_ERROR_TAGS=needs-review
PAPERLESS_ERROR_TAG_THRESHOLD=0.7
PAPERLESS_ERROR_SEVERITY_LEVELS=high,critical
```

#### Advanced Error Classification

```bash
# Detailed error classification with multiple tags
PAPERLESS_ERROR_DETECTION_ENABLED=true
PAPERLESS_ERROR_TAGS=processing:error,automated:detection,review:required
PAPERLESS_ERROR_TAG_THRESHOLD=0.5
PAPERLESS_ERROR_SEVERITY_LEVELS=medium,high,critical
PAPERLESS_ERROR_BATCH_TAGGING=true
```

#### Development/Testing Setup

```bash
# Tag all errors including low-severity ones for development
PAPERLESS_ERROR_DETECTION_ENABLED=true
PAPERLESS_ERROR_TAGS=test:error-detection,test:automated-tagging
PAPERLESS_ERROR_TAG_THRESHOLD=0.0
PAPERLESS_ERROR_SEVERITY_LEVELS=low,medium,high,critical
```

### Usage Examples

#### Processing with Error Detection

```bash
# Process documents with error detection enabled
PAPERLESS_ERROR_DETECTION_ENABLED=true \
uv run python -m src.bank_statement_separator.main \
  process statements.pdf --output ./output --yes
```

The system will:

1. Process the bank statements normally
2. Detect any processing errors during workflow execution
3. Upload separated documents to Paperless
4. Apply error tags to documents where processing errors occurred
5. Log detailed error detection and tagging results

#### Reviewing Tagged Documents

In Paperless-ngx, filter documents by error tags:

```bash
# Search for documents needing review
# In Paperless web interface: Search for "needs-review" tag
# Or use API to find tagged documents:

curl -H "Authorization: Token $PAPERLESS_TOKEN" \
  "$PAPERLESS_URL/api/documents/?tags__name__in=needs-review"
```

### Monitoring and Verification

#### Check Error Detection Results

```bash
# View error detection logs
grep "Detected.*processing errors" logs/statement_processing.log

# Check tagging results
grep "Error Tagging Results" logs/statement_processing.log

# View specific tagging details
grep "Document.*tags applied" logs/statement_processing.log
```

#### Verify in Paperless

1. **Navigate to Documents**: Go to your Paperless-ngx document list
2. **Filter by Error Tags**: Use tag filters to find documents with error tags
3. **Review Document Status**: Check which documents need manual review
4. **Manual Processing**: Reprocess or manually correct flagged documents

### Error Tag Management

#### Creating Error Tags in Paperless

The system assumes error tags exist in your Paperless instance. Create them manually:

1. **Go to Paperless Settings → Tags**
2. **Create Error Tags** such as:
   - `processing:needs-review` (orange color)
   - `error:automated-detection` (red color)
   - `error:pdf` (dark red)
   - `error:severity:high` (bright red)

#### Tag Cleanup After Review

After manually reviewing and fixing documents:

```bash
# Remove error tags from corrected documents
# Via Paperless web interface or API

# Example API call to remove error tag from document 123:
curl -X PATCH \
  -H "Authorization: Token $PAPERLESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tags": [1,2,3]}' \  # List without error tag IDs
  "$PAPERLESS_URL/api/documents/123/"
```

### Troubleshooting Error Tagging

#### Common Issues

=== "Tags Not Applied"

    **Problem**: Error tags not appearing on uploaded documents

    **Solutions**:
    ```bash
    # Check if error detection is enabled
    grep "PAPERLESS_ERROR_DETECTION_ENABLED" .env

    # Verify error tags exist in Paperless
    curl -H "Authorization: Token $PAPERLESS_TOKEN" \
         "$PAPERLESS_URL/api/tags/" | grep "needs-review"

    # Check threshold settings
    echo "Threshold: $PAPERLESS_ERROR_TAG_THRESHOLD"
    ```

=== "Too Many/Few Tags Applied"

    **Problem**: Error tagging too aggressive or not sensitive enough

    **Solutions**:
    ```bash
    # Adjust severity threshold
    PAPERLESS_ERROR_TAG_THRESHOLD=0.7  # More selective (higher threshold)
    PAPERLESS_ERROR_TAG_THRESHOLD=0.3  # Less selective (lower threshold)

    # Adjust severity levels
    PAPERLESS_ERROR_SEVERITY_LEVELS=high,critical  # Only major errors
    PAPERLESS_ERROR_SEVERITY_LEVELS=medium,high,critical  # Include medium errors
    ```

=== "Tagging Permission Errors"

    **Problem**: API token lacks permission to apply tags

    **Solutions**:
    ```bash
    # Test tag creation permission
    curl -X POST \
      -H "Authorization: Token $PAPERLESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"name": "test-tag"}' \
      "$PAPERLESS_URL/api/tags/"

    # Ensure API token has admin permissions
    # Or pre-create all required tags manually
    ```

#### Debug Error Detection

```bash
# Enable verbose error detection logging
LOG_LEVEL=DEBUG
PAPERLESS_ERROR_DETECTION_ENABLED=true

# Run with detailed output
uv run python -m src.bank_statement_separator.main \
  process statements.pdf --verbose

# Check error detection details
grep "error_detector\|error_tagger" logs/statement_processing.log
```

### Integration with Workflow

Error detection integrates seamlessly with the standard processing workflow:

```
1. PDF Ingestion → 2. Document Analysis → 3. Statement Detection →
4. Metadata Extraction → 5. PDF Generation → 6. File Organization →
7. Output Validation → 8. Paperless Upload (with Error Tagging)
```

Error detection occurs throughout steps 2-7, and tagging happens during step 8 when documents are uploaded to Paperless.

### Best Practices

#### Tag Naming Conventions

Use consistent, hierarchical tag naming:

```bash
# Recommended tag structure
PAPERLESS_ERROR_TAGS="
  processing:needs-review,    # Top-level category
  error:automated,           # Error source identifier
  review:priority-high       # Action-oriented tag
"
```

#### Severity Threshold Tuning

Start with conservative settings and adjust based on results:

```bash
# Production: Conservative (fewer false positives)
PAPERLESS_ERROR_TAG_THRESHOLD=0.7
PAPERLESS_ERROR_SEVERITY_LEVELS=high,critical

# Development: Comprehensive (catch more issues)
PAPERLESS_ERROR_TAG_THRESHOLD=0.4
PAPERLESS_ERROR_SEVERITY_LEVELS=medium,high,critical
```

#### Regular Review Process

Establish a workflow for reviewing tagged documents:

1. **Daily**: Check for new documents with error tags
2. **Weekly**: Review and process flagged documents
3. **Monthly**: Analyze error patterns and adjust thresholds
4. **Quarterly**: Clean up resolved error tags

This error detection and tagging system ensures that processing issues are automatically flagged for human review, improving the reliability and quality of automated bank statement processing.

## Auto-Creation Features

The system automatically creates missing entities in Paperless-ngx:

### Tags

- Creates tags from `PAPERLESS_TAGS` if they don't exist
- Applies bank-specific tags based on detected bank names
- Adds processing timestamp tags

### Correspondents

- Creates default correspondent from `PAPERLESS_CORRESPONDENT`
- Creates bank-specific correspondents (e.g., "Westpac", "ANZ")
- Uses exact name matching to avoid duplicates

### Document Types

- Creates document type from `PAPERLESS_DOCUMENT_TYPE`
- Handles different statement types (checking, savings, credit card)

### Storage Paths

- Creates storage path hierarchy from `PAPERLESS_STORAGE_PATH`
- Organizes by bank and year automatically
- Example: `Bank Statements/Westpac/2024/`

## Usage Examples

### Basic Integration

```bash
# Process and upload to Paperless
uv run python -m src.bank_statement_separator.main \
  process statements.pdf --output ./separated --yes
```

With Paperless enabled, this will:

1. Process the PDF and create separated statements
2. Upload each separated statement to Paperless-ngx
3. Apply configured tags, correspondent, and document type
4. Move input file to processed directory

### Custom Configuration

```bash
# Use custom Paperless settings
PAPERLESS_TAGS="bank-statement,westpac,monthly" \
PAPERLESS_CORRESPONDENT="Westpac Bank" \
uv run python -m src.bank_statement_separator.main \
  process westpac-statements.pdf --yes
```

## Workflow Integration

### Processing Pipeline

The Paperless upload occurs as the final step in the 8-node workflow:

1. PDF Ingestion → 2. Document Analysis → 3. Statement Detection →
2. Metadata Extraction → 5. PDF Generation → 6. File Organization →
3. Output Validation → **8. Paperless Upload**

### Upload Process

For each separated statement:

1. **Metadata Extraction**: Extract bank name, account number, statement date
2. **Entity Resolution**: Find or create tags, correspondent, document type
3. **File Upload**: Upload PDF with metadata
4. **Verification**: Confirm successful upload
5. **Logging**: Record upload results

## Metadata Mapping

### Automatic Metadata Extraction

| Statement Data   | Paperless Field | Example          |
| ---------------- | --------------- | ---------------- |
| Bank Name        | Correspondent   | "Westpac Bank"   |
| Account Number   | Tags            | "account-2819"   |
| Statement Date   | Date            | 2024-08-31       |
| Statement Period | Tags            | "2024-08"        |
| Document Type    | Document Type   | "Bank Statement" |

### Smart Tagging

The system applies intelligent tags:

```bash
# Example tags for a Westpac statement
bank-statement          # From PAPERLESS_TAGS
automated              # From PAPERLESS_TAGS
westpac                # From detected bank name
account-2819           # From account number
2024-08               # From statement period
```

## Error Handling

### Upload Failures

The system handles various upload scenarios:

=== "Network Errors" - Automatically retries with [exponential backoff and jitter](../design/backoff_mechanisms.md) - Logs detailed error information including backoff delays - Continues processing other documents - Configurable retry limits and delay parameters

=== "Authentication Errors" - Validates API token before processing - Provides clear error messages - Fails fast to prevent wasted processing

=== "Server Errors" - Distinguishes between temporary and permanent failures - Retries temporary failures (5xx errors) - Reports permanent failures (4xx errors) immediately

### Error Recovery

```bash
# Check upload status
grep "paperless" logs/statement_processing.log

# Retry failed uploads manually
uv run python -c "
from src.bank_statement_separator.utils.paperless_client import PaperlessClient
from src.bank_statement_separator.config import load_config

config = load_config()
client = PaperlessClient(config)
# Retry specific file
client.upload_document('/path/to/failed/statement.pdf', {...})
"
```

## Monitoring and Verification

### Upload Verification

Check that uploads completed successfully:

```bash
# View upload logs
grep "PAPERLESS_UPLOAD" logs/audit.log

# Check processing results for upload status
uv run python -m src.bank_statement_separator.main \
  process statements.pdf --verbose
```

### Paperless-ngx Verification

In your Paperless-ngx interface:

1. Navigate to **Documents**
2. Filter by recent uploads
3. Verify tags, correspondent, and document type
4. Check that files are properly organized

### API Health Check

Test Paperless connection:

```bash
# Test API connectivity
uv run python -c "
from src.bank_statement_separator.utils.paperless_client import PaperlessClient
from src.bank_statement_separator.config import load_config

config = load_config()
if config.paperless_enabled:
    client = PaperlessClient(config)
    print('✅ Paperless connection successful')
    print(f'Server: {config.paperless_url}')
else:
    print('ℹ️ Paperless integration disabled')
"
```

## Troubleshooting

### Common Issues

=== "Connection Refused"

    **Problem**: Cannot connect to Paperless-ngx server

    **Solutions**:
    ```bash
    # Check server URL and port
    curl -I http://localhost:8000/api/

    # Verify network connectivity
    ping paperless-server

    # Check if Paperless is running
    docker ps | grep paperless  # If using Docker
    ```

=== "Authentication Failed"

    **Problem**: API token invalid or expired

    **Solutions**:
    ```bash
    # Test API token manually
    curl -H "Authorization: Token your-token-here" \
         http://localhost:8000/api/documents/

    # Generate new token in Paperless admin
    # Update PAPERLESS_TOKEN in .env
    ```

=== "Upload Timeouts"

    **Problem**: Large files timing out during upload

    **Solutions**:
    ```bash
    # Increase timeout
    PAPERLESS_TIMEOUT_SECONDS=120

    # Process smaller batches
    PAPERLESS_BATCH_SIZE=1
    ```

=== "Metadata Issues"

    **Problem**: Tags or correspondents not created properly

    **Solutions**:
    ```bash
    # Enable verbose logging
    LOG_LEVEL=DEBUG

    # Check API responses
    grep "paperless.*response" logs/statement_processing.log

    # Verify entity resolution
    grep "_resolve_" logs/statement_processing.log
    ```

### Debug Mode

Enable detailed Paperless logging:

```bash
# Debug configuration
LOG_LEVEL=DEBUG
PAPERLESS_ENABLED=true

# Run with verbose output
uv run python -m src.bank_statement_separator.main \
  process statements.pdf --verbose
```

## Production Deployment

### Security Considerations

```bash
# Use HTTPS in production
PAPERLESS_URL=https://paperless.company.com

# Secure token storage
# Store token in secure key management system
PAPERLESS_TOKEN=$(vault kv get -field=token secret/paperless-api)
```

### Performance Optimization

```bash
# Optimize for high-volume processing
PAPERLESS_BATCH_SIZE=10         # Process multiple documents
PAPERLESS_TIMEOUT_SECONDS=60    # Reasonable timeout
PAPERLESS_RETRY_UPLOADS=true    # Handle transient failures
```

### Monitoring Setup

```bash
# Monitor upload success rates
grep "PAPERLESS_UPLOAD" logs/audit.log | \
  grep "$(date +%Y-%m-%d)" | \
  awk '/SUCCESS/{s++} /FAILED/{f++} END{print "Upload success rate: " s/(s+f)*100 "%"}'

# Alert on upload failures
upload_failures=$(grep "PAPERLESS_UPLOAD.*FAILED" logs/audit.log | \
  grep "$(date +%Y-%m-%d)" | wc -l)

if [[ $upload_failures -gt 5 ]]; then
    echo "High Paperless upload failure rate: $upload_failures" | \
        mail -s "Paperless Upload Alert" admin@company.com
fi
```

## Advanced Configuration

### Custom Metadata Templates

Configure dynamic metadata based on document content:

```bash
# Template variables available:
# {bank} - Detected bank name
# {account} - Account number
# {date} - Statement date
# {period} - Statement period

PAPERLESS_TAGS="bank-statement,{bank},{period}"
PAPERLESS_CORRESPONDENT="{bank} Bank"
PAPERLESS_STORAGE_PATH="Statements/{bank}/{year}"
```

### Conditional Processing

Only upload certain types of documents:

```bash
# Custom processing logic
PAPERLESS_AUTO_UPLOAD=false  # Disable automatic upload

# Manual upload in scripts based on conditions
if [[ "$bank_name" == "Westpac" ]]; then
    PAPERLESS_ENABLED=true uv run python -m src.bank_statement_separator.main \
      process statements.pdf --yes
fi
```

### Integration with Other Systems

Paperless integration can work alongside other document management:

```bash
# Multi-system upload
PAPERLESS_ENABLED=true
SHAREPOINT_ENABLED=true  # Custom integration
S3_BACKUP_ENABLED=true   # Custom integration
```

## API Reference

The Paperless client provides these key methods:

### Document Upload

```python
from src.bank_statement_separator.utils.paperless_client import PaperlessClient

client = PaperlessClient(config)

# Upload single document
result = client.upload_document(
    file_path="/path/to/statement.pdf",
    metadata={
        "title": "Westpac Statement 2024-08",
        "tags": ["bank-statement", "westpac"],
        "correspondent": "Westpac Bank",
        "document_type": "Bank Statement"
    }
)
```

### Entity Management

```python
# Create or find entities
tag_id = client._resolve_tags(["bank-statement", "automated"])
correspondent_id = client._resolve_correspondent("Westpac Bank")
doc_type_id = client._resolve_document_type("Bank Statement")
storage_id = client._resolve_storage_path("Bank Statements/Westpac")
```

## Migration and Backup

### Data Migration

When setting up Paperless integration:

1. **Backup existing data** before enabling integration
2. **Test with small batches** first
3. **Verify metadata mapping** is correct
4. **Monitor upload success rates** during rollout

### Disaster Recovery

```bash
# Backup Paperless database before major changes
docker exec paperless-db pg_dump -U paperless > paperless_backup.sql

# Export document list for recovery
curl -H "Authorization: Token $PAPERLESS_TOKEN" \
     "$PAPERLESS_URL/api/documents/" > documents_backup.json
```

This completes the Paperless-ngx integration guide. The system provides robust, production-ready document management integration with comprehensive error handling and monitoring capabilities.

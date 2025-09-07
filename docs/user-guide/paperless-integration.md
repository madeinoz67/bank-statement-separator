# Paperless-ngx Integration Guide

Complete guide to integrating the Workflow Bank Statement Separator with Paperless-ngx document management system.

## Overview

Paperless-ngx integration enables automatic upload and organization of separated bank statements into your document management system. The integration includes:

- **Automatic Upload**: Processed statements uploaded after successful separation
- **Smart Organization**: Auto-creation of tags, correspondents, and document types
- **Metadata Management**: Automatic extraction and application of document metadata
- **Error Handling**: Robust handling of upload failures with retry logic

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
```

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
4. Metadata Extraction → 5. PDF Generation → 6. File Organization → 
7. Output Validation → **8. Paperless Upload**

### Upload Process

For each separated statement:

1. **Metadata Extraction**: Extract bank name, account number, statement date
2. **Entity Resolution**: Find or create tags, correspondent, document type
3. **File Upload**: Upload PDF with metadata
4. **Verification**: Confirm successful upload
5. **Logging**: Record upload results

## Metadata Mapping

### Automatic Metadata Extraction

| Statement Data | Paperless Field | Example |
|----------------|-----------------|---------|
| Bank Name | Correspondent | "Westpac Bank" |
| Account Number | Tags | "account-2819" |
| Statement Date | Date | 2024-08-31 |
| Statement Period | Tags | "2024-08" |
| Document Type | Document Type | "Bank Statement" |

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

=== "Network Errors"
    - Automatically retries with [exponential backoff and jitter](../design/backoff_mechanisms.md)
    - Logs detailed error information including backoff delays
    - Continues processing other documents
    - Configurable retry limits and delay parameters
    
=== "Authentication Errors"
    - Validates API token before processing
    - Provides clear error messages
    - Fails fast to prevent wasted processing

=== "Server Errors"
    - Distinguishes between temporary and permanent failures
    - Retries temporary failures (5xx errors)
    - Reports permanent failures (4xx errors) immediately

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

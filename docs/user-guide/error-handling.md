# Error Handling Guide

Comprehensive guide to understanding and managing errors in the Workflow Bank Statement Separator.

## Error Handling Overview

The system provides a comprehensive error handling framework with multiple layers of protection:

1. **Pre-validation**: Document format and content validation before processing
2. **Processing Errors**: Smart handling of failures during workflow execution
3. **Quarantine System**: Automatic isolation of problematic documents
4. **Recovery Suggestions**: Actionable guidance for resolving issues

## Error Categories

### Critical Errors

These errors stop processing immediately and quarantine the document:

- **Password Protection**: PDF requires password to access
- **File Corruption**: PDF structure is damaged or invalid
- **Access Denied**: Insufficient permissions to read/write files
- **Resource Exhaustion**: Out of memory or disk space

### Recoverable Errors

These errors trigger retry logic with exponential backoff and jitter:

- **Network Timeouts**: API requests that timeout
- **Temporary File Locks**: Files temporarily in use
- **Rate Limiting**: API rate limits exceeded (automatic backoff)
- **Transient API Errors**: Temporary service issues
- **Resource Contention**: Temporary system resource issues

#### Backoff Strategy Details

The system implements a sophisticated backoff mechanism:

- **Exponential Delay**: Base delay doubles with each retry attempt
- **Jitter**: Random variation (10%-100%) prevents thundering herd
- **Maximum Delay**: Capped at 60 seconds to prevent excessive waits
- **Selective Retries**: Only retries on specific error types (RateLimitError, timeouts)
- **Configurable Limits**: Adjustable retry counts and base delays

For detailed information about the backoff implementation, see the [Backoff Mechanisms Design Document](../design/backoff_mechanisms.md).

### Validation Warnings

These generate warnings but may allow processing to continue:

- **Old Documents**: Files older than configured age limit
- **Large Files**: Files exceeding recommended size limits
- **Low Text Content**: Documents with minimal extractable text
- **Missing Metadata**: Statements without clear account information

## Quarantine System

### How It Works

When a document fails critical validation or processing:

1. **Document Quarantine**: File moved to quarantine directory with timestamp
2. **Error Report**: Detailed JSON report generated with failure details
3. **Recovery Suggestions**: Actionable steps provided for resolution
4. **Audit Logging**: Complete failure trail recorded

### Quarantine Directory Structure

```
quarantine/
├── failed_20240831_143022_statement.pdf     # Quarantined document
├── failed_20240831_143055_document.pdf      # Another failed document
└── reports/                                 # Error reports directory
    ├── error_report_20240831_143022.json    # Detailed error report
    └── error_report_20240831_143055.json    # Another error report
```

### Example Error Report

```json
{
  "timestamp": "2024-08-31T14:30:22",
  "quarantine_file": "/quarantine/failed_20240831_143022_statement.pdf",
  "original_file": "/input/problematic_statement.pdf",
  "error_reason": "Document format validation failed: Password protected",
  "workflow_step": "pdf_ingestion_format_error",
  "configuration": {
    "validation_strictness": "normal",
    "max_file_size_mb": 100,
    "allowed_extensions": [".pdf"]
  },
  "recovery_suggestions": [
    "Remove password protection from the PDF",
    "Use a PDF tool to unlock the document",
    "Contact the document source for an unlocked version"
  ],
  "system_info": {
    "python_version": "3.11.0",
    "memory_available": "4.2 GB",
    "disk_space": "150 GB"
  }
}
```

## Validation Strictness Levels

Configure error handling behavior with the `VALIDATION_STRICTNESS` setting:

### Strict Mode

- All validation issues are treated as errors
- Processing stops on first failure
- Highest accuracy, lowest success rate
- Best for critical financial processing

```bash
VALIDATION_STRICTNESS=strict
```

### Normal Mode (Default)

- Balanced approach between validation and success
- Some issues generate warnings but allow processing
- Good accuracy with reasonable success rate
- Recommended for most use cases

```bash
VALIDATION_STRICTNESS=normal
```

### Lenient Mode

- Most validation issues generate warnings only
- Processing continues unless critical failures occur
- Lower accuracy, highest success rate
- Best for exploratory or bulk processing

```bash
VALIDATION_STRICTNESS=lenient
```

## Common Error Scenarios

### Password-Protected PDFs

**Error**: Document requires password for access

**Recovery Steps**:

1. Remove password protection using PDF tools
2. Request unprotected version from source
3. Use PDF utilities like `qpdf` or Adobe Acrobat

```bash
# Remove password protection with qpdf
qpdf --password=PASSWORD --decrypt input.pdf output.pdf
```

### File Corruption

**Error**: PDF structure is damaged or incomplete

**Recovery Steps**:

1. Re-download or re-scan the original document
2. Use PDF repair tools
3. Convert to different format and back to PDF

```bash
# Attempt PDF repair with Ghostscript
gs -o repaired.pdf -sDEVICE=pdfwrite -dPDFSETTINGS=/prepress input.pdf
```

### API Quota Exceeded

**Error**: OpenAI API quota or rate limits exceeded

**Recovery Steps**:

1. Wait for quota reset (usually monthly)
2. Upgrade OpenAI plan for higher limits
3. Use fallback processing mode

```bash
# Process without API key (fallback mode)
OPENAI_API_KEY="" uv run python -m src.bank_statement_separator.main process input.pdf
```

### Insufficient Text Content

**Error**: Document appears to be image-only or has minimal text

**Recovery Steps**:

1. Check if document is scanned image
2. Apply OCR processing before separation
3. Adjust minimum text content ratio

```bash
# Adjust text content requirements
MIN_TEXT_CONTENT_RATIO=0.05  # Lower threshold
REQUIRE_TEXT_CONTENT=false   # Disable requirement
```

### Large File Processing

**Error**: File exceeds size limits or causes memory issues

**Recovery Steps**:

1. Increase file size limits in configuration
2. Process on machine with more memory
3. Split large documents before processing

```bash
# Increase size limits
MAX_FILE_SIZE_MB=500
MAX_TOTAL_PAGES=1000
```

## Error Prevention

### Pre-Processing Validation

Enable comprehensive validation before processing starts:

```bash
# Enable all validation checks
VALIDATE_PDF_STRUCTURE=true
CHECK_PDF_CORRUPTION=true
REQUIRE_TEXT_CONTENT=true
MIN_TEXT_CONTENT_RATIO=0.1
```

### Resource Management

Prevent resource-related errors:

```bash
# Memory and disk management
MAX_FILE_SIZE_MB=200
QUARANTINE_MAX_SIZE_GB=10
LOG_MAX_SIZE_MB=50
```

### Network Reliability

Configure robust API handling with advanced backoff mechanisms:

```bash
# API reliability settings
API_TIMEOUT_SECONDS=120
MAX_RETRY_ATTEMPTS=3

# Backoff configuration
OPENAI_BACKOFF_MIN=1.0      # Minimum delay between retries
OPENAI_BACKOFF_MAX=60.0     # Maximum delay cap
OPENAI_BACKOFF_MULTIPLIER=2.0  # Exponential growth factor

# Rate limiting
OPENAI_REQUESTS_PER_MINUTE=50
OPENAI_BURST_LIMIT=10
```

## CLI Error Management

### Check Quarantine Status

```bash
# View quarantine directory status
uv run python -m src.bank_statement_separator.main quarantine-status

# Detailed view with error analysis
uv run python -m src.bank_statement_separator.main quarantine-status --verbose
```

### Clean Quarantine Directory

```bash
# Preview cleanup (safe)
uv run python -m src.bank_statement_separator.main quarantine-clean --dry-run

# Clean files older than 30 days
uv run python -m src.bank_statement_separator.main quarantine-clean --days 30

# Force cleanup without confirmation
uv run python -m src.bank_statement_separator.main quarantine-clean --yes
```

### Error Log Analysis

```bash
# View recent errors
tail -f logs/statement_processing.log | grep ERROR

# Search for specific error types
grep "quarantined" logs/statement_processing.log

# Monitor API failures
grep "API_ERROR" logs/audit.log
```

## Recovery Workflows

### Document Recovery Process

1. **Identify Issue**: Check error report for specific problem
2. **Apply Fix**: Follow recovery suggestions in report
3. **Reprocess**: Attempt processing with corrected document
4. **Verify Results**: Confirm successful processing

### Batch Recovery

For multiple failed documents:

```bash
#!/bin/bash
# recover_quarantined.sh

QUARANTINE_DIR="./quarantine"
RECOVERED_DIR="./recovered"

for pdf in "$QUARANTINE_DIR"/failed_*.pdf; do
    echo "Attempting to recover: $pdf"

    # Try processing with lenient validation
    VALIDATION_STRICTNESS=lenient uv run python -m src.bank_statement_separator.main \
        process "$pdf" --output "$RECOVERED_DIR" --yes

    if [[ $? -eq 0 ]]; then
        echo "✅ Successfully recovered: $pdf"
    else
        echo "❌ Still failing: $pdf"
    fi
done
```

## Monitoring and Alerts

### Error Rate Monitoring

```bash
# Calculate daily error rate
grep "quarantined" logs/statement_processing.log | \
    grep "$(date +%Y-%m-%d)" | wc -l

# Success rate over last 100 operations
tail -100 logs/statement_processing.log | \
    grep -E "(SUCCESS|ERROR)" | \
    awk '/SUCCESS/{s++} /ERROR/{e++} END{print "Success rate: " s/(s+e)*100 "%"}'
```

### Automated Alerts

Set up monitoring scripts for production:

```bash
#!/bin/bash
# monitor_errors.sh

ERROR_COUNT=$(grep "ERROR" logs/statement_processing.log | \
    grep "$(date +%Y-%m-%d)" | wc -l)

if [[ $ERROR_COUNT -gt 10 ]]; then
    echo "High error rate detected: $ERROR_COUNT errors today" | \
        mail -s "Bank Separator Alert" admin@company.com
fi

# Check quarantine size
QUARANTINE_SIZE=$(du -sm quarantine/ | cut -f1)
if [[ $QUARANTINE_SIZE -gt 1000 ]]; then
    echo "Quarantine directory size: ${QUARANTINE_SIZE}MB" | \
        mail -s "Quarantine Size Alert" admin@company.com
fi
```

## Configuration for Error Handling

### Production Configuration

```bash
# High reliability production setup
VALIDATION_STRICTNESS=strict
MAX_RETRY_ATTEMPTS=3
ENABLE_ERROR_REPORTING=true
AUTO_QUARANTINE_CRITICAL_FAILURES=true
PRESERVE_FAILED_OUTPUTS=true
CONTINUE_ON_VALIDATION_WARNINGS=false

# Comprehensive logging
ENABLE_AUDIT_LOGGING=true
LOG_LEVEL=INFO
LOG_API_CALLS=true
```

### Development Configuration

```bash
# Permissive development setup
VALIDATION_STRICTNESS=lenient
MAX_RETRY_ATTEMPTS=1
CONTINUE_ON_VALIDATION_WARNINGS=true
PRESERVE_FAILED_OUTPUTS=true
ENABLE_ERROR_REPORTING=true

# Debug logging
LOG_LEVEL=DEBUG
DEVELOPMENT_MODE=true
```

## Best Practices

### Error Prevention

1. **Validate Early**: Enable pre-processing validation
2. **Set Appropriate Limits**: Configure reasonable file size and page limits
3. **Monitor Resources**: Watch memory and disk usage
4. **Test Regularly**: Run test suite to catch regressions

### Error Response

1. **Review Error Reports**: Always check detailed error reports
2. **Follow Recovery Steps**: Apply suggested recovery actions
3. **Update Configuration**: Adjust settings based on error patterns
4. **Document Issues**: Keep track of common problems and solutions

### Monitoring

1. **Track Error Rates**: Monitor success/failure ratios
2. **Review Quarantine**: Regularly check quarantined documents
3. **Clean Up**: Implement automated cleanup of old files
4. **Alert on Issues**: Set up monitoring for critical errors

## Troubleshooting Common Issues

### High Error Rates

If you're seeing many errors:

1. Check validation strictness level
2. Review file quality in your input
3. Verify API key and quota status
4. Monitor system resources

### Quarantine Filling Up

If quarantine directory grows large:

1. Review error patterns in reports
2. Fix common document issues at source
3. Implement regular cleanup schedule
4. Consider adjusting validation settings

### Processing Slowdowns

If processing becomes slow:

1. Check for high retry rates due to rate limiting
2. Monitor API response times and backoff delays
3. Review system resource usage
4. Consider adjusting rate limits for your use case
5. Enable backoff monitoring to track delay patterns
6. Consider batch processing optimization

#### Rate Limiting Issues

If experiencing frequent rate limit errors:

1. **Check Current Limits**: Review `OPENAI_REQUESTS_PER_MINUTE` setting
2. **Monitor Usage**: Use rate limiter statistics to understand patterns
3. **Adjust Burst Capacity**: Increase `OPENAI_BURST_LIMIT` for traffic spikes
4. **Optimize Timing**: Process during off-peak hours if possible
5. **Consider Local Models**: Switch to Ollama for unlimited local processing

## Technical Reference

For detailed technical configuration, implementation details, and advanced error handling setup, see the [Error Handling Technical Reference](../reference/error-handling-technical.md).

This technical guide includes:

- Complete environment variable configurations
- Production deployment best practices
- Advanced monitoring and maintenance procedures
- Detailed cron job setups for automation
- Low-level implementation details

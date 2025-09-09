# Error Handling and Document Quarantine System

This document describes the comprehensive error handling system implemented for invalid documents and documents that fail validation tests.

## Configuration Options

The system now includes extensive error handling configuration in `.env` files:

### Error Handling Configuration

```bash
# Directory for failed/invalid documents (uses output_dir/quarantine if None)
QUARANTINE_DIRECTORY=./quarantine

# Maximum retry attempts for transient failures (0-5)
MAX_RETRY_ATTEMPTS=2

# Continue processing despite validation warnings
CONTINUE_ON_VALIDATION_WARNINGS=true

# Automatically quarantine documents with critical failures
AUTO_QUARANTINE_CRITICAL_FAILURES=true

# Keep partial outputs when processing fails
PRESERVE_FAILED_OUTPUTS=true

# Generate detailed error reports for failures
ENABLE_ERROR_REPORTING=true

# Directory for error reports (uses quarantine_dir/reports if None)
ERROR_REPORT_DIRECTORY=./error_reports

# Validation strictness level: strict|normal|lenient
VALIDATION_STRICTNESS=normal
```

### Document Validation Configuration

```bash
# Minimum pages required per statement
MIN_PAGES_PER_STATEMENT=1

# Maximum age of input files in days (None for no limit)
MAX_FILE_AGE_DAYS=365

# Allowed file extensions for processing
ALLOWED_FILE_EXTENSIONS=.pdf

# Require documents to contain extractable text
REQUIRE_TEXT_CONTENT=true

# Minimum ratio of pages with text content (0.0-1.0)
MIN_TEXT_CONTENT_RATIO=0.1
```

## Error Handling Methods

### 1. Tiered Error Handling Strategy

The system implements three severity levels:

- **RECOVERABLE**: Warnings that allow continued processing
- **CRITICAL**: Errors that require stopping processing
- **VALIDATION_FAILURE**: Post-processing validation issues

### 2. Document Format Pre-Validation

Before processing begins, documents are validated for:

- File existence and accessibility
- Allowed file extensions
- File age (if configured)
- PDF-specific checks:
  - Password protection
  - Page count
  - Text content availability
  - Document integrity

### 3. Quarantine System

Invalid or critically failed documents are automatically moved to quarantine:

**Features:**

- Automatic quarantine for critical failures
- Timestamped filenames to prevent conflicts
- Detailed error reports with recovery suggestions
- Management commands for cleanup

**Quarantine Directory Structure:**

```
quarantine/
├── failed_20241201_143022_statement.pdf
├── failed_20241201_143055_document.pdf
└── reports/
    ├── error_report_20241201_143022.json
    └── error_report_20241201_143055.json
```

### 4. Validation Strictness Levels

#### Strict Mode

- File age limits enforced as errors
- File size issues treated as critical
- Page count mismatches cause failure
- Text content requirements strictly enforced

#### Normal Mode (Default)

- File age limits generate warnings
- File size issues generate warnings
- Page count validated normally
- Balanced error handling

#### Lenient Mode

- Most validation issues generate warnings only
- Page count mismatches allowed
- Minimal blocking of documents
- Maximum processing success rate

### 5. Retry Mechanism

Transient failures are automatically retried:

- Network-related errors
- Temporary file access issues
- Recoverable processing errors
- Configurable retry count (0-5 attempts)

### 6. Enhanced Error Reporting

Detailed error reports include:

- Timestamp and file information
- Error reason and context
- Processing step where failure occurred
- System configuration details
- Actionable recovery suggestions

**Example Error Report:**

```json
{
  "timestamp": "2024-12-01T14:30:22",
  "quarantine_file": "/quarantine/failed_20241201_143022_statement.pdf",
  "original_file": "/input/problematic_statement.pdf",
  "error_reason": "Document format validation failed: Password protected",
  "workflow_step": "pdf_ingestion_format_error",
  "recovery_suggestions": [
    "Remove password protection from the PDF",
    "Use a PDF tool to unlock the document",
    "Contact the document source for an unlocked version"
  ]
}
```

## CLI Commands

### Process Documents (Enhanced)

```bash
# Process with error handling
python -m src.bank_statement_separator.main process input.pdf --output ./output

# Process with strict validation
VALIDATION_STRICTNESS=strict python -m src.bank_statement_separator.main process input.pdf
```

### Quarantine Management

```bash
# Check quarantine status
python -m src.bank_statement_separator.main quarantine-status

# Clean old quarantined files (30+ days)
python -m src.bank_statement_separator.main quarantine-clean

# Clean with custom age and preview
python -m src.bank_statement_separator.main quarantine-clean --days 7 --dry-run

# Clean with confirmation
python -m src.bank_statement_separator.main quarantine-clean --days 14 --yes
```

## Error Recovery Suggestions

The system provides specific recovery suggestions based on error types:

### Password Protection Errors

- Remove password protection from the PDF
- Use a PDF tool to unlock the document
- Contact the document source for an unlocked version

### Page Count/Integrity Errors

- Verify the PDF is not corrupted
- Check if pages are missing from the original document
- Try re-downloading or re-scanning the document

### API/Processing Errors

- Verify OPENAI_API_KEY is set correctly
- Check API quota and billing status
- Ensure network connectivity to OpenAI services
- Try using fallback processing if enabled

### File Size/Compression Errors

- Check for PDF corruption or compression issues
- Verify the file was completely downloaded/transferred
- Try processing with a PDF repair tool

### Text Content Errors

- Run OCR on the document to extract text
- Verify document is not purely image-based
- Check if document was scanned at sufficient resolution

### Validation Errors

- Review validation strictness settings
- Check if document meets minimum requirements
- Consider processing in lenient mode

## Best Practices

### For Production Deployment

1. **Configure Quarantine Directory**

   ```bash
   QUARANTINE_DIRECTORY=/secure/quarantine
   ERROR_REPORT_DIRECTORY=/secure/error_reports
   ```

2. **Set Appropriate Strictness**

   ```bash
   # For high-accuracy requirements
   VALIDATION_STRICTNESS=strict

   # For maximum throughput
   VALIDATION_STRICTNESS=lenient
   ```

3. **Enable Comprehensive Reporting**

   ```bash
   ENABLE_ERROR_REPORTING=true
   ENABLE_AUDIT_LOGGING=true
   LOG_LEVEL=INFO
   ```

4. **Configure Cleanup Automation**
   ```bash
   # Add to crontab for weekly cleanup
   0 2 * * 0 /usr/local/bin/python -m bank_separator quarantine-clean --days 30 --yes
   ```

### For Development/Testing

1. **Use Lenient Validation**

   ```bash
   VALIDATION_STRICTNESS=lenient
   CONTINUE_ON_VALIDATION_WARNINGS=true
   ```

2. **Preserve Debug Information**

   ```bash
   PRESERVE_FAILED_OUTPUTS=true
   LOG_LEVEL=DEBUG
   ```

3. **Enable Verbose Error Reporting**
   ```bash
   ENABLE_ERROR_REPORTING=true
   MAX_RETRY_ATTEMPTS=1  # Fail fast for debugging
   ```

## Monitoring and Maintenance

### Regular Health Checks

```bash
# Check quarantine status
python -m bank_separator quarantine-status

# Review error patterns in reports
ls -la /path/to/error_reports/ | head -10
```

### Log Analysis

```bash
# Check recent errors
tail -100 /path/to/logs/statement_processing.log | grep ERROR

# Monitor quarantine activity
tail -f /path/to/logs/statement_processing.log | grep "quarantined"
```

### Cleanup Procedures

```bash
# Weekly cleanup of old quarantine files
python -m bank_separator quarantine-clean --days 30 --yes

# Monthly cleanup with confirmation
python -m bank_separator quarantine-clean --days 60
```

This comprehensive error handling system ensures robust document processing with clear visibility into failures and actionable recovery paths.

# Environment Variables Reference

Complete reference for all 40+ environment variables that control the Workflow Bank Statement Separator.

## Configuration Overview

The system uses environment variables loaded from a `.env` file for configuration. Variables are organized into logical groups for different aspects of the system.

!!! tip "Configuration Template"
Copy `.env.example` to `.env` to get started with documented default values for all variables.

## Core Processing Variables

### AI Processing

| Variable                     | Type    | Default       | Description                                        |
| ---------------------------- | ------- | ------------- | -------------------------------------------------- |
| `OPENAI_API_KEY`             | String  | None          | OpenAI API key for LLM analysis                    |
| `LLM_MODEL`                  | Choice  | `gpt-4o-mini` | AI model: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo` |
| `LLM_TEMPERATURE`            | Float   | `0`           | Model temperature (0-1, 0=deterministic)           |
| `LLM_MAX_TOKENS`             | Integer | `4000`        | Maximum tokens per API call                        |
| `ENABLE_FALLBACK_PROCESSING` | Boolean | `true`        | Enable pattern-matching when AI fails              |

!!! info "AI Model Selection"
    - `gpt-4o-mini`: Best balance of cost and performance (recommended)
    - `gpt-4o`: Highest accuracy, higher cost
    - `gpt-3.5-turbo`: Fastest processing, lower accuracy

### Text Processing

| Variable                 | Type    | Default | Description                        |
| ------------------------ | ------- | ------- | ---------------------------------- |
| `CHUNK_SIZE`             | Integer | `6000`  | Text chunk size for LLM processing |
| `CHUNK_OVERLAP`          | Integer | `800`   | Overlap between chunks for context |
| `TEXT_EXTRACTION_METHOD` | Choice  | `auto`  | Method: `auto`, `text`, `layout`   |

### File Processing

| Variable                  | Type    | Default | Description                            |
| ------------------------- | ------- | ------- | -------------------------------------- |
| `MAX_FILE_SIZE_MB`        | Integer | `100`   | Maximum input file size in MB          |
| `MAX_PAGES_PER_STATEMENT` | Integer | `50`    | Maximum pages per individual statement |
| `MAX_TOTAL_PAGES`         | Integer | `500`   | Maximum total pages in input document  |
| `PDF_RESOLUTION_DPI`      | Integer | `150`   | DPI for PDF processing                 |

## Output Configuration

### File Organization

| Variable                   | Type    | Default                  | Description                           |
| -------------------------- | ------- | ------------------------ | ------------------------------------- |
| `DEFAULT_OUTPUT_DIR`       | Path    | `./separated_statements` | Default output directory              |
| `PROCESSED_INPUT_DIR`      | Path    | Auto                     | Directory for processed input files   |
| `INCLUDE_BANK_IN_FILENAME` | Boolean | `true`                   | Include bank name in output filenames |
| `DATE_FORMAT`              | String  | `YYYY-MM`                | Date format for filenames             |
| `MAX_FILENAME_LENGTH`      | Integer | `240`                    | Maximum filename length               |

!!! example "Filename Format"
With `INCLUDE_BANK_IN_FILENAME=true` and `DATE_FORMAT=YYYY-MM-DD`:
`     westpac-2819-2015-05-21.pdf
    anz-1234-2023-12-31.pdf
    `

### File Naming Patterns

| Variable              | Type    | Default                   | Description                      |
| --------------------- | ------- | ------------------------- | -------------------------------- |
| `FILENAME_PATTERN`    | String  | `{bank}-{account}-{date}` | Filename pattern template        |
| `ACCOUNT_MASK_DIGITS` | Integer | `4`                       | Number of account digits to show |
| `BANK_NAME_CLEANUP`   | Boolean | `true`                    | Clean bank names for filenames   |

## Security & Access Control

### File Access

| Variable              | Type | Default | Description                                |
| --------------------- | ---- | ------- | ------------------------------------------ |
| `ALLOWED_INPUT_DIRS`  | List | None    | Comma-separated allowed input directories  |
| `ALLOWED_OUTPUT_DIRS` | List | None    | Comma-separated allowed output directories |
| `RESTRICTED_PATHS`    | List | None    | Comma-separated forbidden paths            |

!!! warning "Production Security"
Always set `ALLOWED_INPUT_DIRS` and `ALLOWED_OUTPUT_DIRS` in production:
`bash
    ALLOWED_INPUT_DIRS=/secure/input,/approved/documents
    ALLOWED_OUTPUT_DIRS=/secure/output,/processed/statements
    `

### API Security

| Variable                         | Type    | Default | Description                   |
| -------------------------------- | ------- | ------- | ----------------------------- |
| `API_TIMEOUT_SECONDS`            | Integer | `60`    | API request timeout           |
| `API_RETRY_ATTEMPTS`             | Integer | `3`     | API retry attempts on failure |
| `RATE_LIMIT_REQUESTS_PER_MINUTE` | Integer | `60`    | API rate limiting             |

## Error Handling & Quarantine

### Quarantine System

| Variable                            | Type    | Default        | Description                       |
| ----------------------------------- | ------- | -------------- | --------------------------------- |
| `QUARANTINE_DIRECTORY`              | Path    | `./quarantine` | Directory for failed documents    |
| `AUTO_QUARANTINE_CRITICAL_FAILURES` | Boolean | `true`         | Auto-quarantine critical failures |
| `PRESERVE_FAILED_OUTPUTS`           | Boolean | `true`         | Keep partial outputs on failure   |
| `QUARANTINE_MAX_SIZE_GB`            | Integer | `10`           | Maximum quarantine directory size |

### Error Reporting

| Variable                    | Type    | Default           | Description                     |
| --------------------------- | ------- | ----------------- | ------------------------------- |
| `ENABLE_ERROR_REPORTING`    | Boolean | `true`            | Generate detailed error reports |
| `ERROR_REPORT_DIRECTORY`    | Path    | `./error_reports` | Error report storage location   |
| `ERROR_REPORT_MAX_AGE_DAYS` | Integer | `90`              | Maximum age for error reports   |
| `INCLUDE_STACK_TRACES`      | Boolean | `false`           | Include stack traces in reports |

### Retry Logic

| Variable                          | Type    | Default | Description                         |
| --------------------------------- | ------- | ------- | ----------------------------------- |
| `MAX_RETRY_ATTEMPTS`              | Integer | `2`     | Maximum retry attempts for failures |
| `RETRY_DELAY_SECONDS`             | Float   | `1.0`   | Delay between retry attempts        |
| `RETRY_BACKOFF_FACTOR`            | Float   | `2.0`   | Exponential backoff multiplier      |
| `CONTINUE_ON_VALIDATION_WARNINGS` | Boolean | `true`  | Continue processing on warnings     |

## Document Validation

### Pre-Processing Validation

| Variable                  | Type    | Default  | Description                                     |
| ------------------------- | ------- | -------- | ----------------------------------------------- |
| `VALIDATION_STRICTNESS`   | Choice  | `normal` | Validation level: `strict`, `normal`, `lenient` |
| `MIN_PAGES_PER_STATEMENT` | Integer | `1`      | Minimum pages required per statement            |
| `MAX_FILE_AGE_DAYS`       | Integer | `365`    | Maximum age of input files                      |
| `ALLOWED_FILE_EXTENSIONS` | List    | `.pdf`   | Allowed file extensions                         |

!!! info "Validation Strictness Levels"
    - **Strict**: All validation issues cause processing to fail
    - **Normal**: Balance between validation and processing success
    - **Lenient**: Most validation issues generate warnings only

### Content Validation

| Variable                   | Type    | Default | Description                      |
| -------------------------- | ------- | ------- | -------------------------------- |
| `REQUIRE_TEXT_CONTENT`     | Boolean | `true`  | Require extractable text content |
| `MIN_TEXT_CONTENT_RATIO`   | Float   | `0.1`   | Minimum ratio of pages with text |
| `DETECT_SCANNED_DOCUMENTS` | Boolean | `true`  | Detect image-only documents      |
| `MIN_WORDS_PER_PAGE`       | Integer | `10`    | Minimum words per page           |

### Format Validation

| Variable                   | Type    | Default | Description                        |
| -------------------------- | ------- | ------- | ---------------------------------- |
| `VALIDATE_PDF_STRUCTURE`   | Boolean | `true`  | Validate PDF file structure        |
| `ALLOW_PASSWORD_PROTECTED` | Boolean | `false` | Allow password-protected PDFs      |
| `CHECK_PDF_CORRUPTION`     | Boolean | `true`  | Check for PDF corruption           |
| `REQUIRE_PDF_VERSION`      | String  | None    | Required PDF version (e.g., "1.4") |

## Paperless-ngx Integration

### Connection Settings

| Variable                    | Type    | Default | Description                      |
| --------------------------- | ------- | ------- | -------------------------------- |
| `PAPERLESS_ENABLED`         | Boolean | `false` | Enable Paperless-ngx integration |
| `PAPERLESS_URL`             | URL     | None    | Paperless-ngx server URL         |
| `PAPERLESS_TOKEN`           | String  | None    | API authentication token         |
| `PAPERLESS_TIMEOUT_SECONDS` | Integer | `30`    | API request timeout              |

### Document Metadata

| Variable                  | Type    | Default                    | Description                              |
| ------------------------- | ------- | -------------------------- | ---------------------------------------- |
| `PAPERLESS_TAGS`          | List    | `bank-statement,automated` | Auto-applied tags                        |
| `PAPERLESS_CORRESPONDENT` | String  | `Bank`                     | Default correspondent name               |
| `PAPERLESS_DOCUMENT_TYPE` | String  | `Bank Statement`           | Document type                            |
| `PAPERLESS_STORAGE_PATH`  | String  | `Bank Statements`          | Storage path                             |
| `PAPERLESS_TAG_WAIT_TIME` | Integer | `5`                        | Wait time (seconds) before applying tags |

!!! tip "Auto-Creation"
The system automatically creates missing tags, correspondents, document types, and storage paths in Paperless-ngx.

### Input Document Processing

Configure how input documents from Paperless are tagged after successful processing:

| Variable                                 | Type    | Default | Description                                    |
| ---------------------------------------- | ------- | ------- | ---------------------------------------------- |
| `PAPERLESS_INPUT_TAGGING_ENABLED`        | Boolean | `true`  | Enable input document tagging after processing |
| `PAPERLESS_INPUT_PROCESSED_TAG`          | String  | None    | Tag to add to input documents after processing |
| `PAPERLESS_INPUT_REMOVE_UNPROCESSED_TAG` | Boolean | `false` | Remove 'unprocessed' tag after processing      |
| `PAPERLESS_INPUT_PROCESSING_TAG`         | String  | None    | Custom tag to mark documents as processed      |

!!! info "Input Document Tagging Options"
When processing documents that originate from Paperless (using `source_document_id`), configure **one** of these options:

    1. **Add processed tag**: `PAPERLESS_INPUT_PROCESSED_TAG=processed`
    2. **Remove unprocessed tag**: `PAPERLESS_INPUT_REMOVE_UNPROCESSED_TAG=true`
    3. **Use custom tag**: `PAPERLESS_INPUT_PROCESSING_TAG=bank-statement-processed`

    Input document tagging only occurs after successful output document processing and upload. This prevents re-processing of documents that have already been handled.

### Error Detection and Tagging

Configure automatic error detection and tagging for documents with processing issues:

| Variable                            | Type    | Default                | Description                                       |
| ----------------------------------- | ------- | ---------------------- | ------------------------------------------------- |
| `PAPERLESS_ERROR_DETECTION_ENABLED` | Boolean | `false`                | Enable automatic error detection and tagging      |
| `PAPERLESS_ERROR_TAGS`              | List    | None                   | Tags to apply to documents with processing errors |
| `PAPERLESS_ERROR_TAG_THRESHOLD`     | Float   | `0.5`                  | Error severity threshold (0.0-1.0) for tagging    |
| `PAPERLESS_ERROR_SEVERITY_LEVELS`   | List    | `medium,high,critical` | Severity levels that trigger tagging              |
| `PAPERLESS_ERROR_BATCH_TAGGING`     | Boolean | `false`                | Use batch tagging (true) vs individual requests   |

!!! info "Error Detection System"
The error detection system identifies 6 types of processing errors:

    - **LLM Analysis Failures**: AI model errors or timeouts
    - **Low Confidence Boundaries**: Statement detection with low confidence
    - **PDF Processing Errors**: PDF generation or manipulation failures
    - **Metadata Extraction Issues**: Failed to extract bank names, dates, accounts
    - **File Output Problems**: Generated files missing or corrupted
    - **Validation Failures**: Output validation checks failed

    Only errors above the configured threshold and matching severity levels trigger automatic tagging.

!!! example "Error Tagging Configuration"

```bash # Basic error tagging setup
PAPERLESS_ERROR_DETECTION_ENABLED=true
PAPERLESS_ERROR_TAGS=processing:needs-review,error:automated-detection
PAPERLESS_ERROR_TAG_THRESHOLD=0.7
PAPERLESS_ERROR_SEVERITY_LEVELS=high,critical

    # Development/testing with comprehensive error detection
    PAPERLESS_ERROR_DETECTION_ENABLED=true
    PAPERLESS_ERROR_TAGS=test:error-detection,test:automated-tagging
    PAPERLESS_ERROR_TAG_THRESHOLD=0.0
    PAPERLESS_ERROR_SEVERITY_LEVELS=low,medium,high,critical
    ```

### Upload Behavior

| Variable                        | Type    | Default | Description                     |
| ------------------------------- | ------- | ------- | ------------------------------- |
| `PAPERLESS_AUTO_UPLOAD`         | Boolean | `true`  | Auto-upload after processing    |
| `PAPERLESS_DELETE_AFTER_UPLOAD` | Boolean | `false` | Delete local files after upload |
| `PAPERLESS_RETRY_UPLOADS`       | Boolean | `true`  | Retry failed uploads            |
| `PAPERLESS_BATCH_SIZE`          | Integer | `5`     | Maximum documents per batch     |

## Logging & Monitoring

### Log Configuration

| Variable           | Type    | Default                           | Description                                        |
| ------------------ | ------- | --------------------------------- | -------------------------------------------------- |
| `LOG_LEVEL`        | Choice  | `INFO`                            | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE`         | Path    | `./logs/statement_processing.log` | Main log file location                             |
| `LOG_MAX_SIZE_MB`  | Integer | `10`                              | Maximum log file size                              |
| `LOG_BACKUP_COUNT` | Integer | `5`                               | Number of backup log files                         |

### Audit Logging

| Variable               | Type    | Default            | Description                      |
| ---------------------- | ------- | ------------------ | -------------------------------- |
| `ENABLE_AUDIT_LOGGING` | Boolean | `true`             | Enable security audit logging    |
| `AUDIT_LOG_FILE`       | Path    | `./logs/audit.log` | Audit log file location          |
| `AUDIT_LOG_LEVEL`      | Choice  | `INFO`             | Audit log level                  |
| `LOG_API_CALLS`        | Boolean | `true`             | Log all API calls for monitoring |

### Performance Monitoring

| Variable                        | Type    | Default                  | Description                |
| ------------------------------- | ------- | ------------------------ | -------------------------- |
| `ENABLE_PERFORMANCE_MONITORING` | Boolean | `true`                   | Enable performance metrics |
| `LOG_PROCESSING_TIMES`          | Boolean | `true`                   | Log processing duration    |
| `LOG_MEMORY_USAGE`              | Boolean | `false`                  | Log memory consumption     |
| `PERFORMANCE_LOG_FILE`          | Path    | `./logs/performance.log` | Performance metrics log    |

## Development & Testing

### Development Mode

| Variable                      | Type    | Default   | Description                        |
| ----------------------------- | ------- | --------- | ---------------------------------- |
| `DEVELOPMENT_MODE`            | Boolean | `false`   | Enable development features        |
| `DEBUG_OUTPUT_DIR`            | Path    | `./debug` | Debug output directory             |
| `PRESERVE_INTERMEDIATE_FILES` | Boolean | `false`   | Keep intermediate processing files |
| `ENABLE_PROFILING`            | Boolean | `false`   | Enable performance profiling       |

### Testing Configuration

| Variable                | Type    | Default        | Description               |
| ----------------------- | ------- | -------------- | ------------------------- |
| `TEST_MODE`             | Boolean | `false`        | Enable test mode features |
| `MOCK_API_RESPONSES`    | Boolean | `false`        | Use mock API responses    |
| `TEST_DATA_DIR`         | Path    | `./test/input` | Test data directory       |
| `GENERATE_TEST_REPORTS` | Boolean | `false`        | Generate test reports     |

## Configuration Validation

### Variable Types

Variables are automatically validated based on their type:

=== "Boolean Variables"
Accept: `true`, `false`, `1`, `0`, `yes`, `no` (case-insensitive)
`bash
    ENABLE_AUDIT_LOGGING=true
    PAPERLESS_ENABLED=false
    `

=== "Integer Variables"
Must be valid integers within allowed ranges:
`bash
    MAX_FILE_SIZE_MB=100
    CHUNK_SIZE=6000
    `

=== "Float Variables"
Must be valid floating-point numbers:
`bash
    LLM_TEMPERATURE=0.1
    MIN_TEXT_CONTENT_RATIO=0.15
    `

=== "Path Variables"
Validated as file system paths:
`bash
    DEFAULT_OUTPUT_DIR=./separated_statements
    LOG_FILE=/var/log/processing.log
    `

=== "List Variables"
Comma-separated values:
`bash
    PAPERLESS_TAGS=bank-statement,automated,monthly
    ALLOWED_INPUT_DIRS=/secure/input,/approved/docs
    `

=== "Choice Variables"
Must match predefined options:
`bash
    LLM_MODEL=gpt-4o-mini  # or gpt-4o, gpt-3.5-turbo
    VALIDATION_STRICTNESS=normal  # or strict, lenient
    `

## Environment-Specific Configurations

### Development Environment

```bash
# .env.development
OPENAI_API_KEY=sk-dev-key
LOG_LEVEL=DEBUG
VALIDATION_STRICTNESS=lenient
PRESERVE_FAILED_OUTPUTS=true
DEVELOPMENT_MODE=true
ENABLE_PROFILING=true
MAX_RETRY_ATTEMPTS=1
```

### Testing Environment

```bash
# .env.testing
OPENAI_API_KEY=""  # Test fallback mode
LOG_LEVEL=WARNING
TEST_MODE=true
MOCK_API_RESPONSES=true
QUARANTINE_DIRECTORY=./test/quarantine
DEFAULT_OUTPUT_DIR=./test/output
```

### Production Environment

```bash
# .env.production
OPENAI_API_KEY=sk-prod-key
LOG_LEVEL=INFO
VALIDATION_STRICTNESS=strict
ENABLE_AUDIT_LOGGING=true
MAX_FILE_SIZE_MB=200

# Security
ALLOWED_INPUT_DIRS=/secure/input,/approved/documents
ALLOWED_OUTPUT_DIRS=/secure/output,/processed/statements
QUARANTINE_DIRECTORY=/secure/quarantine

# Paperless integration
PAPERLESS_ENABLED=true
PAPERLESS_URL=https://paperless.company.com
PAPERLESS_TOKEN=prod-api-token

# Input document processing tracking
PAPERLESS_INPUT_TAGGING_ENABLED=true
PAPERLESS_INPUT_PROCESSED_TAG=processed

# Error detection and tagging
PAPERLESS_ERROR_DETECTION_ENABLED=true
PAPERLESS_ERROR_TAGS=processing:needs-review,error:automated-detection
PAPERLESS_ERROR_TAG_THRESHOLD=0.7
PAPERLESS_ERROR_SEVERITY_LEVELS=high,critical
```

## Configuration Validation

Test your configuration:

```bash
# Validate all variables
uv run python -c "
from src.bank_statement_separator.config import load_config
try:
    config = load_config()
    print('✅ Configuration valid')
    print(f'Model: {config.llm_model}')
    print(f'Output: {config.default_output_dir}')
    print(f'Validation: {config.validation_strictness}')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"

# Check specific variable
uv run python -c "
import os
print(f'OPENAI_API_KEY: {"Set" if os.getenv("OPENAI_API_KEY") else "Not set"}')
print(f'LOG_LEVEL: {os.getenv("LOG_LEVEL", "Not set")}')
print(f'VALIDATION_STRICTNESS: {os.getenv("VALIDATION_STRICTNESS", "Not set")}')
"
```

## Common Configuration Issues

=== "Invalid Values"

````bash # ❌ Invalid
LLM_TEMPERATURE=2.0 # Must be 0-1
MAX_FILE_SIZE_MB=abc # Must be integer
VALIDATION_STRICTNESS=medium # Must be strict/normal/lenient

    # ✅ Valid
    LLM_TEMPERATURE=0.1
    MAX_FILE_SIZE_MB=100
    VALIDATION_STRICTNESS=normal
    ```

=== "Path Issues"
```bash # ❌ Problematic
DEFAULT_OUTPUT_DIR=~/output # Tilde expansion issues
QUARANTINE_DIRECTORY=output # Relative path confusion

    # ✅ Better
    DEFAULT_OUTPUT_DIR=/home/user/output  # Absolute path
    QUARANTINE_DIRECTORY=./quarantine  # Explicit relative path
    ```

=== "Security Misconfigurations"
```bash # ❌ Insecure
ALLOWED_INPUT_DIRS="" # No restrictions
LOG_LEVEL=DEBUG # Too verbose for production

    # ✅ Secure
    ALLOWED_INPUT_DIRS=/secure/input
    LOG_LEVEL=INFO
    ```

## Configuration Best Practices

### Security

1. **Never commit `.env` files** to version control
2. **Use environment-specific configs** (`.env.production`, `.env.development`)
3. **Restrict file access** in production with `ALLOWED_*_DIRS`
4. **Use strong API keys** and rotate them regularly

### Performance

1. **Tune chunk sizes** for your document types
2. **Set appropriate file size limits** based on your hardware
3. **Configure retry settings** for your network reliability
4. **Enable performance monitoring** in production

### Reliability

1. **Set up log rotation** to prevent disk space issues
2. **Configure quarantine cleanup** to manage storage
3. **Enable error reporting** for troubleshooting
4. **Use strict validation** for critical applications

### Monitoring

1. **Enable audit logging** for compliance
2. **Set up log monitoring** and alerting
3. **Configure performance metrics** collection
4. **Monitor API usage** and costs
````

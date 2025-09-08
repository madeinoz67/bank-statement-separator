# Configuration Guide

Complete guide to configuring the Workflow Bank Statement Separator for your environment.

## Configuration Overview

The system uses environment variables for configuration, managed through a `.env` file. With 40+ configuration options, you can customize every aspect of the processing pipeline.

!!! tip "Configuration Template"
    Copy `.env.example` to `.env` to get started with default values and comprehensive documentation for all options.

## Core Configuration

### Required Variables

```bash
# LLM Provider Selection
LLM_PROVIDER=openai                  # openai, ollama, auto

# OpenAI Configuration (if using openai provider)
OPENAI_API_KEY=sk-your-api-key-here  # Optional - fallback available
```

!!! info "Flexible LLM Support"
    The system supports multiple LLM providers:
    - **OpenAI**: Cloud-based AI with high accuracy (~95%)
    - **Ollama**: Local AI processing for privacy and cost savings
    - **Fallback**: Pattern-matching without AI (~85% accuracy)
    
    No API key required when using Ollama or fallback mode.

### Essential Settings

```bash
# LLM Provider Settings
LLM_PROVIDER=openai                      # Provider selection
OPENAI_MODEL=gpt-4o-mini                # OpenAI model selection
LLM_TEMPERATURE=0                        # Deterministic output

# Processing Settings  
DEFAULT_OUTPUT_DIR=./separated_statements # Output location
LOG_LEVEL=INFO                          # Logging verbosity

# Security
MAX_FILE_SIZE_MB=100                    # File size limit
ENABLE_AUDIT_LOGGING=true               # Compliance logging
```

## Complete Configuration Reference

### LLM Provider Configuration

The system supports multiple LLM providers through a flexible abstraction layer:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openai` | Provider: `openai`, `ollama`, `auto` |
| `LLM_FALLBACK_ENABLED` | `true` | Enable fallback to pattern matching |
| `LLM_TEMPERATURE` | `0` | Model creativity (0-1) |
| `LLM_MAX_TOKENS` | `4000` | Maximum tokens per API call |

#### OpenAI Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | None | OpenAI API key for AI analysis |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model: `gpt-4o-mini`, `gpt-4o`, `gpt-3.5-turbo` |

#### Ollama Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Local model name |

!!! info "Provider Selection"
    - **openai**: Use OpenAI cloud models (requires API key)
    - **ollama**: Use local Ollama models (privacy-focused, no API costs)
    - **auto**: Automatically select best available provider

!!! tip "Model Selection"
    - `gpt-4o-mini`: Best balance of cost and performance (recommended)
    - `gpt-4o`: Highest accuracy, higher cost
    - `gpt-3.5-turbo`: Fastest, lower accuracy

### Processing Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CHUNK_SIZE` | `6000` | Text chunk size for processing |
| `CHUNK_OVERLAP` | `800` | Overlap between text chunks |
| `MAX_FILENAME_LENGTH` | `240` | Maximum filename length |
| `DEFAULT_OUTPUT_DIR` | `./separated_statements` | Default output directory |
| `PROCESSED_INPUT_DIR` | Auto-generated | Processed file storage |

### File Processing Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_FILE_SIZE_MB` | `100` | Maximum input file size |
| `MAX_PAGES_PER_STATEMENT` | `50` | Pages per statement limit |
| `MAX_TOTAL_PAGES` | `500` | Total pages limit |
| `INCLUDE_BANK_IN_FILENAME` | `true` | Include bank name in output |
| `DATE_FORMAT` | `YYYY-MM` | Date format for filenames |

### Security & Access Control

| Variable | Default | Description |
|----------|---------|-------------|
| `ALLOWED_INPUT_DIRS` | None | Comma-separated allowed input directories |
| `ALLOWED_OUTPUT_DIRS` | None | Comma-separated allowed output directories |
| `ENABLE_AUDIT_LOGGING` | `true` | Enable security audit logging |

!!! warning "Production Security"
    For production deployments, always set `ALLOWED_INPUT_DIRS` and `ALLOWED_OUTPUT_DIRS` to restrict file access to specific secure directories.

## Error Handling Configuration

### Quarantine System

| Variable | Default | Description |
|----------|---------|-------------|
| `QUARANTINE_DIRECTORY` | `./quarantine` | Failed document storage |
| `AUTO_QUARANTINE_CRITICAL_FAILURES` | `true` | Auto-quarantine critical failures |
| `PRESERVE_FAILED_OUTPUTS` | `true` | Keep partial outputs on failure |
| `MAX_RETRY_ATTEMPTS` | `2` | Retry count for transient failures |

### Error Reporting

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ERROR_REPORTING` | `true` | Generate detailed error reports |
| `ERROR_REPORT_DIRECTORY` | `./error_reports` | Error report storage |
| `CONTINUE_ON_VALIDATION_WARNINGS` | `true` | Continue processing on warnings |

### Validation Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `VALIDATION_STRICTNESS` | `normal` | Validation level: `strict`, `normal`, `lenient` |
| `MIN_PAGES_PER_STATEMENT` | `1` | Minimum pages per statement |
| `MAX_FILE_AGE_DAYS` | `365` | Maximum file age in days |
| `ALLOWED_FILE_EXTENSIONS` | `.pdf` | Allowed file extensions |
| `REQUIRE_TEXT_CONTENT` | `true` | Require extractable text |
| `MIN_TEXT_CONTENT_RATIO` | `0.1` | Minimum text content ratio |

!!! info "Validation Strictness Levels"
    - **Strict**: All validation issues are errors (highest accuracy)
    - **Normal**: Balanced approach with warnings (recommended)
    - **Lenient**: Most issues are warnings (highest processing success rate)

## Paperless-ngx Integration

### Connection Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `PAPERLESS_ENABLED` | `false` | Enable paperless integration |
| `PAPERLESS_URL` | None | Paperless-ngx server URL |
| `PAPERLESS_TOKEN` | None | API authentication token |

### Document Management

| Variable | Default | Description |
|----------|---------|-------------|
| `PAPERLESS_TAGS` | `bank-statement,automated` | Auto-applied tags |
| `PAPERLESS_CORRESPONDENT` | `Bank` | Default correspondent |
| `PAPERLESS_DOCUMENT_TYPE` | `Bank Statement` | Document type |
| `PAPERLESS_STORAGE_PATH` | `Bank Statements` | Storage path |

!!! tip "Auto-Creation"
    The system automatically creates tags, correspondents, document types, and storage paths in Paperless if they don't exist.

## Logging Configuration

### Log Levels

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE` | `./logs/statement_processing.log` | Log file location |

### Audit Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_AUDIT_LOGGING` | `true` | Enable compliance logging |
| `AUDIT_LOG_FILE` | `./logs/audit.log` | Audit log location |

## Environment-Specific Configurations

### Development Environment

```bash
# .env for development
OPENAI_API_KEY=sk-your-dev-key
LLM_MODEL=gpt-4o-mini
LOG_LEVEL=DEBUG
VALIDATION_STRICTNESS=lenient
PRESERVE_FAILED_OUTPUTS=true
MAX_RETRY_ATTEMPTS=1
ENABLE_ERROR_REPORTING=true
```

### Testing Environment

```bash
# .env for testing
OPENAI_API_KEY=""  # Test fallback mode
LLM_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
VALIDATION_STRICTNESS=normal
DEFAULT_OUTPUT_DIR=./test/output
QUARANTINE_DIRECTORY=./test/quarantine
```

### Production Environment

```bash
# .env for production
OPENAI_API_KEY=sk-your-prod-key
LLM_MODEL=gpt-4o-mini
LOG_LEVEL=INFO
VALIDATION_STRICTNESS=strict
ENABLE_AUDIT_LOGGING=true
MAX_FILE_SIZE_MB=200

# Security restrictions
ALLOWED_INPUT_DIRS=/secure/input,/approved/documents
ALLOWED_OUTPUT_DIRS=/secure/output,/processed/statements
QUARANTINE_DIRECTORY=/secure/quarantine

# Paperless integration
PAPERLESS_ENABLED=true
PAPERLESS_URL=https://paperless.yourcompany.com
PAPERLESS_TOKEN=your-production-token
```

## Configuration Validation

Test your configuration:

```bash
# Validate configuration loading
uv run python -c "
from src.bank_statement_separator.config import load_config
config = load_config()
print('✅ Configuration loaded successfully')
print(f'Model: {config.llm_model}')
print(f'Output Dir: {config.default_output_dir}')
print(f'Validation: {config.validation_strictness}')
"

# Test API key (if configured)
uv run python -c "
import openai
from src.bank_statement_separator.config import load_config
config = load_config()
if config.openai_api_key:
    client = openai.Client(api_key=config.openai_api_key)
    models = client.models.list()
    print('✅ OpenAI API key valid')
else:
    print('ℹ️ No API key configured (fallback mode)')
"
```

## Dynamic Configuration

### Command-Line Overrides

Override configuration via command-line:

```bash
# Override output directory
uv run python -m src.bank_statement_separator.main \
  process input.pdf --output /custom/output

# Override model
uv run python -m src.bank_statement_separator.main \
  process input.pdf --model gpt-4o

# Override env file location
uv run python -m src.bank_statement_separator.main \
  process input.pdf --env-file /path/to/custom.env
```

## Environment File Management

The `--env-file` parameter enables easy switching between different environment configurations without modifying your main `.env` file.

### Creating Environment-Specific Files

Create dedicated environment files for different scenarios:

```bash
# Create environment-specific configs
cp .env.example .env.dev      # Development settings
cp .env.example .env.test     # Testing settings  
cp .env.example .env.prod     # Production settings
```

### Environment File Usage Examples

=== "Development Environment"

    Create `.env.dev` with development-optimized settings:
    
    ```bash
    # .env.dev - Development Configuration
    LLM_PROVIDER=openai
    OPENAI_API_KEY=sk-your-dev-key-here
    OPENAI_MODEL=gpt-4o-mini
    LOG_LEVEL=DEBUG
    DEFAULT_OUTPUT_DIR=./dev_output
    VALIDATION_STRICTNESS=lenient
    PRESERVE_FAILED_OUTPUTS=true
    ENABLE_ERROR_REPORTING=true
    MAX_RETRY_ATTEMPTS=1
    ```
    
    Use the development environment:
    ```bash
    uv run python -m src.bank_statement_separator.main \
      process input.pdf --env-file .env.dev
    ```

=== "Testing Environment"

    Create `.env.test` for testing with fallback mode:
    
    ```bash
    # .env.test - Testing Configuration
    LLM_PROVIDER=auto
    OPENAI_API_KEY=invalid-key-for-testing
    OPENAI_MODEL=gpt-4o-mini
    LOG_LEVEL=ERROR
    DEFAULT_OUTPUT_DIR=./test_output
    VALIDATION_STRICTNESS=normal
    MAX_FILE_SIZE_MB=10
    QUARANTINE_DIRECTORY=./test_quarantine
    ENABLE_FALLBACK_PROCESSING=true
    ```
    
    Run tests with testing environment:
    ```bash
    uv run python -m src.bank_statement_separator.main \
      process test.pdf --env-file .env.test --dry-run
    ```

=== "Production Environment"

    Create `.env.prod` for production deployment:
    
    ```bash
    # .env.prod - Production Configuration
    LLM_PROVIDER=openai
    OPENAI_API_KEY=sk-your-production-key
    OPENAI_MODEL=gpt-4o
    LOG_LEVEL=WARNING
    DEFAULT_OUTPUT_DIR=/var/app/output
    VALIDATION_STRICTNESS=strict
    MAX_FILE_SIZE_MB=200
    
    # Security restrictions
    ALLOWED_INPUT_DIRS=/secure/input,/approved/documents
    ALLOWED_OUTPUT_DIRS=/secure/output,/processed/statements
    QUARANTINE_DIRECTORY=/secure/quarantine
    
    # Paperless integration
    PAPERLESS_ENABLED=true
    PAPERLESS_URL=https://paperless.company.com
    PAPERLESS_TOKEN=prod-token-here
    ```
    
    Deploy with production settings:
    ```bash
    uv run python -m src.bank_statement_separator.main \
      batch_process /secure/input --env-file .env.prod
    ```

### Advanced Environment Patterns

#### Team Collaboration

Each team member maintains their own environment file:

```bash
# Personal environment files
.env.alice    # Alice's development setup
.env.bob      # Bob's development setup
.env.shared   # Shared team defaults

# Usage
uv run python -m src.bank_statement_separator.main \
  process input.pdf --env-file .env.alice
```

#### CI/CD Integration

Use environment files in automated pipelines:

```bash
# GitHub Actions example
- name: Run processing with CI config
  run: |
    uv run python -m src.bank_statement_separator.main \
      process test.pdf --env-file .env.ci --dry-run
```

#### Deployment-Specific Configuration

```bash
# Different deployment targets
.env.staging     # Staging environment
.env.production  # Production environment
.env.dr          # Disaster recovery site

# Deployment
uv run python -m src.bank_statement_separator.main \
  process input.pdf --env-file .env.staging
```

### Environment File Validation

The system validates environment files before loading:

```bash
# Test environment file validity
uv run python -c "
from src.bank_statement_separator.config import load_config, validate_env_file

# Validate file exists and is readable
validate_env_file('.env.dev')
print('✅ Environment file is valid')

# Test configuration loading
config = load_config('.env.dev')
print(f'✅ Configuration loaded successfully')
print(f'Provider: {config.llm_provider}')
print(f'Model: {config.openai_model}')
print(f'Output: {config.default_output_dir}')
"
```

### Error Handling

Common environment file issues and solutions:

=== "File Not Found"

    ```bash
    # Error: Environment file not found: /path/to/.env.missing
    
    # Solution: Check file path and permissions
    ls -la .env.*
    ls -la /path/to/.env.missing
    ```

=== "Permission Denied"

    ```bash
    # Error: Cannot read environment file: .env.locked
    
    # Solution: Fix file permissions
    chmod 644 .env.locked
    ```

=== "Invalid Configuration"

    ```bash
    # Error: Log level must be one of: ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    
    # Solution: Fix invalid values in env file
    sed -i 's/LOG_LEVEL=INVALID/LOG_LEVEL=INFO/' .env.test
    ```

!!! tip "Environment File Best Practices"
    - **Never commit** `.env` files containing secrets to version control
    - **Use descriptive names** like `.env.dev`, `.env.prod` instead of generic names
    - **Document required variables** in each environment file header
    - **Test configurations** before deploying to production
    - **Use relative paths** where possible for portability
    - **Validate configurations** after changes using the validation script above

!!! warning "Security Considerations"
    - Production env files should be stored securely and access-controlled
    - Use different API keys for different environments
    - Set appropriate file permissions (644 or 600)
    - Never expose production credentials in development/test environments

### Environment Variable Precedence

Configuration precedence (highest to lowest):

1. Command-line arguments
2. Environment variables
3. `.env` file values
4. Default values in code

## Configuration Best Practices

### Security

```bash
# Never commit .env files
echo ".env" >> .gitignore

# Use different configs per environment
cp .env.example .env.development
cp .env.example .env.production

# Restrict file access in production
ALLOWED_INPUT_DIRS=/secure/input
ALLOWED_OUTPUT_DIRS=/secure/output
```

### Performance

```bash
# Optimize for large files
MAX_FILE_SIZE_MB=500
CHUNK_SIZE=8000
CHUNK_OVERLAP=1000

# Balance accuracy vs speed
LLM_MODEL=gpt-4o-mini      # Fast
LLM_TEMPERATURE=0          # Consistent
VALIDATION_STRICTNESS=normal  # Balanced
```

### Monitoring

```bash
# Enable comprehensive logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true
ENABLE_ERROR_REPORTING=true

# Set up log rotation
LOG_FILE=/var/log/bank-separator/processing.log
AUDIT_LOG_FILE=/var/log/bank-separator/audit.log
```

## Configuration Templates

### High-Accuracy Setup

```bash
# For maximum processing accuracy
OPENAI_API_KEY=sk-your-key
LLM_MODEL=gpt-4o
LLM_TEMPERATURE=0
VALIDATION_STRICTNESS=strict
MAX_RETRY_ATTEMPTS=3
ENABLE_FALLBACK_PROCESSING=false
```

### High-Throughput Setup

```bash
# For maximum processing speed
LLM_MODEL=gpt-4o-mini
VALIDATION_STRICTNESS=lenient
MAX_RETRY_ATTEMPTS=1
CHUNK_SIZE=8000
CONTINUE_ON_VALIDATION_WARNINGS=true
```

### Budget-Conscious Setup

```bash
# Minimize API costs
OPENAI_API_KEY=""  # Use fallback only
ENABLE_FALLBACK_PROCESSING=true
VALIDATION_STRICTNESS=lenient
MAX_RETRY_ATTEMPTS=1
```

## Troubleshooting Configuration

### Common Issues

=== "Configuration Not Loading"

    ```bash
    # Check file exists and is readable
    ls -la .env
    
    # Verify file format (no spaces around =)
    cat .env | grep -E '^[^#]*='
    
    # Test manual loading
    uv run python -c "
    from dotenv import load_dotenv
    load_dotenv('.env')
    import os
    print(os.getenv('OPENAI_API_KEY', 'Not set'))
    "
    ```

=== "API Key Issues"

    ```bash
    # Test API key validity
    curl -H "Authorization: Bearer $OPENAI_API_KEY" \
         https://api.openai.com/v1/models
    
    # Check quota
    curl -H "Authorization: Bearer $OPENAI_API_KEY" \
         https://api.openai.com/v1/usage
    ```

=== "Path Issues"

    ```bash
    # Check directory permissions
    ls -la $(dirname "$DEFAULT_OUTPUT_DIR")
    
    # Test directory creation
    mkdir -p "$DEFAULT_OUTPUT_DIR" && echo "✅ Can create output dir"
    
    # Verify path restrictions
    echo "Allowed input: $ALLOWED_INPUT_DIRS"
    echo "Allowed output: $ALLOWED_OUTPUT_DIRS"
    ```

## Next Steps

After configuring your system:

1. **Test your setup**: Run the [Quick Start Guide](quick-start.md)
2. **Learn CLI usage**: Review [CLI Commands](../reference/cli-commands.md)
3. **Set up integrations**: Configure [Paperless Integration](../user-guide/paperless-integration.md)
4. **Handle errors**: Understand [Error Handling](../user-guide/error-handling.md)
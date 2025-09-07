# CLI Commands Reference

Complete reference for all command-line interface commands and options.

## Command Overview

The Workflow Bank Statement Separator provides a multi-command CLI interface:

```bash
uv run bank-statement-separator [COMMAND] [OPTIONS]
```

### Available Commands

- **`process`** - Process PDF files containing multiple bank statements
- **`batch-process`** - Process multiple PDF files from a directory
- **`quarantine-status`** - View quarantine directory status and recent failures
- **`quarantine-clean`** - Clean old files from quarantine directory

## Process Command

Process a PDF file containing multiple bank statements.

### Syntax

```bash
uv run bank-statement-separator process [INPUT_FILE] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `INPUT_FILE` | Path to PDF file to process | Yes |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output` | `-o` | PATH | `./separated_statements` | Output directory for separated statements |
| `--env-file` | | PATH | `.env` | Path to .env configuration file |
| `--model` | | CHOICE | `gpt-4o-mini` | LLM model to use |
| `--verbose` | `-v` | FLAG | | Enable verbose logging |
| `--dry-run` | | FLAG | | Analyze document without creating output files |
| `--yes` | `-y` | FLAG | | Skip confirmation prompts |
| `--help` | | FLAG | | Show help message |

### Model Choices

| Model | Speed | Accuracy | Cost | Best For |
|-------|-------|----------|------|----------|
| `gpt-4o-mini` | Fast | High | Low | General use (recommended) |
| `gpt-4o` | Medium | Highest | High | Maximum accuracy |
| `gpt-3.5-turbo` | Fastest | Medium | Lowest | High-volume processing |

### Examples

=== "Basic Usage"

    ```bash
    # Process with defaults
    uv run python -m src.bank_statement_separator.main \
      process statements.pdf
    
    # Custom output directory
    uv run python -m src.bank_statement_separator.main \
      process statements.pdf --output ./my-statements
    
    # Skip confirmations (useful for automation)
    uv run python -m src.bank_statement_separator.main \
      process statements.pdf --yes
    ```

=== "Advanced Options"

    ```bash
    # Use specific model with verbose output
    uv run python -m src.bank_statement_separator.main \
      process statements.pdf --model gpt-4o --verbose
    
    # Dry-run analysis (no files created)
    uv run python -m src.bank_statement_separator.main \
      process statements.pdf --dry-run --yes
    
    # Custom configuration file
    uv run python -m src.bank_statement_separator.main \
      process statements.pdf --env-file /path/to/custom.env
    ```

=== "Production Usage"

    ```bash
    # Production processing with logging
    uv run python -m src.bank_statement_separator.main \
      process /secure/input/statements.pdf \
      --output /secure/output \
      --model gpt-4o-mini \
      --verbose \
      --yes \
      2>&1 | tee /var/log/processing.log
    ```

### Output Examples

#### Successful Processing

```
🔄 Processing PDF file: statements.pdf
📊 Document Analysis: 12 pages detected
🤖 AI Analysis: Using gpt-4o-mini model
✅ Statements detected: 2

📊 Processing Results
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric                ┃ Value  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Total Pages Processed │ 12     │
│ Statements Detected   │ 2      │
│ Processing Time       │ 3.45s  │
│ Status               │ success │
└───────────────────────┴────────┘

📋 Detected Statements:
┏━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ # ┃ Pages  ┃ Account       ┃ Period     ┃ Bank           ┃
┡━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ 1 │ 1-6    │ ****2819      │ 2015-05    │ Westpac        │
│ 2 │ 7-12   │ ****2819      │ 2015-04    │ Westpac        │
└───┴────────┴───────────────┴────────────┴────────────────┘

✅ Successfully created 2 statement files:
   📄 westpac-2819-2015-05-21.pdf
   📄 westpac-2819-2015-04-20.pdf

📁 Processed input file moved to: input/processed/statements.pdf
```

#### Dry-Run Analysis

```
🔍 DRY RUN MODE - No files will be created
🔄 Analyzing PDF file: statements.pdf

📊 Analysis Results
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric                ┃ Value  ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Total Pages           │ 12     │
│ Statements Detected   │ 2      │
│ Analysis Time         │ 1.23s  │
│ Would Create Files    │ 2      │
└───────────────────────┴────────┘

ℹ️ Run without --dry-run to create separated statement files
```

## Batch Process Command

Process multiple PDF files from a directory in a single operation.

### Syntax

```bash
uv run bank-statement-separator batch-process [INPUT_DIRECTORY] [OPTIONS]
```

### Arguments

| Argument | Description | Required |
|----------|-------------|----------|
| `INPUT_DIRECTORY` | Directory containing PDF files to process | Yes |

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--output` | `-o` | PATH | `./separated_statements` | Output directory for separated statements |
| `--pattern` | | STRING | `*.pdf` | File pattern to match (glob syntax) |
| `--exclude` | | STRING | | Pattern to exclude from processing |
| `--max-files` | | INTEGER | | Maximum number of files to process |
| `--env-file` | | PATH | `.env` | Path to .env configuration file |
| `--model` | | CHOICE | `gpt-4o-mini` | LLM model to use |
| `--verbose` | `-v` | FLAG | | Enable verbose logging |
| `--dry-run` | | FLAG | | Analyze documents without creating output files |
| `--yes` | `-y` | FLAG | | Skip confirmation prompts |
| `--help` | | FLAG | | Show help message |

### Key Features

- **Sequential Processing**: Files are processed one by one to avoid system overload
- **Error Isolation**: Failed files are quarantined without stopping the batch
- **Progress Tracking**: Real-time progress display during processing
- **Comprehensive Summary**: Detailed batch results with success/failure metrics
- **Validation Gate**: All outputs validated before Paperless upload

### Examples

=== "Basic Batch Processing"

    ```bash
    # Process all PDFs in a directory
    uv run python -m src.bank_statement_separator.main \
      batch-process /path/to/pdfs
    
    # Custom output directory
    uv run python -m src.bank_statement_separator.main \
      batch-process /path/to/pdfs --output ./batch-output
    
    # Skip confirmations for automation
    uv run python -m src.bank_statement_separator.main \
      batch-process /path/to/pdfs --yes
    ```

=== "Filtered Processing"

    ```bash
    # Process only files matching pattern
    uv run python -m src.bank_statement_separator.main \
      batch-process /path/to/pdfs --pattern "*2024*.pdf"
    
    # Exclude specific patterns
    uv run python -m src.bank_statement_separator.main \
      batch-process /path/to/pdfs --exclude "*draft*"
    
    # Limit number of files
    uv run python -m src.bank_statement_separator.main \
      batch-process /path/to/pdfs --max-files 10
    ```

=== "Production Usage"

    ```bash
    # Production batch processing with logging
    uv run python -m src.bank_statement_separator.main \
      batch-process /secure/input \
      --output /secure/output \
      --pattern "*.pdf" \
      --exclude "*test*" \
      --model gpt-4o-mini \
      --verbose \
      --yes \
      2>&1 | tee /var/log/batch-processing.log
    
    # Dry-run to preview batch
    uv run python -m src.bank_statement_separator.main \
      batch-process /secure/input \
      --dry-run \
      --yes
    ```

### Output Examples

#### Successful Batch Processing

```
🔍 Discovering files in: /path/to/pdfs
📄 Found 5 file(s) to process
  • statement_jan_2024.pdf
  • statement_feb_2024.pdf
  • statement_mar_2024.pdf
  • statement_apr_2024.pdf
  • statement_may_2024.pdf

🚀 Starting batch processing...

  Processing statement_jan_2024.pdf (1/5)
  Processing statement_feb_2024.pdf (2/5)
  Processing statement_mar_2024.pdf (3/5)
  Processing statement_apr_2024.pdf (4/5)
  Processing statement_may_2024.pdf (5/5)

📊 Batch Processing Summary Results
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┓
┃ Metric                ┃ Count ┃ Percentage ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━┩
│ Total Files           │     5 │       100% │
│ Processed             │     5 │     100.0% │
│ Successful            │     4 │      80.0% │
│ Quarantined           │     1 │      20.0% │
│ Uploaded to Paperless │    12 │            │
│ Processing Time       │ 15.3s │            │
└───────────────────────┴───────┴────────────┘

✅ Successfully processed 4 files
⚠️ 1 file(s) quarantined - check error reports
📁 Output files saved to configured directories
```

#### Batch with Errors

```
🔍 Discovering files in: /path/to/pdfs
📄 Found 3 file(s) to process

🚀 Starting batch processing...

  Processing corrupted.pdf (1/3)
  ⚠️ Error processing corrupted.pdf - moved to quarantine
  
  Processing valid.pdf (2/3)
  ✅ Successfully processed valid.pdf
  
  Processing protected.pdf (3/3)
  ⚠️ Error processing protected.pdf - password protected

📊 Batch Processing Summary Results
┏━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┓
┃ Metric                ┃ Count ┃ Percentage ┃
┡━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━┩
│ Total Files           │     3 │       100% │
│ Processed             │     3 │     100.0% │
│ Successful            │     1 │      33.3% │
│ Quarantined           │     2 │      66.7% │
│ Processing Time       │  8.7s │            │
└───────────────────────┴───────┴────────────┘

⚠️ Batch completed with errors
📄 Error reports available in quarantine directory
```

### Batch Processing Workflow

1. **Discovery Phase**: Scan directory for matching PDF files
2. **Sequential Processing**: Process each file individually
3. **Error Isolation**: Failed files quarantined, batch continues
4. **Validation Gate**: Validate outputs before Paperless upload
5. **Summary Report**: Display comprehensive batch results

### Performance Considerations

- **Sequential vs Parallel**: Uses sequential processing to avoid overwhelming system resources
- **Memory Management**: Each file processed independently to manage memory usage
- **Error Recovery**: Individual file failures don't affect other files in batch
- **Progress Feedback**: Real-time progress updates for long-running batches

## Quarantine Status Command

View the status of the quarantine directory and recent processing failures.

### Syntax

```bash
uv run bank-statement-separator quarantine-status [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--env-file` | | PATH | `.env` | Path to .env configuration file |
| `--verbose` | `-v` | FLAG | | Enable verbose logging |
| `--help` | | FLAG | | Show help message |

### Examples

```bash
# Check quarantine status
uv run python -m src.bank_statement_separator.main quarantine-status

# Verbose output with details
uv run python -m src.bank_statement_separator.main quarantine-status --verbose
```

### Output Examples

#### Quarantine Status

```
📁 Quarantine Directory Status
Path: /path/to/quarantine

📊 Summary
┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━┓
┃ Metric            ┃ Count   ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━┩
│ Total Files       │ 3       │
│ This Week         │ 1       │
│ This Month        │ 2       │
│ Older Files       │ 1       │
│ Error Reports     │ 3       │
└───────────────────┴─────────┘

📋 Recent Files (Last 7 days)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ File                           ┃ Date               ┃ Reason                   ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ failed_20240831_143022_doc.pdf │ 2024-08-31 14:30  │ Password protected       │
└─────────────────────────────────┴────────────────────┴──────────────────────────┘

💡 Use 'quarantine-clean' command to remove old files
```

#### Empty Quarantine

```
📁 Quarantine Directory Status
Path: /path/to/quarantine

✅ Quarantine directory is empty - no failed documents
```

## Quarantine Clean Command

Clean old files from the quarantine directory with safety checks.

### Syntax

```bash
uv run bank-statement-separator quarantine-clean [OPTIONS]
```

### Options

| Option | Short | Type | Default | Description |
|--------|-------|------|---------|-------------|
| `--days` | | INTEGER | `30` | Clean files older than N days |
| `--env-file` | | PATH | `.env` | Path to .env configuration file |
| `--dry-run` | | FLAG | | Preview what would be cleaned |
| `--yes` | `-y` | FLAG | | Skip confirmation prompts |
| `--verbose` | `-v` | FLAG | | Enable verbose logging |
| `--help` | | FLAG | | Show help message |

### Examples

=== "Safe Cleaning"

    ```bash
    # Preview cleanup (no files deleted)
    uv run python -m src.bank_statement_separator.main \
      quarantine-clean --dry-run
    
    # Clean files older than 30 days (default)
    uv run python -m src.bank_statement_separator.main \
      quarantine-clean
    
    # Clean files older than 7 days with confirmation
    uv run python -m src.bank_statement_separator.main \
      quarantine-clean --days 7
    ```

=== "Automated Cleaning"

    ```bash
    # Automated cleanup (skip confirmations)
    uv run python -m src.bank_statement_separator.main \
      quarantine-clean --days 30 --yes
    
    # Weekly cleanup script
    uv run python -m src.bank_statement_separator.main \
      quarantine-clean --days 7 --yes --verbose
    ```

### Output Examples

#### Dry-Run Cleanup

```
🗑️ QUARANTINE CLEANUP (DRY RUN)
Files older than 30 days will be identified

📊 Cleanup Preview
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━┓
┃ File                              ┃ Age                ┃ Size       ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━┩
│ failed_20240725_120000_old.pdf    │ 37 days           │ 2.1 MB     │
│ failed_20240720_140000_corrupt.pdf│ 42 days           │ 156 KB     │
└─────────────────────────────────────┴────────────────────┴────────────┘

📋 Summary
- Files to delete: 2
- Total size to free: 2.3 MB
- Error reports to delete: 2

⚠️ Run without --dry-run to actually delete files
```

#### Actual Cleanup

```
🗑️ QUARANTINE CLEANUP
Cleaning files older than 30 days...

⚠️ WARNING: This will permanently delete 2 files (2.3 MB)
Continue? [y/N]: y

🗑️ Deleting files...
   ❌ failed_20240725_120000_old.pdf
   ❌ failed_20240720_140000_corrupt.pdf
   📄 Deleted 2 error reports

✅ Cleanup completed
   - Files deleted: 2
   - Space freed: 2.3 MB
   - Error reports cleaned: 2
```

## Global Options

These options are available for all commands:

### Help System

```bash
# Main help
uv run bank-statement-separator --help

# Command-specific help
uv run bank-statement-separator process --help
uv run bank-statement-separator quarantine-status --help
uv run bank-statement-separator quarantine-clean --help
```

### Environment Variables

Override configuration via environment variables:

```bash
# Override API key
OPENAI_API_KEY="sk-override-key" uv run python -m src.bank_statement_separator.main process input.pdf

# Disable API usage (fallback mode)
OPENAI_API_KEY="" uv run python -m src.bank_statement_separator.main process input.pdf

# Override model
LLM_MODEL=gpt-4o uv run python -m src.bank_statement_separator.main process input.pdf
```

## Error Handling

### Exit Codes

| Code | Description |
|------|-------------|
| `0` | Success |
| `1` | General error |
| `2` | Invalid arguments |
| `3` | File not found |
| `4` | Permission denied |
| `5` | Processing failed |
| `6` | API error |

### Common Error Messages

=== "File Errors"

    ```bash
    # File not found
    Error: Input file 'missing.pdf' not found
    
    # Permission denied
    Error: Permission denied accessing '/restricted/file.pdf'
    
    # Invalid file format
    Error: File 'document.txt' is not a valid PDF
    ```

=== "API Errors"

    ```bash
    # Invalid API key
    Error: Invalid OpenAI API key. Check your OPENAI_API_KEY setting
    
    # API quota exceeded
    Error: OpenAI API quota exceeded. Check your billing
    
    # Network error
    Warning: API request failed, falling back to pattern matching
    ```

=== "Processing Errors"

    ```bash
    # Document validation failed
    Error: Document validation failed - file is password protected
    
    # Output directory error
    Error: Cannot create output directory '/invalid/path'
    
    # Quarantine full
    Warning: Quarantine directory size limit reached
    ```

## Automation Examples

### Batch Processing Script

```bash
#!/bin/bash
# process_statements.sh

INPUT_DIR="/secure/input"
OUTPUT_DIR="/secure/output" 
LOG_FILE="/var/log/bank-separator.log"

# Use the new batch-process command for efficiency
echo "Starting batch processing: $(date)" | tee -a "$LOG_FILE"

uv run bank-statement-separator \
    batch-process "$INPUT_DIR" \
    --output "$OUTPUT_DIR" \
    --pattern "*.pdf" \
    --yes \
    --verbose \
    2>&1 | tee -a "$LOG_FILE"

# Clean old quarantine files weekly
uv run python -m src.bank_statement_separator.main \
    quarantine-clean --days 30 --yes
```

### Cron Job Setup

```bash
# Edit crontab
crontab -e

# Add entries for automated processing
# Process statements daily at 2 AM
0 2 * * * /path/to/process_statements.sh

# Clean quarantine weekly on Sundays at 3 AM
0 3 * * 0 cd /path/to/bank-statement-separator && uv run bank-statement-separator quarantine-clean --days 30 --yes

# Check quarantine status daily
0 9 * * * cd /path/to/bank-statement-separator && uv run bank-statement-separator quarantine-status | mail -s "Daily Quarantine Status" admin@company.com
```

### Docker Integration

```bash
# Docker run example (when available)
docker run --rm -v $(pwd):/workspace \
    -e OPENAI_API_KEY="$OPENAI_API_KEY" \
    your-org/bank-statement-separator:latest \
    process /workspace/input.pdf --output /workspace/output --yes
```

## Performance Tips

### Optimize Processing Speed

```bash
# Use fastest model for high-volume processing
uv run python -m src.bank_statement_separator.main \
  process input.pdf --model gpt-3.5-turbo

# Process without API (fastest, lower accuracy)
OPENAI_API_KEY="" uv run python -m src.bank_statement_separator.main \
  process input.pdf --yes

# Skip confirmations for automation
uv run python -m src.bank_statement_separator.main \
  process input.pdf --yes
```

### Monitor Resource Usage

```bash
# Monitor memory usage
/usr/bin/time -v uv run python -m src.bank_statement_separator.main process large-file.pdf

# Monitor API usage
grep "LLM_API_CALL" /var/log/bank-separator/audit.log | tail -10

# Check processing times
grep "Processing Time" /var/log/bank-separator/processing.log
```

## Troubleshooting Commands

### Diagnostic Commands

```bash
# Test configuration
uv run python -c "from src.bank_statement_separator.config import load_config; print('Config OK')"

# Test API key
uv run python -c "
import openai
from src.bank_statement_separator.config import load_config
config = load_config()
if config.openai_api_key:
    client = openai.Client(api_key=config.openai_api_key)
    print('API key valid')
else:
    print('No API key configured')
"

# Test imports
uv run python -c "import src.bank_statement_separator; print('Import OK')"
```

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uv run python -m src.bank_statement_separator.main \
  process input.pdf --verbose

# Test with minimal file
uv run python -m src.bank_statement_separator.main \
  process small-test.pdf --dry-run --verbose

# Check quarantine details
uv run python -m src.bank_statement_separator.main \
  quarantine-status --verbose
```

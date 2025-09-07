# Quick Start Guide

Get the Workflow Bank Statement Separator running in just 5 minutes!

!!! info "Prerequisites"
    - Python 3.11+
    - [UV package manager](https://docs.astral.sh/uv/) (recommended)
    - OpenAI API key (optional for testing)

## 1. Installation (2 minutes)

=== "Using UV (Recommended)"

    ```bash
    # Clone the repository
    git clone <repository-url>
    cd bank-statement-separator
    
    # Install dependencies
    uv sync
    ```

=== "Using pip"

    ```bash
    # Clone the repository
    git clone <repository-url>
    cd bank-statement-separator
    
    # Create virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    
    # Install dependencies
    pip install -e .
    ```

## 2. Configuration (1 minute)

```bash
# Copy configuration template
cp .env.example .env

# Edit with your OpenAI API key (optional)
echo "OPENAI_API_KEY=sk-your-api-key-here" >> .env
```

!!! tip "No API Key? No Problem!"
    The system works without an OpenAI API key using pattern-matching fallback. AI analysis provides better accuracy, but fallback mode is perfect for testing.

## 3. Test Run (2 minutes)

=== "With Sample Data"

    ```bash
    # Generate test PDF (optional)
    uv run python scripts/generate_test_statements.py
    
    # Test with generated data
    uv run python -m src.bank_statement_separator.main \
      process test/input/generated/single_statement_minimal_test_statements.pdf \
      --dry-run --yes
    ```

=== "With Your PDF"

    ```bash
    # Dry-run analysis (no files created)
    uv run python -m src.bank_statement_separator.main \
      process your-statements.pdf --dry-run --yes
    
    # Process and create separated statements
    uv run python -m src.bank_statement_separator.main \
      process your-statements.pdf -o ./output --yes
    ```

## 4. View Results

```bash
# Check output directory
ls -la output/

# View processing logs
tail -f test/logs/statement_processing.log

# Check for any quarantined documents
uv run python -m src.bank_statement_separator.main quarantine-status
```

## Example Output

A successful run will show something like:

```
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
```

## Common Commands

### Processing Commands

```bash
# Basic processing (single file)
uv run python -m src.bank_statement_separator.main process input.pdf

# Batch processing (multiple files from directory)
uv run python -m src.bank_statement_separator.main batch-process /path/to/pdfs

# With custom output directory
uv run python -m src.bank_statement_separator.main process input.pdf -o ./separated

# Batch with pattern filtering
uv run python -m src.bank_statement_separator.main batch-process ./pdfs --pattern "*2024*.pdf"

# Use specific AI model
uv run python -m src.bank_statement_separator.main process input.pdf --model gpt-4o

# Verbose logging
uv run python -m src.bank_statement_separator.main process input.pdf --verbose

# Dry-run (analysis only, no files created)
uv run python -m src.bank_statement_separator.main process input.pdf --dry-run
```

### Management Commands

```bash
# Check quarantine status
uv run python -m src.bank_statement_separator.main quarantine-status

# Clean old quarantined files
uv run python -m src.bank_statement_separator.main quarantine-clean --dry-run

# Get help
uv run python -m src.bank_statement_separator.main --help
```

## Verification

Run the test suite to verify everything is working:

```bash
# Run all tests
make test

# Run just the unit tests (should see 37/37 passing)
uv run pytest tests/unit/ -v

# Test with edge cases
make test-edge
```

Expected output:
```
===== 37 passed in 2.34s =====
```

## What's Next?

Now that you have the system running:

1. **Learn the CLI**: Explore all [CLI commands](../reference/cli-commands.md)
2. **Configure Features**: Set up [Paperless integration](../user-guide/paperless-integration.md)
3. **Handle Errors**: Learn about [error handling](../user-guide/error-handling.md)
4. **Production Setup**: Review [configuration options](configuration.md)

## Troubleshooting

If something goes wrong:

=== "Installation Issues"
    
    ```bash
    # Verify Python version
    python --version  # Should be 3.11+
    
    # Check UV installation
    uv --version
    
    # Reinstall dependencies
    rm -rf .venv uv.lock
    uv sync
    ```

=== "Runtime Issues"

    ```bash
    # Check configuration
    cat .env
    
    # Verify imports work
    uv run python -c "import src.bank_statement_separator"
    
    # Check logs
    tail -f test/logs/statement_processing.log
    ```

=== "Processing Issues"

    ```bash
    # Test without API key (fallback mode)
    OPENAI_API_KEY="" uv run python -m src.bank_statement_separator.main \
      process input.pdf --dry-run --yes
    
    # Check quarantine for failed documents
    uv run python -m src.bank_statement_separator.main quarantine-status
    ```

Need more help? Check the [Troubleshooting Guide](../reference/troubleshooting.md) or [Working Notes](../reference/working-notes.md).
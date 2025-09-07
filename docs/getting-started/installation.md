# Installation Guide

Complete installation instructions for the Workflow Bank Statement Separator.

## System Requirements

### Minimum Requirements
- **Python**: 3.11 or higher
- **Memory**: 4GB RAM
- **Storage**: 1GB free space
- **Network**: Internet access for AI API calls

### Recommended Requirements
- **Python**: 3.12+
- **Memory**: 8GB+ RAM (for large documents)
- **Storage**: 5GB+ free space (for quarantine and logs)
- **CPU**: Multi-core processor for faster processing

### Operating Systems
- **Linux**: Ubuntu 20.04+, CentOS 8+, any modern distribution
- **macOS**: macOS 11+ (Big Sur)
- **Windows**: Windows 10+ with WSL2 recommended

## Installation Methods

=== "UV Package Manager (Recommended)"

    UV is the fastest and most reliable way to install and manage dependencies.

    ### Install UV
    
    ```bash
    # Linux/macOS
    curl -LsSf https://astral.sh/uv/install.sh | sh
    
    # Windows (PowerShell)
    powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    # Verify installation
    uv --version
    ```

    ### Install Project
    
    ```bash
    # Clone repository
    git clone <repository-url>
    cd bank-statement-separator
    
    # Install all dependencies
    uv sync
    
    # Install development dependencies (optional)
    uv sync --group dev
    ```

=== "Traditional pip"

    If you prefer using pip, follow these steps:

    ```bash
    # Clone repository
    git clone <repository-url>
    cd bank-statement-separator
    
    # Create virtual environment
    python -m venv .venv
    
    # Activate virtual environment
    # Linux/macOS:
    source .venv/bin/activate
    # Windows:
    .venv\Scripts\activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install project
    pip install -e .
    
    # Install development dependencies (optional)
    pip install -e ".[dev]"
    ```

=== "Docker (Coming Soon)"

    Docker installation will be available in the next release.

    ```bash
    # Coming in Phase 3
    docker pull your-org/bank-statement-separator:latest
    docker run -v $(pwd):/workspace your-org/bank-statement-separator process input.pdf
    ```

## Verification

After installation, verify everything is working:

### 1. Test Imports

```bash
# Using UV
uv run python -c "import src.bank_statement_separator; print('✅ Import successful')"

# Using pip/venv
python -c "import src.bank_statement_separator; print('✅ Import successful')"
```

### 2. Check CLI

```bash
# Using UV
uv run python -m src.bank_statement_separator.main --help

# Using pip/venv
python -m src.bank_statement_separator.main --help
```

Expected output:
```
Usage: main.py [OPTIONS] COMMAND [ARGS]...

  Workflow Bank Statement Separator - AI-powered document processing

Commands:
  process            Process a PDF file containing multiple bank statements
  quarantine-clean   Clean old files from quarantine directory
  quarantine-status  Show quarantine directory status
```

### 3. Run Test Suite

```bash
# Using UV
uv run pytest tests/unit/ -v

# Using pip/venv
pytest tests/unit/ -v
```

Expected output:
```
===== 37 passed in 2.34s =====
```

## Configuration Setup

### 1. Environment Variables

```bash
# Copy template
cp .env.example .env

# Edit configuration
nano .env  # or use your preferred editor
```

### 2. Required Variables

Set these essential variables in your `.env` file:

```bash
# AI Processing (recommended but optional)
OPENAI_API_KEY=sk-your-api-key-here

# Core Configuration
LLM_MODEL=gpt-4o-mini
DEFAULT_OUTPUT_DIR=./separated_statements
LOG_LEVEL=INFO
```

### 3. Directory Structure

The system will create these directories automatically:

```
bank-statement-separator/
├── logs/                    # Processing logs
├── separated_statements/    # Default output directory
├── quarantine/             # Failed documents
│   └── reports/           # Error reports
├── test/
│   ├── input/             # Test input files
│   └── output/            # Test outputs
└── .env                   # Your configuration
```

## Optional Integrations

### Paperless-ngx Integration

If you want automatic document management:

```bash
# Add to .env file
PAPERLESS_ENABLED=true
PAPERLESS_URL=http://your-paperless-instance:8000
PAPERLESS_TOKEN=your-api-token
PAPERLESS_TAGS=bank-statement,automated
```

### Development Tools

For development work, install additional tools:

```bash
# Using UV
uv sync --group dev

# Using pip
pip install -e ".[dev]"

# Verify development tools
uv run black --version
uv run ruff --version
uv run pytest --version
```

## Troubleshooting Installation

### Common Issues

=== "Python Version Issues"

    ```bash
    # Check Python version
    python --version
    python3 --version
    
    # Install Python 3.11+ if needed
    # Ubuntu/Debian:
    sudo apt update
    sudo apt install python3.11 python3.11-venv python3.11-pip
    
    # macOS (using Homebrew):
    brew install python@3.11
    
    # Windows: Download from python.org
    ```

=== "UV Installation Issues"

    ```bash
    # Alternative UV installation methods
    pip install uv
    
    # Or use conda
    conda install -c conda-forge uv
    
    # Verify UV can find Python
    uv python list
    ```

=== "Dependency Conflicts"

    ```bash
    # Clean installation
    rm -rf .venv uv.lock
    uv sync
    
    # Or force reinstall
    uv sync --refresh
    ```

=== "Import Errors"

    ```bash
    # Check Python path
    uv run python -c "import sys; print('\n'.join(sys.path))"
    
    # Verify package installation
    uv run python -c "import pkg_resources; print(list(pkg_resources.working_set))"
    
    # Reinstall in editable mode
    uv pip install -e .
    ```

### Performance Optimization

For better performance, especially with large documents:

```bash
# Install optional performance packages
uv add numpy pandas  # For faster data processing
uv add pillow        # For better image handling

# Set environment variables for performance
echo "OMP_NUM_THREADS=4" >> .env
echo "MAX_FILE_SIZE_MB=500" >> .env
```

## Production Deployment

For production environments:

### 1. Security Configuration

```bash
# Set secure directories
echo "ALLOWED_INPUT_DIRS=/secure/input" >> .env
echo "ALLOWED_OUTPUT_DIRS=/secure/output" >> .env
echo "QUARANTINE_DIRECTORY=/secure/quarantine" >> .env

# Enable comprehensive logging
echo "ENABLE_AUDIT_LOGGING=true" >> .env
echo "LOG_LEVEL=INFO" >> .env
```

### 2. System Service (Linux)

Create a systemd service for automated processing:

```ini
# /etc/systemd/system/bank-separator.service
[Unit]
Description=Bank Statement Separator
After=network.target

[Service]
Type=simple
User=app
WorkingDirectory=/opt/bank-statement-separator
Environment=PATH=/opt/bank-statement-separator/.venv/bin
ExecStart=/opt/bank-statement-separator/.venv/bin/python -m src.bank_statement_separator.main process /input/statements.pdf
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### 3. Log Rotation

```bash
# /etc/logrotate.d/bank-separator
/opt/bank-statement-separator/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    sharedscripts
}
```

## Next Steps

After successful installation:

1. **Configure the system**: Review [Configuration Guide](configuration.md)
2. **Test with sample data**: Follow [Quick Start Guide](quick-start.md)
3. **Learn the CLI**: Explore [CLI Commands](../reference/cli-commands.md)
4. **Set up integrations**: Configure [Paperless Integration](../user-guide/paperless-integration.md)

## Support

Need help with installation?

- Check [Troubleshooting Guide](../reference/troubleshooting.md)
- Review [Working Notes](../reference/working-notes.md)
- Report installation issues on GitHub
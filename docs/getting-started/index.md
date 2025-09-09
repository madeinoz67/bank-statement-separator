# Getting Started

Welcome to the Workflow Bank Statement Separator! This guide will help you get up and running quickly.

## What You'll Learn

This getting started guide covers:

- [Quick Start](quick-start.md) - Get running in 5 minutes
- [Installation](installation.md) - Detailed installation instructions
- [Configuration](configuration.md) - Complete configuration guide

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** installed on your system
- **UV package manager** (recommended) or pip
- **OpenAI API key** for optimal AI processing
- **Basic command-line knowledge**

!!! tip "UV Package Manager"
We highly recommend using [UV](https://docs.astral.sh/uv/) for package management. It's faster and more reliable than pip, especially for this project's complex dependencies.

## System Overview

The Workflow Bank Statement Separator uses an 8-node LangGraph workflow to process PDF documents:

1. **PDF Ingestion** - Load and validate documents
2. **Document Analysis** - Extract and chunk text
3. **Statement Detection** - AI-powered boundary identification
4. **Metadata Extraction** - Extract account info and dates
5. **PDF Generation** - Create separate statement files
6. **File Organization** - Apply naming conventions
7. **Output Validation** - Verify processing integrity
8. **Paperless Upload** - Optional document management integration

## Key Capabilities

### Processing Features

- **Multi-Statement PDFs**: Automatically separate combined statements
- **Intelligent Detection**: AI-powered boundary identification
- **Metadata Extraction**: Account numbers, dates, bank names
- **Format Preservation**: Maintains original PDF formatting

### Error Handling

- **Smart Quarantine**: Failed documents moved to quarantine with error reports
- **Validation Levels**: Configurable strictness (strict/normal/lenient)
- **Recovery Suggestions**: Actionable guidance for resolving issues
- **Retry Logic**: Automatic retry for transient failures

### Integration Features

- **Paperless-ngx**: Automatic upload to document management
- **Audit Logging**: Complete processing trails
- **CLI Management**: Multi-command interface for all operations
- **Configuration**: 40+ environment variables for customization

## Next Steps

Choose your path:

=== "Quick Start"
**For immediate testing** - Get running in 5 minutes

    → [Quick Start Guide](quick-start.md)

=== "Full Installation"
**For production setup** - Complete installation and configuration

    → [Installation Guide](installation.md)

=== "Configuration"
**For customization** - Detailed configuration options

    → [Configuration Guide](configuration.md)

## Support

Need help getting started?

- Check the [Troubleshooting](../reference/troubleshooting.md) guide
- Review the [Working Notes](../reference/working-notes.md) for detailed system information
- Report issues on GitHub

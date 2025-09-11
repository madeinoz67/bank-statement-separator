# CLI Help System

The Bank Statement Separator includes a comprehensive help system to guide you through configuration and usage.

## Overview

The CLI help system provides multiple ways to get assistance:

- **Built-in help** - Standard `--help` for each command
- **Environment variable help** - Dedicated `env-help` command for configuration
- **Enhanced command help** - Context-specific environment variable information
- **Version and support links** - Quick access to documentation and issue tracking

## Environment Variable Help

### The `env-help` Command

The `env-help` command provides comprehensive documentation for all 70+ environment variables:

```bash
# Show all environment variables
uv run bank-statement-separator env-help

# Filter by category
uv run bank-statement-separator env-help --category llm
```

### Available Categories

| Category          | Description                                      | Key Variables                    |
| ----------------- | ------------------------------------------------ | -------------------------------- |
| `llm`             | LLM provider configuration                       | `OPENAI_API_KEY`, `OLLAMA_MODEL` |
| `processing`      | Document processing settings                     | `CHUNK_SIZE`, `MAX_FILE_SIZE_MB` |
| `security`        | Security controls and logging                    | `LOG_LEVEL`, `ALLOWED_*_DIRS`    |
| `paperless`       | Paperless-ngx integration                        | `PAPERLESS_*` variables          |
| `error-handling`  | Error recovery and quarantine                    | `QUARANTINE_DIRECTORY`, `MAX_RETRY_ATTEMPTS` |
| `validation`      | Document validation and quality checks           | `MIN_PAGES_PER_STATEMENT`, `REQUIRE_TEXT_CONTENT` |

### Example Usage

=== "All Variables"

    ```bash
    uv run bank-statement-separator env-help
    ```

    Shows all environment variables organized by category with:
    - Variable names and descriptions
    - Default values and examples
    - Requirement status (required/optional)
    - Configuration notes and documentation links

=== "Specific Category"

    ```bash
    # LLM configuration variables
    uv run bank-statement-separator env-help --category llm

    # Processing configuration
    uv run bank-statement-separator env-help --category processing

    # Paperless integration variables
    uv run bank-statement-separator env-help --category paperless
    ```

=== "Quick Reference"

    ```bash
    # Get help about the env-help command itself
    uv run bank-statement-separator env-help --help
    ```

### Sample Output

```
📚 Environment Variable Documentation
============================================================

💡 Use --category <name> to filter by specific category
Available categories: llm, processing, security, paperless, error-handling, validation

🤖 LLM Provider Configuration
Configure AI/LLM providers for document analysis

┏━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Variable          ┃ Description                      ┃ Default        ┃ Required      ┃
┡━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ LLM_PROVIDER      │ LLM provider selection (open... │ openai         │ No            │
│ OPENAI_API_KEY    │ OpenAI API key for GPT models   │ None           │ If using Open...│
│ OPENAI_MODEL      │ OpenAI model to use              │ gpt-4o-mini    │ No            │
└───────────────────┴──────────────────────────────────┴────────────────┴───────────────┘

📋 Configuration Notes
• Create a .env file from .env.example to configure your environment
• Use --env-file option with commands to specify custom config file
• Most variables have sensible defaults and are optional
```

## Enhanced Command Help

### Context-Specific Environment Variables

Each command now includes relevant environment variables in its help text:

```bash
# Process command shows common variables
uv run bank-statement-separator process --help

# Paperless command shows required integration variables
uv run bank-statement-separator process-paperless --help

# Batch command shows error handling variables
uv run bank-statement-separator batch-process --help
```

### Example: Process Command Help

```
Bank Statement Separator

Automatically separate multi-statement PDF files using AI-powered analysis.

🔧 COMMON ENVIRONMENT VARIABLES:
• OPENAI_API_KEY        - OpenAI API key (required for AI analysis)
• OPENAI_MODEL         - Model selection (gpt-4o-mini, gpt-4o)
• DEFAULT_OUTPUT_DIR   - Default output directory
• MAX_FILE_SIZE_MB     - Maximum file size limit (default: 100)
• LOG_LEVEL           - Logging verbosity (DEBUG, INFO, WARNING)
• PAPERLESS_ENABLED   - Enable paperless-ngx upload (true/false)

💡 Configuration: Use 'env-help' command for complete documentation
📋 Example: bank-statement-separator env-help --category processing
```

### Cross-References

Commands include helpful cross-references to the env-help system:

- `process` → References processing and LLM categories
- `process-paperless` → References paperless category
- `batch-process` → References error-handling category
- `quarantine-*` → References error-handling category

## Version and Support Information

### Enhanced Version Command

The `version` command now provides comprehensive support information:

```bash
uv run bank-statement-separator version
```

### Version Output

```
╔═══════════════════════════════════════════════════════════╗
║                   Bank Statement Separator                ║
║                        Version Information                 ║
╚═══════════════════════════════════════════════════════════╝

Version: 0.3.1
Author: Stephen Eaton
License: MIT
Repository: https://github.com/madeinoz67/bank-statement-separator
Documentation: https://madeinoz67.github.io/bank-statement-separator/
Issues: https://github.com/madeinoz67/bank-statement-separator/issues

An AI-powered tool for automatically separating
multi-statement PDF files using LangChain and LangGraph.
```

### Support Links

The version command provides direct links to:

- **Repository**: Source code and releases
- **Documentation**: User guides and reference materials
- **Issue Tracker**: Bug reports and feature requests

## Help System Workflow

### For New Users

1. **Start with version**: `uv run bank-statement-separator version`
2. **Explore environment variables**: `uv run bank-statement-separator env-help`
3. **Check command-specific help**: `uv run bank-statement-separator process --help`
4. **Reference documentation**: Follow links from version command

### For Configuration

1. **Browse all variables**: `uv run bank-statement-separator env-help`
2. **Focus on category**: `uv run bank-statement-separator env-help --category llm`
3. **Copy template**: `cp .env.example .env`
4. **Test configuration**: Use dry-run mode to validate

### For Troubleshooting

1. **Check environment variables**: `uv run bank-statement-separator env-help --category security`
2. **Review command help**: Check relevant environment variables for the failing command
3. **Verify configuration**: Use the links in version command for documentation
4. **Report issues**: Use the issue tracker link from version command

## Tips and Best Practices

### Discovery Workflow

```bash
# 1. Get overview of all available help
uv run bank-statement-separator --help

# 2. Understand environment configuration
uv run bank-statement-separator env-help

# 3. Focus on specific areas
uv run bank-statement-separator env-help --category llm

# 4. Get command-specific guidance
uv run bank-statement-separator process --help

# 5. Access support resources
uv run bank-statement-separator version
```

### Configuration Strategy

1. **Start small**: Use default values and `.env.example` as baseline
2. **Use categories**: Focus on one configuration area at a time (`llm`, `processing`, etc.)
3. **Test incrementally**: Use dry-run mode to test configuration changes
4. **Reference frequently**: Keep `env-help` output handy during configuration

### Integration with Documentation

The CLI help system is designed to complement the online documentation:

- **CLI help**: Quick reference and immediate guidance
- **Online docs**: Comprehensive guides and examples
- **Template files**: Documented default configurations
- **Issue tracker**: Community support and bug reporting

## Accessibility Features

### Multiple Access Methods

- **Interactive CLI**: Rich formatted output with colors and tables
- **Category filtering**: Focus on relevant variables only
- **Cross-references**: Commands point to related help sections
- **Documentation links**: Direct access to online resources

### Consistent Formatting

- **Standardized output**: All help uses consistent Rich formatting
- **Clear organization**: Variables grouped logically by function
- **Visual hierarchy**: Important information highlighted with colors and emojis
- **Practical examples**: Real-world usage patterns shown in command help

This help system ensures users can quickly find the information they need, whether they're just getting started or configuring advanced features.

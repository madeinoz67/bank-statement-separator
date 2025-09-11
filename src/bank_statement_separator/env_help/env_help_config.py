"""Environment variable help configuration.

This module contains the comprehensive environment variable documentation
used by the env-help CLI command.
"""

ENV_CATEGORIES = {
    "llm": {
        "title": "🤖 LLM Provider Configuration",
        "description": "Configure AI/LLM providers for document analysis",
        "variables": {
            "LLM_PROVIDER": {
                "description": "LLM provider selection (openai, ollama, auto)",
                "default": "openai",
                "example": "ollama",
                "required": False,
            },
            "OPENAI_API_KEY": {
                "description": "OpenAI API key for GPT models",
                "default": "None",
                "example": "sk-your-api-key-here",
                "required": "If using OpenAI",
            },
            "OPENAI_MODEL": {
                "description": "OpenAI model to use",
                "default": "gpt-4o-mini",
                "example": "gpt-4o",
                "required": False,
            },
            "OLLAMA_BASE_URL": {
                "description": "Ollama server base URL",
                "default": "http://localhost:11434",
                "example": "http://10.0.0.150:11434",
                "required": "If using Ollama",
            },
            "OLLAMA_MODEL": {
                "description": "Ollama model to use",
                "default": "llama3.2",
                "example": "mistral:instruct",
                "required": False,
            },
            "LLM_TEMPERATURE": {
                "description": "LLM temperature for response randomness",
                "default": "0.0",
                "example": "0.1",
                "required": False,
            },
            "LLM_MAX_TOKENS": {
                "description": "Maximum tokens for LLM responses",
                "default": "4000",
                "example": "8000",
                "required": False,
            },
        },
    },
    "processing": {
        "title": "⚙️ Processing Configuration",
        "description": "Document processing and output settings",
        "variables": {
            "CHUNK_SIZE": {
                "description": "Text chunk size for processing",
                "default": "6000",
                "example": "8000",
                "required": False,
            },
            "CHUNK_OVERLAP": {
                "description": "Overlap between text chunks",
                "default": "800",
                "example": "1000",
                "required": False,
            },
            "DEFAULT_OUTPUT_DIR": {
                "description": "Default output directory for separated statements",
                "default": "./separated_statements",
                "example": "/path/to/output",
                "required": False,
            },
            "PROCESSED_INPUT_DIR": {
                "description": "Directory to move processed input files",
                "default": "None (uses input_dir/processed)",
                "example": "./processed",
                "required": False,
            },
            "MAX_FILE_SIZE_MB": {
                "description": "Maximum file size in MB",
                "default": "100",
                "example": "200",
                "required": False,
            },
            "MAX_PAGES_PER_STATEMENT": {
                "description": "Maximum pages per individual statement",
                "default": "50",
                "example": "100",
                "required": False,
            },
            "MAX_TOTAL_PAGES": {
                "description": "Maximum total pages to process",
                "default": "500",
                "example": "1000",
                "required": False,
            },
            "INCLUDE_BANK_IN_FILENAME": {
                "description": "Include bank name in output filenames",
                "default": "true",
                "example": "false",
                "required": False,
            },
        },
    },
    "security": {
        "title": "🔒 Security & Logging",
        "description": "Security controls and logging configuration",
        "variables": {
            "LOG_LEVEL": {
                "description": "Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
                "default": "INFO",
                "example": "DEBUG",
                "required": False,
            },
            "LOG_FILE": {
                "description": "Path to log file",
                "default": "./logs/statement_processing.log",
                "example": "/var/log/statements.log",
                "required": False,
            },
            "ALLOWED_INPUT_DIRS": {
                "description": "Comma-separated allowed input directories",
                "default": "None (all allowed)",
                "example": "/secure/input,/approved/docs",
                "required": False,
            },
            "ALLOWED_OUTPUT_DIRS": {
                "description": "Comma-separated allowed output directories",
                "default": "None (all allowed)",
                "example": "/secure/output,/processed",
                "required": False,
            },
            "ENABLE_AUDIT_LOGGING": {
                "description": "Enable comprehensive audit logging",
                "default": "true",
                "example": "false",
                "required": False,
            },
        },
    },
    "paperless": {
        "title": "📄 Paperless-ngx Integration",
        "description": "Document management system integration",
        "variables": {
            "PAPERLESS_ENABLED": {
                "description": "Enable paperless-ngx integration",
                "default": "false",
                "example": "true",
                "required": False,
            },
            "PAPERLESS_URL": {
                "description": "Paperless-ngx instance URL",
                "default": "None",
                "example": "https://paperless.example.com",
                "required": "If paperless enabled",
            },
            "PAPERLESS_TOKEN": {
                "description": "Paperless-ngx API token",
                "default": "None",
                "example": "your-api-token-here",
                "required": "If paperless enabled",
            },
            "PAPERLESS_TAGS": {
                "description": "Default tags for uploaded documents",
                "default": "None",
                "example": "bank-statement,automated",
                "required": False,
            },
            "PAPERLESS_CORRESPONDENT": {
                "description": "Default correspondent name",
                "default": "None",
                "example": "Bank",
                "required": False,
            },
            "PAPERLESS_DOCUMENT_TYPE": {
                "description": "Default document type",
                "default": "None",
                "example": "Bank Statement",
                "required": False,
            },
            "PAPERLESS_INPUT_TAGS": {
                "description": "Tags for filtering input documents from paperless",
                "default": "None",
                "example": "unprocessed,bank-statement-raw",
                "required": False,
            },
        },
    },
    "error-handling": {
        "title": "🚨 Error Handling & Quarantine",
        "description": "Error recovery and document quarantine settings",
        "variables": {
            "QUARANTINE_DIRECTORY": {
                "description": "Directory for failed/invalid documents",
                "default": "None (uses output_dir/quarantine)",
                "example": "./quarantine",
                "required": False,
            },
            "MAX_RETRY_ATTEMPTS": {
                "description": "Maximum retry attempts for failures",
                "default": "2",
                "example": "3",
                "required": False,
            },
            "VALIDATION_STRICTNESS": {
                "description": "Validation strictness level",
                "default": "normal",
                "example": "strict",
                "required": False,
            },
            "AUTO_QUARANTINE_CRITICAL_FAILURES": {
                "description": "Automatically quarantine critical failures",
                "default": "true",
                "example": "false",
                "required": False,
            },
            "ENABLE_ERROR_REPORTING": {
                "description": "Generate detailed error reports",
                "default": "true",
                "example": "false",
                "required": False,
            },
        },
    },
    "validation": {
        "title": "✅ Document Validation",
        "description": "Document validation and quality checks",
        "variables": {
            "MIN_PAGES_PER_STATEMENT": {
                "description": "Minimum pages required per statement",
                "default": "1",
                "example": "2",
                "required": False,
            },
            "MAX_FILE_AGE_DAYS": {
                "description": "Maximum age of input files in days",
                "default": "None (no limit)",
                "example": "365",
                "required": False,
            },
            "ALLOWED_FILE_EXTENSIONS": {
                "description": "Allowed file extensions for processing",
                "default": ".pdf",
                "example": ".pdf,.txt",
                "required": False,
            },
            "REQUIRE_TEXT_CONTENT": {
                "description": "Require documents to contain extractable text",
                "default": "true",
                "example": "false",
                "required": False,
            },
            "MIN_TEXT_CONTENT_RATIO": {
                "description": "Minimum ratio of pages with text content",
                "default": "0.1",
                "example": "0.2",
                "required": False,
            },
        },
    },
}

# Pre-computed choices for Click command - avoids recomputation on import
# Use tuple for immutability and better performance
ENV_HELP_CATEGORY_CHOICES = tuple(ENV_CATEGORIES.keys()) + ("all",)

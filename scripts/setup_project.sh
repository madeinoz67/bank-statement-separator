#!/bin/bash

# ==============================================================================
# Bank Statement Separator - Project Setup Script
# ==============================================================================
# This script sets up the project with UV configured for local environments

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project configuration
PROJECT_NAME="bank-statement-separator-workflow"
PYTHON_VERSION="3.11"

echo -e "${BLUE}🚀 Setting up ${PROJECT_NAME} with UV local configuration${NC}"

# ==============================================================================
# Step 1: Check Prerequisites
# ==============================================================================
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ UV is not installed. Installing UV...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.local/bin/env
fi

echo -e "${GREEN}✅ UV is installed: $(uv --version)${NC}"

# ==============================================================================
# Step 2: Create Project Structure
# ==============================================================================
echo -e "${YELLOW}📁 Creating project structure...${NC}"

# Create project directory if it doesn't exist
if [ ! -d "$PROJECT_NAME" ]; then
    uv init "$PROJECT_NAME"
    echo -e "${GREEN}✅ Created project directory${NC}"
else
    echo -e "${YELLOW}⚠️  Project directory already exists${NC}"
fi

cd "$PROJECT_NAME"

# Create additional directories
mkdir -p {src,tests,docs,logs,scripts,config}
mkdir -p separated_statements
mkdir -p .python-versions
mkdir -p .uv-cache

echo -e "${GREEN}✅ Created directory structure${NC}"

# ==============================================================================
# Step 3: Configure UV for Local Environment
# ==============================================================================
echo -e "${YELLOW}⚙️  Configuring UV for local environment...${NC}"

# Set UV to use local project environment
export UV_PROJECT_ENVIRONMENT=true
export UV_PYTHON_DOWNLOADS=.python-versions
export UV_CACHE_DIR=.uv-cache

# Create UV configuration
cat > uv.toml << 'EOF'
# UV Configuration for Local Project Environment
[tool.uv]
project-environment = true
venv-path = ".venv"
cache-dir = ".uv-cache"
python-downloads = ".python-versions"
python-preference = "project"
python-version = "3.11"
compile-bytecode = true
dev = true
editable = true

[tool.uv.dependency-groups]
security = [
    "bandit>=1.7.0",
    "safety>=3.0.0",
    "semgrep>=1.45.0",
    "pip-audit>=2.6.0"
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.0.0"
]
EOF

echo -e "${GREEN}✅ Created UV configuration${NC}"

# ==============================================================================
# Step 4: Install Python and Dependencies
# ==============================================================================
echo -e "${YELLOW}🐍 Installing Python ${PYTHON_VERSION} locally...${NC}"

# Install Python locally in project
uv python install "$PYTHON_VERSION"

echo -e "${YELLOW}📦 Installing project dependencies...${NC}"

# Add core dependencies
uv add langgraph langchain-openai pymupdf python-dotenv

# Add development dependencies
uv add --dev pytest black isort mypy pre-commit

# Add security dependencies
uv add --group security bandit safety semgrep pip-audit

echo -e "${GREEN}✅ Installed all dependencies${NC}"

# ==============================================================================
# Step 5: Create Environment Files
# ==============================================================================
echo -e "${YELLOW}🔧 Creating environment files...${NC}"

# Create .env.example
cat > .env.example << 'EOF'
# ==============================================================================
# Bank Statement Separator - Environment Configuration
# ==============================================================================

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4o-mini
LLM_TEMPERATURE=0
LLM_MAX_TOKENS=4000

# Processing Configuration
CHUNK_SIZE=6000
CHUNK_OVERLAP=800
MAX_FILENAME_LENGTH=240
DEFAULT_OUTPUT_DIR=./separated_statements

# Security Configuration
ENABLE_AUDIT_LOGGING=true
LOG_LEVEL=INFO
LOG_FILE=./logs/statement_processing.log
MAX_FILE_SIZE_MB=100

# Advanced Configuration
ENABLE_FALLBACK_PROCESSING=true
INCLUDE_BANK_IN_FILENAME=true
DATE_FORMAT=YYYY-MM
EOF

# Create initial .env file
cp .env.example .env

echo -e "${GREEN}✅ Created environment configuration files${NC}"

# ==============================================================================
# Step 6: Create Security Configuration
# ==============================================================================
echo -e "${YELLOW}🔒 Setting up security configuration...${NC}"

# Create .gitignore
cat > .gitignore << 'EOF'
# Credentials and Secrets
.env
.env.*
!.env.example
*.key
*.pem
secrets/

# UV Local Environment
.venv/
.uv-cache/
.python-versions/
uv.lock

# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
build/

# Processing Files
logs/
separated_statements/
temp/

# Development
.coverage
.pytest_cache/
.mypy_cache/
.vscode/
.idea/
EOF

# Create pre-commit configuration
cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/psf/black
    rev: 23.12.1
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-c', 'pyproject.toml']
  - repo: https://github.com/pyupio/safety
    rev: 3.0.1
    hooks:
      - id: safety
EOF

echo -e "${GREEN}✅ Created security configuration${NC}"

# ==============================================================================
# Step 7: Create Helper Scripts
# ==============================================================================
echo -e "${YELLOW}📝 Creating helper scripts...${NC}"

# Create run script
cat > scripts/run.sh << 'EOF'
#!/bin/bash
# Helper script to run the bank statement separator

set -euo pipefail

# Ensure we're in the project directory
cd "$(dirname "$0")/.."

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Please copy .env.example to .env and configure it."
    exit 1
fi

# Run with UV
echo "🚀 Running bank statement separator..."
uv run python bank_statement_separator.py "$@"
EOF

# Create security check script
cat > scripts/security-check.sh << 'EOF'
#!/bin/bash
# Run security checks

set -euo pipefail
cd "$(dirname "$0")/.."

echo "🔍 Running security checks..."

echo "📊 Running bandit..."
uv run --group security bandit -r . -f json -o logs/bandit-report.json || true
uv run --group security bandit -r .

echo "🛡️ Running safety check..."
uv run --group security safety check --output json --file logs/safety-report.json || true
uv run --group security safety check

echo "🔎 Running pip-audit..."
uv run --group security pip-audit --format json --output logs/pip-audit-report.json || true
uv run --group security pip-audit

echo "✅ Security checks completed"
EOF

# Make scripts executable
chmod +x scripts/*.sh

echo -e "${GREEN}✅ Created helper scripts${NC}"

# ==============================================================================
# Step 8: Verify Setup
# ==============================================================================
echo -e "${YELLOW}🔍 Verifying setup...${NC}"

# Check UV environment
echo "UV Python location: $(uv python which)"
echo "UV Environment path: $(uv venv --python-preference project)"

# Test imports
uv run python -c "import langgraph; print('✅ LangGraph available')" || echo "❌ LangGraph import failed"
uv run python -c "from dotenv import load_dotenv; print('✅ python-dotenv available')" || echo "❌ python-dotenv import failed"

# Show project structure
echo -e "\n${BLUE}📁 Project Structure:${NC}"
tree -a -I '__pycache__|*.pyc|.git' . 2>/dev/null || find . -type f -name ".*" -o -type f -name "*" | head -20

echo -e "\n${GREEN}🎉 Project setup completed successfully!${NC}"

# ==============================================================================
# Final Instructions
# ==============================================================================
echo -e "\n${BLUE}📋 Next Steps:${NC}"
echo "1. Edit .env file with your OpenAI API key"
echo "2. Copy bank_statement_separator.py to the project root"
echo "3. Run: ./scripts/run.sh your_statements.pdf"
echo "4. Run security checks: ./scripts/security-check.sh"

echo -e "\n${BLUE}💡 Useful Commands:${NC}"
echo "• uv run python bank_statement_separator.py --help"
echo "• uv run --group security bandit -r ."
echo "• uv tree  # Show dependency tree"
echo "• uv python list  # Show available Python versions"

echo -e "\n${YELLOW}⚠️  Remember:${NC}"
echo "• All Python environments are contained within this project directory"
echo "• Cache and downloads are stored locally in .uv-cache and .python-versions"
echo "• Configure your .env file before running the application"

echo -e "\n${GREEN}✨ Happy processing! ✨${NC}"
EOF

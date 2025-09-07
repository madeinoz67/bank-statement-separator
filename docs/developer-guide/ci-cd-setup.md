# CI/CD Setup and Workflows

This document describes the Continuous Integration and Continuous Deployment (CI/CD) setup for the Bank Statement Separator project.

## Overview

The CI/CD pipeline is built using GitHub Actions and consists of several workflows that automate testing, code quality checks, documentation deployment, and releases.

## Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop` branches

**Jobs:**
- **test**: Runs unit and integration tests across Python 3.11 and 3.12
- **test-with-api**: Runs API-dependent tests (only on main branch or with `[api-test]` commit message)
- **security**: Performs security scanning with Safety and Bandit

**Features:**
- Matrix testing across multiple Python versions
- Code formatting and linting with Ruff
- Coverage reporting with Codecov
- Separate handling of API-dependent tests
- Security vulnerability scanning

### 2. Documentation Deployment (`.github/workflows/docs.yml`)

**Triggers:**
- Push to `main` branch
- Manual trigger via GitHub Actions UI

**Features:**
- Builds MkDocs documentation
- Deploys to GitHub Pages
- Automatic deployment on main branch changes

### 3. Release Automation (`.github/workflows/release.yml`)

**Triggers:**
- Git tag push (e.g., `v1.0.0`)

**Features:**
- Runs full test suite
- Builds Python package
- Creates GitHub release with artifacts
- Publishes to PyPI (if configured)

### 4. Dependency Review (`.github/workflows/dependency-review.yml`)

**Triggers:**
- Pull requests to `main` or `develop` branches

**Features:**
- Automated dependency vulnerability scanning
- License compliance checking
- Generates license reports

## Configuration Files

### Dependency Review Config (`.github/dependency-review-config.yml`)
```yaml
fail_on_severity: moderate
allow_licenses:
  - MIT
  - Apache-2.0
  - BSD-2-Clause
  - BSD-3-Clause
  - ISC
  - GPL-3.0-only
  - LGPL-3.0-only
fail_on_scopes:
  - runtime
vulnerability_check: true
license_check: true
```

!!! info "License Compatibility"
    The project uses MIT License, which is fully compatible with the CI/CD pipeline's license checking. The dependency review workflow ensures all dependencies also use approved open-source licenses.

## Documentation Versioning

The CI/CD pipeline includes automated documentation versioning that deploys versioned documentation for each release:

### Versioned Deployment Process

1. **Latest Documentation**: Deployed to root (`/`) on every `main` branch push
2. **Versioned Documentation**: Deployed to `/v{major}.{minor}/` on each release
3. **Version Selector**: Automatically updated with available versions
4. **Cross-linking**: All versions include navigation to other versions

### URL Structure

```
https://madeinoz67.github.io/bank-statement-separator/
├── /                    # Latest documentation
├── /v2.2/              # Version 2.2 documentation
├── /v2.1/              # Version 2.1 documentation
└── /versions.json      # Version metadata
```

### Version Management

- **Automatic**: Versions are created automatically on GitHub releases
- **Manual**: Use workflow dispatch to deploy specific versions
- **Maintenance**: Old versions can be archived or removed as needed

### Version Selector

The documentation includes a version selector in the header that allows users to:
- Switch between documentation versions
- See all available versions
- Access version-specific content

### Pull Request Template (`.github/PULL_REQUEST_TEMPLATE.md`)
Standardized PR template with:
- Change type classification
- Testing checklist
- Code review requirements

### Code Owners (`.github/CODEOWNERS`)
Automatic review assignment for:
- CI/CD changes
- Documentation updates
- Core application code
- Test modifications

## Repository Secrets

The following secrets need to be configured in GitHub repository settings:

- `OPENAI_API_KEY`: For API-dependent tests
- `PYPI_API_TOKEN`: For PyPI package publishing
- `GOOGLE_ANALYTICS_KEY`: For documentation analytics (optional)

## Branch Protection Rules

Recommended branch protection rules for `main` branch:

1. **Require pull request reviews** before merging
2. **Require status checks** to pass:
   - `test (3.11)`
   - `test (3.12)`
   - `security`
   - `dependency-review`
3. **Require branches to be up to date** before merging
4. **Include administrators** in restrictions

## Local Development

### Prerequisites
- Python 3.11 or 3.12
- uv package manager
- Git

### Setup
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone repository
git clone https://github.com/madeinoz67/bank-statement-separator.git
cd bank-statement-separator

# Install dependencies
uv sync --group dev

# Run tests locally
uv run pytest

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

### Pre-commit Checks
```bash
# Run all pre-commit checks
make pre-commit

# Or individually:
make format
make lint
make test-fast
```

## Testing Strategy

### Test Categories
- **Unit Tests**: Fast, isolated tests for individual functions
- **Integration Tests**: Tests for component interactions
- **API Tests**: Tests requiring external API access (OpenAI)
- **Edge Case Tests**: Tests for boundary conditions and error scenarios

### Test Execution
```bash
# Run all tests
make test

# Run unit tests only
make test-unit

# Run integration tests
make test-integration

# Run with coverage
make test-coverage
```

## Deployment

### Documentation
Documentation is automatically deployed to GitHub Pages on pushes to `main`:
- Build command: `uv run mkdocs build`
- Deploy command: `uv run mkdocs gh-deploy`

### Releases
To create a new release:
1. Update version in `pyproject.toml`
2. Create a git tag: `git tag v1.0.0`
3. Push the tag: `git push origin v1.0.0`
4. GitHub Actions will automatically:
   - Run tests
   - Build package
   - Create GitHub release
   - Publish to PyPI

## Monitoring and Maintenance

### Workflow Monitoring
- Check GitHub Actions tab for workflow status
- Review failed jobs for error details
- Monitor coverage trends on Codecov

### Dependency Updates
- Dependencies are managed via `uv`
- Security updates are scanned automatically
- Use `uv lock --upgrade` to update dependencies

### Performance Monitoring
- Test execution times are tracked
- Coverage reports show code coverage trends
- Security scans identify vulnerabilities

## Troubleshooting

### Common Issues

1. **Test Failures**
   - Check Python version compatibility
   - Verify dependencies are installed
   - Review test output for specific errors

2. **CI Pipeline Failures**
   - Check GitHub Actions logs
   - Verify secrets are configured
   - Ensure branch protection rules aren't blocking merges

3. **Documentation Deployment Issues**
   - Verify MkDocs configuration
   - Check GitHub Pages settings
   - Review build logs for errors

### Getting Help
- Check existing issues on GitHub
- Review workflow logs in GitHub Actions
- Consult the project's documentation
- Contact maintainers for support

## CLI Features

### Header Suppression

The CLI includes a `--no-header` option to suppress the application banner display:

```bash
# Process file without header
uv run python -m src.bank_statement_separator.main process input.pdf --no-header

# Batch process without header
uv run python -m src.bank_statement_separator.main batch-process /path/to/pdfs --no-header

# Version command (no header option needed as it has its own display)
uv run python -m src.bank_statement_separator.main version
```

This is useful for:
- **Scripting**: Clean output for automated scripts
- **Integration**: Better integration with other tools
- **CI/CD**: Reduced noise in automated pipelines
- **API Usage**: Cleaner output for programmatic usage

## Future Enhancements

Potential improvements to the CI/CD pipeline:
- Docker container builds and testing
- Performance regression testing
- Automated dependency updates (Dependabot)
- Multi-platform testing (Windows, macOS)
- Integration with external services
- Advanced security scanning
- Automated changelog generation

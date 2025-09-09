# Contributing to Bank Statement Separator

Thank you for your interest in contributing to the Bank Statement Separator project! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/bank-statement-separator.git`
3. Install dependencies: `uv sync`
4. Create a feature branch: `git checkout -b feature/your-feature-name`

## Code Style

- Follow PEP 8 conventions
- Use type hints for all functions
- Write docstrings for public APIs
- Keep functions focused and small
- Use f-strings for string formatting

## Testing

- Write tests for new features
- Run tests with: `uv run pytest`
- Ensure all tests pass before submitting PR
- Add regression tests for bug fixes

## Security

### Secret Detection

This project uses [detect-secrets](https://github.com/Yelp/detect-secrets) to prevent accidental commits of sensitive information:

- **Pre-commit hook**: Automatically scans for potential secrets before commits
- **Baseline file**: `.secrets.baseline` contains known false positives
- **Exclusions**: Test environment files and documentation are excluded

#### Working with detect-secrets

```bash
# Scan for new secrets
uv run detect-secrets scan

# Update baseline with new legitimate secrets
uv run detect-secrets scan --baseline .secrets.baseline

# Audit findings interactively
uv run detect-secrets audit .secrets.baseline
```

#### Common Issues

- **False positives**: Add to baseline or use `# pragma: allowlist secret` comments
- **Test files**: Use placeholder values like `sk-test-key` or `your-api-key-here`
- **Documentation**: Real examples should use obviously fake credentials

## Conventional Commits

This project uses [Conventional Commits](https://conventionalcommits.org/) for automated semantic versioning. Please follow these guidelines:

### Commit Message Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation only changes
- **style**: Changes that do not affect the meaning of the code (white-space, formatting, etc.)
- **refactor**: A code change that neither fixes a bug nor adds a feature
- **perf**: A code change that improves performance
- **test**: Adding missing tests or correcting existing tests
- **build**: Changes that affect the build system or external dependencies
- **ci**: Changes to CI configuration files and scripts
- **chore**: Other changes that don't modify src or test files

### Examples

```
feat: add PDF boundary detection for multi-statement files

fix: resolve account number extraction for Westpac statements

docs: update installation instructions for uv package manager

refactor: simplify LLM analyzer node logic

test: add integration tests for API-dependent features
```

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the footer:

```
feat: change API endpoint structure

BREAKING CHANGE: The API now requires authentication headers
```

### Scope (Optional)

You can add a scope to provide more context:

```
feat(pdf): add support for encrypted PDF files
fix(parser): handle edge case in date parsing
```

## Pull Request Process

1. Ensure your code follows the style guidelines
2. Write or update tests as needed
3. Update documentation if required
4. Ensure all CI checks pass
5. Create a pull request with a clear description
6. Wait for review and address any feedback

## Release Process

Releases are automated using semantic versioning:

- **Patch releases** (1.0.0 → 1.0.1): Bug fixes (`fix:` commits)
- **Minor releases** (1.0.0 → 1.1.0): New features (`feat:` commits)
- **Major releases** (1.0.0 → 2.0.0): Breaking changes (`BREAKING CHANGE:` footer)

The release process is fully automated:

1. Conventional commits are analyzed on push to main
2. Release PR is created/updated with changelog
3. When merged, version is bumped and release is published
4. PyPI package is automatically published
5. Documentation is versioned and deployed

## Getting Help

- Check existing issues and documentation
- Create an issue for bugs or feature requests
- Join discussions in pull request comments

Thank you for contributing! 🎉

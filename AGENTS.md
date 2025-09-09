# Developer Guidelines

This document contains critical information about working with this codebase. Follow these guidelines precisely.

## Core Development Rules

1. Package Management
   - ONLY use uv, NEVER pip
   - Installation: `uv add package`
   - Running tools: `uv run tool`
   - Upgrading: `uv add --dev package --upgrade-package package`
   - FORBIDDEN: `uv pip install`, `@latest` syntax

2. Code Quality
   - Type hints required for all code
   - Public APIs must have docstrings
   - Functions must be focused and small
   - Follow existing patterns exactly
   - Line length: 88 chars maximum

3. Testing Requirements
   - Framework: `uv run pytest`
   - Async testing: use anyio, not asyncio
   - Coverage: test edge cases and errors
   - New features require tests
   - Bug fixes require regression tests

4. Code Style
   - PEP 8 naming (snake_case for functions/variables)
   - Class names in PascalCase
   - Constants in UPPER_SNAKE_CASE
   - Document with docstrings
   - Use f-strings for formatting

- For commits fixing bugs or adding features based on user reports add:

  ```bash
  git commit --trailer "Reported-by:<name>"
  ```

  Where `<name>` is the name of the user.

- For commits related to a Github issue, add
  ```bash
  git commit --trailer "Github-Issue:#<number>"
  ```
- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Development Philosophy

- **Simplicity**: Write simple, straightforward code
- **Readability**: Make code easy to understand
- **Performance**: Consider performance without sacrificing readability
- **Maintainability**: Write code that's easy to update
- **Testability**: Ensure code is testable
- **Reusability**: Create reusable components and functions
- **Less Code = Less Debt**: Minimize code footprint

## Coding Best Practices

- **Early Returns**: Use to avoid nested conditions
- **Descriptive Names**: Use clear variable/function names (prefix handlers with "handle")
- **Constants Over Functions**: Use constants where possible
- **DRY Code**: Don't repeat yourself
- **Functional Style**: Prefer functional, immutable approaches when not verbose
- **Minimal Changes**: Only modify code related to the task at hand
- **Function Ordering**: Define composing functions before their components
- **TODO Comments**: Mark issues in existing code with "TODO:" prefix
- **Simplicity**: Prioritize simplicity and readability over clever solutions
- **Build Iteratively** Start with minimal functionality and verify it works before adding complexity
- **Run Tests**: Test your code frequently with realistic inputs and validate outputs
- **Build Test Environments**: Create testing environments for components that are difficult to validate directly
- **Functional Code**: Use functional and stateless approaches where they improve clarity
- **Clean logic**: Keep core logic clean and push implementation details to the edges
- **File Organsiation**: Balance file organization with simplicity - use an appropriate number of files for the project scale
- **Document Public APIs**: Always document public functions, classes, and modules with clear docstrings
- **Error Handling**: Handle errors gracefully and provide meaningful messages
- **Logging**: Use logging for important events and errors, avoid print statements
- **Security**: Follow security best practices, especially when handling sensitive data
- **Version Control**: Commit frequently with clear messages, use branches for features/bug fixes
- **branching**: Use feature branches for new work or bug fixes
- **Branch Names**: Use descriptive names, e.g. `feature/add-user-auth`, `bugfix/fix-login-error`
- **Commit Messages**: Use conventional commit messages with title, body, and footer
- **Squash Commits**: Squash commits when merging feature branches to keep history clean
- **Pull Changes**: Regularly pull changes from `main` to keep branches up to date
- **Avoid Large Commits**: Break changes into smaller, logical commits
- **Linting**: Always run tests and linters before committing, including RUFF
- **Rebase**: Use `git rebase` to maintain a linear history when updating branches
- **Code Reviews**: Review code thoroughly before merging to `main`
- **Documentation**: Keep documentation up to date with code changes
- **Continuous Learning**: Stay updated with best practices and new technologies
- **Avoid Premature Optimization**: Focus on writing clear and correct code first, optimize later if necessary
- **Avoid Commits to Main**: Do not commit directly to the `main` branch

# Bank Statement Separator

## Key Commands

### Development

```bash
# Install dependencies
uv sync

# Install with dev dependencies
uv sync --group dev

# Run the application
uv run python -m src.bank_statement_separator.main <input.pdf>

# Run with options
uv run python -m src.bank_statement_separator.main input.pdf -o ./output --model gpt-4o --verbose

# Run tests
uv run pytest
```

### Configuration

- Copy `.env.example` to `.env` and configure API keys
- Set `OPENAI_API_KEY` for LLM functionality
- Adjust processing limits and security settings as needed

## Important Notes

- Requires OpenAI API key for AI analysis
- Falls back to pattern matching if LLM fails
- Includes comprehensive logging and audit trails
- Designed with security controls for production use
- Supports dry-run mode for testing

## Documentation Guidelines

- **CRITICAL**: All documentation must be created in the `docs/` directory
- Use appropriate subdirectories: `docs/user-guide/`, `docs/reference/`, `docs/architecture/`, `docs/design/`, `docs/release_notes/`, `docs/known_issues/`
- Never create documentation files in the project root directory
- Update `mkdocs.yml` navigation when adding new documentation
- **Release Notes**: All release notes must be created in `docs/release_notes/` directory
  - Use format: `RELEASE_NOTES_vX.Y.md` (e.g., `RELEASE_NOTES_v2.1.md`)
  - Most recent release should be linked on the front page (`docs/index.md`) as "Latest Release"
  - Add each release to mkdocs.yml navigation under "Release Notes" section

## Test Organization

- **Manual Test Scripts**: All manual test scripts must be created in `tests/manual/` directory
- Manual tests are excluded from automated pytest discovery via `--ignore=tests/manual` in pytest.ini
- Use `tests/unit/` for unit tests and `tests/integration/` for integration tests
- Manual tests should include clear documentation on their purpose and usage requirements

## Pull Requests

- Create a detailed message of what changed. Focus on the high level description of
  the problem it tries to solve, and how it is solved. Don't go into the specifics of the
  code unless it adds clarity.

- Always add `Stephen Eaton` as reviewer.

- NEVER ever mention a `co-authored-by` or similar aspects. In particular, never
  mention the tool used to create the commit message or PR.

## Python Tools

## Code Formatting

1. Ruff
   - Format: `uv run ruff format .`
   - Check: `uv run ruff check .`
   - Fix: `uv run ruff check . --fix`
   - Critical issues:
     - Line length (88 chars)
     - Import sorting (I001)
     - Unused imports
   - Line wrapping:
     - Strings: use parentheses
     - Function calls: multi-line with proper indent
     - Imports: split into multiple lines

2. Type Checking
   - Tool: `uv run pyright`
   - Requirements:
     - Explicit None checks for Optional
     - Type narrowing for strings
     - Version warnings can be ignored if checks pass

3. Pre-commit
   - Config: `.pre-commit-config.yaml`
   - Runs: on git commit
   - Tools: Prettier (YAML/JSON), Ruff (Python)
   - Ruff updates:
     - Check PyPI versions
     - Update config rev
     - Commit config first

## Error Resolution

1. CI Failures
   - Fix order:
     1. Formatting
     2. Type errors
     3. Linting
   - Type errors:
     - Get full line context
     - Check Optional types
     - Add type narrowing
     - Verify function signatures

2. Common Issues
   - Line length:
     - Break strings with parentheses
     - Multi-line function calls
     - Split imports
   - Types:
     - Add None checks
     - Narrow string types
     - Match existing patterns

3. Best Practices
   - Check git status before commits
   - Run formatters before type checks
   - Keep changes minimal
   - Follow existing patterns
   - Document public APIs
   - Test thoroughly

when creating, deleting or updating documentation always update mkdocs.md with the changes

Only use Emojis in docs to:

- highlight important things
- pass/fail test results

DO NOT edit build artifacts, delete and re-generate
DO NOT edit files in .venv, delete and regenerate
DO NOT edit files in .uv-cache, delete and regenerate

## Debugging and Testing

DO use the test directory for generating any temporary testing inputs and outputs, test logs etc while troubleshooting
DO put any manual test scripts in the tests/manual directory
DO use the tests/env/ for any test environment files, if ones need to be created for specific test do so in here

DO NOT commit any temporary testing inputs and outputs, test logs etc to git

## Release Process

- Releases are automated using release-please and a GitHub workflow
- Release notes are generated automatically from commit messages
- Release notes are saved in `docs/release_notes/` directory
- Release notes file format: `RELEASE_NOTES_vX.Y.md` (e.g., `RELEASE_NOTES_v2.1.md`)
- Most recent release should be linked on the front page (`docs/index.md`) as "Latest Release"
- Add each release to mkdocs.yml navigation under "Release Notes" section
- Releases are tagged with `vX.Y.Z` format (e.g., `v1.0.0`)
- Versioning follows Semantic Versioning principles (major.minor.patch)
- Major version changes for breaking changes
- Minor version changes for new features (backwards compatible)
- Patch version changes for bug fixes (backwards compatible)
- Pre-releases (alpha, beta, rc) are supported with appropriate version suffixes (e.g., `1.0.0-beta.1`)
- Releases are triggered by merging to the `main` branch or manually via GitHub workflow dispatch
- Ensure all tests pass and code is formatted before releasing
- Update `CHANGELOG.md` with any additional notes not captured in commit
- Verify release on PyPI and GitHub after Publishing

## git guidelines

- Use feature branches for new work or bug fixes
- Branch names should be descriptive, e.g. `feature/add-user-auth`, `bugfix/fix-login-error`
- Use conventional commit messages
- Commit messages should be clear and concise, following the format:
  - Title: Short summary (max 50 chars)
  - Body: Detailed description (wrap at 72 chars)
  - Footer: References to issues or breaking changes
- Squash commits when merging feature branches to keep history clean
- Regularly pull changes from `main` to keep branches up to date
- Avoid large commits; break changes into smaller, logical commits
- Review code thoroughly before merging to `main`
- Always run tests and linters before committing. including RUFF
- Use `git rebase` to maintain a linear history when updating branches

# Manual Test Scripts

This directory contains manual integration test scripts for testing specific functionality that requires manual verification or real API interactions.

## Test Scripts

### `test_auto_creation.py`
Tests automatic creation of new Paperless-ngx entities (tags, correspondents, document types, storage paths).

**Usage:**
```bash
cd tests/manual
python test_auto_creation.py
```

**Requirements:**
- Paperless-ngx configured and running
- Valid `PAPERLESS_URL` and `PAPERLESS_TOKEN` in `.env`

### `test_unique_creation.py`  
Tests creation of unique entities with UUID suffixes to ensure no conflicts.

**Usage:**
```bash
cd tests/manual
python test_unique_creation.py
```

### `test_creation_verbose.py`
Tests entity creation with verbose debug logging enabled.

**Usage:**
```bash
cd tests/manual
python test_creation_verbose.py
```

### `test_api_search.py`
Tests direct API search functionality to understand Paperless-ngx API behavior.

**Usage:**
```bash
cd tests/manual
python test_api_search.py
```

## Running All Manual Tests

You can run all manual tests from the project root:

```bash
# Run individual tests
python tests/manual/test_auto_creation.py
python tests/manual/test_unique_creation.py
python tests/manual/test_creation_verbose.py
python tests/manual/test_api_search.py
```

## Notes

- These are **manual tests** not included in the automated pytest suite
- They require actual Paperless-ngx integration and configuration
- They may create actual entities in your Paperless-ngx instance
- Use with caution in production environments

## Integration with Automated Tests

These manual tests complement the automated test suite in:
- `tests/unit/` - Unit tests (no external dependencies)
- `tests/integration/` - Integration tests (automated)

The automated tests can be run with:
```bash
pytest tests/unit/
pytest tests/integration/
```
# Pydantic V2 Migration Guide

This document describes the migration from Pydantic V1 to V2 syntax completed in the bank-statement-separator project to resolve deprecation warnings and ensure compatibility with future Pydantic versions.

## Overview

Pydantic V2 introduced significant changes to improve performance and developer experience. The main deprecations addressed were:

- Migration from `@validator` decorators to `@field_validator`
- Replacement of class-based `Config` with `ConfigDict`
- Updates to validator method signatures

## Changes Made

### 1. Validator Migration

#### Before (Pydantic V1):

```python
from pydantic import BaseModel, validator

class Config(BaseModel):
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
```

#### After (Pydantic V2):

```python
from pydantic import BaseModel, field_validator

class Config(BaseModel):
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
```

### 2. Config Class Migration

#### Before (Pydantic V1):

```python
class Config(BaseModel):
    # ... fields ...

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

#### After (Pydantic V2):

```python
from pydantic import ConfigDict

class Config(BaseModel):
    # ... fields ...

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        validate_default=True,
        extra="forbid"
    )
```

### 3. Validator with Dependencies

When validators need access to other field values:

#### Before (Pydantic V1):

```python
@validator("chunk_overlap")
def validate_chunk_overlap(cls, v, values):
    """Ensure chunk overlap is less than chunk size."""
    if "chunk_size" in values and v >= values["chunk_size"]:
        raise ValueError("Chunk overlap must be less than chunk size")
    return v
```

#### After (Pydantic V2):

```python
@field_validator("chunk_overlap")
@classmethod
def validate_chunk_overlap(cls, v: int, info) -> int:
    """Ensure chunk overlap is less than chunk size."""
    if info.data.get("chunk_size") and v >= info.data["chunk_size"]:
        raise ValueError("Chunk overlap must be less than chunk size")
    return v
```

## Key Differences

### 1. Decorator Changes

- `@validator` → `@field_validator`
- All field validators must be class methods with `@classmethod` decorator
- Type hints are now recommended for clarity

### 2. Accessing Other Fields

- V1: `values` parameter contains validated fields
- V2: `info` parameter with `info.data` containing validated fields

### 3. Configuration

- V1: Nested `Config` class
- V2: `model_config` attribute with `ConfigDict`

### 4. New ConfigDict Options

- `validate_default=True`: Validates default values
- `extra="forbid"`: Raises error for extra fields not defined in model
- `use_enum_values=True`: Uses enum values instead of enum instances
- `arbitrary_types_allowed=True`: Allows arbitrary types in model

## Import Changes

### Before:

```python
from pydantic import BaseModel, Field, validator
```

### After:

```python
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Any, Dict  # Additional imports for type hints
```

## Backward Compatibility

The migration maintains full backward compatibility:

- All existing functionality is preserved
- API remains unchanged for consumers
- Configuration loading and validation work identically
- No breaking changes for users of the Config class

## Benefits of Migration

1. **Future-Proof**: Ready for Pydantic V3 when V1 syntax is removed
2. **Performance**: V2 validators are more efficient
3. **Type Safety**: Better type hints and IDE support
4. **Cleaner Code**: More explicit and readable validation logic
5. **No Warnings**: Eliminates deprecation warnings in logs and test output

## Testing the Migration

After migration, verify:

1. **Run Tests**: All existing tests should pass

```bash
uv run pytest tests/unit/
```

2. **Check for Warnings**: No Pydantic deprecation warnings

```bash
uv run python -W default::DeprecationWarning -m pytest
```

3. **Validate Config Loading**: Configuration loads correctly

```python
from src.bank_statement_separator.config import Config
config = Config(openai_api_key="test-key")
```

## Common Migration Issues

### Issue 1: Missing @classmethod

**Error**: `TypeError: field_validator() missing 1 required positional argument`
**Solution**: Add `@classmethod` decorator to all field validators

### Issue 2: Values vs Info

**Error**: `validate_chunk_overlap() got an unexpected keyword argument 'values'`
**Solution**: Replace `values` parameter with `info` and access data via `info.data`

### Issue 3: Config Class

**Error**: `PydanticDeprecatedSince20: Support for class-based config is deprecated`
**Solution**: Replace nested `Config` class with `model_config = ConfigDict(...)`

## Additional Resources

- [Pydantic V2 Migration Guide](https://docs.pydantic.dev/latest/migration/)
- [Pydantic V2 Documentation](https://docs.pydantic.dev/latest/)
- [Field Validators Documentation](https://docs.pydantic.dev/latest/concepts/validators/)
- [ConfigDict Documentation](https://docs.pydantic.dev/latest/concepts/config/)

## Summary

The migration from Pydantic V1 to V2 was completed successfully with:

- ✅ All validators updated to V2 syntax
- ✅ Config class replaced with ConfigDict
- ✅ Type hints added for better IDE support
- ✅ All tests passing
- ✅ No deprecation warnings
- ✅ Full backward compatibility maintained

This ensures the codebase is ready for future Pydantic versions while maintaining stability and performance.

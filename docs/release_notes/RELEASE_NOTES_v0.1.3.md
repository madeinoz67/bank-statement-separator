# Release Notes v0.1.3

**Release Date**: September 7, 2025
**Version**: 0.1.3

## Overview

This release focuses on CI/CD improvements, configuration validation enhancements, and release automation setup. Key improvements include better test environment handling and comprehensive release workflow implementation.

## 🐛 Bug Fixes

- **CI Configuration**: Allow test API keys in configuration validation

  - Added intelligent test environment detection for OpenAI API key validation
  - Skip strict 'sk-' prefix validation for test keys (test-key, mock-key, etc.)
  - Automatically detect pytest execution context and bypass validation accordingly
  - Maintain production security with proper API key format validation
  - Resolves CI workflow failures with Pydantic v2 validation errors

- **Release Workflow**: Improve release workflow configuration and API key validation
  - Enhanced release workflow with proper dependency management
  - Fixed PyPI publishing dependencies by using existing dev group
  - Improved workflow trigger conditions and error handling
  - Added comprehensive release automation infrastructure

## 📚 Documentation

- **Navigation**: Add changelog to mkdocs navigation
  - Improved documentation structure with proper changelog integration
  - Enhanced navigation between release notes and changelog
  - Better organization of project documentation

## ✨ Styles & Code Quality

- **Formatting**: Apply ruff formatting to config.py
  - Consistent code formatting across configuration files
  - Applied standardized ruff formatting rules
  - Improved code readability and maintainability

## 🔧 Infrastructure Improvements

- **Release Automation**: Complete release workflow setup

  - Implemented automated release creation with GitHub Actions
  - Added PyPI publishing automation (workflow ready for future releases)
  - Enhanced release-please integration for semantic versioning

- **Test Environment**: Robust test configuration handling
  - Improved configuration validation for different environments
  - Better handling of test vs production API keys
  - Enhanced CI/CD pipeline reliability

## 📋 Technical Details

### Changes

- **Commit**: [e399ff0](https://github.com/madeinoz67/bank-statement-separator/commit/e399ff0256abafc725a7a7d551991a8dacc8612b) - Allow test API keys in configuration validation
- **Commit**: [461a61c](https://github.com/madeinoz67/bank-statement-separator/commit/461a61c93787cb1665de52ae800427852323d6ec) - Improve release workflow configuration and API key validation
- **Commit**: [0062535](https://github.com/madeinoz67/bank-statement-separator/commit/0062535eabb1e63ecf91898cde9527e55817bcd9) - Add changelog to mkdocs navigation
- **Commit**: [2bb76da](https://github.com/madeinoz67/bank-statement-separator/commit/2bb76daca5a457fa85ade054362b2dd22fe1ed92) - Apply ruff formatting to config.py

### Configuration Validation Enhancements

- Test environment detection with multiple indicators
- Support for pytest execution context detection
- Backward compatible validation for production environments
- Enhanced error messages for better debugging

### Release Infrastructure

- Complete GitHub Actions workflow for automated releases
- PyPI publishing automation (requires workflow trigger)
- Comprehensive release notes generation
- Better integration with semantic versioning

### Compatibility

- No breaking changes to existing APIs
- Enhanced configuration validation maintains backward compatibility
- Improved CI/CD pipeline reliability

## ⚠️ Known Issues

- Release workflow was added after v0.1.3 tag creation, so PyPI publishing for this version requires manual trigger
- Future releases will automatically trigger the complete release workflow

---

[← Previous Version (v0.1.2)](RELEASE_NOTES_v0.1.2.md) | [Changelog](CHANGELOG.md)

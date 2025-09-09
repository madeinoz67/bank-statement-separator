# Release Notes v0.1.4

**Release Date**: September 7, 2025
**Version**: 0.1.4

## Overview

This release focuses on enhancing the release workflow infrastructure with comprehensive debugging capabilities and improved PyPI publishing automation. Key improvements include better error diagnostics, workflow condition simplification, and enhanced package verification processes.

## 🐛 Bug Fixes

- **Release Workflow Enhancement**: Comprehensive improvements to GitHub Actions release workflow

  - Added detailed debugging output for workflow context analysis
  - Simplified job conditions from complex boolean logic to clear `startsWith()` checks
  - Enhanced error handling with explicit checks for missing PYPI_API_TOKEN secret
  - Improved package verification with `twine check` validation before upload
  - Added verbose upload logging for better error diagnostics
  - Implemented optional `skip_pypi` input for manual workflow dispatch testing

- **PyPI Publishing Debugging**: Enhanced release workflow with PyPI publishing debugging
  - Comprehensive debugging output to identify workflow execution issues
  - Better job condition logic using `startsWith(github.ref, 'refs/tags/v')`
  - Enhanced package build and verification steps
  - Improved error messaging and diagnostic information

## 🔧 Infrastructure Improvements

- **Automated Release Process**: Complete release workflow automation ready for production use

  - Fixed workflow trigger conditions that prevented PyPI publishing in previous versions
  - Enhanced GitHub Actions workflow with proper dependency management
  - Improved release creation with better file attachment handling
  - Added comprehensive logging throughout the release process

- **Error Diagnostics**: Advanced debugging capabilities for release troubleshooting
  - Detailed workflow context output for identifying execution issues
  - Enhanced error reporting for missing secrets and configuration problems
  - Better visibility into release process steps and potential failure points

## 📋 Technical Details

### Changes

- **Commit**: [f7753dd](https://github.com/madeinoz67/bank-statement-separator/commit/f7753dd7ff7be554a38417635b9f3f00828515fd) - Enhance release workflow with debugging and improved PyPI publishing
- **Commit**: [4f531c9](https://github.com/madeinoz67/bank-statement-separator/commit/4f531c998c1aa9375b7e189de12907122e1ca9c6) - Enhance release workflow with PyPI publishing debugging

### Release Infrastructure Enhancements

- **Workflow Debugging**: Added comprehensive debug output for all workflow steps
- **Job Conditions**: Simplified complex conditions to `startsWith(github.ref, 'refs/tags/v')`
- **Package Verification**: Enhanced with `twine check` before PyPI upload
- **Error Handling**: Explicit validation of PYPI_API_TOKEN availability
- **Verbose Logging**: Detailed output for troubleshooting upload issues

### Workflow Improvements

- Enhanced concurrency control to prevent multiple releases for same tag
- Improved timeout settings for better resource management
- Better separation between release creation and PyPI publishing jobs
- Added manual workflow dispatch capability with configurable options

### Compatibility

- No breaking changes to existing APIs or functionality
- Enhanced release process maintains backward compatibility
- Improved workflow ready for future automated releases
- Seamless upgrade from previous versions

## ⚠️ Important Notes

- **Release Workflow Ready**: This version includes the complete release workflow infrastructure that was missing in v0.1.3
- **Future Releases**: All future releases will automatically trigger the complete release workflow including PyPI publishing
- **Debugging Enhanced**: Comprehensive debugging output helps identify and resolve any remaining release issues

## 🚀 Next Steps

With this release, the complete automated release infrastructure is now in place:

1. **Automated PyPI Publishing**: Future releases will automatically publish to PyPI
2. **Enhanced Error Handling**: Better diagnostics for troubleshooting release issues
3. **Complete Workflow**: Full GitHub Actions integration for releases, testing, and publishing

---

[← Previous Version (v0.1.3)](RELEASE_NOTES_v0.1.3.md) | [Changelog](CHANGELOG.md)

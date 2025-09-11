# Release Notes v0.3.1

**Release Date:** September 11, 2025
**Version:** 0.3.1

## 🔧 Bug Fixes

### Version Loading Improvements
- **Enhanced exception handling structure in version loading** - Improved error handling for cases where version information cannot be loaded from pyproject.toml
- **Implemented dynamic version loading from pyproject.toml** - The application now dynamically loads version information from pyproject.toml instead of hardcoding it, ensuring version consistency across the codebase

### Documentation Fixes
- **Fixed code block syntax formatting** - Corrected quadruple backticks to proper triple backticks in documentation
- **Standardized markdown admonition block formatting** - Consistent formatting across all documentation files for better readability

## 📋 Summary

This patch release focuses on improving the reliability of version loading and fixing documentation formatting issues. The key improvement is the implementation of dynamic version loading that ensures version consistency between the package metadata and the application runtime.

## 🔄 Migration Notes

No migration steps required for this patch release. All changes are backwards compatible.

## 🐛 Known Issues

No new known issues identified in this release.

## 💬 Feedback

Found a bug or have a suggestion? Please [open an issue](https://github.com/madeinoz67/bank-statement-separator/issues) on GitHub.

---

**Full Changelog**: [v0.3.0...v0.3.1](https://github.com/madeinoz67/bank-statement-separator/compare/v0.3.0...v0.3.1)

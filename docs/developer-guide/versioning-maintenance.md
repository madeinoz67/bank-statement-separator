# Documentation Versioning Maintenance

This guide covers the maintenance and management of versioned documentation for the Bank Statement Separator project.

## Overview

The documentation versioning system automatically creates versioned copies of the documentation for each software release, ensuring users can access accurate documentation that matches their installed version.

## How Versioning Works

### Automatic Version Creation

1. **Release Trigger**: When a GitHub release is published (e.g., `v2.3.0`)
2. **Documentation Build**: MkDocs builds the documentation with version-specific configuration
3. **Versioned Deployment**: Documentation is deployed to `/v2.3/` directory on GitHub Pages
4. **Version Selector Update**: The version selector is automatically updated with the new version

### URL Structure

```
https://madeinoz67.github.io/bank-statement-separator/
├── /                    # Latest (main branch)
├── /v2.3/              # Version 2.3.x documentation
├── /v2.2/              # Version 2.2.x documentation
├── /v2.1/              # Version 2.1.x documentation
└── /versions.json      # Version metadata
```

## Version Management

### Supported Versions

- **Latest**: Always points to the most recent release
- **Last 3 Major Versions**: v2.1, v2.2, v2.3 (current)
- **Long-term Support (LTS)**: Versions with extended support

### Version Lifecycle

1. **Active**: Currently supported versions
2. **Maintenance**: Security updates only
3. **Deprecated**: No longer supported (redirect to latest)
4. **Archived**: Removed from active hosting

## Maintenance Tasks

### Monthly Tasks

- [ ] Review version usage analytics
- [ ] Update version selector if needed
- [ ] Check for broken links in versioned docs
- [ ] Verify version-specific content accuracy

### Release Tasks

- [ ] Test documentation build for new version
- [ ] Verify version selector includes new version
- [ ] Update version metadata in `versions.json`
- [ ] Check cross-version navigation links

### Annual Tasks

- [ ] Archive versions older than 2 years
- [ ] Update version support policy
- [ ] Review and optimize GitHub Pages storage

## Manual Version Deployment

### Deploy Specific Version

1. Go to GitHub Actions → "Deploy Versioned Documentation"
2. Click "Run workflow"
3. Enter version (e.g., `v2.3.0`)
4. Click "Run workflow"

### Update Version Metadata

```json
{
  "versions": ["v2.3", "v2.2", "v2.1"],
  "latest": "v2.3",
  "last_updated": "2025-01-06T10:00:00Z"
}
```

## Troubleshooting

### Common Issues

#### Version Not Appearing in Selector

1. Check if version was deployed to correct directory
2. Verify `versions.json` includes the version
3. Clear browser cache and reload

#### Broken Links in Versioned Docs

1. Check if links use relative paths
2. Verify version-specific edit links are correct
3. Test links in deployed version

#### Documentation Build Failures

1. Check MkDocs configuration for version-specific settings
2. Verify all assets (CSS, JS) are accessible
3. Check for version-specific content that may be missing

### Version Recovery

If a version needs to be redeployed:

1. Checkout the release tag: `git checkout v2.3.0`
2. Build documentation: `mkdocs build`
3. Deploy manually using GitHub Actions workflow dispatch

## Best Practices

### Content Management

- **Version-Specific Content**: Use conditional content for version differences
- **Relative Links**: Always use relative links within documentation
- **Asset Management**: Ensure all assets are version-agnostic or properly versioned

### SEO and Discovery

- **Sitemap**: Each version has its own sitemap
- **Meta Tags**: Version-specific meta descriptions
- **Canonical URLs**: Point to latest version for SEO

### User Experience

- **Clear Version Indicators**: Show current version prominently
- **Easy Switching**: One-click version switching
- **Consistent Navigation**: Same navigation structure across versions

## Monitoring and Analytics

### Version Usage Tracking

```javascript
// Track version usage
gtag('event', 'version_view', {
  version: getCurrentVersion(),
  page_path: window.location.pathname
});
```

### Performance Monitoring

- Page load times by version
- Broken link detection
- User engagement metrics

## Migration Guide

### Upgrading from Non-Versioned Docs

1. **Initial Setup**: Deploy current docs as "latest"
2. **First Release**: Create first versioned deployment
3. **Version Selector**: Add to all documentation pages
4. **URL Redirects**: Set up redirects from old URLs

### Content Migration

- **Identify Version Differences**: Document features that changed between versions
- **Conditional Content**: Use MkDocs macros for version-specific content
- **Cross-References**: Ensure links work across versions

## Automated Semantic Versioning

The project now uses automated semantic versioning with release-please to streamline the release process.

### How It Works

1. **Conventional Commits**: All commits follow conventional commit format (`feat:`, `fix:`, etc.)
2. **Automated Analysis**: Release-please analyzes commits on push to main branch
3. **Release PR Creation**: Creates/updates a release PR with changelog and version bump
4. **Automated Release**: When release PR is merged, creates tag and triggers full release workflow

### Version Bump Rules

- **PATCH** (1.0.0 → 1.0.1): `fix:` commits
- **MINOR** (1.0.0 → 1.1.0): `feat:` commits
- **MAJOR** (1.0.0 → 2.0.0): `BREAKING CHANGE:` footer in commit

### Configuration Files

- `release-please-config.json`: Release configuration
- `.release-please-manifest.json`: Current version tracking
- `.github/workflows/release-please.yml`: Automation workflow

### Manual Release Override

For urgent releases or special cases, you can still create manual tags:

```bash
git tag v1.2.3
git push origin v1.2.3
```

This will trigger the existing release workflow without going through release-please.

## Future Enhancements

### Planned Features

- [ ] Automatic version deprecation warnings
- [ ] Version comparison tool
- [ ] Documentation diff viewer
- [ ] Automated link checking across versions
- [ ] Version-specific search indexing

### Integration Opportunities

- [x] Integration with semantic versioning ✅
- [x] Automated changelog generation ✅
- [ ] Version-specific API documentation
- [ ] Multi-language version support

## Support

For issues with documentation versioning:

1. Check this maintenance guide
2. Review GitHub Actions workflow logs
3. Create an issue in the repository
4. Contact the documentation maintainers

## Quick Reference

### Commands

```bash
# Build versioned docs locally
mkdocs build

# Serve docs locally
mkdocs serve

# Deploy specific version
# Use GitHub Actions workflow dispatch
```

### File Locations

- Version selector: `docs/javascripts/version-selector.js`
- Version styles: `docs/stylesheets/version-selector.css`
- Version data: `docs/versions.json`
- Workflows: `.github/workflows/docs-versioned.yml`

### Key URLs

- Latest docs: `https://madeinoz67.github.io/bank-statement-separator/`
- Version docs: `https://madeinoz67.github.io/bank-statement-separator/v{VERSION}/`
- Repository: `https://github.com/madeinoz67/bank-statement-separator`

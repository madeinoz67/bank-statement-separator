# Mike Documentation Deployment Strategy

## Overview

This document outlines the deployment strategy for versioned documentation using [mike](https://github.com/jimporter/mike) and GitHub Actions to prevent race conditions and conflicts with the `gh-pages` branch.

## Problem Statement

### Race Condition Issues

When using mike with GitHub Actions, several race condition issues can occur:

1. **Concurrent Deployments**: Multiple workflow runs attempting to deploy to `gh-pages` simultaneously
2. **Git Conflicts**: Direct `--push` operations that don't handle conflicts properly
3. **Incomplete Deployments**: Failed pushes leaving documentation in inconsistent states
4. **Version Selector Issues**: Multiple jobs updating version metadata concurrently

### Root Causes

- **Direct Push Operations**: Using `mike deploy --push` bypasses Git's conflict resolution
- **Missing Fetch Operations**: Not fetching latest `gh-pages` state before deployment
- **Inadequate Concurrency Controls**: Multiple workflows competing for the same branch
- **No Retry Logic**: Single-attempt deployments failing on temporary conflicts
- **Corrupted Branch State**: Mike's internal metadata becoming corrupted causing `string indices must be integers, not 'str'` errors
- **Version Schema Conflicts**: Using conflicting version names (e.g., "main" vs "latest") that confuse mike's internal logic

## Solution Architecture

### 1. Robust Deployment Pattern

```bash
# ❌ Problematic approach
uv run mike deploy --push --update-aliases latest main
uv run mike set-default --push latest

# ✅ Robust approach
# Step 1: Deploy locally (no push)
uv run mike deploy --update-aliases latest main
uv run mike set-default latest

# Step 2: Push with conflict resolution and retry
max_attempts=3
attempt=1

while [ $attempt -le $max_attempts ]; do
  git fetch origin gh-pages:gh-pages || true

  if git push origin gh-pages; then
    echo "✅ Successfully deployed on attempt $attempt"
    break
  else
    # Handle conflicts and retry
    sleep_time=$((2 ** attempt))
    sleep $sleep_time

    # Resolve conflicts
    git checkout gh-pages || true
    git pull --rebase origin gh-pages || git reset --hard origin/gh-pages

    # Re-deploy if needed
    uv run mike deploy --update-aliases latest main
    uv run mike set-default latest
  fi

  attempt=$((attempt + 1))
done
```

### 2. Concurrency Control

```yaml
# Prevent all gh-pages conflicts
concurrency:
  group: docs-deployment-gh-pages
  cancel-in-progress: false
```

### 3. Pre-deployment Setup

```bash
# Configure Git properly
git config --local user.email "action@github.com"
git config --local user.name "GitHub Action"
git config --local pull.rebase false

# Fetch latest gh-pages state
git fetch origin gh-pages:gh-pages || git checkout --orphan gh-pages || true
```

## Implementation Details

!!! success "Current Implementation Status"
The `docs-versioned.yml` workflow has been **updated** to implement this robust deployment strategy as of January 2025. The workflow now uses local deployment followed by retry logic with conflict resolution.

### Latest Documentation Deployment

```bash
# 1. Fetch and prepare gh-pages branch
git fetch origin gh-pages:gh-pages || git checkout --orphan gh-pages || true

# 2. Deploy locally (no push)
uv run mike deploy --update-aliases latest
uv run mike set-default latest

# 3. Push with retry logic (3 attempts with exponential backoff)
max_attempts=3
attempt=1

while [ $attempt -le $max_attempts ]; do
  # Fetch latest changes before push attempt
  git fetch origin gh-pages:gh-pages || true

  if git push origin gh-pages; then
    echo "✅ Successfully deployed on attempt $attempt"
    break
  else
    if [ $attempt -eq $max_attempts ]; then
      echo "❌ All attempts failed. Manual intervention required."
      exit 1
    fi

    # Exponential backoff
    sleep_time=$((2 ** attempt))
    sleep $sleep_time

    # Resolve conflicts and retry
    git checkout gh-pages || true
    git pull --rebase origin gh-pages || git reset --hard origin/gh-pages

    # Re-deploy locally after conflict resolution
    uv run mike deploy --update-aliases latest
    uv run mike set-default latest
  fi

  attempt=$((attempt + 1))
done
```

### Versioned Documentation Deployment

```bash
# Similar pattern but for specific versions
VERSION="1.2.3"  # From workflow input/release

# 1. Fetch and prepare gh-pages branch
git fetch origin gh-pages:gh-pages || git checkout --orphan gh-pages || true

# 2. Deploy version locally (no push)
uv run mike deploy --update-aliases "v$VERSION" "$VERSION"

# 3. Push with same retry logic as above
max_attempts=3
attempt=1

while [ $attempt -le $max_attempts ]; do
  git fetch origin gh-pages:gh-pages || true

  if git push origin gh-pages; then
    echo "✅ Successfully deployed version $VERSION on attempt $attempt"
    break
  else
    # Same error handling and retry logic as latest deployment
    # ... (exponential backoff, conflict resolution, re-deployment)
  fi

  attempt=$((attempt + 1))
done
```

### Version Selector Updates

The version selector (`versions.json`) is updated separately with its own retry logic:

1. Extract current versions from mike's gh-pages branch
2. Generate updated versions.json on main branch
3. Push to main branch with retry logic
4. Separate from gh-pages deployment to avoid conflicts

## Benefits

### 1. Conflict Resolution

- Automatic handling of Git conflicts during deployment
- Proper fetching of latest changes before push attempts
- Fallback to hard reset when rebase fails

### 2. Reliability

- Exponential backoff retry logic (2, 4, 8 seconds)
- Multiple deployment attempts (up to 3)
- Clear success/failure indicators in logs

### 3. Consistency

- Single concurrency group prevents simultaneous deployments
- Atomic operations ensure consistent documentation state
- Proper error handling prevents partial deployments

### 4. Observability

- Detailed logging of each deployment attempt
- Clear indication of retry attempts and reasons
- Success confirmation messages

## Monitoring and Troubleshooting

### Success Indicators

- `✅ Successfully deployed on attempt X` messages
- No deployment errors in workflow logs
- Documentation accessible on GitHub Pages

### Common Issues

#### Issue: "Failed to push some refs"

```
error: failed to push some refs to 'https://github.com/user/repo'
hint: Updates were rejected because the remote contains work that you do not have locally
```

**Solution**: The retry logic automatically handles this by:

1. Fetching latest changes
2. Rebasing or resetting local branch
3. Re-deploying and retrying push

#### Issue: "All attempts failed"

```
❌ All attempts failed. Manual intervention required.
```

**Solution**:

1. Check GitHub Pages settings
2. Verify repository permissions
3. Manually reset gh-pages branch if corrupted
4. Re-run workflow after investigation

#### Issue: "string indices must be integers, not 'str'"

```
error: string indices must be integers, not 'str'
```

**Root Cause**: Mike's internal metadata in gh-pages branch is corrupted, often caused by:

- Inconsistent version naming schemes
- Manual gh-pages branch modifications
- Failed previous deployments leaving incomplete state
- Using conflicting alias names (e.g., "main" as both branch and alias)

**Solution**:

1. **Reset gh-pages branch** in workflow:
   ```bash
   git branch -D gh-pages 2>/dev/null || true
   git push origin --delete gh-pages 2>/dev/null || true
   ```
2. **Use consistent version naming**: Avoid "main" as version alias
3. **Test with fresh branch**: Deploy to test branch first to verify fix
4. **Use simplified commands**:
   ```bash
   # Instead of: mike deploy --update-aliases latest main
   uv run mike deploy latest
   uv run mike set-default latest
   ```

#### Issue: Version selector not updating

- Check main branch push permissions
- Verify versions.json generation logic
- Review mike list output for available versions

## Best Practices

### 1. Deployment Timing

- Use concurrency controls to prevent overlapping deployments
- Allow adequate timeout for deployment completion (15-20 minutes)
- Avoid triggering multiple deployments simultaneously

### 2. Branch Management

- Keep gh-pages branch clean and automated-only
- Don't manually modify gh-pages branch
- Use main branch for versions.json updates

### 3. Error Handling

- Always include retry logic for push operations
- Provide clear error messages and troubleshooting steps
- Set appropriate timeout values for long deployments

### 4. Testing

- Test deployment workflows in feature branches
- Use workflow_dispatch for manual testing
- Verify documentation accessibility after deployment

## Migration from Direct Push

If migrating from direct `--push` deployments:

1. **Update workflow files** to use the new pattern
2. **Test thoroughly** with workflow_dispatch before merging
3. **Monitor first few deployments** for any issues
4. **Document any project-specific customizations**

### Handling Corrupted Mike State

If encountering `"string indices must be integers, not 'str'"` errors:

1. **Reset Strategy** (Recommended for corrupted state):

   ```yaml
   - name: Reset corrupted gh-pages branch state
     run: |
       git branch -D gh-pages 2>/dev/null || true
       git push origin --delete gh-pages 2>/dev/null || true

   - name: Deploy with clean state
     run: |
       uv run mike deploy --push latest
       uv run mike set-default --push latest
   ```

2. **Prevention**:
   - Avoid manual gh-pages modifications
   - Use consistent version naming conventions
   - Don't use git branch names as mike aliases
   - Test deployments in isolated environments first

## Security Considerations

- Use minimal required permissions (`contents: write`)
- Avoid exposing secrets in deployment logs
- Validate input versions to prevent injection attacks
- Use official actions with pinned versions

## Performance Optimization

- Cache mike dependencies when possible
- Use parallel jobs for independent operations
- Minimize redundant git operations
- Set appropriate timeouts to prevent hanging workflows

---

This strategy provides a robust, conflict-resistant approach to mike documentation deployment that handles race conditions gracefully while maintaining deployment reliability.

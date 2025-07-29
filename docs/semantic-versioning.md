# Semantic Versioning Guide

This project uses [python-semantic-release](https://python-semantic-release.readthedocs.io/) for automated version management and releases.

## Overview

- **Production releases**: Automatically created from the `master` branch
- **Beta releases**: Automatically created from the `staging` branch with `-beta.X` suffix
- **Version source**: Git tags (managed automatically)

## Commit Message Format

This project follows the [Conventional Commits](https://www.conventionalcommits.org/) specification. The commit message format determines the version bump:

### Version Bumps

- **Patch Release (0.0.X)**: Bug fixes and minor changes
  ```
  fix: correct SQL query in tracker module
  fix(models): resolve foreign key constraint issue
  ```

- **Minor Release (0.X.0)**: New features (backwards compatible)
  ```
  feat: add support for environment variables tracking
  feat(cli): implement data export command
  ```

- **Major Release (X.0.0)**: Breaking changes
  ```
  feat!: change database schema for better performance
  BREAKING CHANGE: The API now requires authentication
  ```

### Other Commit Types (no version bump)

- `docs:` Documentation changes
- `style:` Code style changes (formatting, semicolons, etc.)
- `refactor:` Code refactoring without changing functionality
- `perf:` Performance improvements
- `test:` Adding or modifying tests
- `build:` Build system changes
- `ci:` CI/CD configuration changes
- `chore:` Other changes that don't affect source code

## Release Process

### Automatic Releases

1. **For Production Release (master)**:
   - Merge PR into `master` branch
   - GitHub Actions automatically:
     - Analyzes commits since last release
     - Determines version bump type
     - Creates new version tag
     - Generates changelog
     - Publishes to PyPI (if configured)
     - Creates GitHub release

2. **For Beta Release (staging)**:
   - Merge PR into `staging` branch
   - Same process but creates versions like `1.2.3-beta.1`

### Manual Version Override

If needed, you can manually trigger a specific version:
```bash
# Install python-semantic-release
pip install python-semantic-release

# Force a specific version
semantic-release publish --force-level minor
```

## Configuration

The semantic versioning is configured in:

1. **pyproject.toml**: Main configuration for python-semantic-release
2. **.releaserc.json**: Additional release configuration
3. **.github/workflows/release.yml**: GitHub Actions workflow

## Local Development

To test version generation locally:
```bash
# See what version would be generated
semantic-release version --print

# See next version without creating it
semantic-release version --print-last-released
```

## Troubleshooting

1. **No release created**: Check that your commit messages follow the conventional format
2. **Wrong version bump**: Ensure breaking changes are properly marked with `!` or `BREAKING CHANGE:`
3. **Beta versions on master**: Make sure you're working on the correct branch

## Examples

### Feature Development Workflow
```bash
# Create feature branch from staging
git checkout staging
git pull origin staging
git checkout -b feat/new-feature

# Make changes and commit
git add .
git commit -m "feat: add new tracking capability"

# Push and create PR to staging
git push origin feat/new-feature
# Create PR to staging branch for beta testing

# After testing, create PR from staging to master for production release
```

### Hotfix Workflow
```bash
# Create hotfix branch from master
git checkout master
git pull origin master
git checkout -b fix/critical-bug

# Make fix and commit
git add .
git commit -m "fix: resolve critical data loss issue"

# Push and create PR directly to master
git push origin fix/critical-bug
# Create PR to master branch for immediate release
```

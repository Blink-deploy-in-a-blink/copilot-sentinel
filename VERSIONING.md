# Version Management Guide

## How to Release a New Version

### 1. Update VERSION File
```bash
# Edit VERSION file with new version number
echo "1.1.0" > VERSION
```

### 2. Update CHANGELOG.md
Add entry under `## [Unreleased]` or create new version section:

```markdown
## [1.1.0] - 2026-01-15

### Added
- New feature X
- New feature Y

### Changed
- Updated behavior of Z

### Fixed
- Bug in component A
```

### 3. Commit and Tag
```bash
git add VERSION CHANGELOG.md
git commit -m "Release v1.1.0"
git tag -a v1.1.0 -m "Version 1.1.0: Brief description"
git push origin main
git push origin v1.1.0
```

### 4. Create GitHub Release (Optional)
1. Go to GitHub → Releases → "Draft a new release"
2. Select tag `v1.1.0`
3. Copy changelog entry as release notes
4. Publish release

---

## Version Number Guidelines

Follow [Semantic Versioning](https://semver.org/):

**MAJOR.MINOR.PATCH**

### MAJOR (e.g., 1.0.0 → 2.0.0)
Breaking changes that require user action:
- Changed command names
- Removed commands
- Changed file formats (incompatible)
- Changed workflow (incompatible)

**Example:** Renamed `wrapper` command to `sentinel`

### MINOR (e.g., 1.0.0 → 1.1.0)
New features (backwards-compatible):
- New commands
- New optional features
- Enhanced existing features
- New file fields (optional)

**Example:** Added `wrapper snapshot` command

### PATCH (e.g., 1.0.0 → 1.0.1)
Bug fixes only (backwards-compatible):
- Fixed bugs
- Fixed typos in output
- Performance improvements
- Documentation fixes

**Example:** Fixed UTF-8 encoding issue

---

## Quick Reference

```bash
# Check current version
wrapper --version

# Release patch (bug fixes)
echo "1.0.1" > VERSION
# Update CHANGELOG.md
git commit -am "Release v1.0.1: Fix encoding issue"
git tag v1.0.1
git push && git push --tags

# Release minor (new features)
echo "1.1.0" > VERSION
# Update CHANGELOG.md
git commit -am "Release v1.1.0: Add snapshot command"
git tag v1.1.0
git push && git push --tags

# Release major (breaking changes)
echo "2.0.0" > VERSION
# Update CHANGELOG.md
git commit -am "Release v2.0.0: Rename to sentinel"
git tag v2.0.0
git push && git push --tags
```

---

## Changelog Template

When making changes, add to `## [Unreleased]` section:

```markdown
## [Unreleased]

### Added
- New feature or command

### Changed
- Modification to existing feature

### Deprecated
- Feature marked for removal

### Removed
- Deleted feature

### Fixed
- Bug fix

### Security
- Security patch
```

Then on release, rename `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` and create new `[Unreleased]` section.

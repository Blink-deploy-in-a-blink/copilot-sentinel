# Changelog

All notable changes to Copilot Sentinel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-01-11

### Added
- **Automatic Baseline Capture**: First `wrapper verify` auto-scans repository and generates `baseline_snapshot.json`
- **Auto-Generated Deviations**: LLM compares architecture vs baseline, creates `deviations.yaml` automatically
- **Cross-Repo Dependency Blocking**: `wrapper sync-external` reads deviations from dependency repos and blocks work if high-severity issues exist
- **Smart Deviation Resolution**: `wrapper accept` uses LLM to auto-update which deviations were resolved by each step
- **Copilot Output File**: `copilot_output.txt` template for pasting AI responses (required for verification-only steps)
- **First Verification Always Passes**: Baseline verification documents current state without failing
- **New Commands**:
  - `wrapper snapshot`: Manual baseline capture
  - `wrapper diff-baseline`: Compare current state vs baseline

### Changed
- `.wrapper/` files (architecture.md, step.yaml, etc.) now ignored by file change verification
- `wrapper verify` requires `copilot_output.txt` for verification steps with no git diff
- `wrapper propose` includes baseline snapshot and deviation context in LLM prompt
- `wrapper sync-external` extracts deviations and computes blockers from dependency repos
- All file I/O now uses UTF-8 encoding explicitly (fixes Windows compatibility)

### Fixed
- Import errors in snapshot.py and verify.py (missing `wrapper.` prefix)
- Character encoding issues on Windows (charmap codec errors)
- Removed non-existent `get_repo_root()` function call

## [0.1.0] - 2025-12-XX (Initial Release)

### Added
- Initial CLI tool with basic propose → compile → verify → accept workflow
- LLM-based step proposal system
- Git diff verification against allowed files
- State tracking with `state.json`
- External repo state syncing
- Support for DeepSeek, OpenAI, and Anthropic LLMs
- Template generation with `wrapper init`

---

## Version Numbering

**Format:** MAJOR.MINOR.PATCH

- **MAJOR**: Breaking changes (incompatible API/workflow changes)
- **MINOR**: New features (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

**Current stable:** v1.0.0

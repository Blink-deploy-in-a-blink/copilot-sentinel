# Changelog

All notable changes to Copilot Sentinel will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.0] - 2026-01-30

### Added
- **Feature Testing System** (`wrapper test`)
  - Test completed features against implementation plan
  - Interactive menu to test phases, steps, or all work
  - LLM analyzes actual code files for logic bugs
  - Verifies features, requirements, and security
  - Only tests completed steps (plan-aware)
- **Implementation Tracking** in `wrapper accept`
  - Captures files changed automatically from git diff
  - Prompts for optional implementation notes
  - Stores in implementation plan for testing reference
- **Direct Step Testing** (`wrapper test --step <step-id>`)
  - Test specific step by ID
  - Useful for CI/CD integration

### Changed
- `wrapper accept` now captures implementation metadata
- Implementation plan tracks `files_changed` and `implementation_notes` per step

### Fixed
- None

## [1.1.0] - 2026-01-30

### Added
- **Interactive Planning System** (`wrapper plan init`)
  - High-level phase breakdown with LLM assistance
  - Detailed step planning with features and requirements
  - Non-functional requirements templates (security, performance, cost)
  - User can refine phases (reorder, merge, split)
  - Captures planning context and user preferences
- **Plan-Driven Propose** (`wrapper propose --from-plan`)
  - Automatically reads next step from implementation plan
  - Generates step.yaml with features and requirements
  - Tracks plan progress
  - Falls back to legacy mode with `--no-plan` flag
- **Logic Verification** (`wrapper verify --check-logic`)
  - Verifies features checklist against git diff
  - Checks non-functional requirements (security, performance, cost)
  - Detects missing or incomplete implementations
  - Identifies logic errors
- **Plan Progress Tracking**
  - `wrapper plan status` - Show completion percentage
  - `wrapper plan show` - Visual plan tree
  - Plan updated automatically on `wrapper accept`
- **Enhanced Prompts**
  - copilot_prompt.txt now includes non-functional requirements
  - Security requirements marked as NON-NEGOTIABLE
  - Performance and cost optimization guidance included

### Changed
- `wrapper propose` now checks for implementation plan by default
- `wrapper verify` automatically runs logic verification if features present
- `wrapper accept` updates implementation plan progress
- `wrapper compile` includes non-functional requirements in prompts

### Fixed
- None

## [1.0.5] - 2026-01-12

### Fixed
- Verification prompt now explicitly ignores .wrapper/ file mentions in AI output
- Added clarification that .wrapper/ files are metadata and NOT code violations
- Strengthened instruction to only check allowed_files for CODE files, not metadata

## [1.0.4] - 2026-01-12

### Fixed
- Propose now explicitly blocks creation of documentation/deviation report files
- Added reminder that deviations are already in .wrapper/deviations.yaml
- Strengthened rule to propose FIXES after verification, not more documentation
- Added critical reminders section to prevent duplicate analysis steps

## [1.0.3] - 2026-01-12

### Fixed
- Compile template now explicitly marks verification step files as "READ-ONLY - for analysis"
- Verification prompts now say "ANALYZE ONLY - do NOT create/modify files"
- Propose rules clarified: verification steps analyze files, implementation steps modify files
- Removed contradictory instructions about file creation in verification steps

## [1.0.2] - 2026-01-12

### Fixed
- Propose now enforces max 2 verification steps before requiring implementation/cleanup
- Propose explicitly shows verification step count to LLM to prevent endless verification loops
- Compile prompt now instructs AI NOT to create documentation files in .wrapper/
- Verification analysis now outputs directly to copilot_output.txt instead of creating files

### Changed
- Verification step limit prominently displayed in propose prompt
- Template prompts updated to discourage file creation for verification steps

## [1.0.1] - 2026-01-12

### Fixed
- Git diff operations now use UTF-8 encoding explicitly (prevents Windows charmap decode errors)
- Git diff now excludes `.wrapper/` directory by default (prevents false verification failures)
- LLM verification prompt explicitly instructs to ignore `.wrapper/` file operations
- Verification no longer flags `.wrapper/` metadata file creation as constraint violation

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

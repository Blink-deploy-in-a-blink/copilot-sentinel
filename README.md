# Copilot Sentinel

**A stateful AI workflow discipline engine with deterministic git-diff guardrails and LLM-based semantic review.**

This is not a formal static analyzer, not a full architecture enforcement engine, and not a CI replacement. It's a workflow wrapper that turns chaotic AI-assisted coding into an auditable, step-by-step process with hard gates on file modifications and soft gates on architectural compliance. It tracks what you've done, what you're doing, and blocks you from breaking rules—using git as the source of truth and LLMs as semantic reviewers.

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/Blink-deploy-in-a-blink/copilot-sentinel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

AI coding assistants (Copilot, Claude, Cursor, ChatGPT) are powerful but chaotic:

- **No audit trail** - You can't prove what changed or why
- **Architectural drift** - AI doesn't know your rules and makes changes that violate your design
- **Random file edits** - AI modifies files you didn't expect
- **Cross-repo inconsistency** - Changes in one repo break assumptions in another
- **No verification** - You paste AI code and hope it's correct

Result: **Fast iteration with invisible technical debt.**

---

## What This Tool Actually Enforces

### Deterministic (Hard) Guarantees

These cannot be bypassed:

1. ✅ **File modification allowlist** - Only files in `step.yaml` can be changed (git diff checked)
2. ✅ **Accept blocking** - Cannot run `wrapper accept` without passing `wrapper verify`
3. ✅ **Cross-repo state sync** - External repo state is read from filesystem, not guessed
4. ✅ **Append-only audit log** - `state.json` tracks every accepted step with timestamp

### Soft (LLM-Based) Guarantees

These rely on LLM interpretation and can be tricked:

1. ⚠️ **Architecture compliance** - LLM compares your code to `architecture.md` (natural language)
2. ⚠️ **Logic verification** - LLM checks if features are implemented correctly
3. ⚠️ **Forbidden pattern detection** - Keyword search + LLM analysis (e.g., "no HTTP" → searches for `app.get()`)
4. ⚠️ **Deviation detection** - LLM scans your codebase and lists architecture violations

**Key insight**: File-level enforcement is strict. Everything else is guidance.

---

## Mental Model

```
┌─────────────────────────────────────────────────────────────┐
│  BASELINE CAPTURE (first run only)                          │
│  - Scans repo filesystem                                    │
│  - LLM generates deviations.yaml (violations of arch.md)   │
│  - Always passes (just documenting reality)                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  STEP PROPOSAL                                               │
│  - LLM reads deviations.yaml, proposes next fix             │
│  - OR: Read from implementation_plan.yaml                   │
│  - Creates step.yaml (goal, allowed files, features)        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  PROMPT COMPILATION                                          │
│  - Converts step.yaml into copilot_prompt.txt               │
│  - You give this to AI, paste response in copilot_output.txt│
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  VERIFICATION (git diff + LLM review)                        │
│  - Git diff: Only allowed_files changed? ✅ Hard gate       │
│  - LLM: Does diff match goal? ⚠️  Soft gate                │
│  - LLM: Are features implemented? ⚠️  Soft gate            │
│  - Result: PASS or FAIL → stored in state.json              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│  ACCEPTANCE (state update)                                   │
│  - BLOCKED if verify status != PASS ✅ Hard gate            │
│  - Appends step to state.json (audit log)                   │
│  - Updates deviations.yaml (marks resolved)                 │
│  - Updates implementation_plan.yaml (marks complete)         │
└─────────────────────────────────────────────────────────────┘
                          ↓
                   (repeat until done)
```

---

## 60-Second Example

```bash
# 1. Initialize (one-time setup)
$ wrapper init
# Creates .wrapper/architecture.md and .wrapper/repo.yaml
# Edit these to define your target architecture

# 2. First verification (baseline capture)
$ wrapper propose
# LLM proposes: "verify-baseline" step

$ wrapper compile
# Generates copilot_prompt.txt (give to AI)

$ wrapper verify
# ✅ PASS - Baseline captured
#    Found 13 deviations from architecture
#    Saved to .wrapper/deviations.yaml

$ wrapper accept
# ✅ Step accepted

# 3. Fix first deviation
$ wrapper propose
# LLM reads deviations.yaml
# Proposes: "remove-flask-server" (fixes http-server-present)

$ wrapper compile
# Generates prompt: "Remove Flask app from src/main.py"

# Give prompt to AI, paste response in copilot_output.txt
# Make the changes AI suggests

$ wrapper verify
# Git diff check: src/main.py modified ✅ (in allowed_files)
# LLM analysis: Flask removed ✅
# Logic check: Features implemented ✅
# ✅ PASS

$ wrapper accept
# ✅ Step accepted
#    Deviation "http-server-present" marked as resolved

# Repeat until all deviations fixed
```

---

## Core Concepts

### `.wrapper/state.json` - Audit Log

Append-only record of accepted steps:

```json
{
  "repo": "agent",
  "done_steps": [
    {
      "step_id": "verify-baseline",
      "result": "verification completed",
      "timestamp": "2024-01-15T10:30:00"
    },
    {
      "step_id": "remove-flask-server",
      "result": "implementation completed",
      "timestamp": "2024-01-15T11:45:00"
    }
  ],
  "invariants": ["Uses polling for jobs", "No HTTP server"],
  "last_verify_status": "PASS",  // ← Blocks accept if not PASS
  "last_verify_step": "remove-flask-server"
}
```

### `.wrapper/step.yaml` - Current Work Unit

Defines what you're doing right now:

```yaml
step_id: remove-flask-server
type: implementation
goal: |
  Remove Flask HTTP server code, violates no-http-server constraint
allowed_files:
  - src/main.py
  - requirements.txt
forbidden:
  - "Add new HTTP endpoints"
  - "Create new Flask routes"
features:
  - Remove Flask app initialization
  - Remove route handlers (@app.route)
  - Remove Flask from requirements.txt
success_criteria:
  - No Flask imports remain
  - No HTTP server starts on any port
```

**Key**: `allowed_files` is enforced deterministically via git diff.

### `.wrapper/deviations.yaml` - Architecture Violations

Generated by LLM on first verify:

```yaml
deviations:
  - id: http-server-present
    description: "Flask server in main.py violates no-http-server constraint"
    severity: high
    affected_files: ["src/main.py"]
    resolution_step: "remove-flask-server"  // ← Updated on accept
  
  - id: direct-db-access
    description: "SQLAlchemy in models.py violates no-direct-db constraint"
    severity: high
    affected_files: ["src/models/user.py", "src/models/job.py"]
    resolution_step: null  // ← Still unresolved
```

### `.wrapper/baseline_snapshot.json` - Repository State

Captured on first verify, used for deviation detection:

```json
{
  "timestamp": "2024-01-15T10:00:00",
  "summary": {
    "total_files": 47,
    "total_directories": 12,
    "file_types": {".py": 42, ".yaml": 3, ".md": 2}
  },
  "files": ["src/main.py", "src/models/user.py", ...],
  "directories": ["src/", "src/models/", "tests/"]
}
```

### `.wrapper/architecture.md` - Target State (You Write This)

Natural language description of your ideal architecture:

```markdown
# Agent Architecture

## Constraints
- NO HTTP endpoints (security requirement)
- NO direct database access (use API layer)
- Jobs MUST timeout after 5 minutes

## Components
- JobPoller: Checks queue every 30s
- Executor: Runs jobs in isolated containers
```

This is passed as text to LLM prompts. **Not parsed**, just interpreted.

### `.wrapper/implementation_plan.yaml` - Strategic Plan (Optional)

Multi-step refactoring plan generated via `wrapper plan init`:

```yaml
phases:
  - id: phase-1
    name: "Remove HTTP Server"
    steps:
      - step_id: remove-flask-routes
        features: ["Remove Flask app", "Remove route handlers"]
        files_to_modify: ["src/main.py"]
        requirements:
          security: ["Ensure no ports remain open"]
        completed: false
      - step_id: update-dependencies
        features: ["Remove Flask from requirements.txt"]
        completed: false
```

When plan exists, `wrapper propose` reads from plan instead of asking LLM.

---

## Deterministic vs Soft Guarantees

| Check | How It Works | Can Be Bypassed? |
|-------|--------------|------------------|
| **File allowlist** | Git diff → set subtraction | ❌ No (git is source of truth) |
| **Accept blocking** | `state.json["last_verify_status"] == "PASS"` | ❌ No (checked in code) |
| **Baseline capture** | Filesystem scan with `os.walk()` | ❌ No (reads actual files) |
| **Cross-repo sync** | Read other repo's `.wrapper/state.json` | ❌ No (filesystem read) |
| **Forbidden patterns** | Keyword search in diff (`"http"` → `"app.get("`) | ✅ Yes (use synonyms like `fetch()`) |
| **Architecture compliance** | LLM reads `architecture.md` + diff | ✅ Yes (trick LLM with comments) |
| **Logic verification** | LLM checks features in diff | ✅ Yes (make code look correct, break at runtime) |
| **Deviation detection** | LLM scans code vs architecture | ✅ Yes (LLM can hallucinate) |

**Summary**: File-level enforcement is strict. Semantic enforcement is guidance.

---

## Commands

| Command | Description |
|---------|-------------|
| `wrapper init` | Creates `.wrapper/` directory with templates |
| `wrapper plan init` | Interactive planning - build implementation plan (v1.1.0+) |
| `wrapper plan status` | Show plan progress (X of Y steps complete) |
| `wrapper plan show` | Visualize plan tree |
| `wrapper propose` | Generates next step (from plan if exists, or from deviations) |
| `wrapper propose --from-plan` | Explicitly use plan (fails if no plan exists) |
| `wrapper propose --no-plan` | Ignore plan, generate from deviations |
| `wrapper compile` | Creates `copilot_prompt.txt` for AI assistant |
| `wrapper verify` | Checks git diff + AI output against constraints |
| `wrapper verify --check-logic` | Verify features checklist implemented correctly (v1.1.0+) |
| `wrapper test` | Test completed features against plan (v1.2.0+) |
| `wrapper test --step <id>` | Test specific step by ID |
| `wrapper accept` | Records completed step, updates plan progress |
| `wrapper sync-external` | Syncs dependency repo states (multi-repo setups) |
| `wrapper snapshot` | Manual baseline capture (rarely needed) |
| `wrapper diff-baseline` | Shows drift from baseline (debugging) |
| `wrapper --version` | Show version |

---

## Multi-Repo Support

### Problem: Dependency Hell

You have three repos:
- `ui` (React app) calls `agent` API
- `agent` depends on `auth` for tokens

If `auth` changes its token format, `agent` breaks. But you're working in `agent` and don't know `auth` changed.

### Solution: External State Sync

```bash
# In agent repo
$ wrapper sync-external --from ../ui --from ../auth
```

**What this does**:
1. Reads `../ui/.wrapper/state.json` and `../ui/.wrapper/deviations.yaml`
2. Reads `../auth/.wrapper/state.json` and `../auth/.wrapper/deviations.yaml`
3. Finds high-severity unresolved deviations in dependencies
4. Writes to `.wrapper/external_state.json`

```json
{
  "auth": {
    "done_steps": ["verify-baseline: verification completed"],
    "deviations": [
      {"id": "token-format-change", "severity": "high", "resolved": false}
    ],
    "blockers": ["token-format-change"]  // ← HIGH + unresolved
  }
}
```

5. Next time you run `wrapper propose` in `agent`:
   - LLM sees `external_state.json` has blockers
   - Proposes a "BLOCKED" step instead of real work
   - You must go fix `auth` first, then re-sync

**Key**: This is **not automatic**. You manually run `sync-external` when you want to check dependencies.

### Cross-Repo Blocking Flow

```
[auth repo]
  ↓ Make breaking change
  ↓ wrapper verify → Creates deviation "token-format-change" (high severity)
  ↓ (not fixed yet)

[agent repo]
  ↓ wrapper sync-external --from ../auth
  ↓ Reads auth's deviations.yaml
  ↓ Finds "token-format-change" (high + unresolved) → blocker
  ↓
  ↓ wrapper propose
  ↓ LLM sees blocker in external_state.json
  ↓ Proposes step: "BLOCKED - waiting for auth to fix token-format-change"
  ↓ (you cannot do real work)

[auth repo]
  ↓ Fix the issue
  ↓ wrapper accept → Marks "token-format-change" as resolved

[agent repo]
  ↓ wrapper sync-external --from ../auth (re-sync)
  ↓ Now auth has no blockers
  ↓ wrapper propose → Real work step
```

**Limitation**: Relies on LLM following "YOU MUST propose BLOCKED" instruction. Could theoretically ignore it.

---

## Who This Is For

✅ **Teams refactoring legacy code with AI assistance**
- Need audit trail of AI changes
- Need to enforce architecture during migration
- Want step-by-step progress tracking

✅ **Solo developers using AI heavily**
- Want discipline/structure for AI workflow
- Need to prevent AI from making random changes
- Want to catch logic errors before commit

✅ **Multi-repo projects with tight coupling**
- Need to track dependency changes
- Want to block work if dependencies are broken

## Who This Is NOT For

❌ **Teams wanting formal verification**
- This uses LLMs for semantic checks (not proofs)
- Cannot guarantee correctness

❌ **Projects needing CI/CD replacement**
- This is a local workflow tool
- Does not run tests, deploy code, or integrate with CI

❌ **Greenfield projects with no AI**
- Overhead is not worth it if you're writing code manually
- Better suited for refactoring/migration

❌ **Projects needing static analysis**
- No AST parsing, no type checking, no linting
- Use ESLint, mypy, etc. for that

---

## Quick Start

### Install

```bash
git clone https://github.com/Blink-deploy-in-a-blink/copilot-sentinel.git
cd copilot-sentinel
pip install -e .
```

### Configure LLM

Set API key (required for LLM calls):

```bash
# Linux/Mac
export DEEPSEEK_API_KEY="sk-..."

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-..."

# Or use OpenAI
export OPENAI_API_KEY="sk-..."

# Or Anthropic
export ANTHROPIC_API_KEY="sk-..."
```

### Initialize Project

```bash
cd your-project
wrapper init
```

Edit `.wrapper/architecture.md` with your target architecture.
Edit `.wrapper/repo.yaml` with repo constraints.

### Basic Workflow

```bash
# 1. Propose next step
wrapper propose

# 2. Generate AI prompt
wrapper compile

# 3. Give .wrapper/copilot_prompt.txt to AI
#    Paste AI's response in .wrapper/copilot_output.txt

# 4. Verify changes
wrapper verify

# 5. Accept if passed
wrapper accept
```

### With Planning (v1.1.0+)

```bash
# Create implementation plan
wrapper plan init
# (Interactive Q&A to build plan)

# Execute plan step-by-step
wrapper propose --from-plan
wrapper compile
# ... work with AI ...
wrapper verify --check-logic
wrapper accept

# Check progress
wrapper plan status
```

---

## Command Reference

### `wrapper init`
Create `.wrapper/` directory with template files.

**Files created**:
- `architecture.md` - Target architecture (you edit this)
- `repo.yaml` - Repo boundaries (you edit this)
- `config.yaml` - LLM settings (optional, env vars preferred)

### `wrapper propose`
Generate `step.yaml` for next work unit.

**Two modes**:
1. **Plan-driven** (default if `implementation_plan.yaml` exists):
   - Reads plan, finds next uncompleted step
   - No LLM call
   
2. **Legacy** (no plan or `--no-plan` flag):
   - LLM reads `deviations.yaml`, proposes next fix
   - Checks `external_state.json` for blockers

**Flags**:
- `--no-plan` - Ignore plan even if it exists

### `wrapper compile`
Generate AI prompts from `step.yaml`.

**Creates**:
- `copilot_prompt.txt` - Give this to AI
- `verify.md` - Checklist for verification
- `copilot_output.txt` - Template (paste AI response here)

### `wrapper verify`
Check git diff against step constraints.

**Checks**:
1. ✅ Only `allowed_files` modified (deterministic)
2. ⚠️  Forbidden patterns not present (keyword search)
3. ⚠️  LLM: Diff matches goal (semantic)
4. ⚠️  LLM: Features implemented (if `--check-logic`)

**First run**: Always passes, captures baseline + deviations.

**Flags**:
- `--staged` - Check only staged changes (default: all uncommitted)
- `--check-logic` - Run LLM feature verification

**Outputs**:
- Updates `state.json` with `last_verify_status` (PASS or FAIL)

### `wrapper accept`
Accept verified step into state.

**Gates**:
- ✅ `state.json["last_verify_status"] == "PASS"` (hard block)
- ✅ Step ID matches last verified step (hard block)

**Side effects**:
- Appends to `state.json["done_steps"]`
- Updates `deviations.yaml` (marks resolved via LLM)
- Updates `implementation_plan.yaml` (marks completed)

### `wrapper snapshot`
Manually capture baseline (auto-runs on first verify).

**Scans**:
- Files (excluding `.git`, `node_modules`, `.wrapper`)
- Directories
- File types (by extension)
- Git status (branch, commit hash)

**Output**: `baseline_snapshot.json`

### `wrapper diff-baseline`
Compare current repo against baseline snapshot.

Shows:
- New files
- Removed files
- New directories
- File type changes

### `wrapper sync-external`
Sync external repo state for dependency blocking.

```bash
wrapper sync-external --from ../ui --from ../auth
```

**Reads from each repo**:
- `.wrapper/state.json`
- `.wrapper/deviations.yaml`

**Writes**: `.wrapper/external_state.json`

**Blockers**: High-severity unresolved deviations

### `wrapper plan init`
Interactive planning session.

**Process**:
1. LLM proposes phases (high-level breakdown)
2. You review/edit/reorder phases
3. LLM details each phase into steps
4. You review/edit steps
5. Saves `implementation_plan.yaml`

**Output**: Multi-phase strategic plan with:
- Features per step
- Security/performance/cost requirements
- Estimated hours
- File modification list

### `wrapper plan status`
Show plan progress.

**Displays**:
- Phases completed/total
- Steps completed/total per phase
- Current step
- Estimated time remaining

### `wrapper test`
Test implemented features against plan (v1.1.0+).

**Process**:
1. Reads `implementation_plan.yaml`
2. For each completed step:
   - Reads modified files
   - Sends to LLM: "Are features implemented correctly?"
3. LLM verifies logic per feature

**Flags**:
- `--step <id>` - Test specific step only

---

## Configuration Files

### `.wrapper/architecture.md`

```markdown
# Your Target Architecture

## Constraints
- NO HTTP endpoints (security)
- NO direct database access
- All jobs timeout after 5 minutes

## Components
- JobPoller: Checks queue every 30s
- Executor: Runs jobs
```

### `.wrapper/repo.yaml`

```yaml
repo_name: agent
repo_role: Job execution engine

must_not:
  - expose HTTP APIs
  - contain UI logic
  - access databases directly

depends_on:
  - repo: ui
    via: REST API
```

### `.wrapper/config.yaml`

```yaml
llm_provider: deepseek  # or 'openai' or 'anthropic'
# API keys (prefer environment variables)
```

---

## File Structure

```
your-repo/
├── .wrapper/
│   ├── architecture.md          # [YOU] Target architecture
│   ├── repo.yaml                # [YOU] Boundaries
│   ├── config.yaml              # [YOU] LLM config (optional)
│   │
│   ├── step.yaml                # [AUTO] Current step
│   ├── copilot_prompt.txt       # [AUTO] For AI
│   ├── copilot_output.txt       # [YOU] Paste AI response
│   │
│   ├── state.json               # [AUTO] Audit log
│   ├── baseline_snapshot.json   # [AUTO] Repo scan
│   ├── deviations.yaml          # [AUTO] Violations
│   ├── implementation_plan.yaml # [AUTO] Plan (v1.1.0+)
│   └── external_state.json      # [AUTO] Dependencies
```

---

## Limitations (Be Aware)

### What This Tool Does NOT Do

1. **Does not run tests** - You still need CI/CD
2. **Does not parse code** - No AST analysis, no type checking
3. **Does not guarantee correctness** - LLM verification is guidance, not proof
4. **Does not prevent malicious code** - Can be bypassed if you try
5. **Does not work offline** - Requires LLM API access
6. **Does not support all languages** - LLM-based, works best with popular languages

### Known Bypass Vectors

- **Forbidden patterns**: Use synonyms (e.g., `fetch()` instead of `axios()`)
- **Architecture compliance**: Trick LLM with misleading comments
- **Logic verification**: Make diff look correct, break at runtime
- **Dependency blocking**: Manually edit `external_state.json`

**This is workflow discipline, not security.**

---

## Documentation

- **[How It Works](docs/how-it-works.md)** - Baseline capture, deviation tracking, step generation
- **[Multi-Repo Setup](docs/multi-repo.md)** - Cross-repository dependency management
- **[Testing Guide](docs/testing.md)** - Feature testing and logic verification
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions
- **[Examples](docs/examples.md)** - Real-world usage scenarios

---

## Version

**Current: v1.2.0**

See [CHANGELOG.md](CHANGELOG.md) for version history.  
See [VERSIONING.md](VERSIONING.md) for release process.

---

## License

MIT

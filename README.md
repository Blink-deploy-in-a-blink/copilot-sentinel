# wrapper

**Prompt Compiler + Verifier for Copilot-based coding.**

A strict, boring CLI tool that enforces architectural discipline when using GitHub Copilot.

## What It Does

1. **Proposes** next development steps based on architecture
2. **Compiles** strict Copilot prompts with explicit constraints
3. **Verifies** git diffs against those constraints
4. **Maintains** explicit state across steps

## Installation

```bash
# Clone or copy the wrapper directory to your machine
cd wrapper

# Install dependencies
pip install -r requirements.txt

# Option A: Install globally
pip install -e .

# Option B: Use directly
alias wrapper="python /path/to/wrapper/wrapper.py"
```

## Quick Start

```bash
# In your project repo
cd your-repo

# Initialize wrapper
wrapper init

# Edit the generated files:
#   .wrapper/architecture.md  - Your target architecture
#   .wrapper/repo.yaml        - Repo constraints
#   .wrapper/config.yaml      - LLM API key

# Set API key (or edit config.yaml)
export DEEPSEEK_API_KEY="your-key"

# Propose first step (will be verification)
wrapper propose

# Review and edit .wrapper/step.yaml
# Then compile the Copilot prompt
wrapper compile

# Two files created:
#   - copilot_prompt.txt (give to AI)
#   - copilot_output.txt (template for AI response)

# Copy copilot_prompt.txt to your AI assistant
# Paste the AI's response into copilot_output.txt

# Verify the changes
wrapper verify
# On FIRST verify: automatically captures baseline_snapshot.json
#                  and auto-generates deviations.yaml

# If passed, commit and accept
git commit -am "step: baseline-verification"
wrapper accept

# Repeat for next step
wrapper propose  # Now uses baseline context!
```

## Commands

### `wrapper init`

Creates `.wrapper/` directory with template files:
- `architecture.md` - Target architecture description
- `repo.yaml` - Repository constraints
- `config.yaml` - LLM configuration

### `wrapper propose`

Uses LLM to propose the next `step.yaml` based on:
- Target architecture (from `architecture.md`)
- **Actual repository state** (from `baseline_snapshot.json`)
- **Known deviations** (from `deviations.yaml`)
- Completed steps history
- External repo state

First step is always a verification step to establish baseline.

### `wrapper compile`

Generates from `step.yaml`:
- `copilot_prompt.txt` - Strict prompt to paste into AI assistant
- `copilot_output.txt` - Template file for AI's response (paste AI output here)
- `verify.md` - Human-readable checklist

**Important:** After getting AI's response, paste it into `copilot_output.txt` before running `verify`.

### `wrapper verify [--staged]`

Checks git diff AND AI output against step constraints:
- Verifies only allowed files changed
- Checks for forbidden patterns
- Uses `copilot_output.txt` for verification steps with no code changes
- Runs LLM analysis on both diff and output
- Generates `repair_prompt.txt` on failure

**First-time magic (when no steps completed yet):**
- Automatically captures `baseline_snapshot.json` (repo structure/files)
- Automatically generates `deviations.yaml` (architecture vs actual mismatches)
- Sets up baseline for all future steps

Options:
- `--staged` - Check only staged changes (default: all uncommitted)

### `wrapper accept`

Records completed step in state. Only works after `verify` passes.

### `wrapper sync-external --from <path> [--from <path> ...]`

Syncs external_state.json from other repos. This is the ONLY way to populate external_state.json.

```bash
# From your current repo, sync state from sibling repos
wrapper sync-external --from ../ui --from ../llm
```

Extracts from each repo's `.wrapper/state.json`:
- `done_steps` summaries
- `invariants`

Does NOT scan source code or infer anything.

### `wrapper snapshot`

Manually capture baseline snapshot of repository.

**Usually not needed** - automatically captured on first `wrapper verify`.

Scans repository and creates `baseline_snapshot.json` with:
- Complete file tree
- Directory structure
- File counts by type (.ts, .py, etc.)
- Presence of key files (package.json, Dockerfile, etc.)
- Git status (branch, last commit)

### `wrapper diff-baseline`

Compare current repository state against baseline snapshot.

Shows drift from verified baseline:
- New/removed files
- New/removed directories  
- File type count changes
- Structural changes

Useful for detecting unexpected modifications or growth.

## File Structure

```
your-repo/
├── .wrapper/
│   # === Manual Setup (edit once) ===
│   ├── architecture.md       # [Human] Target architecture description
│   ├── repo.yaml            # [Human] Repository role and constraints
│   ├── config.yaml          # [Human] LLM API configuration
│   
│   # === Per-Step Workflow (regenerated each step) ===
│   ├── step.yaml            # [LLM→Human] Proposed step (review/edit before compile)
│   ├── copilot_prompt.txt   # [Generated] Prompt for AI assistant
│   ├── copilot_output.txt   # [Template] Paste AI's response here
│   ├── verify.md            # [Generated] Human-readable checklist
│   ├── diff.txt             # [Generated] Last git diff analyzed
│   ├── repair_prompt.txt    # [Generated] Fix instructions (on failure)
│   
│   # === Persistent State (append-only) ===
│   ├── state.json           # [Auto] All completed steps + invariants
│   ├── baseline_snapshot.json # [Auto] Repository structure at baseline
│   ├── deviations.yaml      # [Auto] Known architecture mismatches
│   └── external_state.json  # [Synced] Other repos' state
│   
└── ... your code ...
```

### File Lifecycle

| File | Created By | Updated When | Purpose |
|------|------------|--------------|---------|
| **architecture.md** | `init` | Manual once | Define target state |
| **repo.yaml** | `init` | Manual once | Define boundaries |
| **config.yaml** | `init` | Manual once | API keys |
| **step.yaml** | `propose` | Each step | Current step plan |
| **copilot_prompt.txt** | `compile` | Each step | AI assistant input |
| **copilot_output.txt** | `compile` | Each step (you paste) | AI assistant output |
| **state.json** | First run | `accept` | Append-only history |
| **baseline_snapshot.json** | First `verify` | Never (permanent baseline) | Repo structure snapshot |
| **deviations.yaml** | First `verify` | As deviations resolve | Architecture gaps |

## Configuration

### LLM Setup

Environment variables (take precedence):
```bash
export DEEPSEEK_API_KEY="your-key"
# or
export OPENAI_API_KEY="your-key"
# or
export ANTHROPIC_API_KEY="your-key"
```

Or in `.wrapper/config.yaml`:
```yaml
llm_provider: deepseek  # or openai, anthropic
deepseek_api_key: your-key
```

### repo.yaml Example

```yaml
repo_name: agent
repo_role: |
  Core execution engine for job processing.
  Handles state machines and worker coordination.

must_not:
  - expose HTTP APIs
  - contain UI logic
  - manage user authentication
  - directly access external databases

depends_on:
  - repo: llm
    via: function calls
```

### step.yaml Example

```yaml
step_id: implement-job-state-machine
type: implementation
repo: agent
goal: |
  Implement the job lifecycle state machine with explicit
  state transitions and no side effects.
allowed_files:
  - src/job/state.ts
  - src/job/transitions.ts
forbidden:
  - HTTP endpoints
  - Database queries
  - External API calls
success_criteria:
  - States are explicitly defined as enum
  - Transitions are pure functions
  - No async operations in state logic
```

## Key Features

### 🎯 Automatic Baseline Capture

On first `wrapper verify`:
- Scans your entire repository
- Creates `baseline_snapshot.json` with complete file/directory structure
- LLM analyzes target architecture vs actual state
- Auto-generates `deviations.yaml` listing all mismatches
- **Zero manual work** - happens automatically!

### 📋 AI Output Verification

Not just code changes - verifies AI's analysis too:
- For verification steps: AI analyzes repo, you paste output
- For implementation steps: AI describes changes made
- `wrapper verify` checks both git diff AND AI's explanation
- Ensures AI understood the constraints correctly

### 🔍 Deviation Tracking

Structured tracking of reality vs target:
```yaml
deviations:
  - id: missing-tests-directory
    description: tests/ doesn't exist but architecture requires it
    severity: high
    expected: tests/ with unit and integration subdirectories
    actual: No tests directory found
    resolution_step: null  # Filled when addressed
```

### 📊 Context-Aware Proposals

LLM gets concrete context when proposing steps:
- "Your repo has 47 files across 12 directories"
- "src/routes/ contains api.ts, health.ts"
- "Known deviation: missing tests/ directory"
- Results in specific, actionable step proposals

## Multi-Repo Usage

Each repo has its own `.wrapper/` directory.

Use `external_state.json` to share awareness:

```json
{
  "ui": {
    "status": "baseline_verified",
    "known_endpoints": ["POST /jobs", "GET /jobs/:id"]
  },
  "llm": {
    "status": "baseline_verified",
    "models": ["deepseek-chat"]
  }
}
```

## Key Features

### 🎯 Automatic Baseline Capture

On first `wrapper verify`:
- Scans your entire repository
- Creates `baseline_snapshot.json` with complete file/directory structure
- LLM analyzes target architecture vs actual state
- Auto-generates `deviations.yaml` listing all mismatches
- **Zero manual work** - happens automatically!

### 📋 AI Output Verification

Not just code changes - verifies AI's analysis too:
- For verification steps: AI analyzes repo, you paste output
- For implementation steps: AI describes changes made
- `wrapper verify` checks both git diff AND AI's explanation
- Ensures AI understood the constraints correctly

### 🔍 Deviation Tracking

Structured tracking of reality vs target:
```yaml
deviations:
  - id: missing-tests-directory
    description: tests/ doesn't exist but architecture requires it
    severity: high
    expected: tests/ with unit and integration subdirectories
    actual: No tests directory found
    resolution_step: null  # Filled when addressed
```

### 📊 Context-Aware Proposals

LLM gets concrete context when proposing steps:
- "Your repo has 47 files across 12 directories"
- "src/routes/ contains api.ts, health.ts"
- "Known deviation: missing tests/ directory"
- Results in specific, actionable step proposals

## Philosophy

This tool exists to **enforce discipline, not intelligence**.

- AI assistants are powerful but implicit
- This tool makes constraints explicit
- Captures reality, not just ideals
- Every change verified against architecture AND baseline
- State is append-only and auditable
- Human reviews and approves everything

## Troubleshooting

### "No LLM API key configured"

Set `DEEPSEEK_API_KEY` environment variable or add to `.wrapper/config.yaml`.

### "Not in a git repository"

Run `git init` first. The tool requires git for diff checking.

### "step.yaml not found"

Run `wrapper propose` first, or create manually.

### "Verification step requires Copilot output"

For verification-only steps with no code changes:
1. Check `.wrapper/copilot_output.txt` 
2. Paste the AI's analysis into that file
3. Run `wrapper verify` again

### Verification keeps failing

Check `repair_prompt.txt` for specific issues. Common causes:
- Modified files not in `allowed_files`
- Forbidden patterns detected in diff
- New directories created unexpectedly
- AI output missing or incomplete

### Want to see what changed from baseline?

```bash
wrapper diff-baseline
```

Shows all files/directories added or removed since baseline was captured.

## License

MIT

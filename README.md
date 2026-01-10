# Copilot Sentinel

**Prompt Compiler + Verifier for AI-assisted coding.**

A strict, boring CLI tool that enforces architectural discipline when using GitHub Copilot, Claude Code, Cursor, or any AI coding assistant.

## What It Does

1. **Proposes** next development steps based on architecture
2. **Compiles** strict Copilot prompts with explicit constraints
3. **Verifies** git diffs against those constraints
4. **Maintains** explicit state across steps

## Installation

```bash
# Clone the repository
git clone https://github.com/Blink-deploy-in-a-blink/copilot-sentinel.git
cd copilot-sentinel

# Install dependencies
pip install -r requirements.txt

# Install the CLI tool (installs as 'wrapper' command)
pip install -e .

# Verify installation
wrapper --help
```

### Custom Command Name (Optional)

If you want to rename the CLI command (e.g., to `sentinel` or `guard`), edit `setup.py`:

```python
entry_points={
    "console_scripts": [
        "sentinel=wrapper.cli:main",  # Change 'sentinel' to your preferred name
    ],
},
```

Then reinstall: `pip install -e .`

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

# Copy .wrapper/copilot_prompt.txt to Copilot
# Let Copilot make changes

# Verify the changes
wrapper verify

# If passed, commit and accept
git commit -am "step: baseline-verification"
wrapper accept

# Repeat for next step
wrapper propose
```

## Commands

### `wrapper init`

Creates `.wrapper/` directory with template files:
- `architecture.md` - Target architecture description
- `repo.yaml` - Repository constraints
- `config.yaml` - LLM configuration

### `wrapper propose`

Uses LLM to propose the next `step.yaml` based on:
- Current architecture
- Completed steps
- External repo state

First step is always a verification step.

### `wrapper compile`

Generates from `step.yaml`:
- `copilot_prompt.txt` - Strict prompt to paste into Copilot
- `verify.md` - Human-readable checklist

### `wrapper verify [--staged]`

Checks git diff against step constraints:
- Verifies only allowed files changed
- Checks for forbidden patterns
- Runs LLM analysis
- Generates `repair_prompt.txt` on failure

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

## File Structure

```
your-repo/
├── .wrapper/
│   ├── architecture.md      # [Human] Target architecture
│   ├── repo.yaml           # [Human] Repo constraints
│   ├── config.yaml         # [Human] LLM config
│   ├── step.yaml           # [Proposed/Edited] Current step
│   ├── state.json          # [Auto] Execution state
│   ├── external_state.json # [sync-external] Other repos state (READ-ONLY for Copilot)
│   ├── copilot_prompt.txt  # [Generated] Copilot prompt
│   ├── verify.md           # [Generated] Verification checklist
│   ├── diff.txt            # [Generated] Last git diff
│   └── repair_prompt.txt   # [Generated] On verification failure
└── ... your code ...
```

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

## Philosophy

This tool exists to **enforce discipline, not intelligence**.

- Copilot is powerful but implicit
- This tool makes constraints explicit
- Every change is verified against architecture
- State is append-only and auditable
- Human reviews and approves everything

## Troubleshooting

### "No LLM API key configured"

Set `DEEPSEEK_API_KEY` environment variable or add to `.wrapper/config.yaml`.

### "Not in a git repository"

Run `git init` first. The tool requires git for diff checking.

### "step.yaml not found"

Run `wrapper propose` first, or create manually.

### Verification keeps failing

Check `repair_prompt.txt` for specific issues. Common causes:
- Modified files not in `allowed_files`
- Forbidden patterns detected in diff
- New directories created unexpectedly

## Contributing

Issues and pull requests welcome!

## License

MIT

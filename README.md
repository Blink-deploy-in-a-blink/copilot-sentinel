# Copilot Sentinel

**AI-assisted development with architectural guardrails.**

A strict, boring CLI tool that enforces discipline when using GitHub Copilot, Claude, Cursor, or any AI coding assistant.

-  **Interactive Planning** - Build strategic implementation plans with LLM guidance
-  **Baseline Capture** - Auto-scans your repo, finds architecture violations
-  **Step-by-Step Fixes** - Execute plan step-by-step with verification  
-  **Feature Testing** - Test completed features against plan for logic bugs
-  **Logic Verification** - Checks features are actually implemented correctly
-  **Strict Verification** - Checks git diff + AI output against constraints
-  **Cross-Repo Blocking** - Prevents work if dependencies have unresolved issues
-  **Non-Functional Requirements** - Security, performance, cost requirements in every step

---

## Quick Start (New: With Planning)

```bash
# Install
git clone https://github.com/Blink-deploy-in-a-blink/copilot-sentinel.git
cd copilot-sentinel
pip install -e .

# In your project
cd your-project
wrapper init

# Set API key
export DEEPSEEK_API_KEY="sk-..."      # Linux/Mac
$env:DEEPSEEK_API_KEY="sk-..."        # Windows

# NEW: Create implementation plan
wrapper plan init
# Interactive Q&A to build strategic plan
# Breaks work into phases and steps
# Captures security/performance requirements

# Execute plan step-by-step
wrapper propose --from-plan   # Gets next step from plan
wrapper compile               # Generate AI prompt
# ... work with AI ...
wrapper verify --check-logic  # Verify features implemented
wrapper accept                # Mark complete, move to next

# Check progress anytime
wrapper plan status
```

---

## Quick Start (Legacy: Without Planning)

```bash
# First run (captures baseline)
wrapper propose
wrapper compile
# Give copilot_prompt.txt to AI, paste response in copilot_output.txt
wrapper verify     # Auto-captures baseline, always passes first time
wrapper accept

# Repeat for each step
wrapper propose    # Next step (fixes deviations)
wrapper compile
# ... work with AI ...
wrapper verify
wrapper accept
```

---

## What You Need to Configure (One Time)

After `wrapper init`, edit these files in `.wrapper/`:

### `.wrapper/architecture.md`
Your target architecture. Example:

```markdown
# Agent Architecture

## Structure
- Polling-based job execution
- No inbound HTTP server
- Communicate via message queue

## Components
- JobPoller: Checks for new jobs every 30s
- Executor: Runs jobs in isolated containers
- Reporter: Sends results back

## Constraints
- NO HTTP endpoints (security requirement)
- NO direct database access (use API)
- Jobs MUST timeout after 5 minutes
```

### `.wrapper/repo.yaml`
Repository boundaries and dependencies. Example:

```yaml
repo_name: agent
repo_role: |
  Core execution engine. Polls for jobs, executes them.

must_not:
  - expose inbound HTTP APIs
  - contain UI logic
  - directly access databases

depends_on:
  - repo: ui
    via: polling endpoints
```

### `.wrapper/config.yaml`
LLM provider (optional, defaults to DeepSeek):

```yaml
llm_provider: deepseek  # or 'openai' or 'anthropic'
deepseek_api_key: sk-...  # or set via environment variable
```

That's it! Everything else is automatic.

---

## How It Works

### 1. Baseline Capture (Automatic)
First `wrapper verify`:
- Scans entire repo (files, directories, structure)
- LLM compares actual code vs `architecture.md`
- Generates `deviations.yaml` with all violations
- **Always passes** (just documenting reality)

Example output:
```
✅ PASS - Baseline captured
Found 13 deviations from architecture
```

### 2. Step-by-Step Deviation Fixing
```
Step 1: Remove HTTP server code (fixes 2 deviations)
  ↓ verify + accept
Step 2: Add polling mechanism (fixes 1 deviation)
  ↓ verify + accept
Step 3: Restructure directories (fixes 4 deviations)
  ↓ verify + accept
... continue until clean
```

### 3. Cross-Repo Dependency Blocking
```bash
# In Agent repo (depends on UI)
wrapper sync-external --from ../ui
wrapper propose

# If UI has unresolved deviations:
❌ BLOCKED: ui has high-severity deviation "no-polling-endpoint"
Proposed: "blocked-waiting-for-ui" step

# After UI fixes it:
wrapper sync-external --from ../ui
wrapper propose
✅ Can proceed with actual work
```

---

## Commands

| Command | What It Does |
|---------|-------------|
| `wrapper init` | Creates `.wrapper/` directory with templates |
| `wrapper plan init` | **NEW** Interactive planning - build implementation plan |
| `wrapper plan status` | **NEW** Show plan progress (X of Y steps complete) |
| `wrapper plan show` | **NEW** Visualize plan tree |
| `wrapper propose` | Generates next step (from plan if exists, or from deviations) |
| `wrapper propose --no-plan` | Ignore plan, generate step from deviations |
| `wrapper compile` | Creates `copilot_prompt.txt` for AI assistant |
| `wrapper verify` | Checks git diff + AI output against step constraints |
| `wrapper verify --check-logic` | **NEW** Verify features checklist implemented correctly |
| `wrapper test` | **NEW** Test completed features against plan |
| `wrapper test --step <id>` | **NEW** Test specific step by ID |
| `wrapper accept` | Records completed step, updates plan progress |
| `wrapper sync-external` | Syncs dependency repo states (multi-repo setups) |
| `wrapper snapshot` | Manual baseline capture (rarely needed) |
| `wrapper diff-baseline` | Shows drift from baseline (debugging) |
| `wrapper --version` | Show version |

---

## Typical Workflow

```bash
# 1. Get next step
wrapper propose
# → Creates .wrapper/step.yaml

# 2. Generate AI prompt
wrapper compile
# → Creates .wrapper/copilot_prompt.txt

# 3. Give prompt to AI
# Copy copilot_prompt.txt content
# Paste into Copilot/Claude/Cursor
# Paste AI's response into copilot_output.txt

# 4. Verify changes
wrapper verify
# → Checks git diff + copilot_output.txt against step constraints

# 5. Accept if passed
wrapper accept
# → Records step, auto-resolves matched deviations
```

---

## Multi-Repo Setup

When you have dependencies between repos:

```bash
# Setup each repo once
cd ui && wrapper init && wrapper propose && wrapper verify && wrapper accept
cd agent && wrapper init && wrapper propose && wrapper verify && wrapper accept

# Before working on agent
cd agent
wrapper sync-external --from ../ui --from ../auth

wrapper propose
# → Checks for blockers in ui & auth
# → Proposes "blocked" step if dependencies broken
# → Proposes real work if clean

# After dependency repo fixes issues
wrapper sync-external --from ../ui
wrapper propose
# → Now unblocked
```

---

## File Structure

```
your-repo/
├── .wrapper/
│   ├── architecture.md          # [YOU EDIT] Target architecture
│   ├── repo.yaml                # [YOU EDIT] Boundaries & dependencies
│   ├── config.yaml              # [YOU EDIT] API key (optional)
│   │
│   ├── step.yaml                # [AUTO] Current step
│   ├── copilot_prompt.txt       # [AUTO] For AI assistant
│   ├── copilot_output.txt       # [YOU] Paste AI response here
│   │
│   ├── state.json               # [AUTO] Completed steps history
│   ├── baseline_snapshot.json   # [AUTO] Repo structure snapshot
│   ├── deviations.yaml          # [AUTO] Architecture violations
│   └── external_state.json      # [AUTO] Dependency repo states
```

---

## Supported LLMs

- **DeepSeek** (default) - Fast, cheap, good results
- **OpenAI** - GPT-4 / GPT-3.5
- **Anthropic** - Claude

Set via environment variable or `.wrapper/config.yaml`:

```bash
# DeepSeek (default)
export DEEPSEEK_API_KEY="sk-..."

# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-..."
```

---

## Testing Completed Features

After completing some steps, test your implementation:

```bash
# Interactive testing menu
wrapper test

# Choose what to test:
#   - Test Phase: Authentication (3/3 done)
#   - Test Phase: Database Layer (1/2 done)
#   - Test specific step
#   - Test ALL completed work

# Test specific step directly
wrapper test --step step-1-remove-flask

# What it does:
# 1. Reads implementation plan
# 2. Finds completed steps with features
# 3. Reads actual code files (files_changed)
# 4. Sends to LLM: "Does this code implement X correctly?"
# 5. Reports:
#    - Feature checklist (✓ CORRECT | ✗ BROKEN | ⚠ INCOMPLETE)
#    - Logic bugs found
#    - Security issues
#    - Recommendations
```

**When to use `wrapper test`:**
- After completing a phase (test all steps in phase)
- Before releasing (test all completed work)
- When debugging (test specific step)
- In CI/CD (automate testing with `--step`)

**How it's different from `wrapper verify`:**
- `verify` = Checks git diff against constraints (during development)
- `test` = Checks actual code against features (after completion)

---

## Troubleshooting

**"No LLM API key configured"**
```bash
export DEEPSEEK_API_KEY="your-key"
```

**"Not in a git repository"**
```bash
git init
```

**"Verification step requires Copilot output"**
- Paste AI's analysis into `.wrapper/copilot_output.txt`

**"ACCEPT BLOCKED - must PASS verify first"**
- Run `wrapper verify` until it passes

**Check what changed since baseline:**
```bash
wrapper diff-baseline
```

---

## Example: Real Baseline Capture

```bash
$ wrapper propose
Analyzing repository...

$ wrapper verify
✅ PASS - Baseline captured

Deviations found (13 total):
  [HIGH] http-server-present: Flask server in main.py (violates no-http-server)
  [HIGH] direct-db-access: SQLAlchemy in models.py (violates no-direct-db)
  [MED] missing-polling: No polling mechanism found
  [MED] no-timeout: Job execution has no timeout
  ... 9 more

$ wrapper propose
Analyzing deviations...

Proposed Step:
  Title: Remove Flask HTTP server
  Goal: Eliminate HTTP server code, violates architecture
  Fixes: [http-server-present, unused-routes]
```

---

## Philosophy

**Enforce discipline, not intelligence.**

- AI is powerful but implicit
- This tool makes constraints explicit
- Captures reality (baseline), not just ideals  
- Verifies changes against architecture AND current state
- Blocks cross-repo work until dependencies ready
- Human reviews everything (no auto-apply)

---

## Version

Current: **v1.2.0**

See [CHANGELOG.md](CHANGELOG.md) for version history.  
See [VERSIONING.md](VERSIONING.md) for release process.

---

## License

MIT

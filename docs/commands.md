# Commands Reference

Complete reference for all Copilot Sentinel commands.

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `wrapper init` | Initialize `.wrapper/` directory |
| `wrapper propose` | Generate next step |
| `wrapper compile` | Create AI prompts from step |
| `wrapper verify` | Check changes against constraints |
| `wrapper accept` | Record completed step |
| `wrapper plan init` | Create implementation plan |
| `wrapper plan status` | Show plan progress |
| `wrapper plan show` | Visualize plan tree |
| `wrapper test` | Test implemented features |
| `wrapper sync-external` | Sync dependency repo states |
| `wrapper snapshot` | Capture baseline manually |
| `wrapper diff-baseline` | Show drift from baseline |
| `wrapper --version` | Show version |

---

## Core Commands

### `wrapper init`

Initialize Copilot Sentinel in your project.

**Usage:**
```bash
wrapper init
```

**What it does:**
- Creates `.wrapper/` directory
- Generates template configuration files

**Files created:**
- `architecture.md` - Edit with your target architecture
- `repo.yaml` - Edit with repo boundaries
- `config.yaml` - Optional LLM configuration

**Requirements:**
- Must be in a git repository
- Directory must not already have `.wrapper/`

**Example output:**
```
✅ Initialized .wrapper/ directory
Created:
  - architecture.md (edit this with your target architecture)
  - repo.yaml (edit this with your repo boundaries)
  - config.yaml (optional, prefer environment variables)
```

---

### `wrapper propose`

Generate the next work step.

**Usage:**
```bash
wrapper propose [OPTIONS]
```

**Options:**
- `--from-plan` - Explicitly use implementation plan (fails if no plan exists)
- `--no-plan` - Ignore plan even if it exists

**What it does:**

**First run:**
- Generates "verify-baseline" step

**With plan:**
- Reads `implementation_plan.yaml`
- Finds next incomplete step
- Generates `step.yaml` from plan context

**Without plan:**
- Reads `deviations.yaml`
- Reads `external_state.json` (checks for blockers)
- LLM proposes next fix step

**Output:**
- Creates `.wrapper/step.yaml`

**Example output:**
```
✅ Generated step: remove-flask-server
Created: .wrapper/step.yaml

Next: Run 'wrapper compile' to generate AI prompts
```

---

### `wrapper compile`

Generate AI prompts from current step.

**Usage:**
```bash
wrapper compile
```

**What it does:**
- Reads `.wrapper/step.yaml`
- Generates prompts for AI interaction
- Creates verification checklist

**Files created:**
- `copilot_prompt.txt` - Give this to your AI assistant
- `copilot_output.txt` - Template (paste AI response here)
- `verify.md` - Checklist for manual verification

**Example output:**
```
✅ Generated prompts
Created:
  - copilot_prompt.txt (give this to AI)
  - copilot_output.txt (paste AI response here)
  - verify.md (checklist)

Next: 
1. Copy copilot_prompt.txt content
2. Paste into AI assistant
3. Get AI response
4. Paste response into copilot_output.txt
5. Run 'wrapper verify'
```

---

### `wrapper verify`

Verify changes against step constraints.

**Usage:**
```bash
wrapper verify [OPTIONS]
```

**Options:**
- `--staged` - Check only staged changes (default: all uncommitted)
- `--check-logic` - Run LLM feature verification

**What it does:**

**Deterministic checks:**
1. Git diff → Only `allowed_files` modified?
2. Keyword search → Forbidden patterns present?

**LLM checks:**
3. Does diff match goal?
4. Are features implemented? (if `--check-logic`)

**First run:**
- Always PASS (baseline capture)
- Scans repository
- Generates `deviations.yaml`
- Generates `baseline_snapshot.json`

**Updates:**
- `state.json["last_verify_status"]` - "PASS" or "FAIL"
- `state.json["last_verify_step"]` - Step ID

**Example output (first run):**
```
✅ PASS - Baseline captured

Repository snapshot saved:
  - 47 files scanned
  - 12 directories

Deviations found: 13
  High severity: 3
  Medium severity: 7
  Low severity: 3

Created:
  - baseline_snapshot.json
  - deviations.yaml

Next: Run 'wrapper accept' to proceed
```

**Example output (normal run):**
```
✅ PASS

Git diff check:
  ✓ Only allowed files modified
  ✓ Modified: src/main.py, requirements.txt
  ✓ Allowed: src/main.py, requirements.txt

Forbidden pattern check:
  ✓ No forbidden patterns detected

Architecture check:
  ✓ Flask imports removed
  ✓ No HTTP server code found

Result: PASS
Status saved to state.json

Next: Run 'wrapper accept' to record step
```

**Example output (failure):**
```
❌ FAIL

Git diff check:
  ✗ Modified files not in allowed_files
  
Modified: src/main.py, src/unauthorized.py
Allowed: src/main.py, requirements.txt

Please:
1. Revert unauthorized changes: git checkout src/unauthorized.py
2. Or update step.yaml to include src/unauthorized.py
3. Run 'wrapper verify' again
```

---

### `wrapper accept`

Accept verified step and update state.

**Usage:**
```bash
wrapper accept
```

**What it does:**
1. Checks `state.json["last_verify_status"] == "PASS"` (BLOCKS if not)
2. Appends step to `state.json["done_steps"]`
3. LLM updates `deviations.yaml` (marks resolved deviations)
4. Updates `implementation_plan.yaml` (marks step completed if plan exists)

**Hard gates:**
- ✅ Verification must have passed
- ✅ Step ID must match last verified step

**Example output:**
```
✅ Step accepted: remove-flask-server

Updated:
  - state.json (step recorded)
  - deviations.yaml (2 deviations marked resolved)

Resolved deviations:
  - http-server-present
  - http-route-handlers

Remaining deviations: 11

Next: Run 'wrapper propose' for next step
```

**Example output (blocked):**
```
❌ Cannot accept - verification has not passed

Last verify status: FAIL

Please:
1. Fix the issues
2. Run 'wrapper verify' until it passes
3. Then run 'wrapper accept'
```

---

## Planning Commands (v1.1.0+)

### `wrapper plan init`

Interactive planning session to create implementation plan.

**Usage:**
```bash
wrapper plan init
```

**What it does:**
1. LLM proposes high-level phases
2. You review/edit/reorder phases
3. LLM breaks each phase into steps
4. You review/edit steps
5. Saves `implementation_plan.yaml`

**Interactive prompts:**
```
Planning Session
================

Analyzing your repository and architecture...

Proposed phases:
1. Remove HTTP Server
2. Add Polling Mechanism
3. Implement API Client
4. Add Timeout Handling

Accept phases? (y/n): y

Detailing Phase 1: Remove HTTP Server
--------------------------------------

Proposed steps:
1. remove-flask-routes (2 hours)
   - Remove Flask app
   - Remove route handlers
   
2. update-dependencies (0.5 hours)
   - Remove Flask from requirements.txt

Edit steps? (y/n): n

Detailing Phase 2: Add Polling Mechanism
-----------------------------------------
...

✅ Plan created: implementation_plan.yaml

Next: Run 'wrapper propose' to start first step
```

**Output:**
- Creates `implementation_plan.yaml`

---

### `wrapper plan status`

Show plan progress.

**Usage:**
```bash
wrapper plan status
```

**What it does:**
- Reads `implementation_plan.yaml`
- Shows completed vs total steps
- Shows current phase
- Shows estimated time remaining

**Example output:**
```
Implementation Plan Status
==========================

Overall Progress: 3/10 steps completed (30%)

Phase 1: Remove HTTP Server [COMPLETE]
  ✓ remove-flask-routes (2 hours)
  ✓ update-dependencies (0.5 hours)
  
Phase 2: Add Polling Mechanism [IN PROGRESS]
  ✓ implement-poller (4 hours)
  ⏳ add-error-handling (2 hours) ← CURRENT
  ☐ add-logging (1 hour)
  
Phase 3: Implement API Client [NOT STARTED]
  ☐ create-api-client (3 hours)
  ☐ add-authentication (2 hours)
  ☐ add-rate-limiting (1.5 hours)

Estimated time remaining: 9.5 hours
```

---

### `wrapper plan show`

Visualize plan as tree structure.

**Usage:**
```bash
wrapper plan show
```

**What it does:**
- Reads `implementation_plan.yaml`
- Displays hierarchical tree

**Example output:**
```
Implementation Plan
===================

📦 Phase 1: Remove HTTP Server
├─ ✓ remove-flask-routes
└─ ✓ update-dependencies

📦 Phase 2: Add Polling Mechanism
├─ ✓ implement-poller
├─ ⏳ add-error-handling (CURRENT)
└─ ☐ add-logging

📦 Phase 3: Implement API Client
├─ ☐ create-api-client
├─ ☐ add-authentication
└─ ☐ add-rate-limiting

Legend: ✓ Complete | ⏳ In Progress | ☐ Not Started
```

---

## Testing Commands (v1.2.0+)

### `wrapper test`

Test implemented features against plan.

**Usage:**
```bash
wrapper test [OPTIONS]
```

**Options:**
- `--step <id>` - Test specific step by ID

**What it does:**
1. Reads `implementation_plan.yaml`
2. For completed steps:
   - Reads modified files
   - Sends to LLM: "Are features implemented correctly?"
3. Reports results

**Interactive mode (no flags):**
```
Available test targets:
1. Test Phase: Authentication (3/3 done)
2. Test Phase: Database Layer (1/2 done, skips incomplete)
3. Test Step: step-1-remove-flask
4. Test Step: step-2-add-polling
5. Test ALL completed work

Choose: 3

Testing Step: step-1-remove-flask
──────────────────────────────────

Features:
  ✓ CORRECT: Remove Flask app initialization
  ✓ CORRECT: Remove route handlers
  ✗ INCOMPLETE: Update requirements.txt (Flask==2.0.0 still present)

Security:
  ✓ PASS: No HTTP ports remain open

Logic bugs found:
  - requirements.txt still contains Flask dependency

Recommendations:
  - Remove Flask==2.0.0 from requirements.txt

Overall: ⚠ NEEDS FIXES
```

**Direct step testing:**
```bash
wrapper test --step step-1-remove-flask
```

---

## Multi-Repo Commands

### `wrapper sync-external`

Sync external repository states (multi-repo setups).

**Usage:**
```bash
wrapper sync-external --from <path> [--from <path> ...]
```

**Arguments:**
- `--from <path>` - Path to dependency repo (can specify multiple)

**What it does:**
1. Reads each repo's `.wrapper/state.json`
2. Reads each repo's `.wrapper/deviations.yaml`
3. Extracts high-severity unresolved deviations
4. Writes to `.wrapper/external_state.json`

**Example:**
```bash
wrapper sync-external --from ../ui --from ../auth
```

**Output:**
```
✅ Synced external state from 2 repos

ui:
  - 2 high-severity deviations
  - Blocker: no-polling-endpoint

auth:
  - 0 high-severity deviations
  - Clean

Created: external_state.json

Next: Run 'wrapper propose' to check for blockers
```

**Result:**
- If blockers exist, `wrapper propose` generates "BLOCKED" step
- If clean, `wrapper propose` generates normal work step

---

## Utility Commands

### `wrapper snapshot`

Manually capture baseline snapshot.

**Usage:**
```bash
wrapper snapshot
```

**What it does:**
- Scans repository (files, directories, structure)
- Saves to `baseline_snapshot.json`

**Note:** Automatically runs during first `wrapper verify`, rarely needed manually.

**Example output:**
```
✅ Baseline snapshot captured

Repository snapshot:
  - 47 files
  - 12 directories
  - 3 file types

Created: baseline_snapshot.json
```

---

### `wrapper diff-baseline`

Show drift from baseline snapshot.

**Usage:**
```bash
wrapper diff-baseline
```

**What it does:**
- Compares current repo to `baseline_snapshot.json`
- Shows added/removed files and directories

**Example output:**
```
Drift from Baseline
===================

New files:
  + src/poller.py
  + src/api_client.py

Removed files:
  - src/flask_server.py

New directories:
  + src/polling/

File type changes:
  .py: 42 → 44 (+2)

Overall: 2 files added, 1 removed, 1 directory added
```

---

### `wrapper --version`

Show Copilot Sentinel version.

**Usage:**
```bash
wrapper --version
```

**Example output:**
```
Copilot Sentinel v1.2.0
```

---

## Common Workflows

### Basic Workflow
```bash
wrapper propose    # Generate next step
wrapper compile    # Create AI prompt
# Work with AI, make changes
wrapper verify     # Check changes
wrapper accept     # Record progress
```

### With Planning
```bash
wrapper plan init      # Create strategic plan
wrapper plan status    # Check progress
wrapper propose        # Get next step from plan
wrapper compile        # Create prompt
# Work with AI
wrapper verify --check-logic
wrapper test --step <id>
wrapper accept
```

### Multi-Repo
```bash
# In dependency repo
cd dependency-repo
wrapper sync-external --from ../other-repo

# Check for blockers
wrapper propose        # May generate BLOCKED step

# If blocked, fix dependency first
cd ../other-repo
# ... fix issue ...
wrapper accept

# Re-sync and continue
cd ../dependency-repo
wrapper sync-external --from ../other-repo
wrapper propose        # Now generates real work
```

---

## Next Steps

- **[Getting Started](getting-started.md)** - Hands-on tutorial
- **[Core Concepts](core-concepts.md)** - Understand file structures
- **[How It Works](how-it-works.md)** - Understand workflows
- **[Examples](examples.md)** - Real-world scenarios
- **[Troubleshooting](troubleshooting.md)** - Common issues

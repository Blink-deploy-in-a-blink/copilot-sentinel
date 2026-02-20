# How It Works

Internal workflows and process flows for Copilot Sentinel.

---

## Overview

Copilot Sentinel uses a baseline-deviation-fix workflow:

1. **Capture baseline** - Scan repo structure, find architecture violations
2. **Generate steps** - Create fix steps or implementation steps
3. **Verify changes** - Check git diff against constraints
4. **Track progress** - Update plan and deviation status

---

## Complete Workflow Diagram

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

## 1. Baseline Capture (Automatic)

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

### What Gets Captured

```json
{
  "files": [
    "src/main.py",
    "src/models/user.py",
    ...
  ],
  "directories": [
    "src/",
    "src/models/",
    ...
  ],
  "file_types": {
    ".py": 47,
    ".yaml": 3,
    ".md": 2
  }
}
```

### Deviation Detection

LLM analyzes your code against `architecture.md` and generates:

```yaml
deviations:
  - id: http-server-present
    severity: HIGH
    description: Flask server in main.py violates no-http-server constraint
    files:
      - src/main.py
    
  - id: direct-db-access
    severity: HIGH
    description: SQLAlchemy in models.py violates no-direct-db constraint
    files:
      - src/models/user.py
      - src/models/job.py
    
  - id: missing-polling
    severity: MEDIUM
    description: No polling mechanism found
    files: []
```

---

## 2. Step-by-Step Deviation Fixing

```
Step 1: Remove HTTP server code (fixes 2 deviations)
  ↓ verify + accept
Step 2: Add polling mechanism (fixes 1 deviation)
  ↓ verify + accept
Step 3: Restructure directories (fixes 4 deviations)
  ↓ verify + accept
... continue until clean
```

### How `wrapper propose` Works

**Without plan:**
1. Reads `deviations.yaml`
2. Reads `state.json` (completed steps)
3. Sends to LLM: "Generate next fix step"
4. LLM creates `step.yaml` targeting unresolved deviations

**With plan:**
1. Reads `implementation_plan.yaml`
2. Finds next incomplete step
3. Extracts features, requirements, constraints
4. Generates `step.yaml` from plan context

### Step Structure

```yaml
step_number: 3
title: "Remove Flask HTTP server"
goal: "Eliminate HTTP server code, violates architecture"
constraints:
  - "Must not break existing functionality"
  - "Must remove ALL Flask imports"
allowed_files:
  - "src/main.py"
  - "requirements.txt"
fixes_deviations:
  - "http-server-present"
  - "unused-routes"
features:  # v1.1.0+
  - "Remove Flask app initialization"
  - "Remove route handlers"
  - "Update requirements.txt"
non_functional_requirements:  # v1.1.0+
  security:
    - "Ensure no HTTP ports remain open"
  performance: []
  cost: []
```

---

## 3. Verification Process

### Git Diff Verification

`wrapper verify` checks:

1. **File constraints**: Only `allowed_files` modified
2. **Feature implementation**: Features from step.yaml completed
3. **Non-functional requirements**: Security/performance rules met
4. **AI output analysis**: Reads `copilot_output.txt` for verification-only steps

**Example:**
```
Step allows: src/main.py, requirements.txt
Git diff shows: src/main.py, requirements.txt ✅

Checking features:
  ✓ Remove Flask app initialization
  ✓ Remove route handlers
  ✓ Update requirements.txt

Security requirements:
  ✓ Ensure no HTTP ports remain open

✅ PASS - All constraints satisfied
```

### Logic Verification (v1.1.0+)

`wrapper verify --check-logic` sends to LLM:

**Prompt:**
```
Features checklist:
- Remove Flask app initialization
- Remove route handlers
- Update requirements.txt

Git diff:
[actual code changes]

Question: Are these features implemented CORRECTLY?
- Is logic sound?
- Are there bugs?
- Security issues?
```

**Response:**
```
✓ CORRECT: Flask app initialization removed
✓ CORRECT: Route handlers removed
✗ INCOMPLETE: requirements.txt still has Flask==2.0.0

Recommendation: Remove Flask from requirements.txt
```

---

## 4. Smart Deviation Resolution

When you run `wrapper accept`, the LLM automatically determines which deviations were resolved:

**Prompt:**
```
Completed step:
  Title: Remove Flask HTTP server
  Files changed: src/main.py, requirements.txt
  
Current deviations:
  - http-server-present (Flask server in main.py)
  - unused-routes (Route handlers defined)
  - direct-db-access (SQLAlchemy in models.py)

Which deviations did this step resolve?
```

**Response:**
```yaml
resolved_deviations:
  - http-server-present  # Flask removed
  - unused-routes        # Routes removed
# direct-db-access still present (not touched)
```

The system updates `deviations.yaml`:

```yaml
deviations:
  - id: http-server-present
    status: RESOLVED
    resolved_by_step: 3
    
  - id: direct-db-access
    status: OPEN
```

---

## 5. Cross-Repo Dependency Blocking

### How `wrapper sync-external` Works

```bash
cd agent-repo
wrapper sync-external --from ../ui-repo --from ../auth-repo
```

**Process:**
1. Reads `../ui-repo/.wrapper/deviations.yaml`
2. Reads `../ui-repo/.wrapper/repo.yaml`
3. Extracts high-severity deviations
4. Checks if any match `agent-repo`'s `depends_on` constraints
5. Stores in `agent-repo/.wrapper/external_state.json`

**Example external_state.json:**
```json
{
  "ui": {
    "high_severity_deviations": [
      {
        "id": "no-polling-endpoint",
        "description": "Missing /api/jobs/poll endpoint",
        "severity": "HIGH"
      }
    ]
  },
  "auth": {
    "high_severity_deviations": []
  }
}
```

### Blocking Behavior

When you run `wrapper propose` in agent-repo:

1. Checks `external_state.json`
2. Finds `ui` has high-severity deviation
3. **Blocks real work**, proposes:

```yaml
step_number: 5
title: "BLOCKED - Waiting for ui repo to implement polling endpoint"
goal: "Cannot proceed until dependency is resolved"
type: blocked
blocked_by:
  - repo: ui
    deviation: no-polling-endpoint
```

After `ui` fixes the issue:

```bash
cd ui
wrapper accept  # Resolves no-polling-endpoint

cd ../agent
wrapper sync-external --from ../ui
wrapper propose  # Now generates real work step
```

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

## First Run Always Passes

The first `wrapper verify` in a repository:
- **Purpose**: Document current reality, not enforce ideal
- **Result**: Always returns ✅ PASS
- **Side effect**: Creates baseline_snapshot.json and deviations.yaml
- **Message**: "Baseline captured - found X deviations"

This ensures you can adopt Copilot Sentinel in existing projects without immediate failures.

---

## Next Steps

- **[Getting Started](getting-started.md)** - Hands-on tutorial
- **[Core Concepts](core-concepts.md)** - Understand file structures and guarantees
- **[Commands](commands.md)** - Complete command reference
- **[Examples](examples.md)** - Real-world scenarios
- **[Multi-Repo Setup](multi-repo.md)** - Cross-repository management


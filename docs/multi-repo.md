# Multi-Repo Setup

## Overview

Copilot Sentinel supports multi-repository environments with explicit dependency management. Services can declare dependencies on other repos and block work if those dependencies have unresolved issues.

---

## Setup

### 1. Initialize Each Repository

```bash
# UI service
cd ui
wrapper init

# Agent service (depends on UI)
cd ../agent
wrapper init

# Auth service
cd ../auth
wrapper init
```

### 2. Configure Dependencies

In `agent/.wrapper/repo.yaml`:

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
  - repo: auth
    via: token validation API
```

### 3. Run Initial Baseline

```bash
# Each repo independently
cd ui && wrapper propose && wrapper verify && wrapper accept
cd agent && wrapper propose && wrapper verify && wrapper accept
cd auth && wrapper propose && wrapper verify && wrapper accept
```

---

## Working with Dependencies

### Before Working on Dependent Repo

```bash
cd agent
wrapper sync-external --from ../ui --from ../auth

wrapper propose
# → Checks for blockers in ui & auth
# → Proposes "blocked" step if dependencies broken
# → Proposes real work if clean
```

### Example: Blocked Workflow

**Scenario:** Agent depends on UI's polling endpoint, but UI hasn't implemented it yet.

```bash
cd agent
wrapper sync-external --from ../ui

wrapper propose
```

**Output:**
```
❌ BLOCKED: ui has high-severity deviation "no-polling-endpoint"

Generated step:
  Title: BLOCKED - Waiting for ui repo to implement polling endpoint
  Type: blocked
  Blocked by: ui (no-polling-endpoint)
```

**Step YAML:**
```yaml
step_number: 5
title: "BLOCKED - Waiting for ui repo to implement polling endpoint"
goal: "Cannot proceed until dependency is resolved"
type: blocked
blocked_by:
  - repo: ui
    deviation: no-polling-endpoint
    description: "Missing /api/jobs/poll endpoint required for agent polling"
constraints:
  - "Do not proceed with agent work until ui implements endpoint"
```

### After Dependency Fixes Issue

```bash
# In UI repo
cd ui
# ... fix polling endpoint ...
wrapper verify
wrapper accept  # Marks no-polling-endpoint as resolved

# In Agent repo
cd ../agent
wrapper sync-external --from ../ui

wrapper propose
```

**Output:**
```
✅ All dependencies clean

Generated step:
  Title: Implement job polling mechanism
  Goal: Poll UI endpoint every 30s for new jobs
  ...
```

---

## External State Tracking

### What Gets Synced

`wrapper sync-external --from ../ui` extracts:

1. **High-severity deviations** from `ui/.wrapper/deviations.yaml`
2. **Repository role** from `ui/.wrapper/repo.yaml`
3. **Baseline snapshot** (optional, for debugging)

### External State File

Stored in `agent/.wrapper/external_state.json`:

```json
{
  "ui": {
    "last_synced": "2026-01-30T14:23:45",
    "repo_role": "Frontend application. Provides job management UI.",
    "high_severity_deviations": [
      {
        "id": "no-polling-endpoint",
        "description": "Missing /api/jobs/poll endpoint",
        "severity": "HIGH",
        "files": []
      }
    ]
  },
  "auth": {
    "last_synced": "2026-01-30T14:23:45",
    "repo_role": "Authentication service. Provides token validation.",
    "high_severity_deviations": []
  }
}
```

---

## Blocking Rules

### When Work Gets Blocked

A step is marked as "blocked" if:

1. Dependency repo has **HIGH severity** deviation
2. Deviation relates to functionality this repo depends on
3. Deviation is marked as `OPEN` (not resolved)

### When Work Proceeds

Work proceeds normally if:

1. All dependencies have zero high-severity deviations, OR
2. High-severity deviations don't affect this repo's dependencies

---

## Example: Full Multi-Repo Workflow

### Initial State

```
ui/.wrapper/deviations.yaml:
  - id: no-polling-endpoint
    severity: HIGH
    status: OPEN

agent/.wrapper/repo.yaml:
  depends_on:
    - repo: ui
      via: polling endpoints
```

### Step 1: Agent Attempts Work

```bash
cd agent
wrapper sync-external --from ../ui
wrapper propose
```

**Result:** Blocked step generated

### Step 2: UI Fixes Endpoint

```bash
cd ui
wrapper propose
# → Step: Implement polling endpoint

# ... work with AI ...
wrapper verify
wrapper accept
```

**deviations.yaml updated:**
```yaml
deviations:
  - id: no-polling-endpoint
    severity: HIGH
    status: RESOLVED
    resolved_by_step: 7
```

### Step 3: Agent Unblocked

```bash
cd agent
wrapper sync-external --from ../ui
wrapper propose
```

**Result:** Real work step generated (polling mechanism)

---

## Best Practices

### 1. Sync Before Every Work Session

```bash
# Always sync dependencies first
wrapper sync-external --from ../ui --from ../auth
wrapper propose
```

### 2. Communicate Breaking Changes

If you're about to introduce a breaking change in a dependency:

```bash
cd ui
# Add deviation manually or let verify capture it
# Other repos will be blocked until you fix it
```

### 3. Use Severity Appropriately

- **HIGH**: Breaks dependent repos (missing endpoint, incompatible API)
- **MEDIUM**: Doesn't break others (performance issue, code smell)
- **LOW**: Minor issues (documentation, naming)

Only HIGH severity blocks dependent repos.

### 4. Sync Multiple Dependencies

```bash
wrapper sync-external --from ../ui --from ../auth --from ../billing
```

---

## Troubleshooting

### "Cannot find external repo"

```bash
# Use absolute paths if relative paths fail
wrapper sync-external --from /full/path/to/ui
```

### "External state shows stale data"

```bash
# Re-sync to refresh
wrapper sync-external --from ../ui
```

### "Blocked but dependency looks clean"

```bash
# Check external_state.json
cat .wrapper/external_state.json

# Check dependency's deviations
cat ../ui/.wrapper/deviations.yaml
```

---

## Directory Structure (Multi-Repo)

```
workspace/
├── ui/
│   ├── .wrapper/
│   │   ├── deviations.yaml
│   │   ├── repo.yaml
│   │   └── ...
│   └── src/
│
├── agent/
│   ├── .wrapper/
│   │   ├── deviations.yaml
│   │   ├── repo.yaml
│   │   ├── external_state.json  ← Synced from ui & auth
│   │   └── ...
│   └── src/
│
└── auth/
    ├── .wrapper/
    │   ├── deviations.yaml
    │   ├── repo.yaml
    │   └── ...
    └── src/
```

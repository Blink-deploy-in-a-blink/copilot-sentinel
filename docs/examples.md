# Examples

Real-world usage scenarios for Copilot Sentinel.

---

## Example 1: Removing HTTP Server (Architecture Violation)

### Scenario

Your architecture says "no HTTP servers" but your repo has a Flask app.

### Setup

**architecture.md:**
```markdown
# Agent Architecture

## Constraints
- NO HTTP endpoints (security requirement)
- Polling-based communication only
```

**Actual code (main.py):**
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/jobs', methods=['GET'])
def get_jobs():
    return {"jobs": [...]}

if __name__ == '__main__':
    app.run(port=5000)
```

### Workflow

#### Step 1: Capture Baseline

```bash
wrapper init
wrapper propose
wrapper verify
```

**Output:**
```
✅ PASS - Baseline captured
Found 2 deviations:
  [HIGH] http-server-present: Flask server in main.py
  [HIGH] http-route-handlers: Route handlers violate no-http constraint
```

#### Step 2: Get Fix Step

```bash
wrapper propose
```

**Generated step.yaml:**
```yaml
step_number: 2
title: "Remove Flask HTTP server"
goal: "Eliminate HTTP server code, violates architecture"
constraints:
  - "Must not break job retrieval functionality"
allowed_files:
  - "src/main.py"
  - "requirements.txt"
fixes_deviations:
  - "http-server-present"
  - "http-route-handlers"
```

#### Step 3: Compile Prompt

```bash
wrapper compile
```

**copilot_prompt.txt:**
```
You are implementing this step:

Title: Remove Flask HTTP server
Goal: Eliminate HTTP server code, violates architecture

Constraints:
- Must not break job retrieval functionality

Allowed files:
- src/main.py
- requirements.txt

Instructions:
1. Remove Flask app and route handlers
2. Replace with polling mechanism (future step will implement)
3. Update requirements.txt to remove Flask
```

#### Step 4: Work with AI

Give `copilot_prompt.txt` to Copilot/Claude, get response, make changes.

**New main.py:**
```python
# Flask removed
# Polling mechanism will be added in next step

def get_jobs_placeholder():
    # TODO: Implement polling in next step
    pass
```

#### Step 5: Verify

```bash
wrapper verify
```

**Output:**
```
✅ PASS
Files changed: src/main.py, requirements.txt
Constraints satisfied
```

#### Step 6: Accept

```bash
wrapper accept
```

**deviations.yaml updated:**
```yaml
deviations:
  - id: http-server-present
    status: RESOLVED
    resolved_by_step: 2
  - id: http-route-handlers
    status: RESOLVED
    resolved_by_step: 2
```

---

## Example 2: Multi-Repo Dependency Blocking

### Scenario

Agent service depends on UI service's polling endpoint. UI hasn't implemented it yet.

### Setup

**ui/.wrapper/deviations.yaml:**
```yaml
deviations:
  - id: no-polling-endpoint
    severity: HIGH
    description: "Missing /api/jobs/poll endpoint"
    status: OPEN
```

**agent/.wrapper/repo.yaml:**
```yaml
repo_name: agent
depends_on:
  - repo: ui
    via: polling endpoints
```

### Workflow

#### In Agent Repo

```bash
cd agent
wrapper sync-external --from ../ui
wrapper propose
```

**Output:**
```
❌ BLOCKED: ui has high-severity deviation "no-polling-endpoint"

Generated step:
  Title: BLOCKED - Waiting for ui to implement polling endpoint
  Type: blocked
```

**step.yaml:**
```yaml
step_number: 5
title: "BLOCKED - Waiting for ui to implement polling endpoint"
type: blocked
blocked_by:
  - repo: ui
    deviation: no-polling-endpoint
```

#### In UI Repo (Fix Dependency)

```bash
cd ../ui
wrapper propose
# → Step: Implement polling endpoint

# ... work with AI ...
wrapper verify
wrapper accept
```

**ui/deviations.yaml updated:**
```yaml
deviations:
  - id: no-polling-endpoint
    status: RESOLVED
    resolved_by_step: 7
```

#### Back to Agent Repo

```bash
cd ../agent
wrapper sync-external --from ../ui
wrapper propose
```

**Output:**
```
✅ All dependencies clean

Generated step:
  Title: Implement job polling mechanism
  Goal: Poll UI endpoint every 30s
```

**Now unblocked!**

---

## Example 3: Planning a New Feature

### Scenario

Adding authentication system from scratch using plan-driven workflow.

### Workflow

#### Step 1: Create Plan

```bash
wrapper plan init
```

**Interactive Q&A:**
```
What are you building? 
> Authentication system with JWT tokens

Break it into high-level phases (comma-separated):
> Remove hardcoded credentials, Implement JWT validation, Add password hashing

Let's detail Phase 1: Remove hardcoded credentials

Break this phase into steps:
> Find all hardcoded credentials, Replace with environment variables, Add .env.example file

Step 1: Find all hardcoded credentials
Features (comma-separated):
> Scan all Python files, Identify API keys and passwords, Document locations

Security requirements:
> Never log credentials, Use secure file permissions for .env

... (continues for all steps/phases)
```

**Generated implementation_plan.yaml:**
```yaml
phases:
  - name: Remove hardcoded credentials
    steps:
      - id: step-1-find-credentials
        title: "Find all hardcoded credentials"
        features:
          - "Scan all Python files"
          - "Identify API keys and passwords"
          - "Document locations"
        non_functional_requirements:
          security:
            - "Never log credentials"
            - "Use secure file permissions for .env"
        status: NOT_STARTED
      
      - id: step-2-replace-with-env
        title: "Replace with environment variables"
        features:
          - "Create .env file"
          - "Update code to use os.environ"
          - "Remove hardcoded values"
        status: NOT_STARTED
      
      - id: step-3-add-env-example
        title: "Add .env.example file"
        features:
          - "Create template file"
          - "Document required variables"
        status: NOT_STARTED
```

#### Step 2: Execute Plan

```bash
wrapper propose --from-plan
```

**Output:**
```
Next step from plan:
  Phase: Remove hardcoded credentials (step 1/3)
  Step: Find all hardcoded credentials
```

**Generated step.yaml:**
```yaml
step_number: 1
title: "Find all hardcoded credentials"
features:
  - "Scan all Python files"
  - "Identify API keys and passwords"
  - "Document locations"
non_functional_requirements:
  security:
    - "Never log credentials"
```

```bash
wrapper compile
# ... work with AI ...
wrapper verify --check-logic
wrapper accept
```

#### Step 3: Track Progress

```bash
wrapper plan status
```

**Output:**
```
Implementation Plan Progress
═══════════════════════════

Phase 1: Remove hardcoded credentials (1/3 complete)
  ✅ step-1-find-credentials
  ⏳ step-2-replace-with-env
  ⏳ step-3-add-env-example

Phase 2: Implement JWT validation (0/2 complete)
  ⏳ step-4-add-jwt-library
  ⏳ step-5-implement-validation

Phase 3: Add password hashing (0/1 complete)
  ⏳ step-6-bcrypt-hashing

Overall: 1/6 steps complete (17%)
```

---

## Example 4: Testing Completed Features

### Scenario

Completed authentication phase, want to verify features work correctly.

### Workflow

#### After Completing Steps

```bash
# Completed step-1, step-2, step-3
wrapper accept  # (for step-3)
```

**implementation_plan.yaml:**
```yaml
phases:
  - name: Remove hardcoded credentials
    steps:
      - id: step-1-find-credentials
        status: COMPLETED
        files_changed:
          - src/auth.py
          - src/api.py
      
      - id: step-2-replace-with-env
        status: COMPLETED
        files_changed:
          - src/auth.py
          - .env
          - .env.example
      
      - id: step-3-add-env-example
        status: COMPLETED
        files_changed:
          - .env.example
```

#### Test the Phase

```bash
wrapper test
# Choose: Test Phase: Remove hardcoded credentials
```

**Output:**
```
Testing Phase: Remove hardcoded credentials (3 steps)
═══════════════════════════════════════════════════

Step 1/3: Find all hardcoded credentials
  Reading files: src/auth.py, src/api.py
  
  Features:
    ✓ CORRECT: Scan all Python files
    ✓ CORRECT: Identify API keys and passwords
    ✓ CORRECT: Document locations
  
  ✅ PASS

Step 2/3: Replace with environment variables
  Reading files: src/auth.py, .env, .env.example
  
  Features:
    ✓ CORRECT: Create .env file
    ✗ BROKEN: Update code to use os.environ
    ✓ CORRECT: Remove hardcoded values
  
  Logic bugs found:
    - src/auth.py line 23: Still uses hardcoded API_KEY fallback
  
  Security:
    ⚠ WARNING: .env file has 0644 permissions (should be 0600)
  
  ⚠ NEEDS FIXES

Step 3/3: Add .env.example file
  Reading files: .env.example
  
  Features:
    ✓ CORRECT: Create template file
    ✓ CORRECT: Document required variables
  
  ✅ PASS

Phase Summary:
  ✓ Passed: 2/3
  ⚠ Needs fixes: 1/3

Recommendations:
  - Fix step-2: Remove API_KEY fallback in src/auth.py
  - Fix step-2: Set .env permissions to 0600
```

#### Fix Issues

```bash
# Fix the bugs identified
# ... make changes ...
wrapper verify
wrapper accept --update-metadata

# Re-test
wrapper test --step step-2-replace-with-env
```

**Output:**
```
Testing Step: step-2-replace-with-env
  ✅ PASS - All features correct
```

---

## Example 5: Legacy Mode (No Plan)

### Scenario

Quick fix project, don't want full planning overhead.

### Workflow

```bash
wrapper init
wrapper propose --no-plan  # Skip planning

# First run captures baseline
wrapper verify
# ✅ PASS - Baseline captured, 5 deviations found

# Get next fix
wrapper propose --no-plan
wrapper compile
# ... work with AI ...
wrapper verify
wrapper accept

# Repeat until clean
wrapper propose --no-plan
# Eventually: "No deviations remaining"
```

**Use case:** Small repos, quick refactors, one-off fixes.

---

## Example 6: CI/CD Integration

### GitHub Actions

```yaml
name: Test Implementation

on: [push, pull_request]

jobs:
  test-features:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Copilot Sentinel
        run: pip install -e .
      
      - name: Test Specific Step
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        run: |
          wrapper test --step step-5-add-auth
```

### Use Case

- Test critical steps on every PR
- Ensure logic correctness before merge
- Catch bugs that pass code review

---

## Example 7: Verification-Only Step

### Scenario

Need to analyze codebase without making changes.

### Workflow

```bash
wrapper propose
# → Generates verification step (type: verification)

wrapper compile
```

**copilot_prompt.txt:**
```
VERIFICATION STEP - ANALYZE ONLY, DO NOT MODIFY FILES

Analyze:
- src/auth.py
- src/api.py

Find:
- All authentication mechanisms
- Security vulnerabilities

Output analysis to copilot_output.txt (not as code files)
```

**Work with AI:**
```bash
# AI analyzes code, outputs report
# Paste report into .wrapper/copilot_output.txt
```

```bash
wrapper verify
# ✅ PASS (checks copilot_output.txt exists)

wrapper accept
# Proceeds to next step (implementation)
```

**Use case:** Understanding complex codebase, security audits, documentation.

# Testing Guide

## Overview

Copilot Sentinel includes a feature testing system (v1.2.0+) that verifies completed implementation steps against their original feature checklists. This catches logic bugs that pass git diff verification but fail functional requirements.

---

## When to Test

**During Development:**
- After completing a phase (test all steps in phase)
- When you suspect a logic bug
- Before marking work as "done"

**In CI/CD:**
- Automated testing with `wrapper test --step <id>`
- Regression testing on merged PRs

**Before Release:**
- Test all completed work with `wrapper test` → "Test ALL"

---

## Testing Commands

### Interactive Testing Menu

```bash
wrapper test
```

**Menu:**
```
Available test targets:
1. Test Phase: Authentication (3/3 done)
2. Test Phase: Database Layer (1/2 done, skips incomplete)
3. Test Step: step-1-remove-flask
4. Test Step: step-2-add-polling
5. Test ALL completed work

Choose: 
```

### Direct Step Testing

```bash
wrapper test --step step-1-remove-flask
```

**Use case:** CI/CD integration, specific bug investigation

---

## How It Works

### 1. Identifies Completed Steps

Reads `implementation_plan.yaml`:

```yaml
phases:
  - name: Remove HTTP Server
    steps:
      - id: step-1-remove-flask
        status: COMPLETED
        features:
          - "Remove Flask app initialization"
          - "Remove route handlers"
          - "Update requirements.txt"
        files_changed:
          - src/main.py
          - requirements.txt
```

### 2. Reads Actual Code

Loads files from `files_changed`:

```python
# src/main.py content
# requirements.txt content
```

### 3. Sends to LLM for Analysis

**Prompt:**
```
Step: Remove Flask HTTP server

Features checklist:
- Remove Flask app initialization
- Remove route handlers  
- Update requirements.txt

Non-functional requirements:
Security:
  - Ensure no HTTP ports remain open

Actual code (src/main.py):
[file contents]

Actual code (requirements.txt):
[file contents]

Question: Are these features implemented CORRECTLY?
- Check each feature: ✓ CORRECT | ✗ BROKEN | ⚠ INCOMPLETE
- Identify logic bugs
- Verify security requirements
- Provide recommendations
```

### 4. Reports Results

```
Testing Step: step-1-remove-flask
─────────────────────────────────

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
  - Run pip freeze to verify no Flask dependencies remain

Overall: ⚠ NEEDS FIXES
```

---

## Testing vs Verification

### `wrapper verify` (During Development)

- **When**: Before `wrapper accept`
- **What**: Checks git diff against `step.yaml` constraints
- **Purpose**: Ensure changes match step requirements
- **Scope**: Current uncommitted changes only

**Example:**
```
Step allows: src/main.py, requirements.txt
Git diff shows: src/main.py, requirements.txt ✅
Features present in diff: ✅
Security requirements met: ✅

✅ PASS
```

### `wrapper test` (After Completion)

- **When**: After `wrapper accept` (step marked complete)
- **What**: Reads actual code files, analyzes logic correctness
- **Purpose**: Find bugs in "completed" implementations
- **Scope**: All files_changed for completed steps

**Example:**
```
Reading src/main.py (actual committed code)
Reading requirements.txt

Analysis:
  ✗ INCOMPLETE: Flask dependency not removed

⚠ NEEDS FIXES
```

**Key difference:** `verify` checks constraints, `test` checks correctness.

---

## Phase Testing

Testing a phase tests all completed steps within that phase:

```bash
wrapper test
# Choose: Test Phase: Authentication
```

**Process:**
1. Finds all completed steps in "Authentication" phase
2. Tests each step sequentially
3. Reports overall phase health

**Output:**
```
Testing Phase: Authentication (3 steps)
═══════════════════════════════════════

Step 1/3: Remove hardcoded credentials
  ✓ PASS - All features correct

Step 2/3: Add JWT validation
  ⚠ NEEDS FIXES - Token expiry not checked

Step 3/3: Implement password hashing
  ✓ PASS - All features correct

Phase Summary:
  ✓ Passed: 2/3
  ⚠ Needs fixes: 1/3
  
Overall: ⚠ PHASE HAS ISSUES
```

---

## Testing ALL Completed Work

```bash
wrapper test
# Choose: Test ALL
```

**Use case:** Pre-release verification, comprehensive audit

**Process:**
1. Scans entire `implementation_plan.yaml`
2. Tests every completed step across all phases
3. Generates full report

**Output:**
```
Testing ALL completed work (12 steps)
════════════════════════════════════

Phase 1: Remove HTTP Server (3/3 steps)
  ✓ step-1-remove-flask
  ✓ step-2-remove-routes
  ✓ step-3-update-requirements

Phase 2: Add Polling (2/2 steps)
  ✓ step-4-job-poller
  ⚠ step-5-error-handling (retry logic incorrect)

Phase 3: Security (2/3 steps, 1 incomplete)
  ✓ step-6-input-validation
  ✗ step-7-rate-limiting (not implemented correctly)

Overall Summary:
  ✓ Passed: 10/12
  ⚠ Needs fixes: 1/12
  ✗ Broken: 1/12
  
Recommendation: Fix step-5, step-7 before release
```

---

## Test Output Interpretation

### Feature Status

| Symbol | Meaning | Action |
|--------|---------|--------|
| ✓ CORRECT | Feature implemented correctly | None |
| ⚠ INCOMPLETE | Feature partially implemented | Complete implementation |
| ✗ BROKEN | Feature has logic bugs | Fix bugs |
| − MISSING | Feature not implemented | Implement feature |

### Overall Step Status

| Status | Meaning |
|--------|---------|
| ✓ PASS | All features correct, no bugs |
| ⚠ NEEDS FIXES | Some features incomplete or minor bugs |
| ✗ BROKEN | Critical bugs or missing features |

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test Implementation

on: [push, pull_request]

jobs:
  test-features:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Install Copilot Sentinel
        run: |
          pip install -e .
      
      - name: Test Completed Steps
        env:
          DEEPSEEK_API_KEY: ${{ secrets.DEEPSEEK_API_KEY }}
        run: |
          # Test specific steps
          wrapper test --step step-1-remove-flask
          wrapper test --step step-2-add-polling
          
          # Or test all (if you want full coverage)
          # wrapper test → automate menu with 'ALL' input
```

### Test Specific Steps on PR

```bash
# In PR check script
wrapper test --step step-${PR_NUMBER}
```

---

## Common Testing Scenarios

### Scenario 1: Logic Bug in "Completed" Feature

```
Feature: "Add timeout to job execution (5 minutes)"
Status: COMPLETED

Test result:
  ✗ BROKEN: Timeout set to 500 seconds instead of 300 seconds
  
Logic bug: Math error (5 min = 300s, not 500s)
```

### Scenario 2: Security Requirement Missed

```
Feature: "Validate user input before DB query"
Status: COMPLETED

Test result:
  ⚠ INCOMPLETE: Input validation present but doesn't check SQL injection
  
Security issue: Only validates format, not malicious content
```

### Scenario 3: Edge Case Not Handled

```
Feature: "Retry failed jobs 3 times"
Status: COMPLETED

Test result:
  ✗ BROKEN: Retry logic infinite loops on network errors
  
Logic bug: No max retry check, retries indefinitely
```

---

## Limitations

### What Testing CANNOT Do

1. **Runtime testing**: Only analyzes code statically, doesn't execute
2. **Integration testing**: Only checks individual steps, not full flow
3. **Performance testing**: Only checks code logic, not actual performance
4. **External dependencies**: Can't verify third-party API behavior

### What Testing CAN Do

1. **Logic verification**: Catches off-by-one errors, wrong constants, etc.
2. **Feature completeness**: Ensures all checklist items implemented
3. **Security checks**: Verifies security requirements in code
4. **Code quality**: Identifies missing error handling, edge cases

---

## Best Practices

### 1. Test After Each Phase

```bash
# Complete phase
wrapper accept  # (last step in phase)

# Immediately test
wrapper test  # Choose phase
```

### 2. Capture Implementation Details

When running `wrapper accept`, provide good implementation notes:

```
Files changed: src/main.py, src/poller.py
Implementation notes: Used ThreadPoolExecutor for polling, 30s interval with sleep()
```

This helps the LLM understand your implementation during testing.

### 3. Fix Issues Immediately

Don't accumulate broken steps. Fix issues as testing reveals them:

```bash
wrapper test
# → Finds bug in step-5

# Fix it immediately
# ... make changes ...
wrapper verify
wrapper accept

# Re-test
wrapper test --step step-5
# → Now passes
```

### 4. Test Before Merging

```bash
# Before PR merge
wrapper test  # Choose "Test ALL"

# Only merge if all tests pass
```

---

## Troubleshooting

### "No completed steps to test"

- Ensure you've run `wrapper accept` to mark steps complete
- Check `implementation_plan.yaml` has `status: COMPLETED`

### "Missing files_changed field"

- Steps completed before v1.2.0 may not have `files_changed`
- Re-capture with: `wrapper accept --update-metadata`

### "LLM says tests pass but code is broken"

- LLM analysis has limitations (no runtime execution)
- Use traditional unit tests alongside Copilot Sentinel testing
- Provide more context in implementation notes

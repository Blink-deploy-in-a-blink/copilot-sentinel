# Troubleshooting

Common issues and solutions when using Copilot Sentinel.

---

## Installation & Setup

### "No LLM API key configured"

**Error:**
```
Error: No LLM API key configured
```

**Solution:**
```bash
# DeepSeek (default)
export DEEPSEEK_API_KEY="sk-..."      # Linux/Mac
$env:DEEPSEEK_API_KEY="sk-..."        # Windows

# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-..."
```

Or set in `.wrapper/config.yaml`:
```yaml
llm_provider: deepseek
deepseek_api_key: sk-...
```

### "Not in a git repository"

**Error:**
```
Error: Not in a git repository
```

**Solution:**
```bash
git init
git add .
git commit -m "Initial commit"
```

Copilot Sentinel requires git for diff tracking.

---

## Verification Issues

### "Verification step requires Copilot output"

**Error:**
```
Error: Verification step requires copilot_output.txt
```

**Cause:** Step type is `verification` (analysis-only, no code changes)

**Solution:**
1. Copy LLM's analysis response
2. Paste into `.wrapper/copilot_output.txt`
3. Run `wrapper verify` again

### "File not in allowed_files list"

**Error:**
```
❌ FAIL - Modified files not in allowed_files
Modified: src/unauthorized.py
Allowed: src/main.py, src/poller.py
```

**Cause:** You modified files not listed in `step.yaml`

**Solution:**

**Option 1:** Undo unauthorized changes
```bash
git checkout src/unauthorized.py
wrapper verify
```

**Option 2:** If changes are necessary, update step
```bash
# Manually edit .wrapper/step.yaml
allowed_files:
  - src/main.py
  - src/poller.py
  - src/unauthorized.py  # Add this

wrapper verify
```

### "ACCEPT BLOCKED - must PASS verify first"

**Error:**
```
❌ Cannot accept - verification has not passed
```

**Solution:**
```bash
# Run verify until it passes
wrapper verify

# Only then accept
wrapper accept
```

### ".wrapper/ files flagged as violations"

**Error:**
```
Modified: .wrapper/step.yaml (not in allowed_files)
```

**Cause:** Older version bug (fixed in v1.0.1+)

**Solution:**
- Upgrade to v1.0.1 or later
- `.wrapper/` files are automatically ignored

---

## Planning Issues

### "No implementation plan found"

**Error:**
```
Error: No implementation plan found, run 'wrapper plan init' first
```

**Solution:**
```bash
# Create a plan first
wrapper plan init

# OR use legacy mode (no plan)
wrapper propose --no-plan
```

### "Step not found in plan"

**Error:**
```
Error: Step 'step-5' not found in implementation plan
```

**Cause:** Step ID doesn't match plan

**Solution:**
```bash
# Check plan
wrapper plan show

# Verify step IDs
cat .wrapper/implementation_plan.yaml | grep "id:"
```

---

## Multi-Repo Issues

### "Cannot find external repo"

**Error:**
```
Error: Directory ../ui not found
```

**Solution:**
```bash
# Use absolute paths
wrapper sync-external --from /full/path/to/ui

# Or ensure relative path is correct
ls ../ui/.wrapper/deviations.yaml  # Should exist
```

### "External state shows stale data"

**Symptom:** Dependency repo fixed issue, but still showing as blocked

**Solution:**
```bash
# Re-sync to refresh external state
wrapper sync-external --from ../ui
wrapper propose
```

### "Blocked but dependency looks clean"

**Debug:**
```bash
# Check what external state sees
cat .wrapper/external_state.json

# Check dependency's actual deviations
cat ../ui/.wrapper/deviations.yaml

# Look for HIGH severity, status: OPEN
```

**Solution:**
- Ensure dependency ran `wrapper accept` to mark deviations resolved
- Re-sync after dependency fixes issues

---

## Baseline & Deviation Issues

### "Check what changed since baseline"

**Command:**
```bash
wrapper diff-baseline
```

**Output:**
```
Files added: src/new_module.py
Files removed: src/old_module.py
Files modified: src/main.py
```

### "Want to re-capture baseline"

**Use case:** Major refactor, want fresh baseline

**Command:**
```bash
wrapper snapshot

# Then verify to regenerate deviations
wrapper verify
```

**Warning:** This resets deviation tracking. Only use if intentional.

### "Deviations not being resolved"

**Symptom:** `wrapper accept` doesn't mark deviations as resolved

**Debug:**
```bash
# Check state
cat .wrapper/deviations.yaml

# Check if step targeted the deviation
cat .wrapper/step.yaml | grep fixes_deviations
```

**Solution:**
- Ensure `step.yaml` has `fixes_deviations` list
- LLM auto-determines resolution, may miss some
- Manually edit `deviations.yaml` if needed:
  ```yaml
  - id: http-server-present
    status: RESOLVED  # Change from OPEN
    resolved_by_step: 5
  ```

---

## Testing Issues

### "No completed steps to test"

**Error:**
```
No completed steps found in implementation plan
```

**Solution:**
- Ensure you've run `wrapper accept` to mark steps complete
- Check `implementation_plan.yaml`:
  ```yaml
  steps:
    - id: step-1
      status: COMPLETED  # Must be COMPLETED
  ```

### "Missing files_changed field"

**Error:**
```
Warning: Step step-1 has no files_changed, skipping
```

**Cause:** Step completed before v1.2.0

**Solution:**
```bash
# Manually add to implementation_plan.yaml
steps:
  - id: step-1
    status: COMPLETED
    files_changed:  # Add this
      - src/main.py
      - requirements.txt
```

---

## Encoding Issues (Windows)

### "charmap codec can't decode"

**Error:**
```
UnicodeDecodeError: 'charmap' codec can't decode byte
```

**Cause:** Fixed in v1.0.1+, Windows encoding issue

**Solution:**
- Upgrade to v1.0.1 or later
- UTF-8 encoding now explicit in all file operations

---

## LLM Provider Issues

### "OpenAI rate limit exceeded"

**Error:**
```
Error: Rate limit exceeded (OpenAI)
```

**Solution:**
- Switch to DeepSeek (cheaper, faster):
  ```bash
  export DEEPSEEK_API_KEY="sk-..."
  ```
- Or wait and retry

### "Anthropic API error"

**Error:**
```
Error: Anthropic API returned 500
```

**Solution:**
- Check API key is valid
- Retry (transient error)
- Switch to another provider temporarily

---

## Git Issues

### "Git diff is empty but I made changes"

**Cause:** Changes not staged or committed

**Debug:**
```bash
git status
git diff  # Unstaged changes
git diff --staged  # Staged changes
```

**Solution:**
```bash
# Stage changes
git add .

# Verify picks up changes
wrapper verify
```

### "Git diff too large"

**Symptom:** Verification takes forever or times out

**Cause:** Step modifies too many files

**Solution:**
- Break into smaller steps
- Use `allowed_files` to limit scope
- Ensure you're not modifying node_modules, .venv, etc.

---

## Command Issues

### "wrapper command not found"

**Error:**
```bash
bash: wrapper: command not found
```

**Solution:**
```bash
# Ensure installed in editable mode
pip install -e .

# Or run via Python
python -m wrapper --version
```

### "--version shows old version"

**Symptom:** Updated VERSION file but `wrapper --version` shows old

**Cause:** Not reinstalled

**Solution:**
```bash
pip install -e . --force-reinstall
wrapper --version
```

---

## General Debugging

### Enable Verbose Output

```bash
# (Feature not yet implemented)
# Future: wrapper --verbose propose
```

### Check State Files

```bash
# Current state
cat .wrapper/state.json

# Baseline snapshot
cat .wrapper/baseline_snapshot.json

# Deviations
cat .wrapper/deviations.yaml

# Current step
cat .wrapper/step.yaml

# Implementation plan
cat .wrapper/implementation_plan.yaml
```

### Clean Slate (Nuclear Option)

**Warning:** Deletes all Copilot Sentinel state

```bash
rm -rf .wrapper/
wrapper init
# Start fresh
```

---

## Getting Help

If none of these solutions work:

1. **Check version**: `wrapper --version` (ensure latest)
2. **Check logs**: Look for error messages in terminal
3. **GitHub Issues**: https://github.com/Blink-deploy-in-a-blink/copilot-sentinel/issues
4. **Provide context**:
   - Copilot Sentinel version
   - OS (Windows/Linux/Mac)
   - Command that failed
   - Full error message
   - Relevant .wrapper/ file contents

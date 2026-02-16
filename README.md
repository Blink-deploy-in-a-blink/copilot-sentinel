# Copilot Sentinel

**Make AI follow your architecture. Or block it.**

Copilot is powerful. It's also chaotic. This CLI enforces discipline: captures your architecture as explicit rules, verifies every change against constraints, tests logic correctness, and blocks cross-repo work when dependencies break.

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/Blink-deploy-in-a-blink/copilot-sentinel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

You use GitHub Copilot, Claude, or Cursor. The code looks great. You ship it. Then:

**Scenario 1: Architectural violation**
```
Your architecture.md: "NO HTTP servers (security requirement)"
Copilot's code: Adds Flask app with @app.route('/api/jobs')
Your review: Looks fine, ships to prod
Reality: Now you have an unapproved attack surface
```

**Scenario 2: Logic bug in "completed" feature**
```
Step: "Add authentication check before processing"
Copilot's code: if not is_authenticated(): return True  # Bug: inverted logic
Your review: Function exists ✓, ships
Reality: Unauthenticated users get full access
```

**Scenario 3: Cross-repo chaos**
```
Service A (agent): Built assuming Service B (UI) has /api/jobs/poll endpoint
Service B reality: Endpoint doesn't exist yet, marked as HIGH deviation
Your build: Agent deploys, crashes in production polling non-existent endpoint
```

**You need guardrails, not just autocomplete.**

---

## What This Does

1. **Captures your architecture** as explicit rules (no HTTP servers, no direct DB access, etc.)
2. **Scans your repo** and finds ALL violations automatically (baseline snapshot)
3. **Plans implementation** with LLM-assisted strategic breakdown
4. **Generates steps** that fix violations or implement features
5. **Verifies git diff** against constraints before accepting changes
6. **Tests logic** to confirm features actually work correctly
7. **Blocks cross-repo work** if dependencies have unresolved issues

**Everything explicit. Everything verified. No implicit trust.**

---

## 60-Second Example

```bash
# Install
git clone https://github.com/Blink-deploy-in-a-blink/copilot-sentinel.git
cd copilot-sentinel
pip install -e .

# In your project
cd your-project
wrapper init

# Set API key (DeepSeek is default - fast & cheap)
export DEEPSEEK_API_KEY="sk-..."      # Linux/Mac
$env:DEEPSEEK_API_KEY="sk-..."        # Windows

# Create implementation plan (NEW in v1.1.0)
wrapper plan init
# Interactive Q&A builds strategic plan
# Breaks work into phases → steps → features

# Execute plan step-by-step
wrapper propose --from-plan   # Get next step
wrapper compile               # Generate AI prompt
# → Give copilot_prompt.txt to AI
# → Paste response in copilot_output.txt
wrapper verify --check-logic  # Verify features implemented correctly
wrapper accept                # Mark complete, move to next

# Check progress anytime
wrapper plan status
```

**Output (success):**
```
✅ Phase 1: Remove HTTP Server (3/3 steps complete)
⏳ Phase 2: Add Polling Mechanism (1/3 steps complete)
   → Next: Implement job poller with 30s interval
```

**Output (failure - catches violations):**
```
❌ VERIFICATION FAILED

Step allows modifications to: src/poller.py, src/config.py
Git diff shows changes to: src/poller.py, src/server.py ❌

Unauthorized file modified: src/server.py
Constraint violated: Step does not permit touching server code

→ Fix: Revert src/server.py changes, re-run wrapper verify
```

---

## Quick Start (With Planning - Recommended)

```bash
# 1. Initialize
wrapper init

# 2. Set API key
export DEEPSEEK_API_KEY="sk-..."

# 3. Create implementation plan
wrapper plan init
# Interactive planning session:
#   - Define high-level phases
#   - Break into detailed steps
#   - Capture security/performance requirements

# 4. Execute step-by-step
wrapper propose --from-plan   # Gets next step from plan
wrapper compile               # Generates copilot_prompt.txt
# ... work with AI ...
wrapper verify --check-logic  # Verifies features checklist
wrapper accept                # Updates plan, moves forward

# Repeat step 4 until done
```

---

## Quick Start (Without Planning - Legacy Mode)

```bash
# First run (captures baseline)
wrapper propose
wrapper compile
# Give copilot_prompt.txt to AI, paste response in copilot_output.txt
wrapper verify     # Auto-captures baseline, always passes first time
wrapper accept

# Repeat for each deviation fix
wrapper propose    # Generates fix step
wrapper compile
# ... work with AI ...
wrapper verify
wrapper accept
```

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

## Multi-Repo Dependency Enforcement

**Cross-repo safety:** If dependency repos have unresolved architectural violations, new work is blocked.

```bash
# Service A depends on Service B
cd service-a
wrapper sync-external --from ../service-b
wrapper propose
```

**If Service B is broken:**
```
❌ BLOCKED: service-b has HIGH severity deviation "missing-auth-endpoint"
Cannot proceed until dependency resolves architectural violation

Step proposed: BLOCKED - waiting for service-b
```

**After Service B fixes the issue:**
```
✅ All dependencies clean
Step proposed: Implement authentication flow (uses service-b endpoint)
```

**This prevents building on broken foundations.**

---

## Configuration (One-Time Setup)

After `wrapper init`, edit these files in `.wrapper/`:

### `.wrapper/architecture.md` - Your Target Architecture

```markdown
# Agent Architecture

## Structure
- Polling-based job execution
- No inbound HTTP server
- Communicate via message queue

## Constraints
- NO HTTP endpoints (security requirement)
- NO direct database access (use API)
- Jobs MUST timeout after 5 minutes
```

### `.wrapper/repo.yaml` - Repository Boundaries

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

### `.wrapper/config.yaml` - LLM Provider (Optional)

```yaml
llm_provider: deepseek  # or 'openai' or 'anthropic'
deepseek_api_key: sk-...  # or set via environment variable
```

**Supported LLMs:**
- **DeepSeek** (default) - Fast, cheap, good results
- **OpenAI** - GPT-4 / GPT-3.5  
- **Anthropic** - Claude

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
│   ├── implementation_plan.yaml # [AUTO] Strategic plan (v1.1.0+)
│   └── external_state.json      # [AUTO] Dependency repo states
```

---

## Why This Is Different

**AI assistants generate code. This tool ensures that code respects your rules.**

| Feature | Copilot/Cursor/Claude | Copilot Sentinel |
|---------|----------------------|------------------|
| Architectural rules | Implicit (buried in comments) | Explicit (architecture.md, enforced) |
| Verification | Manual code review | Automatic git diff + constraint checking |
| Logic correctness | Hope and pray | LLM analyzes features vs actual code |
| Cross-repo safety | "It should work" | Blocks if dependencies have violations |
| Drift tracking | None | Baseline snapshot + deviation YAML |
| Planning | Ad-hoc prompts | Strategic phase/step breakdown |

**Philosophy:** Discipline over intelligence. Make constraints explicit, verify everything, block chaos.

---

## Who This Is For

✅ **Use this if you:**
- Code with AI assistants (Copilot, Claude, Cursor) and need guardrails
- Have architectural rules that AI keeps violating
- Work in multi-repo systems where one broken service cascades
- Want logic verification, not just "code exists" verification
- Need audit trails for compliance or team accountability

❌ **Skip this if you:**
- Write throwaway scripts with no architecture constraints
- Trust AI output 100% without verification
- Work solo on prototypes where "anything goes"

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

# Copilot Sentinel

**AI-assisted development with architectural guardrails.**

Stop architectural drift before it ships. A discipline-enforcing CLI that makes AI coding assistants respect your architecture, verify implementations, and track cross-repo dependencies.

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/Blink-deploy-in-a-blink/copilot-sentinel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

You use GitHub Copilot, Claude, or Cursor. The code looks great. Then:

- **Architectural violations** slip through (added HTTP server when you explicitly banned it)
- **Logic bugs** hide in "implemented" features (security check returns true instead of false)
- **Cross-repo chaos** when Service A depends on Service B's broken state
- **No verification** that AI actually implemented what you asked for

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

**Output:**
```
✅ Phase 1: Remove HTTP Server (3/3 steps complete)
⏳ Phase 2: Add Polling Mechanism (1/3 steps complete)
   → Next: Implement job poller with 30s interval
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

**Other tools:** "Here's some code that might work"  
**Copilot Sentinel:** "Here's verified code that respects your architecture"

| Feature | Copilot/Cursor/Claude | Copilot Sentinel |
|---------|----------------------|------------------|
| Architectural rules | Implicit (comments, docs) | Explicit (architecture.md) |
| Verification | Manual code review | Automatic constraint checking |
| Logic testing | Manual QA | LLM-verified feature checklists |
| Cross-repo dependencies | Hope it works | Blocks work if deps broken |
| Baseline tracking | None | Auto-scans repo, tracks violations |
| Implementation planning | Ad-hoc | Strategic phase/step breakdown |

**Philosophy:** Enforce discipline, not intelligence. AI is powerful but implicit. This tool makes constraints explicit.

---

## Who This Is For

✅ **You should use this if:**
- You use AI assistants (Copilot, Claude, Cursor) for coding
- You have explicit architecture rules that must not be violated
- You work in multi-repo environments with dependencies
- You want verification that features are actually implemented correctly
- You need audit trails of what changed and why

❌ **This is overkill if:**
- Solo throwaway scripts with no architecture
- Prototypes where "anything goes"
- You trust AI output without verification

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

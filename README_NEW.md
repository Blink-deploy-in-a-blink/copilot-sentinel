# Copilot Sentinel

**AI-assisted development with architectural guardrails.**

Enforces discipline when using GitHub Copilot, Claude Code, Cursor, or any AI coding assistant. Proposes steps, verifies changes, tracks deviations, and blocks cross-repo work until dependencies are ready.

## Quick Start

```bash
# Clone and install
git clone https://github.com/Blink-deploy-in-a-blink/copilot-sentinel.git
cd copilot-sentinel
pip install -r requirements.txt
pip install -e .

# In your project repo

wrapper init

# Edit these files (ONE TIME):
#   .wrapper/architecture.md  - Your target architecture
#   .wrapper/repo.yaml        - Repository boundaries

# Set API key
export DEEPSEEK_API_KEY="your-key"  # Linux/Mac
$env:DEEPSEEK_API_KEY="your-key"    # Windows

# First step (always baseline verification)
wrapper propose    # → generates step.yaml
wrapper compile    # → generates copilot_prompt.txt

# Give copilot_prompt.txt to AI, paste response in copilot_output.txt
wrapper verify     # → auto-captures baseline, passes
wrapper accept     # → step complete

# Repeat for each step
wrapper propose    # → next step (fixes deviations)
wrapper compile
# ... work with AI ...
wrapper verify
wrapper accept
```

---

## What It Does

1. **Baseline Capture** - Scans repo, generates deviation list (automatic)
2. **Step Proposals** - LLM proposes next step based on deviations + architecture
3. **Strict Verification** - Checks git diff + AI output against constraints
4. **Cross-Repo Blocking** - Prevents work if dependencies have unresolved issues
5. **Auto-Resolution** - Tracks which steps fix which deviations

---

## Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `wrapper init` | Create `.wrapper/` templates | Once per repo |
| `wrapper propose` | Generate next step | After each accept |
| `wrapper compile` | Create AI prompt | After propose/editing step |
| `wrapper verify` | Check changes against rules | After AI makes changes |
| `wrapper accept` | Record completed step | After verify passes |
| `wrapper sync-external` | Sync dependency repo state | Before propose (multi-repo) |
| `wrapper snapshot` | Manual baseline capture | Rarely (auto-done on first verify) |
| `wrapper diff-baseline` | Show drift from baseline | Debugging |

---

## Key Features

### 🎯 Automatic Baseline
First `wrapper verify`:
- Scans entire repo (files, structure)
- LLM compares architecture vs reality
- Auto-generates `deviations.yaml` with mismatches
- **Always passes** (just documenting current state)

### 🔄 Step-by-Step Deviation Fixing
```
Baseline → 13 deviations found
  ↓
Step 1: Remove HTTP server (fixes 2 deviations)
  ↓
Step 2: Restructure directories (fixes 4 deviations)
  ↓
Step 3: Add polling mechanism (fixes 1 deviation)
  ↓
... continue until all resolved
```

###  Cross-Repo Dependency Blocking
```bash
# In Agent repo
wrapper sync-external --from ../ui

wrapper propose
#  BLOCKED: UI has unresolved deviation "no-polling-support"
# → Proposes: "blocked-waiting-for-ui" step
# → Output: "Fix UI repo first!"

# After UI fixes deviation:
wrapper sync-external --from ../ui
wrapper propose
# ✅ Can proceed (blocker resolved)
```

###  Smart Deviation Resolution
```bash
wrapper accept
# → LLM checks: "Does this step resolve any deviations?"
# → Auto-updates deviations.yaml
# → Unblocks dependent repos on next sync
```

---

## File Structure

```
your-repo/
├── .wrapper/
│   ├── architecture.md          # [MANUAL] Target architecture
│   ├── repo.yaml                # [MANUAL] Boundaries & dependencies
│   ├── config.yaml              # [MANUAL] API key
│   │
│   ├── step.yaml                # [Auto] Current step (review before compile)
│   ├── copilot_prompt.txt       # [Auto] For AI assistant
│   ├── copilot_output.txt       # [You] Paste AI response here
│   │
│   ├── state.json               # [Auto] All completed steps
│   ├── baseline_snapshot.json   # [Auto] Repo structure at start
│   ├── deviations.yaml          # [Auto] Architecture mismatches
│   └── external_state.json      # [Auto] Dependency repo states
```

---

## Configuration

**API Key (choose one):**
```bash
# Environment variable (recommended)
export DEEPSEEK_API_KEY="your-key"

# Or in .wrapper/config.yaml
llm_provider: deepseek
deepseek_api_key: your-key
```

**Supported LLMs:** DeepSeek (default), OpenAI, Anthropic

**Repository Configuration (`.wrapper/repo.yaml`):**
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

---

## Multi-Repo Workflow

```bash
# Setup each repo
cd ui && wrapper init && wrapper propose && wrapper verify && wrapper accept
cd agent && wrapper init && wrapper propose && wrapper verify && wrapper accept

# Before working on agent
cd agent
wrapper sync-external --from ../ui --from ../llm
# → Checks ui & llm for blockers

wrapper propose
# → If ui has blocker: proposes "blocked" step
# → If clean: proposes actual work

# After ui fixes its blocker
cd agent
wrapper sync-external --from ../ui
wrapper propose
# → Now unblocked, can proceed
```

---

## Troubleshooting

**"No LLM API key configured"**
- Set `DEEPSEEK_API_KEY` environment variable or add to `.wrapper/config.yaml`

**"Not in a git repository"**
- Run `git init` first

**"Verification step requires Copilot output"**
- Paste AI's analysis into `.wrapper/copilot_output.txt`

**"ACCEPT BLOCKED"**
- Run `wrapper verify` and get PASS first

**Check drift from baseline:**
```bash
wrapper diff-baseline
```

---

## Philosophy

**Enforce discipline, not intelligence.**

- AI is powerful but implicit
- This tool makes constraints explicit
- Captures reality, not just ideals  
- Verifies changes against architecture AND baseline
- Blocks cross-repo work until dependencies ready
- Human reviews and approves everything

---

## Version

**Current:** v1.0.0 (Baseline Snapshot & Cross-Repo Blocking)

See [CHANGELOG.md](CHANGELOG.md) for version history.

---

## License

MIT

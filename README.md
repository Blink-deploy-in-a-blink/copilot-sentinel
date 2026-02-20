# Copilot Sentinel

**Turn chaotic AI-assisted coding into an auditable, step-by-step workflow with guardrails.**

Copilot Sentinel wraps AI-assisted development in a controlled workflow.
It uses git to enforce file boundaries and LLMs to review architectural and logical intent.
Track what changed, enforce which files can be modified, and maintain an audit trail of every step.

[![Version](https://img.shields.io/badge/version-1.2.0-blue.svg)](https://github.com/Blink-deploy-in-a-blink/copilot-sentinel)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## The Problem

AI coding assistants are powerful but chaotic:

- **No audit trail** - Can't prove what changed or why
- **Random file edits** - AI modifies unexpected files
- **Architecture drift** - AI doesn't follow your design rules
- **Cross-repo chaos** - Changes break dependencies

**Result:** Fast iteration with invisible technical debt.

---

## What Copilot Sentinel Does

✅ **File allowlist enforcement** - Only approved files can be modified (git diff verification)  
✅ **Step-by-step workflow** - Propose → Compile → Verify → Accept  
✅ **Audit trail** - Every change recorded with timestamp  
✅ **Architecture compliance** - LLM checks code against your rules  
✅ **Deviation tracking** - Find and fix violations systematically  
✅ **Multi-repo coordination** - Block work if dependencies are broken  
✅ **Feature verification** - Test if implementations match requirements  
✅ **Planning support** - Break large refactors into phases  

---

## Quick Example

```bash
# 1. Initialize (choose one)
$ wrapper init --guided          # Interactive AI-assisted setup (recommended)
# OR
$ wrapper init                   # Manual setup (edit templates yourself)

# Guided mode asks 7 questions and generates architecture.md + repo.yaml
# Manual mode creates templates you fill in yourself

# 2. Capture baseline (first run)
$ wrapper propose
# → Generates "verify-baseline" step

$ wrapper verify
# ✅ PASS - Baseline captured
# Found 13 deviations from architecture
# Saved to .wrapper/deviations.yaml

$ wrapper accept

# 3. Fix first deviation
$ wrapper propose
# → Proposes "remove-flask-server" step

$ wrapper compile
# → Generates copilot_prompt.txt

# Give prompt to AI, make changes, paste response

$ wrapper verify
# ✅ PASS - All constraints satisfied

$ wrapper accept
# ✅ Deviation resolved

# Repeat until clean
```

---

## Installation

### Requirements

- Python 3.8+
- Git repository
- LLM API key (DeepSeek, OpenAI, or Anthropic)

### Install from Source

```bash
git clone https://github.com/Blink-deploy-in-a-blink/copilot-sentinel.git
cd copilot-sentinel
pip install .
```

### Verify Installation

```bash
wrapper --version
# Should output: wrapper v1.3.0
```

### Configure LLM API Key

**Option 1: Environment Variable (Recommended)**

```bash
# DeepSeek (default, recommended)
export DEEPSEEK_API_KEY="sk-..."

# Or OpenAI
export OPENAI_API_KEY="sk-..."

# Or Anthropic
export ANTHROPIC_API_KEY="sk-..."
```

**Windows PowerShell:**
```powershell
$env:DEEPSEEK_API_KEY="sk-..."
```

**Option 2: Config File**

After running `wrapper init`, edit `.wrapper/config.yaml`:
```yaml
llm_provider: deepseek
deepseek_api_key: sk-...
```

---

## Basic Workflow

### 1. Initialize Your Project

```bash
cd your-project
wrapper init
```

Edit `.wrapper/architecture.md` with your target architecture:

```markdown
# My Architecture

## Constraints
- NO HTTP endpoints
- NO direct database access
- All jobs timeout after 5 minutes
```

### 2. Run the Workflow Loop

```bash
# Get next step
wrapper propose

# Generate AI prompt
wrapper compile

# Work with AI
# 1. Copy .wrapper/copilot_prompt.txt
# 2. Paste into AI assistant (Copilot/Claude/ChatGPT)
# 3. Make suggested changes
# 4. Paste AI response into .wrapper/copilot_output.txt (for verification steps)

# Verify changes
wrapper verify

# Accept if passed
wrapper accept
```

Repeat until all deviations are fixed.

---

## Key Commands

| Command | What It Does |
|---------|--------------|
| `wrapper init` | Initialize `.wrapper/` directory with templates |
| `wrapper init --guided` | Interactive AI-assisted setup (7 questions) |
| `wrapper propose` | Generate next step (from plan or deviations) |
| `wrapper compile` | Create AI prompt from current step |
| `wrapper verify` | Check git diff against step constraints |
| `wrapper accept` | Record completed step in audit log |
| `wrapper plan init` | Create multi-phase implementation plan |
| `wrapper test` | Verify completed features work correctly |
| `wrapper sync-external` | Sync dependency repo states (multi-repo) |

**→ See [Commands Reference](docs/commands.md) for complete details**


---

## Who Should Use This

### ✅ Good Fit

- **Teams refactoring with AI** - Need audit trail and architecture enforcement
- **Solo devs using AI heavily** - Want discipline and structure
- **Multi-repo projects** - Need to track cross-repo dependencies
- **Legacy migrations** - Step-by-step progress tracking

### ❌ Not a Good Fit

- **Formal verification needed** - Uses LLMs, not proofs
- **CI/CD replacement** - This is a local workflow tool
- **Greenfield projects** - Overhead not worth it for new code
- **Static analysis** - Use ESLint, mypy, etc. for that

---

## How It Works

### Hard Guarantees (Enforced by Code)

- ✅ **File allowlist** - Git diff checked against `allowed_files`
- ✅ **Accept blocking** - Cannot accept without passing verify
- ✅ **Audit log** - Append-only `state.json`

### Soft Guarantees (Enforced by LLM)

- ⚠️ **Architecture compliance** - LLM compares code to `architecture.md`
- ⚠️ **Logic verification** - LLM checks feature implementation
- ⚠️ **Deviation detection** - LLM finds violations

**→ See [Core Concepts](docs/core-concepts.md) for detailed explanations**

---

## Documentation

### Getting Started
- **[Getting Started Guide](docs/getting-started.md)** - Installation and first workflow

### Core Documentation
- **[Core Concepts](docs/core-concepts.md)** - Understand files and guarantees
- **[How It Works](docs/how-it-works.md)** - Internal workflows and processes
- **[Commands Reference](docs/commands.md)** - Complete command documentation

### Advanced Topics
- **[Examples](docs/examples.md)** - Real-world usage scenarios
- **[Multi-Repo Setup](docs/multi-repo.md)** - Cross-repository management
- **[Testing Guide](docs/testing.md)** - Feature verification and testing
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

---

## Version

**Current: v1.2.0**

- [CHANGELOG.md](CHANGELOG.md) - Version history
- [VERSIONING.md](VERSIONING.md) - Release process

---

## License

MIT - See [LICENSE](LICENSE)

---

## Quick Links

- **Documentation:** [docs/](docs/)
- **GitHub:** [Blink-deploy-in-a-blink/copilot-sentinel](https://github.com/Blink-deploy-in-a-blink/copilot-sentinel)
- **Issues:** [Report a bug](https://github.com/Blink-deploy-in-a-blink/copilot-sentinel/issues)

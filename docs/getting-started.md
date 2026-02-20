# Getting Started

A hands-on guide to installing and running your first Copilot Sentinel workflow.

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Blink-deploy-in-a-blink/copilot-sentinel.git
cd copilot-sentinel
```

### 2. Install the Package

```bash
pip install -e .
```

### 3. Verify Installation

```bash
wrapper --version
```

**Expected output:**
```
Copilot Sentinel v1.2.0
```

---

## LLM Configuration

Copilot Sentinel requires an LLM API key for semantic analysis.

### Option 1: Environment Variables (Recommended)

**DeepSeek (default):**
```bash
# Linux/Mac
export DEEPSEEK_API_KEY="sk-..."

# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-..."

# Windows Command Prompt
set DEEPSEEK_API_KEY=sk-...
```

**OpenAI:**
```bash
export OPENAI_API_KEY="sk-..."
```

**Anthropic:**
```bash
export ANTHROPIC_API_KEY="sk-..."
```

### Option 2: Config File

Create `.wrapper/config.yaml` in your project:

```yaml
llm_provider: deepseek  # or 'openai' or 'anthropic'
deepseek_api_key: sk-...
```

---

## Your First Workflow

### Prerequisites

Your project must be a git repository:

```bash
cd your-project
git init
git add .
git commit -m "Initial commit"
```

---

## Step 1: Initialize Copilot Sentinel

**Option A: Guided Setup (Recommended for new users)**

```bash
wrapper init --guided
```

**What happens:**
- Asks 7 interactive questions about your project
- AI formats your answers into proper documentation
- Creates architecture.md and repo.yaml automatically

**Requirements:**
- Must have API key set (DEEPSEEK_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY)

**Example interaction:**
```
🤖 Guided Repository Setup
============================================================

📋 ARCHITECTURE QUESTIONS

1/7: What is the PRIMARY PURPOSE of this repository?
    > A CLI tool for managing Docker containers with better UX

2/7: What are the MAIN COMPONENTS or modules?
    > CLI interface, Docker API wrapper, Configuration manager

...

✅ Created architecture.md
✅ Created repo.yaml
✅ Created config.yaml
```

---

**Option B: Manual Setup**

```bash
wrapper init
```

**What happens:**
- Creates `.wrapper/` directory
- Generates template files

**Expected output:**
```
Initializing .wrapper/
  Created architecture.md
  Created repo.yaml
  Created config.yaml

Next steps:
  1. Edit .wrapper/architecture.md with your target architecture
  2. Edit .wrapper/repo.yaml with repo constraints
  3. Set DEEPSEEK_API_KEY environment variable
  4. Run: wrapper propose
```

**Files created:**
```
your-project/
├── .wrapper/
│   ├── architecture.md
│   ├── repo.yaml
│   └── config.yaml
```

---

## Step 2: Define Your Architecture

**If you used `--guided`:** Your architecture.md is already filled in! Review and refine it.

**If you used manual init:** Edit `.wrapper/architecture.md` to describe your target architecture.

**Example:**

```markdown
# My Application Architecture

## Constraints
- NO HTTP endpoints (security requirement)
- NO direct database access (use API layer)
- All jobs MUST timeout after 5 minutes

## Components
- JobPoller: Checks queue every 30 seconds
- Executor: Runs jobs in isolated containers
- API Client: Communicates with backend API
```

**This is natural language** - write it however makes sense for your project.

---

## Step 3: Define Repo Boundaries

Edit `.wrapper/repo.yaml` to set boundaries.

**Example:**

```yaml
repo_name: agent
repo_role: Job execution engine

must_not:
  - expose HTTP APIs
  - contain UI logic
  - access databases directly

depends_on:
  - repo: ui
    via: REST API
  - repo: auth
    via: token validation
```

---

## Step 4: Propose First Step

```bash
wrapper propose
```

**What happens:**
- First run generates a "verify-baseline" step
- This captures your current state

**Expected output:**
```
✅ Generated step: verify-baseline
Created: .wrapper/step.yaml
```

**Generated `.wrapper/step.yaml`:**
```yaml
step_id: verify-baseline
type: verification
goal: Capture baseline state and identify deviations from architecture
allowed_files: []
features:
  - Scan repository structure
  - Compare against architecture.md
  - Generate deviations list
```

---

## Step 5: Compile AI Prompt

```bash
wrapper compile
```

**What happens:**
- Generates prompts from `step.yaml`
- Creates files for AI interaction

**Expected output:**
```
✅ Generated prompts
Created:
  - copilot_prompt.txt (give this to AI)
  - copilot_output.txt (paste AI response here)
  - verify.md (checklist)
```

---

## Step 6: Work with AI

### 6a. Give Prompt to AI

Open `.wrapper/copilot_prompt.txt` and copy the content.

Paste it into your AI assistant:
- GitHub Copilot Chat
- Claude
- ChatGPT
- Cursor

### 6b. Get AI Response

The AI will analyze your codebase and provide a response.

**Example AI response:**
```
I've analyzed the repository against your architecture.

Current state:
- 47 Python files
- 12 directories
- Flask server found in src/main.py

Deviations from architecture:
1. HTTP server present (Flask app violates no-HTTP constraint)
2. Direct database access in models.py (violates API layer requirement)
3. No timeout mechanism found for jobs

Recommendation: Start by removing Flask server, then address DB access.
```

### 6c. Paste Response

Copy the AI's entire response and paste it into `.wrapper/copilot_output.txt`.

---

## Step 7: Verify

```bash
wrapper verify
```

**What happens:**
- First verify always passes (baseline capture)
- Scans your repository structure
- LLM reads your code and architecture.md
- Generates `.wrapper/deviations.yaml` with violations

**Expected output:**
```
✅ PASS - Baseline captured

Repository snapshot saved:
  - 47 files scanned
  - 12 directories
  - 3 file types

Deviations found: 13

High severity:
  - http-server-present (Flask server in main.py)
  - direct-db-access (SQLAlchemy in models.py)

Medium severity:
  - missing-timeout-handler (No job timeout mechanism)
  - ...

Created:
  - baseline_snapshot.json
  - deviations.yaml

Next: Run 'wrapper accept' to proceed
```

---

## Step 8: Accept Baseline

```bash
wrapper accept
```

**What happens:**
- Records the step in audit log
- You can now start fixing deviations

**Expected output:**
```
✅ Step accepted: verify-baseline

Updated:
  - state.json (step recorded)

Next: Run 'wrapper propose' to get first fix step
```

---

## Your First Fix Step

Now let's fix one of the deviations.

### Step 9: Propose Next Step

```bash
wrapper propose
```

**What happens:**
- LLM reads `deviations.yaml`
- Proposes a fix for the first high-severity deviation

**Expected output:**
```
✅ Generated step: remove-flask-server
Created: .wrapper/step.yaml
```

**Generated `.wrapper/step.yaml`:**
```yaml
step_id: remove-flask-server
type: implementation
goal: Remove Flask HTTP server code, violates no-http-server constraint
allowed_files:
  - src/main.py
  - requirements.txt
forbidden:
  - "Add new HTTP endpoints"
  - "Create new Flask routes"
features:
  - Remove Flask app initialization
  - Remove route handlers (@app.route)
  - Remove Flask from requirements.txt
success_criteria:
  - No Flask imports remain
  - No HTTP server starts on any port
```

---

### Step 10: Compile Prompt

```bash
wrapper compile
```

**Expected output:**
```
✅ Generated prompts
Created: copilot_prompt.txt
```

**`.wrapper/copilot_prompt.txt` contains:**
```
You are implementing this step:

Title: Remove Flask HTTP server
Goal: Remove Flask HTTP server code, violates no-http-server constraint

Allowed files (you may ONLY modify these):
- src/main.py
- requirements.txt

Forbidden actions:
- Add new HTTP endpoints
- Create new Flask routes

Features to implement:
- Remove Flask app initialization
- Remove route handlers (@app.route)
- Remove Flask from requirements.txt

Success criteria:
- No Flask imports remain
- No HTTP server starts on any port

Instructions:
1. Analyze the current code
2. Remove all Flask-related code
3. Update requirements.txt
4. Ensure no HTTP functionality remains
```

---

### Step 11: Give to AI and Make Changes

1. Copy `.wrapper/copilot_prompt.txt` content
2. Paste into AI assistant
3. AI will suggest changes
4. **Make the changes manually** in your code
5. Paste AI's response into `.wrapper/copilot_output.txt` (optional for implementation steps)

**Example changes:**

Before (`src/main.py`):
```python
from flask import Flask, request

app = Flask(__name__)

@app.route('/jobs', methods=['GET'])
def get_jobs():
    return {"jobs": [...]}

if __name__ == '__main__':
    app.run(port=5000)
```

After (`src/main.py`):
```python
# Flask removed - will implement polling in next step

def main():
    # Polling mechanism to be added
    pass

if __name__ == '__main__':
    main()
```

---

### Step 12: Verify Changes

```bash
wrapper verify
```

**What happens:**
- Checks git diff against `allowed_files`
- Verifies only `src/main.py` and `requirements.txt` were modified
- Checks for forbidden patterns
- LLM analyzes if features were implemented

**Expected output:**
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
  ✓ requirements.txt updated

Features implemented:
  ✓ Remove Flask app initialization
  ✓ Remove route handlers
  ✓ Remove Flask from requirements.txt

Result: PASS
Status saved to state.json
```

---

### Step 13: Accept the Fix

```bash
wrapper accept
```

**What happens:**
- Records step in audit log
- Automatically updates `deviations.yaml`
- Marks resolved deviations

**Expected output:**
```
✅ Step accepted: remove-flask-server

Updated:
  - state.json (step recorded)
  - deviations.yaml (2 deviations marked resolved)

Resolved deviations:
  - http-server-present
  - http-route-handlers

Remaining deviations: 11

Next: Run 'wrapper propose' for next fix step
```

---

## Continue the Workflow

Repeat the cycle until all deviations are fixed:

```bash
wrapper propose    # Get next fix step
wrapper compile    # Generate AI prompt
# Work with AI, make changes
wrapper verify     # Check changes
wrapper accept     # Record progress
```

---

## Check Your Progress

View audit log:

```bash
cat .wrapper/state.json
```

View remaining deviations:

```bash
cat .wrapper/deviations.yaml
```

View baseline snapshot:

```bash
cat .wrapper/baseline_snapshot.json
```

---

## What You've Learned

✅ **Initialize**: `wrapper init` creates `.wrapper/` directory
✅ **Define architecture**: Edit `architecture.md` with your rules
✅ **Baseline capture**: First `verify` documents current state
✅ **Fix deviations**: Propose → Compile → Work with AI → Verify → Accept
✅ **File allowlist**: Only `allowed_files` can be modified
✅ **Audit trail**: Every step recorded in `state.json`

---

## Next Steps

- **[Core Concepts](core-concepts.md)** - Understand how files and guarantees work
- **[Commands Reference](commands.md)** - Learn all available commands
- **[How It Works](how-it-works.md)** - Understand the internal workflows
- **[Examples](examples.md)** - See real-world scenarios
- **[Multi-Repo Setup](multi-repo.md)** - Work with multiple repositories
- **[Testing](testing.md)** - Test your implementations
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions

# Roadmap

This document outlines the major next steps for Copilot Sentinel. Each item explains **what** the improvement is, **why** it matters, and **how** it will help users and contributors.

---

## 1. Test Suite

### What
Add a comprehensive automated test suite covering the CLI commands (`init`, `propose`, `compile`, `verify`, `accept`, `plan`, `test`, `sync-external`), core logic (deviation detection, file-allowlist enforcement, baseline snapshots), and edge cases (missing config, invalid YAML, empty repos).

### Why This Is an Improvement
- **Confidence in changes** — Contributors can refactor or add features without fear of breaking existing functionality.
- **Regression prevention** — Bugs that are fixed stay fixed; tests catch regressions before they ship.
- **Faster code review** — Reviewers can trust that passing tests mean the change works, reducing manual verification effort.
- **Onboarding** — New contributors can read tests to understand expected behavior, serving as living documentation.

### How It Helps
Without tests, every pull request is a leap of faith. A test suite turns Copilot Sentinel from a "works on my machine" project into a production-grade tool that teams can depend on.

---

## 2. CI/CD Pipeline

### What
Set up GitHub Actions workflows to automatically run linting (e.g., `flake8`, `ruff`), the test suite, and packaging checks on every push and pull request. Include matrix testing across Python 3.9 – 3.13.

### Why This Is an Improvement
- **Catch breakage early** — Failures surface in the PR, not after merge.
- **Enforce quality gates** — Code that doesn't pass lint or tests cannot be merged.
- **Cross-version safety** — Matrix testing ensures Copilot Sentinel works on all supported Python versions.
- **Contributor experience** — Green CI badges give contributors immediate feedback on their changes.

### How It Helps
CI/CD is the backbone of any collaborative open-source project. It removes the burden of "did you run the tests?" from maintainers and makes the contribution process self-service.

---

## 3. PyPI Publishing

### What
Publish Copilot Sentinel to the Python Package Index (PyPI) so users can install it with a single command: `pip install copilot-sentinel`. Automate releases via GitHub Actions on tagged commits.

### Why This Is an Improvement
- **Frictionless installation** — Users no longer need to clone the repo and `pip install .` manually.
- **Version management** — PyPI enforces unique version numbers and provides a clear release history.
- **Discoverability** — Being on PyPI makes the project visible to the broader Python ecosystem.
- **Dependency management** — Downstream projects can pin `copilot-sentinel>=1.3.0` in their `requirements.txt`.

### How It Helps
Lowering the installation barrier is the single biggest lever for adoption. Every extra step (clone, cd, pip install .) loses a percentage of potential users. `pip install copilot-sentinel` is the expected standard.

---

## 4. Plugin System

### What
Introduce a plugin architecture that lets users extend Copilot Sentinel with custom verifiers, step generators, and LLM providers without modifying core code. Plugins would be discovered via Python entry points (e.g., `wrapper.plugins`).

### Why This Is an Improvement
- **Extensibility without fragmentation** — Users can add custom rules (e.g., "all SQL must go through the ORM") without forking.
- **Community growth** — Third-party plugins encourage an ecosystem around Copilot Sentinel.
- **Separation of concerns** — Core stays lean; specialized logic lives in plugins.
- **Enterprise adoption** — Teams can write internal plugins for company-specific architecture rules.

### How It Helps
Every team has unique constraints. A plugin system lets Copilot Sentinel handle the universal workflow (propose → compile → verify → accept) while delegating domain-specific checks to plugins. This turns the tool from a fixed product into a platform.

---

## 5. IDE Integration

### What
Build extensions for popular IDEs (VS Code, JetBrains) that surface Copilot Sentinel's workflow directly in the editor: inline deviation markers, one-click verify/accept, step status in the sidebar, and architecture violation highlights.

### Why This Is an Improvement
- **Reduced context switching** — Developers stay in their editor instead of switching to a terminal.
- **Real-time feedback** — Deviation warnings appear as you type, not after running a command.
- **Lower learning curve** — GUI buttons and panels are more approachable than CLI commands for some users.
- **Wider adoption** — IDE integrations make the tool accessible to developers who rarely use the terminal.

### How It Helps
The terminal CLI is powerful but adds friction. IDE integration meets developers where they already work, dramatically increasing the chance that Copilot Sentinel becomes part of a team's daily workflow rather than an occasional audit tool.

---

## 6. Undo / Rollback

### What
Add `wrapper undo` and `wrapper rollback --to <step-id>` commands that revert accepted steps, restore previous `state.json` snapshots, and optionally reset the git working tree to the pre-step state.

### Why This Is an Improvement
- **Safety net** — Mistakes happen; being able to undo reduces the cost of errors.
- **Experimentation** — Developers can try a refactoring direction, and roll back if it doesn't work.
- **Audit trail preservation** — Rolled-back steps are recorded (not deleted), maintaining full history.
- **Trust** — Users are more willing to adopt a workflow tool when they know they can reverse course.

### How It Helps
Currently, `wrapper accept` is a one-way door. If a step is accepted with a subtle bug, the only recourse is manual git surgery. Undo/rollback makes the workflow forgiving and encourages experimentation.

---

## 7. Dashboard

### What
Build a local web dashboard (e.g., using Flask or Streamlit) that visualizes project state: deviation trends over time, step completion progress, architecture compliance scores, audit log timeline, and multi-repo dependency graphs.

### Why This Is an Improvement
- **Visibility** — A dashboard gives a bird's-eye view of project health that CLI output cannot.
- **Team communication** — Managers and leads can check progress without running CLI commands.
- **Trend tracking** — Charts showing deviation count over time reveal whether the codebase is getting healthier.
- **Multi-repo overview** — Dependency graphs make cross-repo relationships immediately understandable.

### How It Helps
CLI tools are great for execution but poor for reporting. A dashboard turns Copilot Sentinel's data (state.json, deviations.yaml, implementation plans) into actionable insights that justify continued investment in architectural discipline.

---

## 8. LLM Cost Tracking

### What
Track and report LLM API usage per command: token counts (prompt + completion), estimated cost in USD, cumulative spend per session/project, and cost-per-step breakdowns. Optionally set budget limits that warn or block when exceeded.

### Why This Is an Improvement
- **Cost awareness** — LLM calls are not free; developers should know what each `verify` or `propose` costs.
- **Budget control** — Teams can set spending limits to prevent surprise bills.
- **Provider comparison** — Cost-per-step data helps teams choose the most cost-effective LLM provider.
- **Optimization** — Identifying expensive steps helps optimize prompts to reduce token usage.

### How It Helps
LLM costs are opaque by default. Without tracking, teams discover their bill at the end of the month. Cost tracking makes spending visible, controllable, and optimizable — turning Copilot Sentinel from a potential cost liability into a cost-aware tool.

---

## 9. Offline Mode

### What
Add an `--offline` flag (or auto-detect no network) that skips LLM-dependent steps (architecture review, logic verification) while preserving hard-guarantee features (file-allowlist enforcement, git diff checking, audit logging).

### Why This Is an Improvement
- **Reliability** — Works on planes, in secure environments, or when API keys are unavailable.
- **Speed** — Skipping LLM calls makes `verify` and `propose` near-instant.
- **Security** — Some teams cannot send code to external APIs; offline mode respects that constraint.
- **Graceful degradation** — Instead of failing completely without an API key, the tool does what it can.

### How It Helps
Copilot Sentinel's hard guarantees (file allowlist, accept blocking, audit log) are valuable even without LLM assistance. Offline mode ensures the tool is always useful, regardless of network conditions, making it viable in air-gapped enterprise environments and day-to-day commutes alike.

---

## Priority and Sequencing

| Priority | Item | Rationale |
|----------|------|-----------|
| 🔴 High | Test suite | Foundation for all other improvements |
| 🔴 High | CI/CD pipeline | Depends on test suite; enables safe collaboration |
| 🟡 Medium | PyPI publishing | Depends on CI/CD; unlocks easy installation |
| 🟡 Medium | Offline mode | Low complexity, high value for enterprise users |
| 🟡 Medium | LLM cost tracking | Low complexity, high visibility |
| 🟡 Medium | Undo/rollback | Improves user confidence and safety |
| 🔵 Future | Plugin system | Requires stable API surface first |
| 🔵 Future | Dashboard | Nice-to-have; depends on stable data model |
| 🔵 Future | IDE integration | Highest effort; depends on stable CLI interface |

> **Recommended order:** Test suite → CI/CD → PyPI → Offline mode → LLM cost tracking → Undo/rollback → Plugin system → Dashboard → IDE integration.

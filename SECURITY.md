# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.3.x   | :white_check_mark: |
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Copilot Sentinel, please report it responsibly.

**How to report:**
- Open a [GitHub Issue](https://github.com/Blink-deploy-in-a-blink/copilot-sentinel/issues) with the label `security`
- Or email the maintainers directly (see repository contact info)

**What to expect:**
- Acknowledgment within 48 hours
- Status update within 7 days
- Fix or mitigation plan within 30 days for confirmed vulnerabilities

**Scope:**
- Copilot Sentinel is a local CLI tool — it does not run a server or handle network traffic directly
- LLM API keys are user-configured; secure storage of keys is the user's responsibility
- The `.wrapper/` directory may contain sensitive project context — it is gitignored by default

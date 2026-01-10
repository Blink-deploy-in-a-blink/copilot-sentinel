"""
wrapper verify - Verify git diff against step constraints.
"""

import re
from typing import List, Tuple

from wrapper.core.files import (
    load_architecture,
    load_repo_yaml,
    load_state,
    load_step_yaml,
    save_diff,
    save_repair_prompt,
    save_state,
)
from wrapper.core.paths import get_file_path, STEP_YAML_FILE
from wrapper.core.git import get_diff, get_changed_files, get_new_directories, is_git_repo
from wrapper.core.llm import get_llm_client


class VerificationResult:
    """Result of verification checks."""
    
    def __init__(self):
        self.passed = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.llm_analysis: str = ""
    
    def add_error(self, msg: str):
        self.passed = False
        self.errors.append(msg)
    
    def add_warning(self, msg: str):
        self.warnings.append(msg)


def check_allowed_files(
    changed: set,
    allowed: List[str],
    result: VerificationResult
) -> None:
    """Check that only allowed files were modified."""
    
    # If allowed is empty, no files should be changed
    if not allowed:
        if changed:
            result.add_error(
                f"No files should be modified, but found changes in: {', '.join(sorted(changed))}"
            )
        return
    
    # Convert allowed to set for comparison
    allowed_set = set(allowed)
    
    # Check for disallowed files
    disallowed = changed - allowed_set
    if disallowed:
        result.add_error(
            f"Modified files not in allowed list: {', '.join(sorted(disallowed))}"
        )


def check_new_directories(
    new_dirs: set,
    architecture: str,
    result: VerificationResult
) -> None:
    """Check for unexpected new directories."""
    
    if new_dirs:
        # Check if any are in known deviations
        # For now, flag all new directories as warnings
        result.add_warning(
            f"New directories created: {', '.join(sorted(new_dirs))}"
        )


def normalize_forbidden_item(item) -> str:
    """Convert forbidden item to string, handling both string and dict formats."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        # Handle format like {example: "description"}
        return str(list(item.values())[0]) if item else ""
    return str(item)


def check_forbidden_patterns(
    diff: str,
    forbidden: List,
    result: VerificationResult
) -> None:
    """Check for forbidden patterns in diff."""
    
    # Common patterns to check for
    pattern_keywords = {
        "ui": ["<div", "<button", "useState", "className=", "render("],
        "http": ["app.get(", "app.post(", "@Get(", "@Post(", "router.get", "express()"],
        "database": ["CREATE TABLE", "SELECT * FROM", "INSERT INTO", ".query(", "prisma."],
    }
    
    for item in forbidden:
        forbidden_item = normalize_forbidden_item(item)
        if not forbidden_item:
            continue
        forbidden_lower = forbidden_item.lower()
        
        # Check for keyword-based patterns
        for keyword, patterns in pattern_keywords.items():
            if keyword in forbidden_lower:
                for pattern in patterns:
                    if pattern.lower() in diff.lower():
                        result.add_error(
                            f"Forbidden pattern detected ({forbidden_item}): found '{pattern}' in diff"
                        )


def build_llm_verify_prompt(
    diff: str,
    step: dict,
    repo_yaml: dict,
    architecture: str,
    rule_check_results: VerificationResult
) -> str:
    """Build prompt for LLM verification analysis."""
    
    allowed = step.get("allowed_files", [])
    allowed_str = "\n".join(f"- {f}" for f in allowed) if allowed else "None (verification only)"
    
    forbidden = list(repo_yaml.get("must_not", []))
    forbidden.extend(step.get("forbidden", []))
    forbidden_str = "\n".join(f"- {normalize_forbidden_item(f)}" for f in forbidden) if forbidden else "None"
    
    success = step.get("success_criteria", [])
    success_str = "\n".join(f"- {s}" for s in success) if success else "None"
    
    rule_issues = ""
    if rule_check_results.errors:
        rule_issues = "RULE CHECK FAILURES:\n" + "\n".join(f"- {e}" for e in rule_check_results.errors)
    
    prompt = f'''Analyze this git diff against the step constraints.

STEP:
- ID: {step.get("step_id")}
- Type: {step.get("type")}
- Goal: {step.get("goal")}

CONSTRAINTS:
Allowed files:
{allowed_str}

Forbidden:
{forbidden_str}

Success criteria:
{success_str}

ARCHITECTURE CONTEXT (for reference):
{architecture[:2000]}...

{rule_issues}

GIT DIFF:
```
{diff[:8000]}
```

ANALYSIS REQUIRED:
1. Check if the changes align with the stated goal
2. Identify any architectural violations
3. Check if success criteria can be verified from the diff
4. Flag any concerning patterns

OUTPUT FORMAT:
```
VERDICT: PASS or FAIL

SUMMARY:
[1-2 sentence summary]

ISSUES:
- [list any issues found, or "None"]

SUCCESS CRITERIA STATUS:
- [criterion]: MET / NOT MET / UNCLEAR
[for each criterion]

RECOMMENDATIONS:
- [any recommendations, or "None"]
```

Analyze now:'''

    return prompt


def build_repair_prompt(
    diff: str,
    step: dict,
    repo_yaml: dict,
    errors: List[str],
    llm_analysis: str
) -> str:
    """Build repair prompt for failed verification."""
    
    lines = [
        "# REPAIR REQUIRED",
        "",
        f"Step `{step.get('step_id')}` failed verification.",
        "",
        "## Errors Found",
        ""
    ]
    
    for error in errors:
        lines.append(f"- {error}")
    
    lines.extend([
        "",
        "## Analysis",
        "",
        llm_analysis,
        "",
        "## Required Fixes",
        "",
        "Please fix the following issues before re-running `wrapper verify`:",
        ""
    ])
    
    # Generate specific fix instructions based on errors
    for error in errors:
        if "not in allowed list" in error:
            lines.append(f"- Revert changes to disallowed files")
        elif "Forbidden pattern" in error:
            lines.append(f"- Remove forbidden code patterns")
        elif "No files should be modified" in error:
            lines.append(f"- Revert all changes (this was a verification-only step)")
    
    lines.extend([
        "",
        "## Original Goal",
        "",
        step.get("goal", "Not specified"),
        "",
        "---",
        "",
        "After fixes, run: `wrapper verify`"
    ])
    
    return "\n".join(lines)


def cmd_verify(args) -> bool:
    """Verify git diff against step constraints."""
    
    # Check we're in a git repo
    if not is_git_repo():
        print("Error: Not in a git repository")
        return False
    
    # Load step
    step = load_step_yaml()
    if not step:
        print(f"Error: {STEP_YAML_FILE} not found. Run 'wrapper compile' first.")
        return False
    
    staged_only = getattr(args, 'staged', False)
    
    print(f"Verifying step: {step.get('step_id')}")
    print(f"Mode: {'staged changes only' if staged_only else 'all uncommitted changes'}")
    
    # Get diff
    diff = get_diff(staged_only)
    if not diff.strip():
        print("No changes detected.")
        if step.get("type") == "verification":
            print("PASS: Verification step - no changes expected.")
            # Record successful verification in state
            state = load_state()
            state["last_verify_status"] = "PASS"
            state["last_verify_step"] = step.get("step_id")
            state["last_verify_timestamp"] = __import__("datetime").datetime.now().isoformat()
            save_state(state)
            return True
        else:
            print("Warning: Implementation step but no changes found.")
            # Still mark as pass if no changes (maybe they're already done)
            state = load_state()
            state["last_verify_status"] = "PASS"
            state["last_verify_step"] = step.get("step_id")
            state["last_verify_timestamp"] = __import__("datetime").datetime.now().isoformat()
            save_state(state)
            return True
    
    # Save diff
    save_diff(diff)
    print(f"Diff saved to: {get_file_path('diff.txt')}")
    
    # Load configuration
    architecture = load_architecture() or ""
    repo_yaml = load_repo_yaml() or {}
    
    # Run rule-based checks
    result = VerificationResult()
    
    changed_files = get_changed_files(staged_only)
    print(f"Changed files: {len(changed_files)}")
    
    # Check allowed files
    allowed_files = step.get("allowed_files", [])
    check_allowed_files(changed_files, allowed_files, result)
    
    # Check new directories
    new_dirs = get_new_directories(staged_only)
    if new_dirs:
        check_new_directories(new_dirs, architecture, result)
    
    # Check forbidden patterns
    forbidden = list(repo_yaml.get("must_not", []))
    forbidden.extend(step.get("forbidden", []))
    check_forbidden_patterns(diff, forbidden, result)
    
    # Report rule check results
    if result.errors:
        print("\nRule check FAILURES:")
        for error in result.errors:
            print(f"  ✗ {error}")
    
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ! {warning}")
    
    # Run LLM analysis
    print("\nRunning LLM analysis...")
    try:
        llm = get_llm_client()
        prompt = build_llm_verify_prompt(diff, step, repo_yaml, architecture, result)
        llm_response = llm.generate(prompt, "verifier")
        result.llm_analysis = llm_response
        
        print("\nLLM Analysis:")
        print("-" * 40)
        print(llm_response)
        print("-" * 40)
        
        # Check if LLM verdict is FAIL
        if "VERDICT: FAIL" in llm_response.upper():
            result.add_error("LLM analysis found issues")
        
    except RuntimeError as e:
        print(f"Warning: LLM analysis failed: {e}")
        print("Proceeding with rule-based checks only.")
    
    # Final verdict
    print()
    if result.passed:
        print("=" * 40)
        print("VERIFICATION PASSED")
        print("=" * 40)
        
        # Record successful verification in state
        state = load_state()
        state["last_verify_status"] = "PASS"
        state["last_verify_step"] = step.get("step_id")
        state["last_verify_timestamp"] = __import__("datetime").datetime.now().isoformat()
        save_state(state)
        
        print("\nNext steps:")
        print("  1. git add .")
        print("  2. git commit -m 'step: " + step.get('step_id', 'unknown') + "'")
        print("  3. wrapper accept")
        return True
    else:
        print("=" * 40)
        print("VERIFICATION FAILED")
        print("=" * 40)
        
        # Record failed verification in state - blocks accept
        state = load_state()
        state["last_verify_status"] = "FAIL"
        state["last_verify_step"] = step.get("step_id")
        state["last_verify_timestamp"] = __import__("datetime").datetime.now().isoformat()
        save_state(state)
        
        # Generate repair prompt
        repair = build_repair_prompt(
            diff, step, repo_yaml, result.errors, result.llm_analysis
        )
        save_repair_prompt(repair)
        
        repair_path = get_file_path("repair_prompt.txt")
        print(f"\nRepair prompt written to: {repair_path}")
        print("Fix the issues and run 'wrapper verify' again.")
        print("\n** wrapper accept is BLOCKED until verify passes **")
        
        return False

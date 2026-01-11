"""
wrapper verify - Verify git diff against step constraints.
"""

import re
from typing import List, Tuple, Optional

from wrapper.core.files import (
    load_architecture,
    load_repo_yaml,
    load_state,
    load_step_yaml,
    load_copilot_output,
    load_baseline_snapshot,
    save_diff,
    save_repair_prompt,
    save_state,
    save_baseline_snapshot,
    save_deviations,
)
from wrapper.core.paths import get_file_path, STEP_YAML_FILE, COPILOT_OUTPUT_FILE, BASELINE_SNAPSHOT_FILE
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
    
    # Filter out .wrapper/ files - these are allowed to change
    changed_code = {f for f in changed if not f.startswith('.wrapper/')}
    
    # If allowed is empty, no CODE files should be changed (but .wrapper/ files are OK)
    if not allowed:
        if changed_code:
            result.add_error(
                f"No files should be modified, but found changes in: {', '.join(sorted(changed_code))}"
            )
        return
    
    # Convert allowed to set for comparison
    allowed_set = set(allowed)
    
    # Check for disallowed files (excluding .wrapper/ files)
    disallowed = changed_code - allowed_set
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
    rule_check_results: VerificationResult,
    copilot_output: Optional[str] = None
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
    
    # Build copilot output section
    copilot_section = ""
    if copilot_output:
        copilot_section = f"""
COPILOT/AI ASSISTANT OUTPUT:
```
{copilot_output[:6000]}
```
"""
    
    # Build diff section (may be empty for verification steps)
    diff_section = ""
    if diff.strip():
        diff_section = f"""
GIT DIFF:
```
{diff[:8000]}
```
"""
    else:
        diff_section = """
GIT DIFF:
(No code changes - this is a verification-only step)
"""

    prompt = f'''Analyze this step against the constraints.

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
{copilot_section}
{diff_section}

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


def is_first_verification(state: dict) -> bool:
    """Check if this is the first verification (no done_steps yet)."""
    return len(state.get("done_steps", [])) == 0


def get_copilot_output_content() -> Optional[str]:
    """
    Load and validate copilot_output.txt content.
    Returns None if file doesn't exist or only contains template.
    """
    content = load_copilot_output()
    if content is None:
        return None
    
    # Check if content has actual output (not just template)
    marker = "[PASTE AI OUTPUT BELOW THIS LINE]"
    if marker in content:
        # Get content after the marker
        parts = content.split(marker)
        if len(parts) > 1:
            actual_content = parts[1].strip()
            if actual_content:
                return actual_content
        return None
    
    # No marker found - return whole content if non-empty
    return content.strip() if content.strip() else None


def capture_baseline_if_first(state: dict, architecture: str) -> bool:
    """
    Capture baseline snapshot if this is first verification.
    Also generates deviations via LLM.
    
    Returns True if baseline was captured.
    """
    if not is_first_verification(state):
        return False
    
    # Check if baseline already exists
    existing = load_baseline_snapshot()
    if existing is not None:
        return False
    
    print()
    print("=" * 50)
    print("FIRST VERIFICATION - Capturing Baseline Snapshot")
    print("=" * 50)
    
    # Import here to avoid circular imports
    from wrapper.commands.snapshot import capture_baseline_snapshot
    
    snapshot = capture_baseline_snapshot()
    save_baseline_snapshot(snapshot)
    
    print(f"\nBaseline captured:")
    print(f"  Files: {snapshot['summary']['total_files']}")
    print(f"  Directories: {snapshot['summary']['total_directories']}")
    print(f"  Saved to: {get_file_path(BASELINE_SNAPSHOT_FILE)}")
    
    # Update state with baseline timestamp
    state["baseline_snapshot_timestamp"] = snapshot["timestamp"]
    state["baseline_verified"] = False  # Will be set True on accept
    save_state(state)
    
    # Generate deviations via LLM
    print("\nAnalyzing deviations from target architecture...")
    try:
        generate_deviations_via_llm(architecture, snapshot)
    except Exception as e:
        print(f"Warning: Could not generate deviations: {e}")
        # Create empty deviations file
        save_deviations({"deviations": []})
    
    print()
    return True


def generate_deviations_via_llm(architecture: str, snapshot: dict) -> None:
    """Generate deviations.yaml by comparing architecture to baseline."""
    
    try:
        llm = get_llm_client()
    except RuntimeError as e:
        print(f"  LLM not available: {e}")
        save_deviations({"deviations": []})
        return
    
    # Build summary of snapshot for prompt
    file_types_str = "\n".join(
        f"  {ext}: {count}" 
        for ext, count in list(snapshot["summary"]["file_types"].items())[:10]
    )
    
    dirs_str = "\n".join(f"  - {d}" for d in snapshot["directories"][:30])
    files_str = "\n".join(f"  - {f}" for f in snapshot["files"][:50])
    
    key_files = [k for k, v in snapshot["key_files_present"].items() if v]
    key_files_str = ", ".join(key_files) if key_files else "None"
    
    prompt = f'''Compare target architecture against actual repository state.
Generate deviations.yaml listing ALL significant mismatches.

TARGET ARCHITECTURE:
{architecture}

ACTUAL REPOSITORY STATE:
- Total files: {snapshot["summary"]["total_files"]}
- Total directories: {snapshot["summary"]["total_directories"]}
- Git branch: {snapshot["git_status"]["branch"]}
- Last commit: {snapshot["git_status"]["last_commit_hash"]}

File types:
{file_types_str}

Key files present: {key_files_str}

Directories:
{dirs_str}

Sample files:
{files_str}

Generate ONLY valid YAML (no markdown code fences) with this structure:

deviations:
  - id: descriptive-kebab-case-id
    description: Clear description of the deviation
    severity: high|medium|low
    category: missing-component|extra-code|structural|configuration
    auto_detected: true
    affected_files: []
    expected: What architecture specifies
    actual: What currently exists
    resolution_step: null

List ALL significant deviations. Be thorough but focus on architectural mismatches.
If repository matches architecture well, return: deviations: []
'''
    
    try:
        response = llm.generate(prompt, "verifier")
        
        # Clean up response
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response = "\n".join(lines)
        
        # Parse YAML
        import yaml
        deviations = yaml.safe_load(response)
        
        if not isinstance(deviations, dict):
            deviations = {"deviations": []}
        if "deviations" not in deviations:
            deviations = {"deviations": []}
        
        save_deviations(deviations)
        
        dev_count = len(deviations.get("deviations", []))
        print(f"  Found {dev_count} deviation(s)")
        
        # Show high severity ones
        for dev in deviations.get("deviations", [])[:3]:
            if dev.get("severity") == "high":
                print(f"    [HIGH] {dev.get('id')}: {dev.get('description', '')[:60]}...")
        
    except Exception as e:
        print(f"  Error parsing LLM response: {e}")
        save_deviations({"deviations": []})


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
    step_type = step.get("type", "implementation")
    
    print(f"Verifying step: {step.get('step_id')}")
    print(f"Type: {step_type}")
    print(f"Mode: {'staged changes only' if staged_only else 'all uncommitted changes'}")
    
    # Load state and architecture early
    state = load_state()
    architecture = load_architecture() or ""
    
    # Auto-capture baseline on first verification
    capture_baseline_if_first(state, architecture)
    
    # Load copilot output
    copilot_output = get_copilot_output_content()
    
    # Get diff
    diff = get_diff(staged_only)
    has_diff = bool(diff.strip())
    
    # For verification steps with no diff, require copilot_output
    if step_type == "verification" and not has_diff:
        if copilot_output is None:
            print()
            print("=" * 50)
            print("COPILOT OUTPUT REQUIRED")
            print("=" * 50)
            print()
            print("This is a verification step with no code changes.")
            print(f"You must paste the AI's analysis into: {get_file_path(COPILOT_OUTPUT_FILE)}")
            print()
            print("Steps:")
            print("  1. Give copilot_prompt.txt to your AI assistant")
            print("  2. Paste the response into copilot_output.txt")
            print("  3. Run 'wrapper verify' again")
            return False
        else:
            print(f"\nUsing copilot output for verification ({len(copilot_output)} chars)")
    
    if has_diff:
        # Save diff
        save_diff(diff)
        print(f"Diff saved to: {get_file_path('diff.txt')}")
    else:
        print("No git diff detected.")
    
    # Load configuration
    repo_yaml = load_repo_yaml() or {}
    
    # Run rule-based checks
    result = VerificationResult()
    
    if has_diff:
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
        prompt = build_llm_verify_prompt(
            diff, step, repo_yaml, architecture, result, copilot_output
        )
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

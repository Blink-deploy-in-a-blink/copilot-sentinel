"""
wrapper test - Test implemented features against plan.

Reads the implementation plan and tests completed features
using LLM to verify logic correctness.
"""

import os
from typing import List, Dict, Optional, Tuple

from wrapper.core.files import (
    load_implementation_plan,
    load_architecture,
    load_repo_yaml,
)
from wrapper.core.llm import get_llm_client
from wrapper.core.cli_helpers import (
    ask_choice,
    ask_yes_no,
    display_header,
    display_box,
    display_success,
    display_error,
    display_info,
    display_warning,
)


def get_completed_steps(plan: dict) -> List[Tuple[str, dict, dict]]:
    """
    Get all completed steps from plan.
    
    Returns:
        List of (phase_id, phase_dict, step_dict) tuples
    """
    completed = []
    for phase in plan.get("phases", []):
        for step in phase.get("steps", []):
            if step.get("completed", False):
                completed.append((phase.get("id"), phase, step))
    return completed


def get_phase_completion(phase: dict) -> Tuple[int, int]:
    """
    Get completion stats for a phase.
    
    Returns:
        (completed_count, total_count)
    """
    steps = phase.get("steps", [])
    completed = sum(1 for s in steps if s.get("completed", False))
    return completed, len(steps)


def read_file_safely(filepath: str, max_lines: int = 500) -> Optional[str]:
    """
    Read file content safely with size limits.
    
    Args:
        filepath: Path to file
        max_lines: Maximum lines to read (prevent huge files)
    
    Returns:
        File content or None if error
    """
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    lines.append(f"\n... (truncated after {max_lines} lines) ...")
                    break
                lines.append(line.rstrip('\n'))
            return '\n'.join(lines)
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}")
        return None


def build_test_prompt(
    scope_name: str,
    features: List[str],
    requirements: dict,
    files_content: Dict[str, str],
    implementation_notes: str = None
) -> str:
    """
    Build LLM prompt for testing features.
    
    Args:
        scope_name: Name of what's being tested (phase/step)
        features: List of features to verify
        requirements: Non-functional requirements
        files_content: Dict of {filepath: content}
        implementation_notes: Optional notes from developer
    
    Returns:
        Test prompt for LLM
    """
    features_str = "\n".join(f"  {i+1}. {f}" for i, f in enumerate(features))
    
    # Build requirements section
    req_lines = []
    if requirements:
        if requirements.get('security'):
            sec_reqs = requirements['security']
            if isinstance(sec_reqs, list):
                for req in sec_reqs:
                    req_lines.append(f"  [SECURITY] {req}")
        
        if requirements.get('performance'):
            perf = requirements['performance']
            if isinstance(perf, dict):
                if 'latency_target_ms' in perf:
                    req_lines.append(f"  [PERFORMANCE] Latency < {perf['latency_target_ms']}ms")
                if 'cache_ttl_seconds' in perf:
                    req_lines.append(f"  [PERFORMANCE] Caching enabled ({perf['cache_ttl_seconds']}s TTL)")
        
        if requirements.get('cost'):
            cost_reqs = requirements['cost']
            if isinstance(cost_reqs, list):
                for req in cost_reqs:
                    req_lines.append(f"  [COST] {req}")
    
    req_section = ""
    if req_lines:
        req_section = "\n\nNON-FUNCTIONAL REQUIREMENTS:\n" + "\n".join(req_lines)
    
    notes_section = ""
    if implementation_notes:
        notes_section = f"\n\nIMPLEMENTATION NOTES:\n{implementation_notes}"
    
    # Build files section
    files_section = ""
    for filepath, content in files_content.items():
        files_section += f"\n\n--- FILE: {filepath} ---\n```\n{content}\n```"
    
    prompt = f"""Test the implementation of: {scope_name}

FEATURES THAT SHOULD BE IMPLEMENTED:
{features_str}
{req_section}
{notes_section}

CODE TO TEST:
{files_section}

TESTING TASK:
1. Verify EACH feature is implemented correctly
2. Check for logic bugs or errors
3. Verify non-functional requirements are met
4. Check for security issues or bad practices
5. Identify any missing edge cases

OUTPUT FORMAT:
```
TEST RESULT: PASS or FAIL

FEATURE VERIFICATION:
1. [Feature name]: ✓ CORRECT | ✗ BROKEN | ⚠ INCOMPLETE
   Status: [Brief explanation]
   Issues: [Any bugs or problems, or "None"]

2. [Feature name]: ...
...

NON-FUNCTIONAL REQUIREMENTS:
- [Requirement]: ✓ MET | ✗ NOT MET
  Explanation: ...

BUGS FOUND:
- [List any bugs, logic errors, or issues]
- OR "None found"

SECURITY ISSUES:
- [List any security problems]
- OR "None found"

RECOMMENDATIONS:
- [Suggestions for improvement]
- OR "Code looks good"

OVERALL VERDICT:
[Summary: Pass if all features work correctly and no critical bugs]
```

Test now:"""

    return prompt


def test_step(phase: dict, step: dict) -> bool:
    """
    Test a specific completed step.
    
    Args:
        phase: Phase containing the step
        step: Step to test
    
    Returns:
        True if test passed
    """
    step_id = step.get('step_id', 'unknown')
    goal = step.get('goal', 'No goal specified')
    features = step.get('features', [])
    requirements = step.get('requirements', {})
    files_changed = step.get('files_changed', [])
    implementation_notes = step.get('implementation_notes')
    
    print()
    display_header(f"TESTING STEP: {step_id}", width=70)
    print(f"Goal: {goal}")
    print(f"Features: {len(features)}")
    print(f"Files: {len(files_changed)}")
    print()
    
    if not features:
        display_warning("No features defined for this step - skipping test")
        return True
    
    if not files_changed:
        display_warning("No files recorded - cannot test without code")
        print("Tip: This step was completed before file tracking was added.")
        return True
    
    # Read all files
    print("📖 Reading files...")
    files_content = {}
    for filepath in files_changed:
        if filepath.startswith('.wrapper/'):
            continue  # Skip metadata files
        
        content = read_file_safely(filepath)
        if content:
            files_content[filepath] = content
            print(f"  ✓ {filepath} ({len(content)} chars)")
        else:
            print(f"  ✗ {filepath} (not found or unreadable)")
    
    if not files_content:
        display_error("No files could be read - cannot test")
        return False
    
    # Build test prompt
    print()
    print("🤖 Sending to LLM for testing...")
    prompt = build_test_prompt(
        scope_name=f"{step_id}: {goal}",
        features=features,
        requirements=requirements,
        files_content=files_content,
        implementation_notes=implementation_notes
    )
    
    # Call LLM
    try:
        llm = get_llm_client()
        response = llm.generate(prompt, "verifier")
        
        print()
        print("=" * 70)
        print("TEST RESULTS")
        print("=" * 70)
        print(response)
        print("=" * 70)
        print()
        
        # Check if passed
        if "TEST RESULT: PASS" in response.upper():
            display_success("✓ Test PASSED")
            return True
        else:
            display_error("✗ Test FAILED")
            return False
        
    except Exception as e:
        display_error(f"Testing failed: {e}")
        return False


def test_phase(phase: dict) -> bool:
    """
    Test all completed steps in a phase.
    
    Args:
        phase: Phase to test
    
    Returns:
        True if all tests passed
    """
    phase_id = phase.get('id', 'unknown')
    phase_name = phase.get('name', 'Unnamed phase')
    
    completed_steps = [s for s in phase.get('steps', []) if s.get('completed', False)]
    
    if not completed_steps:
        display_warning(f"No completed steps in {phase_name}")
        return True
    
    print()
    display_header(f"TESTING PHASE: {phase_name}", width=70)
    print(f"Testing {len(completed_steps)} completed step(s)")
    print()
    
    passed = 0
    failed = 0
    
    for i, step in enumerate(completed_steps, 1):
        print(f"\n--- Step {i}/{len(completed_steps)} ---")
        if test_step(phase, step):
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 70)
    print(f"PHASE TEST SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


def cmd_test(args) -> bool:
    """Main test command - interactive testing menu."""
    
    # Handle --step argument
    if hasattr(args, 'step') and args.step:
        return cmd_test_step_direct(args.step)
    
    display_header("🧪 COPILOT SENTINEL - FEATURE TESTING", width=70)
    
    # Load plan
    plan = load_implementation_plan()
    if not plan:
        display_error("No implementation plan found!")
        print()
        print("Run 'wrapper plan init' first to create a plan.")
        return False
    
    # Get completed steps
    completed = get_completed_steps(plan)
    
    if not completed:
        display_warning("No completed steps to test!")
        print()
        print("Complete some steps using 'wrapper propose' and 'wrapper accept' first.")
        return False
    
    # Show stats
    print()
    print(f"Total completed steps: {len(completed)}")
    print()
    
    # Build menu options
    menu_options = []
    phase_map = {}
    step_map = {}
    
    for phase in plan.get("phases", []):
        completed_count, total_count = get_phase_completion(phase)
        if completed_count > 0:
            phase_id = phase.get('id')
            phase_name = phase.get('name', 'Unnamed')
            menu_options.append(f"Test Phase: {phase_name} ({completed_count}/{total_count} done)")
            phase_map[len(menu_options) - 1] = phase
    
    menu_options.append("Test specific step")
    menu_options.append("Test ALL completed work")
    menu_options.append("Cancel")
    
    # Ask what to test
    choice_idx = ask_choice("What would you like to test?", menu_options)
    
    # Handle choice
    if choice_idx == len(menu_options) - 1:  # Cancel
        print("Cancelled.")
        return True
    
    elif choice_idx == len(menu_options) - 2:  # Test all
        confirm = ask_yes_no("This will test ALL completed steps. Continue?")
        if not confirm:
            print("Cancelled.")
            return True
        
        all_passed = True
        for phase in plan.get("phases", []):
            completed_count, _ = get_phase_completion(phase)
            if completed_count > 0:
                if not test_phase(phase):
                    all_passed = False
        
        return all_passed
    
    elif choice_idx == len(menu_options) - 3:  # Test specific step
        # Build step menu
        step_options = []
        step_list = []
        for phase_id, phase, step in completed:
            step_id = step.get('step_id', 'unknown')
            goal = step.get('goal', 'No goal')
            phase_name = phase.get('name', 'Unknown phase')
            step_options.append(f"{step_id} - {goal} (in {phase_name})")
            step_list.append((phase, step))
        
        step_idx = ask_choice("Which step to test?", step_options)
        phase, step = step_list[step_idx]
        return test_step(phase, step)
    
    else:  # Test a specific phase
        phase = phase_map[choice_idx]
        return test_phase(phase)


def cmd_test_step_direct(step_id: str) -> bool:
    """
    Test a specific step by ID (for CLI argument).
    
    Args:
        step_id: Step ID to test
    
    Returns:
        True if test passed
    """
    plan = load_implementation_plan()
    if not plan:
        display_error("No implementation plan found!")
        return False
    
    # Find step
    for phase in plan.get("phases", []):
        for step in phase.get("steps", []):
            if step.get('step_id') == step_id:
                if not step.get('completed', False):
                    display_error(f"Step {step_id} is not completed yet!")
                    return False
                return test_step(phase, step)
    
    display_error(f"Step {step_id} not found in plan!")
    return False

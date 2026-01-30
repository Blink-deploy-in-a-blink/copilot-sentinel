"""
wrapper accept - Accept verified step into state.
"""

from datetime import datetime

from wrapper.core.files import (
    load_state,
    load_step_yaml,
    load_deviations,
    load_implementation_plan,
    save_state,
    save_deviations,
    save_implementation_plan,
    add_done_step,
)
from wrapper.core.paths import get_file_path, STEP_YAML_FILE


def update_deviation_resolutions(step_id: str, step_goal: str) -> int:
    """
    Check if this step resolves any deviations and update them.
    
    Uses LLM to match step goal against unresolved deviations.
    
    Returns:
        Number of deviations marked as resolved
    """
    deviations = load_deviations()
    if not deviations or not deviations.get("deviations"):
        return 0
    
    unresolved = [
        dev for dev in deviations["deviations"]
        if dev.get("resolution_step") is None
    ]
    
    if not unresolved:
        return 0
    
    # Use LLM to determine which deviations this step resolves
    from wrapper.core.llm import get_llm_client
    
    unresolved_list = "\n".join(
        f"- {dev.get('id')}: {dev.get('description', '')[:100]}"
        for dev in unresolved
    )
    
    prompt = f"""Analyze if this step resolves any of the listed deviations.

STEP COMPLETED:
- ID: {step_id}
- Goal: {step_goal}

UNRESOLVED DEVIATIONS:
{unresolved_list}

OUTPUT REQUIREMENTS:
Return ONLY a JSON array of deviation IDs that this step resolves.
If none are resolved, return empty array: []

Example outputs:
["no-polling-support"]
["missing-tests-directory", "missing-ci-config"]
[]

Output now (ONLY the JSON array, nothing else):"""

    try:
        llm = get_llm_client()
        response = llm.generate(prompt, "verifier")
        
        # Parse JSON response
        import json
        response = response.strip()
        
        # Clean up if wrapped in code fences
        if response.startswith("```"):
            lines = response.split("\n")
            response = "\n".join(line for line in lines if not line.startswith("```"))
            response = response.strip()
        
        resolved_ids = json.loads(response)
        
        if not isinstance(resolved_ids, list):
            return 0
        
        # Update deviations
        updated_count = 0
        for dev in deviations["deviations"]:
            if dev.get("id") in resolved_ids and dev.get("resolution_step") is None:
                dev["resolution_step"] = step_id
                updated_count += 1
        
        if updated_count > 0:
            save_deviations(deviations)
        
        return updated_count
        
    except Exception as e:
        # If LLM fails, silently skip (don't block accept)
        print(f"  Note: Could not auto-update deviations ({e})")
        return 0


def cmd_accept(args) -> bool:
    """Accept verified step into state."""
    
    # Load step
    step = load_step_yaml()
    if not step:
        print(f"Error: {STEP_YAML_FILE} not found.")
        return False
    
    step_id = step.get("step_id", "unknown")
    step_type = step.get("type", "unknown")
    
    # Load current state
    state = load_state()
    
    # STRICT GATE: Check last verification status
    last_status = state.get("last_verify_status")
    last_step = state.get("last_verify_step")
    
    if last_status != "PASS":
        print("=" * 40)
        print("ACCEPT BLOCKED")
        print("=" * 40)
        print()
        if last_status == "FAIL":
            print(f"Last verification FAILED for step: {last_step}")
        else:
            print("No successful verification found.")
        print()
        print("You must run 'wrapper verify' and get PASS before accepting.")
        print("This is non-negotiable.")
        return False
    
    if last_step != step_id:
        print("=" * 40)
        print("ACCEPT BLOCKED")
        print("=" * 40)
        print()
        print(f"Last verified step: {last_step}")
        print(f"Current step: {step_id}")
        print()
        print("Step mismatch. Run 'wrapper verify' for the current step first.")
        return False
    
    print(f"Accepting step: {step_id}")
    
    # Check if already accepted
    done_ids = [s["step_id"] for s in state.get("done_steps", [])]
    if step_id in done_ids:
        print(f"Warning: Step '{step_id}' already accepted.")
        response = input("Accept again? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return False
    
    # Add to done steps
    add_done_step(step_id, f"{step_type} completed")
    
    # Check if this step resolves any deviations
    step_goal = step.get("goal", "")
    if step_goal:
        resolved_count = update_deviation_resolutions(step_id, step_goal)
        if resolved_count > 0:
            print(f"✓ Marked {resolved_count} deviation(s) as resolved by this step")
    
    # Update invariants if this was a verification step
    if step_type == "verification":
        success_criteria = step.get("success_criteria", [])
        if success_criteria:
            state = load_state()  # Reload after add_done_step
            existing = set(state.get("invariants", []))
            for criterion in success_criteria:
                if criterion not in existing:
                    state["invariants"].append(criterion)
            save_state(state)
            print(f"Added {len(success_criteria)} invariants from verification.")
    
    # NEW: Update implementation plan if exists
    plan = load_implementation_plan()
    if plan:
        # Get git diff to capture files changed
        from wrapper.core.git import get_changed_files
        files_changed = list(get_changed_files())
        
        # Ask for implementation notes
        print()
        print("📝 Implementation Notes (optional)")
        print("   Add any comments about this implementation:")
        print("   (Press Enter to skip, or type notes and press Enter)")
        implementation_notes = input("   > ").strip()
        
        updated = mark_step_complete_in_plan(
            plan, 
            step_id, 
            files_changed=files_changed,
            implementation_notes=implementation_notes or None
        )
        if updated:
            save_implementation_plan(plan)
            print(f"✓ Updated implementation plan progress")
            if files_changed:
                print(f"✓ Captured {len(files_changed)} file(s) changed")
            if implementation_notes:
                print(f"✓ Saved implementation notes")
    
    print()
    print(f"Step '{step_id}' accepted.")
    print()
    print("State updated. You can now:")
    print("  - Run 'wrapper propose' for next step")
    
    if plan:
        print("  - Check progress: wrapper plan --status")
    else:
        print("  - Or manually create a new step.yaml")
    
    # Show current state summary
    state = load_state()
    print()
    print(f"Progress: {len(state.get('done_steps', []))} steps completed")
    print(f"Invariants: {len(state.get('invariants', []))}")
    
    return True


def mark_step_complete_in_plan(
    plan: dict, 
    step_id: str,
    files_changed: list = None,
    implementation_notes: str = None
) -> bool:
    """
    Mark a step as complete in the implementation plan.
    
    Args:
        plan: Implementation plan dict
        step_id: ID of step to mark complete
        files_changed: List of files modified in this step
        implementation_notes: Optional notes about implementation
    
    Returns True if step was found and marked, False otherwise.
    """
    for phase in plan.get("phases", []):
        for step in phase.get("steps", []):
            if step.get('step_id') == step_id:
                step['completed'] = True
                step['completed_at'] = datetime.now().isoformat()
                
                # Add implementation tracking
                if files_changed:
                    step['files_changed'] = [f for f in files_changed if not f.startswith('.wrapper/')]
                if implementation_notes:
                    step['implementation_notes'] = implementation_notes
                
                return True
    
    return False
    return True

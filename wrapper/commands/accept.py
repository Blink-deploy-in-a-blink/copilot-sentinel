"""
wrapper accept - Accept verified step into state.
"""

from datetime import datetime

from wrapper.core.files import (
    load_state,
    load_step_yaml,
    save_state,
    add_done_step,
)
from wrapper.core.paths import get_file_path, STEP_YAML_FILE


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
    
    print()
    print(f"Step '{step_id}' accepted.")
    print()
    print("State updated. You can now:")
    print("  - Run 'wrapper propose' for next step")
    print("  - Or manually create a new step.yaml")
    
    # Show current state summary
    state = load_state()
    print()
    print(f"Progress: {len(state.get('done_steps', []))} steps completed")
    print(f"Invariants: {len(state.get('invariants', []))}")
    
    return True

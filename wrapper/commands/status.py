"""
wrapper status - Show current workflow state at a glance.

Helps users understand where they are in the propose → compile → verify → accept loop,
and what to do next.
"""

from wrapper.core.files import (
    load_architecture,
    load_repo_yaml,
    load_state,
    load_step_yaml,
    load_copilot_output,
    load_baseline_snapshot,
    load_deviations,
    load_implementation_plan,
)
from wrapper.core.paths import (
    get_wrapper_dir,
    ARCHITECTURE_FILE,
    REPO_YAML_FILE,
    STEP_YAML_FILE,
    COPILOT_PROMPT_FILE,
    COPILOT_OUTPUT_FILE,
)
from wrapper.core.git import is_git_repo


def cmd_status(args) -> bool:
    """Show current workflow status and next action."""

    wrapper_dir = get_wrapper_dir()

    print()
    print("━" * 60)
    print("  COPILOT SENTINEL — STATUS")
    print("━" * 60)

    # 1. Check initialization
    if not wrapper_dir.exists():
        print()
        print("  ⚠  Not initialized")
        print()
        print("  Run: wrapper init          (basic setup)")
        print("       wrapper init --guided  (interactive AI-assisted setup)")
        print()
        print("━" * 60)
        return True

    arch = load_architecture()
    repo = load_repo_yaml()
    state = load_state()
    step = load_step_yaml()
    plan = load_implementation_plan()
    baseline = load_baseline_snapshot()
    deviations = load_deviations()

    # 2. Show repo info
    repo_name = repo.get("repo_name", "unknown") if repo else "unknown"
    print(f"\n  📦 Repository: {repo_name}")

    # 3. Show file status
    print()
    _status_line("architecture.md", arch is not None)
    _status_line("repo.yaml", repo is not None)
    _status_line("baseline snapshot", baseline is not None)
    _status_line("implementation plan", plan is not None)

    # 4. Show progress
    done_steps = state.get("done_steps", [])
    invariants = state.get("invariants", [])
    print(f"\n  📊 Progress: {len(done_steps)} step(s) completed, {len(invariants)} invariant(s)")

    if plan:
        total_steps = sum(len(p.get("steps", [])) for p in plan.get("phases", []))
        done_ids = {s["step_id"] for s in done_steps}
        plan_completed = sum(
            1
            for phase in plan.get("phases", [])
            for s in phase.get("steps", [])
            if s.get("step_id") in done_ids
        )
        if total_steps > 0:
            pct = (plan_completed / total_steps) * 100
            bar_width = 20
            filled = int(bar_width * plan_completed / total_steps)
            bar = "▓" * filled + "░" * (bar_width - filled)
            print(f"  📋 Plan:     [{bar}] {pct:.0f}% ({plan_completed}/{total_steps})")

    if deviations and deviations.get("deviations"):
        dev_list = deviations["deviations"]
        unresolved = [d for d in dev_list if d.get("resolution_step") is None]
        print(f"  ⚠  Deviations: {len(unresolved)} unresolved / {len(dev_list)} total")

    # 5. Determine workflow state and next action
    print()
    print("  " + "─" * 56)
    _show_next_action(arch, repo, step, state, plan, baseline)

    print()
    print("━" * 60)
    return True


def _status_line(label: str, exists: bool) -> None:
    """Print a status indicator line."""
    icon = "✅" if exists else "❌"
    print(f"  {icon} {label}")


def _show_next_action(arch, repo, step, state, plan, baseline) -> None:
    """Determine and display the recommended next action."""

    # Not fully initialized
    if arch is None or repo is None:
        print("  🔜 Next: Edit your architecture.md and repo.yaml")
        print("     then run: wrapper propose")
        return

    # No baseline yet
    if baseline is None and len(state.get("done_steps", [])) == 0:
        if step:
            print(f"  🔜 Current step: {step.get('step_id', 'unknown')}")
            _show_step_workflow_state(step, state)
        else:
            print("  🔜 Next: wrapper propose")
            print("     (First run will capture baseline snapshot)")
        return

    # Active step in progress
    if step:
        step_id = step.get("step_id", "unknown")
        last_verify = state.get("last_verify_status")
        last_verify_step = state.get("last_verify_step")

        print(f"  🔄 Active step: {step_id}")
        _show_step_workflow_state(step, state)
        return

    # No active step — need to propose
    if plan:
        from wrapper.commands.propose import get_next_step_from_plan
        next_step = get_next_step_from_plan(plan, state)
        if next_step:
            print(f"  🔜 Next planned step: {next_step.get('name', next_step.get('step_id', '?'))}")
            print("     Run: wrapper propose")
        else:
            print("  🎉 All planned steps complete!")
            print("     Run: wrapper plan status   (review progress)")
            print("          wrapper plan init     (create new plan)")
    else:
        print("  🔜 Next: wrapper propose")
        print("     Tip: Run 'wrapper plan init' to create a structured plan first")


def _show_step_workflow_state(step, state) -> None:
    """Show where the user is in the propose→compile→verify→accept loop."""

    step_id = step.get("step_id", "unknown")
    last_verify = state.get("last_verify_status")
    last_verify_step = state.get("last_verify_step")

    copilot_prompt_path = get_wrapper_dir() / COPILOT_PROMPT_FILE
    has_prompt = copilot_prompt_path.exists()

    if not has_prompt:
        # Step exists but not compiled yet
        print("     → Run: wrapper compile")
        return

    if last_verify_step == step_id and last_verify == "PASS":
        # Verified and passed — ready to accept
        print("     ✅ Verified PASS")
        print("     → Run: wrapper accept")
        return

    if last_verify_step == step_id and last_verify == "FAIL":
        # Verified but failed — fix and re-verify
        print("     ❌ Verified FAIL — fix issues then re-verify")
        print("     → Run: wrapper verify")
        return

    # Compiled but not yet verified
    print("     → Steps:")
    print("       1. Give copilot_prompt.txt to your AI assistant")
    print("       2. Make changes / paste output into copilot_output.txt")
    print("       3. Run: wrapper verify")

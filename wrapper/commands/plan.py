"""
wrapper plan - Interactive implementation planning.

Generates a strategic plan for fixing architectural deviations.
"""

import json
from typing import List, Dict, Optional, Any

from wrapper.core.files import (
    load_architecture,
    load_repo_yaml,
    load_baseline_snapshot,
    load_deviations,
    load_state,
    load_implementation_plan,
    save_implementation_plan,
)
from wrapper.core.paths import get_file_path, IMPLEMENTATION_PLAN_FILE
from wrapper.core.llm import get_llm_client
from wrapper.core.planning_session import PlanningSession
from wrapper.core.cli_helpers import (
    ask_choice,
    ask_yes_no,
    ask_text,
    ask_number,
    display_header,
    display_box,
    display_success,
    display_error,
    display_info,
    display_warning,
)


def cmd_plan_init(args) -> bool:
    """Interactive planning - generate implementation plan."""
    
    display_header("🤖 COPILOT SENTINEL - INTERACTIVE PLANNING", width=70)
    
    # Check if plan already exists
    existing_plan = load_implementation_plan()
    if existing_plan:
        display_warning("Implementation plan already exists!")
        choice = ask_choice(
            "What would you like to do?",
            [
                "View existing plan status",
                "Regenerate plan (overwrites current)",
                "Cancel"
            ]
        )
        
        if choice == 0:  # View status
            return cmd_plan_status(args)
        elif choice == 2:  # Cancel
            print("Cancelled.")
            return False
        # choice == 1: Continue to regenerate
    
    # Load required data
    display_info("Loading project data...")
    
    architecture = load_architecture()
    if not architecture:
        display_error("architecture.md not found. Run 'wrapper init' first.")
        return False
    
    repo_yaml = load_repo_yaml()
    if not repo_yaml:
        display_error("repo.yaml not found. Run 'wrapper init' first.")
        return False
    
    baseline = load_baseline_snapshot()
    deviations = load_deviations()
    
    if not baseline or not deviations:
        display_warning("No baseline/deviations found. Run 'wrapper verify' first to capture baseline.")
        if not ask_yes_no("Continue anyway?", default=False):
            return False
    
    # Start planning session
    session = PlanningSession()
    session.clear()  # Start fresh
    session.set_phase("phase_planning")
    
    # Show summary
    display_info("Repository Analysis:")
    if baseline:
        summary = baseline.get("summary", {})
        print(f"  📁 Files: {summary.get('total_files', '?')}")
        print(f"  📁 Directories: {summary.get('total_directories', '?')}")
    
    if deviations:
        dev_list = deviations.get("deviations", [])
        print(f"  ⚠️  Deviations: {len(dev_list)}")
        
        # Show high-severity deviations
        high_devs = [d for d in dev_list if d.get("severity") == "high"]
        if high_devs:
            print(f"\n  High-severity issues:")
            for dev in high_devs[:3]:
                print(f"    - {dev.get('id')}: {dev.get('description', '')[:60]}...")
    
    print()
    
    if not ask_yes_no("Ready to create implementation plan?", default=True):
        print("Cancelled.")
        return False
    
    # Phase 1: High-level phase breakdown
    phases = generate_phases(architecture, repo_yaml, baseline, deviations, session)
    if not phases:
        display_error("Failed to generate phases.")
        return False
    
    phases = refine_phases(phases, session)
    if not phases:
        print("Planning cancelled.")
        return False
    
    # Phase 2: Detail each phase
    session.set_phase("step_detailing")
    
    for i, phase in enumerate(phases):
        display_header(f"DETAILING PHASE {i+1}: {phase['name']}", width=70)
        session.set_current_phase_idx(i)
        
        steps = detail_phase(phase, architecture, repo_yaml, session)
        if not steps:
            display_error(f"Failed to detail phase {i+1}")
            return False
        
        phase['steps'] = steps
        session.add_phase_data(phase)
    
    # Build final plan
    plan = build_final_plan(phases, repo_yaml, session)
    
    # Save plan
    save_implementation_plan(plan)
    session.set_phase("complete")
    
    display_success(f"Implementation plan saved to: {get_file_path(IMPLEMENTATION_PLAN_FILE)}")
    
    # Show summary
    total_steps = sum(len(p['steps']) for p in phases)
    total_hours = sum(
        sum(s.get('estimated_hours', 1) for s in p['steps'])
        for p in phases
    )
    
    display_box(
        "PLANNING COMPLETE! 🎉",
        f"""Total: {len(phases)} phases, {total_steps} steps
Estimated time: ~{total_hours:.0f} hours

Next steps:
  1. Review plan: wrapper plan --show
  2. Start execution: wrapper propose --from-plan
""",
        width=70
    )
    
    return True


def generate_phases(
    architecture: str,
    repo_yaml: dict,
    baseline: Optional[dict],
    deviations: Optional[dict],
    session: PlanningSession
) -> Optional[List[dict]]:
    """
    Use LLM to propose high-level phases.
    
    Returns list of phase dicts or None on failure.
    """
    display_info("Analyzing architecture and generating phase breakdown...")
    
    # Build context for LLM
    deviations_summary = "No deviations captured yet"
    if deviations and deviations.get("deviations"):
        dev_list = deviations["deviations"]
        high = len([d for d in dev_list if d.get("severity") == "high"])
        med = len([d for d in dev_list if d.get("severity") == "medium"])
        low = len([d for d in dev_list if d.get("severity") == "low"])
        deviations_summary = f"{len(dev_list)} total ({high} high, {med} medium, {low} low)"
    
    baseline_summary = "No baseline captured yet"
    if baseline:
        summary = baseline.get("summary", {})
        baseline_summary = f"{summary.get('total_files', '?')} files, {summary.get('total_directories', '?')} directories"
    
    prompt = f"""You are an expert software architect helping plan a refactoring project.

ARCHITECTURE (target state):
{architecture[:2000]}

CURRENT STATE:
{baseline_summary}

DEVIATIONS FROM ARCHITECTURE:
{deviations_summary}

TASK:
Propose 4-6 high-level implementation phases to fix these deviations and align with architecture.

Each phase should:
- Have a clear goal
- Group related changes together
- Have reasonable scope (not too big or small)
- Consider dependencies between phases

OUTPUT FORMAT (valid JSON only, no markdown):
[
  {{
    "id": "phase-1",
    "name": "Short descriptive name",
    "goal": "Clear description of what this phase accomplishes",
    "deviations_addressed": ["deviation-id-1", "deviation-id-2"],
    "estimated_complexity": "low|medium|high",
    "dependencies": []
  }},
  ...
]

Propose phases now:"""
    
    try:
        llm = get_llm_client()
        response = llm.generate(prompt, "step_proposer")
        
        # Clean response
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response = "\n".join(lines).strip()
        
        # Parse JSON
        phases = json.loads(response)
        
        if not isinstance(phases, list):
            raise ValueError("Response is not a list")
        
        return phases
    
    except Exception as e:
        display_error(f"Failed to generate phases: {e}")
        print(f"LLM response: {response[:500] if 'response' in locals() else 'N/A'}")
        return None


def refine_phases(phases: List[dict], session: PlanningSession) -> Optional[List[dict]]:
    """
    Let user refine the proposed phases.
    
    Returns refined phases or None if cancelled.
    """
    while True:
        # Display phases
        display_header("PROPOSED PHASES", width=70)
        for i, phase in enumerate(phases, 1):
            print(f"\n{i}. {phase['name']} [{phase.get('estimated_complexity', '?').upper()}]")
            print(f"   Goal: {phase['goal'][:100]}...")
            if phase.get('deviations_addressed'):
                print(f"   Fixes: {len(phase['deviations_addressed'])} deviation(s)")
        
        print()
        
        # Ask what to do
        choice = ask_choice(
            "What would you like to do?",
            [
                "Looks good, continue to detailed planning",
                "Change phase order",
                "Merge phases",
                "Split a phase",
                "Remove a phase",
                "Regenerate phases",
                "Cancel planning"
            ]
        )
        
        if choice == 0:  # Continue
            return phases
        
        elif choice == 1:  # Reorder
            phases = reorder_phases(phases, session)
        
        elif choice == 2:  # Merge
            phases = merge_phases(phases, session)
        
        elif choice == 3:  # Split
            display_info("Phase splitting not implemented yet. Edit plan file manually later.")
        
        elif choice == 4:  # Remove
            phases = remove_phase(phases, session)
        
        elif choice == 5:  # Regenerate
            display_warning("Regeneration would lose current phases.")
            if ask_yes_no("Are you sure?", default=False):
                return None  # Signal to regenerate
        
        elif choice == 6:  # Cancel
            return None


def reorder_phases(phases: List[dict], session: PlanningSession) -> List[dict]:
    """Let user reorder phases."""
    print("\nCurrent order:")
    for i, phase in enumerate(phases, 1):
        print(f"  {i}. {phase['name']}")
    
    print("\nEnter new order as comma-separated numbers (e.g., 2,1,3,4)")
    order_str = input("> ").strip()
    
    try:
        indices = [int(x.strip()) - 1 for x in order_str.split(",")]
        if len(indices) != len(phases) or any(i < 0 or i >= len(phases) for i in indices):
            display_error("Invalid order")
            return phases
        
        new_phases = [phases[i] for i in indices]
        
        # Ask for reasoning
        reasoning = ask_text("Why this order? (optional, helps guide planning)", optional=True)
        if reasoning:
            session.add_context("Phase order preference", order_str, reasoning)
            session.record_preference("phase_order_reasoning", reasoning)
        
        display_success("Phase order updated")
        return new_phases
    
    except Exception as e:
        display_error(f"Failed to reorder: {e}")
        return phases


def merge_phases(phases: List[dict], session: PlanningSession) -> List[dict]:
    """Let user merge two phases."""
    print("\nWhich phases to merge? (enter two numbers, e.g., 1,3)")
    for i, phase in enumerate(phases, 1):
        print(f"  {i}. {phase['name']}")
    
    choice_str = input("> ").strip()
    
    try:
        indices = [int(x.strip()) - 1 for x in choice_str.split(",")]
        if len(indices) != 2:
            display_error("Must select exactly 2 phases")
            return phases
        
        idx1, idx2 = sorted(indices)
        if idx1 < 0 or idx2 >= len(phases):
            display_error("Invalid phase numbers")
            return phases
        
        # Merge
        merged_name = ask_text(f"Name for merged phase? [default: {phases[idx1]['name']}]", optional=True)
        if not merged_name:
            merged_name = phases[idx1]['name']
        
        merged_devs = list(set(
            phases[idx1].get('deviations_addressed', []) +
            phases[idx2].get('deviations_addressed', [])
        ))
        
        merged_phase = {
            "id": phases[idx1]['id'],
            "name": merged_name,
            "goal": f"{phases[idx1]['goal']} AND {phases[idx2]['goal']}",
            "deviations_addressed": merged_devs,
            "estimated_complexity": "high",  # Merged = more complex
            "dependencies": []
        }
        
        # Build new list
        new_phases = [p for i, p in enumerate(phases) if i not in [idx1, idx2]]
        new_phases.insert(idx1, merged_phase)
        
        display_success(f"Merged into: {merged_name}")
        return new_phases
    
    except Exception as e:
        display_error(f"Failed to merge: {e}")
        return phases


def remove_phase(phases: List[dict], session: PlanningSession) -> List[dict]:
    """Let user remove a phase."""
    print("\nWhich phase to remove?")
    for i, phase in enumerate(phases, 1):
        print(f"  {i}. {phase['name']}")
    
    try:
        idx = int(input("> ").strip()) - 1
        if idx < 0 or idx >= len(phases):
            display_error("Invalid phase number")
            return phases
        
        if ask_yes_no(f"Remove '{phases[idx]['name']}'?", default=False):
            removed = phases.pop(idx)
            display_success(f"Removed: {removed['name']}")
        
        return phases
    
    except Exception as e:
        display_error(f"Failed to remove: {e}")
        return phases


def detail_phase(
    phase: dict,
    architecture: str,
    repo_yaml: dict,
    session: PlanningSession
) -> Optional[List[dict]]:
    """
    Generate detailed steps for a phase.
    
    Returns list of step dicts or None on failure.
    """
    display_info(f"Generating steps for: {phase['name']}...")
    
    # Get user preferences
    context_summary = session.get_context_summary()
    
    prompt = f"""Break down this implementation phase into detailed steps.

PHASE:
- Name: {phase['name']}
- Goal: {phase['goal']}
- Complexity: {phase.get('estimated_complexity', 'medium')}

ARCHITECTURE CONTEXT:
{architecture[:1500]}

USER PREFERENCES (from earlier):
{context_summary}

TASK:
Propose 3-6 concrete implementation steps for this phase.

Each step should:
- Be small enough to complete in 1-3 hours
- Have clear scope and boundaries
- List specific files to modify
- List features to implement (for verification)

OUTPUT FORMAT (valid JSON only):
[
  {{
    "step_id": "descriptive-kebab-case-id",
    "name": "Short step name",
    "scope": "Clear description of what to do",
    "files_to_modify": ["path/to/file1.py", "path/to/file2.py"],
    "features": [
      "Feature 1 to implement",
      "Feature 2 to implement"
    ],
    "estimated_hours": 1.5,
    "risk": "low|medium|high"
  }},
  ...
]

Propose steps now:"""
    
    try:
        llm = get_llm_client()
        response = llm.generate(prompt, "step_proposer")
        
        # Clean response
        response = response.strip()
        if response.startswith("```"):
            lines = response.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            response = "\n".join(lines).strip()
        
        # Parse JSON
        steps = json.loads(response)
        
        if not isinstance(steps, list):
            raise ValueError("Response is not a list")
        
        # Let user refine steps
        steps = refine_steps(steps, phase, session)
        
        return steps
    
    except Exception as e:
        display_error(f"Failed to detail phase: {e}")
        print(f"LLM response: {response[:500] if 'response' in locals() else 'N/A'}")
        return None


def refine_steps(steps: List[dict], phase: dict, session: PlanningSession) -> List[dict]:
    """Let user refine steps and add non-functional requirements."""
    
    # Show steps
    print(f"\nProposed steps for '{phase['name']}':")
    for i, step in enumerate(steps, 1):
        print(f"\n  {i}. {step['name']}")
        print(f"     Scope: {step['scope'][:80]}...")
        print(f"     Files: {len(step.get('files_to_modify', []))} file(s)")
        print(f"     Features: {len(step.get('features', []))}")
        print(f"     Time: ~{step.get('estimated_hours', '?')}h | Risk: {step.get('risk', '?')}")
    
    print()
    
    if not ask_yes_no("Add non-functional requirements (security, performance, etc.)?", default=True):
        return steps
    
    # Add requirements to each step
    for i, step in enumerate(steps):
        print(f"\n{'─' * 70}")
        print(f"Step {i+1}: {step['name']}")
        print(f"{'─' * 70}")
        
        step['requirements'] = gather_requirements(step, session)
    
    display_success("Non-functional requirements added to all steps")
    
    return steps


def gather_requirements(step: dict, session: PlanningSession) -> dict:
    """Gather non-functional requirements for a step."""
    
    requirements = {}
    
    # Security
    if ask_yes_no("  Add security requirements?", default=False):
        requirements['security'] = gather_security_requirements(step)
    
    # Performance
    if ask_yes_no("  Add performance requirements?", default=False):
        requirements['performance'] = gather_performance_requirements(step)
    
    # Cost optimization
    if ask_yes_no("  Add cost optimization notes?", default=False):
        requirements['cost'] = gather_cost_requirements(step)
    
    # Free-form notes
    if ask_yes_no("  Add any other notes for the AI assistant?", default=False):
        notes = ask_text("Additional requirements/notes (free-text)", optional=True, multiline=False)
        if notes:
            requirements['notes'] = notes
    
    return requirements


def gather_security_requirements(step: dict) -> List[str]:
    """Template-based security requirements."""
    reqs = []
    
    print("\n    Security checklist (select all that apply):")
    options = [
        "Input validation required",
        "Password/secret hashing required",
        "Authorization/access control checks",
        "Rate limiting required",
        "SQL injection prevention (parameterized queries)",
        "XSS prevention (output escaping)",
        "CSRF protection",
        "Audit logging required",
        "None of the above"
    ]
    
    for i, opt in enumerate(options, 1):
        print(f"      [{i}] {opt}")
    
    print("\n    Enter numbers (comma-separated, e.g., 1,2,5):")
    choices_str = input("    > ").strip()
    
    try:
        indices = [int(x.strip()) - 1 for x in choices_str.split(",")]
        for idx in indices:
            if 0 <= idx < len(options) - 1:  # Exclude "None"
                reqs.append(options[idx])
    except:
        pass
    
    return reqs


def gather_performance_requirements(step: dict) -> dict:
    """Template-based performance requirements."""
    perf = {}
    
    # Latency target
    if ask_yes_no("    Set latency target?", default=False):
        target_ms = ask_number("      Max latency (ms)", default=200)
        perf['latency_target_ms'] = target_ms
    
    # Caching
    if ask_yes_no("    Enable caching?", default=False):
        ttl = ask_number("      Cache TTL (seconds)", default=60)
        perf['cache_ttl_seconds'] = ttl
    
    # Other optimizations
    notes = ask_text("    Other performance notes? (optional)", optional=True)
    if notes:
        perf['notes'] = notes
    
    return perf


def gather_cost_requirements(step: dict) -> List[str]:
    """Template-based cost optimization requirements."""
    reqs = []
    
    print("\n    Cost optimization (select all that apply):")
    options = [
        "Minimize API calls (use caching/batching)",
        "Minimize database queries (use joins, avoid N+1)",
        "Connection pooling required",
        "Batch operations where possible",
        "None"
    ]
    
    for i, opt in enumerate(options, 1):
        print(f"      [{i}] {opt}")
    
    print("\n    Enter numbers (comma-separated):")
    choices_str = input("    > ").strip()
    
    try:
        indices = [int(x.strip()) - 1 for x in choices_str.split(",")]
        for idx in indices:
            if 0 <= idx < len(options) - 1:
                reqs.append(options[idx])
    except:
        pass
    
    return reqs


def build_final_plan(phases: List[dict], repo_yaml: dict, session: PlanningSession) -> dict:
    """Build final implementation plan structure."""
    
    total_steps = sum(len(p['steps']) for p in phases)
    total_hours = sum(
        sum(s.get('estimated_hours', 1) for s in p['steps'])
        for p in phases
    )
    
    return {
        "metadata": {
            "created": session.state.get("started"),
            "repo_name": repo_yaml.get("repo_name", "unknown"),
            "total_phases": len(phases),
            "total_steps": total_steps,
            "estimated_hours": round(total_hours, 1),
            "planning_context": session.get_context_summary(),
        },
        "phases": phases
    }


def cmd_plan_status(args) -> bool:
    """Show implementation plan status."""
    
    plan = load_implementation_plan()
    if not plan:
        display_error("No implementation plan found. Run 'wrapper plan init' first.")
        return False
    
    state = load_state()
    done_step_ids = {s['step_id'] for s in state.get('done_steps', [])}
    
    display_header("IMPLEMENTATION PLAN STATUS", width=70)
    
    metadata = plan.get("metadata", {})
    print(f"Created: {metadata.get('created', 'unknown')}")
    print(f"Repository: {metadata.get('repo_name', 'unknown')}")
    print()
    
    total_steps = 0
    completed_steps = 0
    
    for i, phase in enumerate(plan.get("phases", []), 1):
        steps = phase.get("steps", [])
        phase_completed = sum(1 for s in steps if s.get('step_id') in done_step_ids)
        total_steps += len(steps)
        completed_steps += phase_completed
        
        status_icon = "✅" if phase_completed == len(steps) else "🔄" if phase_completed > 0 else "⏸️"
        
        print(f"{status_icon} Phase {i}: {phase['name']} ({phase_completed}/{len(steps)} complete)")
        
        for j, step in enumerate(steps, 1):
            step_id = step.get('step_id')
            if step_id in done_step_ids:
                print(f"   ├─ ✅ {j}. {step['name']}")
            else:
                print(f"   ├─ ⏸️  {j}. {step['name']}")
        
        print()
    
    # Progress bar
    if total_steps > 0:
        progress_pct = (completed_steps / total_steps) * 100
        bar_width = 30
        filled = int(bar_width * completed_steps / total_steps)
        bar = "▓" * filled + "░" * (bar_width - filled)
        
        print(f"Progress: [{bar}] {progress_pct:.0f}% ({completed_steps}/{total_steps} steps)")
        
        remaining_hours = metadata.get('estimated_hours', 0) * (1 - progress_pct / 100)
        print(f"Estimated time remaining: ~{remaining_hours:.1f} hours")
    
    print()
    print("Next step:")
    print("  wrapper propose --from-plan")
    
    return True


def cmd_plan_show(args) -> bool:
    """Show implementation plan visualization."""
    
    plan = load_implementation_plan()
    if not plan:
        display_error("No implementation plan found. Run 'wrapper plan init' first.")
        return False
    
    state = load_state()
    done_step_ids = {s['step_id'] for s in state.get('done_steps', [])}
    
    display_header("IMPLEMENTATION PLAN", width=70)
    
    for i, phase in enumerate(plan.get("phases", []), 1):
        steps = phase.get("steps", [])
        phase_completed = sum(1 for s in steps if s.get('step_id') in done_step_ids)
        
        if phase_completed == len(steps):
            status = "COMPLETE"
        elif phase_completed > 0:
            status = f"IN PROGRESS {phase_completed}/{len(steps)}"
        else:
            status = "PENDING"
        
        print(f"\n📦 Phase {i}: {phase['name']} [{status}]")
        print(f"   Goal: {phase['goal']}")
        print(f"   Steps:")
        
        for j, step in enumerate(steps, 1):
            step_id = step.get('step_id')
            done = step_id in done_step_ids
            icon = "✅" if done else "⏸️"
            
            hours = step.get('estimated_hours', '?')
            risk = step.get('risk', '?')
            
            print(f"   {icon} {j}. {step['name']} ({hours}h, {risk} risk)")
    
    print()
    
    return True

"""
wrapper propose - Propose next step.yaml using LLM.
"""

from wrapper.core.files import (
    load_architecture,
    load_repo_yaml,
    load_state,
    load_external_state,
    load_step_yaml,
    load_baseline_snapshot,
    load_deviations,
    save_step_yaml,
)
from wrapper.core.paths import get_file_path, STEP_YAML_FILE, ARCHITECTURE_FILE, REPO_YAML_FILE
from wrapper.core.llm import get_llm_client


def check_required_files() -> bool:
    """Check if required input files exist, create templates if missing."""
    from wrapper.commands.init import cmd_init
    import argparse
    
    arch = load_architecture()
    repo = load_repo_yaml()
    
    if arch is None or repo is None:
        print("Required files missing. Running init...")
        cmd_init(argparse.Namespace())
        print()
        print("Please edit the template files and run 'wrapper propose' again.")
        return False
    
    return True


def build_propose_prompt(
    architecture: str,
    repo_yaml: dict,
    state: dict,
    external_state: dict | None,
    baseline: dict | None = None,
    deviations: dict | None = None
) -> str:
    """Build the LLM prompt for proposing next step."""
    
    done_steps = state.get("done_steps", [])
    done_summary = "None yet" if not done_steps else "\n".join(
        f"- {s['step_id']}: {s['result']}" for s in done_steps
    )
    
    external_summary = "None configured"
    has_dependencies = False
    if external_state:
        parts = []
        for repo, info in external_state.items():
            parts.append(f"- {repo}: {info}")
            # Check if any dependency is not baseline_verified
            if isinstance(info, dict) and info.get("status") != "baseline_verified":
                has_dependencies = True
        external_summary = "\n".join(parts)
    
    # Check for unverified dependencies in repo.yaml
    depends_on = repo_yaml.get("depends_on", [])
    unverified_deps = []
    if depends_on and external_state:
        for dep in depends_on:
            dep_repo = dep.get("repo") if isinstance(dep, dict) else dep
            if dep_repo:
                dep_info = external_state.get(dep_repo, {})
                if isinstance(dep_info, dict) and dep_info.get("status") != "baseline_verified":
                    unverified_deps.append(dep_repo)
    
    must_not = repo_yaml.get("must_not", [])
    must_not_str = "\n".join(f"- {item}" for item in must_not) if must_not else "None specified"
    
    # Build dependency warning
    dep_warning = ""
    if unverified_deps:
        dep_warning = f"""
DEPENDENCY WARNING:
The following dependencies are NOT baseline verified: {', '.join(unverified_deps)}
You MUST propose a verification or cleanup step, NOT a feature step.
Cross-repo features are BLOCKED until all dependencies are verified.
"""
    
    # Build baseline context section
    baseline_section = ""
    if baseline:
        file_types = baseline.get("summary", {}).get("file_types", {})
        file_types_str = ", ".join(f"{ext}: {count}" for ext, count in list(file_types.items())[:8])
        
        sample_files = baseline.get("files", [])[:30]
        sample_files_str = "\n".join(f"  - {f}" for f in sample_files)
        
        dirs = baseline.get("directories", [])[:20]
        dirs_str = ", ".join(dirs) if dirs else "None"
        
        baseline_section = f"""
ACTUAL REPOSITORY STATE (from baseline snapshot):
- Captured: {baseline.get("timestamp", "unknown")}
- Total files: {baseline.get("summary", {}).get("total_files", "?")}
- Total directories: {baseline.get("summary", {}).get("total_directories", "?")}
- File types: {file_types_str}
- Directories: {dirs_str}

Sample files:
{sample_files_str}
"""
    
    # Build deviations section
    deviations_section = ""
    if deviations and deviations.get("deviations"):
        dev_list = deviations["deviations"]
        dev_lines = []
        for dev in dev_list[:10]:
            severity = dev.get("severity", "?")
            dev_id = dev.get("id", "unknown")
            desc = dev.get("description", "")[:80]
            dev_lines.append(f"  - [{severity.upper()}] {dev_id}: {desc}")
        deviations_section = f"""
KNOWN DEVIATIONS FROM TARGET ARCHITECTURE:
{chr(10).join(dev_lines)}
"""
        if len(dev_list) > 10:
            deviations_section += f"  ... and {len(dev_list) - 10} more\n"

    prompt = f'''Based on the architecture and current state, propose the NEXT development step.

CRITICAL RULES - READ FIRST:
1. BE CONSERVATIVE. When in doubt, propose verification or cleanup.
2. NEVER propose cross-repo changes
3. NEVER propose features if baseline not verified
4. PREFER smaller steps over larger ones
5. PREFER cleanup over new features
6. PREFER verification over implementation
7. If dependencies exist and are unverified, BLOCK feature work

{dep_warning}

ARCHITECTURE:
{architecture}
{baseline_section}
{deviations_section}
REPO CONFIGURATION:
- Name: {repo_yaml.get("repo_name", "unknown")}
- Role: {repo_yaml.get("repo_role", "unspecified")}
- Must NOT:
{must_not_str}

COMPLETED STEPS:
{done_summary}

INVARIANTS ESTABLISHED:
{", ".join(state.get("invariants", [])) or "None yet"}

EXTERNAL REPOS STATE:
{external_summary}

OUTPUT REQUIREMENTS:
- Output ONLY valid YAML
- No markdown code fences
- No explanations before or after
- Follow this exact structure:

step_id: descriptive-kebab-case-id
type: verification OR implementation
repo: {repo_yaml.get("repo_name", "unknown")}
goal: |
  Clear description of what this step accomplishes.
allowed_files:
  - path/to/file1.ts
  - path/to/file2.ts
forbidden:
  - thing that must not happen
  - another forbidden action
success_criteria:
  - measurable outcome 1
  - measurable outcome 2

STEP PROPOSAL RULES (STRICT):
1. If no steps done yet → MUST be type: verification (baseline check)
2. If baseline not clean → MUST be type: verification or cleanup
3. If dependencies unverified → MUST be verification, NOT features
4. Each step touches AT MOST 3 files
5. Each step has AT MOST 3 success criteria
6. forbidden list MUST include all repo-level must_not items
7. NEVER touch files in other repos
8. NEVER add new directories without explicit architecture approval
9. When uncertain → propose verification to gather information

CONSERVATIVE STEP PREFERENCE ORDER:
1. Verification (check current state matches architecture)
2. Cleanup (remove violations, fix existing issues)
3. Refactor (improve structure without new features)
4. Implementation (new features - ONLY if 1-3 not needed)

Propose the next logical step:'''

    return prompt


def cmd_propose(args) -> bool:
    """Propose next step.yaml."""
    
    if not check_required_files():
        return False
    
    print("Loading configuration...")
    architecture = load_architecture()
    repo_yaml = load_repo_yaml()
    state = load_state()
    external_state = load_external_state()
    baseline = load_baseline_snapshot()
    deviations = load_deviations()
    
    # Check if step.yaml already exists
    existing_step = load_step_yaml()
    if existing_step:
        print(f"Warning: {STEP_YAML_FILE} already exists.")
        print(f"Current step: {existing_step.get('step_id', 'unknown')}")
        response = input("Overwrite? [y/N]: ").strip().lower()
        if response != 'y':
            print("Aborted.")
            return False
    
    print("Generating step proposal...")
    
    # Show context info
    if baseline:
        print(f"  Using baseline snapshot from: {baseline.get('timestamp', 'unknown')}")
    if deviations and deviations.get("deviations"):
        print(f"  Known deviations: {len(deviations['deviations'])}")
    
    try:
        llm = get_llm_client()
    except RuntimeError as e:
        print(f"Error: {e}")
        return False
    
    prompt = build_propose_prompt(
        architecture, repo_yaml, state, external_state, baseline, deviations
    )
    
    try:
        response = llm.generate(prompt, "step_proposer")
    except RuntimeError as e:
        print(f"LLM error: {e}")
        return False
    
    # Clean up response - remove any markdown fences
    response = response.strip()
    if response.startswith("```"):
        lines = response.split("\n")
        # Remove first and last lines if they're fence markers
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        response = "\n".join(lines)
    
    # Validate it's valid YAML
    import yaml
    try:
        step_data = yaml.safe_load(response)
        if not isinstance(step_data, dict):
            raise ValueError("Response is not a YAML dictionary")
        if "step_id" not in step_data:
            raise ValueError("Missing step_id field")
    except Exception as e:
        print(f"Error: LLM returned invalid YAML: {e}")
        print("Raw response:")
        print(response)
        return False
    
    # Save the step
    step_path = get_file_path(STEP_YAML_FILE)
    step_path.write_text(response)
    
    print(f"\nProposed step written to: {step_path}")
    print(f"\nStep ID: {step_data.get('step_id')}")
    print(f"Type: {step_data.get('type')}")
    print(f"Goal: {step_data.get('goal', '').strip()[:100]}...")
    print(f"\nReview and edit {STEP_YAML_FILE} as needed, then run: wrapper compile")
    
    return True

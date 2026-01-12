"""
wrapper compile - Compile copilot_prompt.txt and verify.md from step.yaml.
"""

from wrapper.core.files import (
    load_architecture,
    load_repo_yaml,
    load_state,
    load_step_yaml,
    save_copilot_prompt,
    save_copilot_output,
    save_verify_md,
)
from wrapper.core.paths import get_file_path, STEP_YAML_FILE, ARCHITECTURE_FILE, REPO_YAML_FILE, COPILOT_OUTPUT_FILE
from wrapper.core.llm import get_llm_client


def check_required_files() -> bool:
    """Check if required files exist."""
    arch = load_architecture()
    repo = load_repo_yaml()
    step = load_step_yaml()
    
    missing = []
    if arch is None:
        missing.append(ARCHITECTURE_FILE)
    if repo is None:
        missing.append(REPO_YAML_FILE)
    if step is None:
        missing.append(STEP_YAML_FILE)
    
    if missing:
        print(f"Missing required files: {', '.join(missing)}")
        if STEP_YAML_FILE in missing:
            print("Run 'wrapper propose' first to create step.yaml")
        else:
            print("Run 'wrapper init' first to create templates")
        return False
    
    return True


def normalize_forbidden_item(item) -> str:
    """Convert forbidden item to string, handling both string and dict formats."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        # Handle format like {example: "description"}
        return str(list(item.values())[0]) if item else ""
    return str(item)


def build_compile_prompt(
    architecture: str,
    repo_yaml: dict,
    state: dict,
    step: dict
) -> str:
    """Build the LLM prompt for compiling Copilot prompt."""
    
    must_not = repo_yaml.get("must_not", [])
    must_not_str = "\n".join(f"- {normalize_forbidden_item(item)}" for item in must_not) if must_not else "- None specified"
    
    allowed_files = step.get("allowed_files", [])
    allowed_str = "\n".join(f"- {f}" for f in allowed_files) if allowed_files else "- None (verification only)"
    
    forbidden = step.get("forbidden", [])
    forbidden_str = "\n".join(f"- {normalize_forbidden_item(f)}" for f in forbidden) if forbidden else "- None specified"
    
    success = step.get("success_criteria", [])
    success_str = "\n".join(f"- {s}" for s in success) if success else "- None specified"
    
    invariants = state.get("invariants", [])
    invariants_str = "\n".join(f"- {i}" for i in invariants) if invariants else "- None established yet"
    
    prompt = f'''Generate a strict Copilot execution prompt based on this step definition.

ARCHITECTURE CONTEXT:
{architecture}

REPO:
- Name: {repo_yaml.get("repo_name")}
- Role: {repo_yaml.get("repo_role")}
- Repo-level MUST NOT:
{must_not_str}

CURRENT STATE:
- Completed steps: {len(state.get("done_steps", []))}
- Established invariants:
{invariants_str}

STEP TO COMPILE:
- ID: {step.get("step_id")}
- Type: {step.get("type")}
- Goal: {step.get("goal")}

ALLOWED FILES:
{allowed_str}

FORBIDDEN ACTIONS:
{forbidden_str}

SUCCESS CRITERIA:
{success_str}

IMPORTANT FOR VERIFICATION STEPS:
- DO NOT create analysis files (like .wrapper/analysis.md)
- Output your analysis directly in your response text
- The user will paste your response into copilot_output.txt
- No need for persistent documentation files

OUTPUT REQUIREMENTS:
Generate a Copilot prompt with this EXACT structure (no markdown, no code fences):

---------------------------------
REPO CONTEXT:
This is the [REPO_NAME] repo.
[Brief role description]

RULES (NON-NEGOTIABLE):
- You may ONLY modify the files listed below
- You may NOT refactor, move files, or add structure
- You must document findings, not implement missing functionality
- DO NOT create documentation files (output analysis in your response text)
[Add any other critical rules]

ALLOWED FILES:
[List each file]

FORBIDDEN:
[List each forbidden action - combine repo-level and step-level]

CURRENT STATE:
[Summarize what has been established]

TASK:
[Clear, imperative description of what to do]

SUCCESS:
[List success criteria]

If any rule must be violated, STOP and explain instead of coding.
---------------------------------

Generate the prompt now:'''

    return prompt


def build_verify_checklist(step: dict, repo_yaml: dict) -> str:
    """Build verify.md checklist content."""
    
    lines = [
        f"# Verification Checklist: {step.get('step_id')}",
        "",
        f"**Type:** {step.get('type')}",
        f"**Goal:** {step.get('goal', '').strip()}",
        "",
        "## Files Check",
        "",
        "Only these files may be modified:",
        ""
    ]
    
    allowed = step.get("allowed_files", [])
    if allowed:
        for f in allowed:
            lines.append(f"- [ ] `{f}`")
    else:
        lines.append("- [ ] No files should be modified (verification only)")
    
    lines.extend([
        "",
        "## Forbidden Actions Check",
        "",
        "None of these should be present:",
        ""
    ])
    
    # Combine repo-level and step-level forbidden
    forbidden = list(repo_yaml.get("must_not", []))
    forbidden.extend(step.get("forbidden", []))
    
    for f in forbidden:
        lines.append(f"- [ ] {normalize_forbidden_item(f)}")
    
    lines.extend([
        "",
        "## Success Criteria",
        ""
    ])
    
    success = step.get("success_criteria", [])
    for s in success:
        lines.append(f"- [ ] {s}")
    
    lines.extend([
        "",
        "## New Directories",
        "",
        "- [ ] No unexpected new directories created",
        "",
        "---",
        "",
        "*Run `wrapper verify` to automatically check these constraints.*"
    ])
    
    return "\n".join(lines)


def build_copilot_output_template(step: dict) -> str:
    """Build template for copilot_output.txt."""
    step_type = step.get("type", "unknown")
    step_id = step.get("step_id", "unknown")
    
    return f'''================================================================================
COPILOT OUTPUT FILE
================================================================================

Step: {step_id}
Type: {step_type}

INSTRUCTIONS:
After getting AI assistant's response, paste it below, save this file,
then run: wrapper verify

{"For VERIFICATION steps: Paste the analysis of repository state" if step_type == "verification" else "For IMPLEMENTATION steps: Paste description of changes made"}

================================================================================

[PASTE AI OUTPUT BELOW THIS LINE]

'''


def cmd_compile(args) -> bool:
    """Compile copilot_prompt.txt, verify.md, and copilot_output.txt template."""
    
    if not check_required_files():
        return False
    
    print("Loading configuration...")
    architecture = load_architecture()
    repo_yaml = load_repo_yaml()
    state = load_state()
    step = load_step_yaml()
    
    print(f"Compiling step: {step.get('step_id')}")
    
    # Generate Copilot prompt using LLM
    try:
        llm = get_llm_client()
    except RuntimeError as e:
        print(f"Error: {e}")
        return False
    
    prompt = build_compile_prompt(architecture, repo_yaml, state, step)
    
    print("Generating Copilot prompt...")
    try:
        copilot_prompt = llm.generate(prompt, "prompt_compiler")
    except RuntimeError as e:
        print(f"LLM error: {e}")
        return False
    
    # Clean up - remove markdown fences if present
    copilot_prompt = copilot_prompt.strip()
    if copilot_prompt.startswith("```"):
        lines = copilot_prompt.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        copilot_prompt = "\n".join(lines)
    
    # Generate verify.md checklist
    verify_content = build_verify_checklist(step, repo_yaml)
    
    # Generate copilot_output.txt template
    output_template = build_copilot_output_template(step)
    
    # Save outputs
    save_copilot_prompt(copilot_prompt)
    save_verify_md(verify_content)
    save_copilot_output(output_template)
    
    prompt_path = get_file_path("copilot_prompt.txt")
    verify_path = get_file_path("verify.md")
    output_path = get_file_path(COPILOT_OUTPUT_FILE)
    
    print(f"\nGenerated:")
    print(f"  - {prompt_path}")
    print(f"  - {verify_path}")
    print(f"  - {output_path}")
    print(f"\nNext steps:")
    print(f"  1. Copy contents of copilot_prompt.txt to Copilot")
    print(f"  2. Paste Copilot's response into copilot_output.txt")
    print(f"  3. Run: wrapper verify")
    
    return True

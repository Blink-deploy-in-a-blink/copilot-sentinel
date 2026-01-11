"""
wrapper sync-external - Sync external_state.json from other repos.

Reads state.json from other repos and aggregates into local external_state.json.
This is the ONLY way external_state.json should be populated.
"""

import json
from pathlib import Path
from typing import List

from wrapper.core.paths import get_file_path, WRAPPER_DIR, STATE_FILE
from wrapper.core.files import save_json_file


def extract_repo_state(repo_path: Path) -> dict:
    """
    Extract minimal state from another repo's .wrapper/state.json.
    
    Returns dict with:
        - done_steps: list of step summaries
        - invariants: list of invariants
    
    Raises:
        FileNotFoundError: if path doesn't exist
        ValueError: if state.json is missing or invalid
    """
    if not repo_path.exists():
        raise FileNotFoundError(f"Path does not exist: {repo_path}")
    
    if not repo_path.is_dir():
        raise ValueError(f"Path is not a directory: {repo_path}")
    
    wrapper_dir = repo_path / WRAPPER_DIR
    if not wrapper_dir.exists():
        raise ValueError(f"No .wrapper directory found in: {repo_path}")
    
    state_file = wrapper_dir / STATE_FILE
    if not state_file.exists():
        raise ValueError(f"No state.json found in: {wrapper_dir}")
    
    try:
        content = state_file.read_text(encoding='utf-8')
        state = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {state_file}: {e}")
    
    if not isinstance(state, dict):
        raise ValueError(f"state.json is not a dict in: {state_file}")
    
    # Extract repo name
    repo_name = state.get("repo")
    if not repo_name:
        # Fall back to directory name
        repo_name = repo_path.name
    
    # Extract done_steps summaries (just the result strings)
    done_steps = []
    for step in state.get("done_steps", []):
        if isinstance(step, dict):
            step_id = step.get("step_id", "unknown")
            result = step.get("result", "completed")
            done_steps.append(f"{step_id}: {result}")
        elif isinstance(step, str):
            done_steps.append(step)
    
    # Extract invariants (as-is)
    invariants = state.get("invariants", [])
    if not isinstance(invariants, list):
        invariants = []
    
    return {
        "repo_name": repo_name,
        "done_steps": done_steps,
        "invariants": invariants,
    }


def cmd_sync_external(args) -> bool:
    """Sync external_state.json from other repos."""
    
    from_paths: List[str] = args.from_paths
    
    if not from_paths:
        print("Error: No --from paths provided.")
        print("Usage: wrapper sync-external --from ../ui --from ../llm")
        return False
    
    print(f"Syncing external state from {len(from_paths)} repo(s)...")
    
    external_state = {}
    errors = []
    
    for path_str in from_paths:
        repo_path = Path(path_str).resolve()
        print(f"\n  Reading: {repo_path}")
        
        try:
            extracted = extract_repo_state(repo_path)
            repo_name = extracted["repo_name"]
            
            external_state[repo_name] = {
                "done_steps": extracted["done_steps"],
                "invariants": extracted["invariants"],
            }
            
            print(f"    Repo: {repo_name}")
            print(f"    Steps: {len(extracted['done_steps'])}")
            print(f"    Invariants: {len(extracted['invariants'])}")
            
        except FileNotFoundError as e:
            errors.append(str(e))
            print(f"    ERROR: {e}")
        except ValueError as e:
            errors.append(str(e))
            print(f"    ERROR: {e}")
    
    if not external_state:
        print("\nNo valid repos found. external_state.json NOT written.")
        return False
    
    # Write external_state.json
    output_path = get_file_path("external_state.json")
    save_json_file(output_path, external_state)
    
    print(f"\nWritten: {output_path}")
    print(f"Repos synced: {', '.join(external_state.keys())}")
    
    if errors:
        print(f"\nWarnings: {len(errors)} repo(s) had errors (see above)")
    
    return True

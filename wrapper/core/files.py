"""
File loading and saving utilities.
"""

import json
import yaml
from pathlib import Path
from typing import Optional, Any
from datetime import datetime

from wrapper.core.paths import (
    get_file_path,
    ensure_wrapper_dir,
    ARCHITECTURE_FILE,
    REPO_YAML_FILE,
    STEP_YAML_FILE,
    STATE_FILE,
    EXTERNAL_STATE_FILE,
    CONFIG_FILE,
)


def load_text_file(filepath: Path) -> Optional[str]:
    """Load a text file, return None if not found."""
    if filepath.exists():
        return filepath.read_text()
    return None


def load_yaml_file(filepath: Path) -> Optional[dict]:
    """Load a YAML file, return None if not found."""
    if filepath.exists():
        content = filepath.read_text()
        return yaml.safe_load(content) or {}
    return None


def load_json_file(filepath: Path) -> Optional[dict]:
    """Load a JSON file, return None if not found."""
    if filepath.exists():
        content = filepath.read_text()
        return json.loads(content)
    return None


def save_text_file(filepath: Path, content: str) -> None:
    """Save content to a text file."""
    ensure_wrapper_dir()
    filepath.write_text(content)


def save_yaml_file(filepath: Path, data: dict) -> None:
    """Save data to a YAML file."""
    ensure_wrapper_dir()
    content = yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)
    filepath.write_text(content)


def save_json_file(filepath: Path, data: dict) -> None:
    """Save data to a JSON file."""
    ensure_wrapper_dir()
    content = json.dumps(data, indent=2)
    filepath.write_text(content)


# Specific loaders

def load_architecture() -> Optional[str]:
    """Load architecture.md content."""
    return load_text_file(get_file_path(ARCHITECTURE_FILE))


def load_repo_yaml() -> Optional[dict]:
    """Load repo.yaml content."""
    return load_yaml_file(get_file_path(REPO_YAML_FILE))


def load_step_yaml() -> Optional[dict]:
    """Load step.yaml content."""
    return load_yaml_file(get_file_path(STEP_YAML_FILE))


def load_state() -> dict:
    """Load state.json, create default if missing."""
    state = load_json_file(get_file_path(STATE_FILE))
    if state is None:
        state = create_default_state()
        save_state(state)
    return state


def load_external_state() -> Optional[dict]:
    """Load external_state.json if exists."""
    return load_json_file(get_file_path(EXTERNAL_STATE_FILE))


def load_config() -> dict:
    """Load config.yaml, return empty dict if missing."""
    config = load_yaml_file(get_file_path(CONFIG_FILE))
    return config or {}


def create_default_state() -> dict:
    """Create default state.json structure."""
    repo_yaml = load_repo_yaml()
    repo_name = repo_yaml.get("repo_name", "unknown") if repo_yaml else "unknown"
    
    return {
        "repo": repo_name,
        "done_steps": [],
        "invariants": [],
        "last_verified": None
    }


def save_state(state: dict) -> None:
    """Save state.json."""
    save_json_file(get_file_path(STATE_FILE), state)


def save_step_yaml(step: dict) -> None:
    """Save step.yaml."""
    save_yaml_file(get_file_path(STEP_YAML_FILE), step)


def save_copilot_prompt(content: str) -> None:
    """Save copilot_prompt.txt."""
    save_text_file(get_file_path("copilot_prompt.txt"), content)


def save_verify_md(content: str) -> None:
    """Save verify.md."""
    save_text_file(get_file_path("verify.md"), content)


def save_repair_prompt(content: str) -> None:
    """Save repair_prompt.txt."""
    save_text_file(get_file_path("repair_prompt.txt"), content)


def save_diff(content: str) -> None:
    """Save diff.txt."""
    save_text_file(get_file_path("diff.txt"), content)


def add_done_step(step_id: str, result: str) -> None:
    """Add a completed step to state.json."""
    state = load_state()
    state["done_steps"].append({
        "step_id": step_id,
        "result": result,
        "timestamp": datetime.now().isoformat()
    })
    state["last_verified"] = datetime.now().isoformat()
    save_state(state)

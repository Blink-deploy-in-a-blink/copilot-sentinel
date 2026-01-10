"""
Core constants and path utilities.
"""

from pathlib import Path

# Directory name for wrapper files
WRAPPER_DIR = ".wrapper"

# Human-written input files
ARCHITECTURE_FILE = "architecture.md"
REPO_YAML_FILE = "repo.yaml"
STEP_YAML_FILE = "step.yaml"

# Machine-written state files
STATE_FILE = "state.json"
EXTERNAL_STATE_FILE = "external_state.json"
CONFIG_FILE = "config.yaml"

# Machine-generated output files
COPILOT_PROMPT_FILE = "copilot_prompt.txt"
VERIFY_FILE = "verify.md"
REPAIR_PROMPT_FILE = "repair_prompt.txt"
DIFF_FILE = "diff.txt"


def get_wrapper_dir() -> Path:
    """Get the .wrapper directory path relative to current working directory."""
    return Path.cwd() / WRAPPER_DIR


def get_file_path(filename: str) -> Path:
    """Get full path for a wrapper file."""
    return get_wrapper_dir() / filename


def ensure_wrapper_dir() -> Path:
    """Ensure .wrapper directory exists and return its path."""
    wrapper_dir = get_wrapper_dir()
    wrapper_dir.mkdir(exist_ok=True)
    return wrapper_dir

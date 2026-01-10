"""
Git utilities for wrapper.
"""

import subprocess
from pathlib import Path
from typing import List, Set


def run_git_command(args: List[str]) -> str:
    """
    Run a git command and return stdout.
    
    Raises:
        RuntimeError on git command failure
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git command failed: git {' '.join(args)}\n{e.stderr}")
    except FileNotFoundError:
        raise RuntimeError("Git not found. Please install git.")


def get_diff(staged_only: bool = False) -> str:
    """
    Get git diff.
    
    Args:
        staged_only: If True, only staged changes. Otherwise all uncommitted.
    
    Returns:
        Diff output as string
    """
    if staged_only:
        return run_git_command(["diff", "--cached"])
    else:
        return run_git_command(["diff", "HEAD"])


def get_changed_files(staged_only: bool = False) -> Set[str]:
    """
    Get set of changed file paths.
    
    Args:
        staged_only: If True, only staged changes. Otherwise all uncommitted.
    
    Returns:
        Set of relative file paths that changed
    """
    if staged_only:
        output = run_git_command(["diff", "--cached", "--name-only"])
    else:
        output = run_git_command(["diff", "HEAD", "--name-only"])
    
    files = set()
    for line in output.strip().split("\n"):
        if line:
            files.add(line)
    return files


def get_new_directories(staged_only: bool = False) -> Set[str]:
    """
    Get set of newly created directories.
    
    Returns:
        Set of directory paths that are new
    """
    changed = get_changed_files(staged_only)
    
    # Find directories that contain new files
    new_dirs = set()
    for filepath in changed:
        parts = Path(filepath).parts
        for i in range(1, len(parts)):
            dir_path = "/".join(parts[:i])
            # Check if this directory is new (not in HEAD)
            try:
                run_git_command(["cat-file", "-e", f"HEAD:{dir_path}"])
            except RuntimeError:
                # Directory doesn't exist in HEAD, it's new
                new_dirs.add(dir_path)
    
    return new_dirs


def is_git_repo() -> bool:
    """Check if current directory is a git repository."""
    try:
        run_git_command(["rev-parse", "--git-dir"])
        return True
    except RuntimeError:
        return False


def get_repo_root() -> Path:
    """Get the root directory of the git repository."""
    output = run_git_command(["rev-parse", "--show-toplevel"])
    return Path(output.strip())

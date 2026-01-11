"""
wrapper snapshot - Capture baseline snapshot of repository.

Scans repository filesystem and creates baseline_snapshot.json.
Auto-triggered on first verification, but can be run manually.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Set, Dict, List, Any

from wrapper.core.files import save_baseline_snapshot, load_baseline_snapshot
from wrapper.core.paths import get_file_path, get_wrapper_dir, BASELINE_SNAPSHOT_FILE
from wrapper.core.git import run_git_command, is_git_repo


# Directories to exclude from scanning
EXCLUDED_DIRS: Set[str] = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    ".wrapper",
    "dist",
    "build",
    ".next",
    "coverage",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".eggs",
    "*.egg-info",
    ".cache",
}

# File patterns to exclude
EXCLUDED_FILES: Set[str] = {
    ".DS_Store",
    "Thumbs.db",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.dylib",
}

# Key files to check for presence
KEY_FILES: List[str] = [
    "package.json",
    "Dockerfile",
    "docker-compose.yml",
    "README.md",
    "README",
    "requirements.txt",
    "setup.py",
    "pyproject.toml",
    "Makefile",
    "tsconfig.json",
    ".gitignore",
    "go.mod",
    "Cargo.toml",
]


def should_exclude_dir(name: str) -> bool:
    """Check if directory should be excluded."""
    # Exclude hidden directories
    if name.startswith("."):
        return True
    # Check against excluded set
    return name in EXCLUDED_DIRS


def should_exclude_file(name: str) -> bool:
    """Check if file should be excluded."""
    if name.startswith("."):
        return False  # Allow hidden files like .gitignore
    for pattern in EXCLUDED_FILES:
        if pattern.startswith("*"):
            if name.endswith(pattern[1:]):
                return True
        elif name == pattern:
            return True
    return False


def scan_repository(root_path: Path) -> Dict[str, Any]:
    """
    Scan repository and return snapshot data.
    
    Args:
        root_path: Root directory to scan
    
    Returns:
        Dictionary with snapshot data
    """
    directories: List[str] = []
    files: List[str] = []
    file_types: Dict[str, int] = {}
    
    for dirpath, dirnames, filenames in os.walk(root_path):
        # Filter out excluded directories (modifies dirnames in-place)
        dirnames[:] = [d for d in dirnames if not should_exclude_dir(d)]
        
        # Get relative path from root
        rel_dir = os.path.relpath(dirpath, root_path)
        
        # Add directory (skip root ".")
        if rel_dir != ".":
            # Normalize to forward slashes
            directories.append(rel_dir.replace(os.sep, "/"))
        
        # Process files
        for filename in filenames:
            if should_exclude_file(filename):
                continue
            
            if rel_dir == ".":
                rel_file = filename
            else:
                rel_file = f"{rel_dir}/{filename}".replace(os.sep, "/")
            
            files.append(rel_file)
            
            # Count file types by extension
            ext = Path(filename).suffix.lower()
            if ext:
                file_types[ext] = file_types.get(ext, 0) + 1
            else:
                file_types["(no extension)"] = file_types.get("(no extension)", 0) + 1
    
    # Sort for consistency
    directories.sort()
    files.sort()
    
    # Sort file types by count (descending)
    file_types = dict(sorted(file_types.items(), key=lambda x: -x[1]))
    
    return {
        "directories": directories,
        "files": files,
        "file_types": file_types,
        "total_files": len(files),
        "total_directories": len(directories),
    }


def check_key_files(root_path: Path, files: List[str]) -> Dict[str, bool]:
    """Check which key files are present."""
    files_set = set(files)
    result = {}
    for key_file in KEY_FILES:
        result[key_file] = key_file in files_set
    return result


def get_git_status() -> Dict[str, Any]:
    """Get current git branch and last commit."""
    try:
        branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"]).strip()
        commit_hash = run_git_command(["rev-parse", "--short", "HEAD"]).strip()
        return {
            "branch": branch,
            "last_commit_hash": commit_hash,
        }
    except RuntimeError:
        return {
            "branch": "unknown",
            "last_commit_hash": "unknown",
        }


def capture_baseline_snapshot() -> Dict[str, Any]:
    """
    Capture complete baseline snapshot of repository.
    
    Returns:
        Complete snapshot dictionary
    """
    # Use current working directory as root
    root_path = Path.cwd()
    
    # Scan repository
    scan_data = scan_repository(root_path)
    
    # Build snapshot
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_files": scan_data["total_files"],
            "total_directories": scan_data["total_directories"],
            "file_types": scan_data["file_types"],
        },
        "directories": scan_data["directories"],
        "files": scan_data["files"],
        "key_files_present": check_key_files(root_path, scan_data["files"]),
        "git_status": get_git_status(),
    }
    
    return snapshot


def cmd_snapshot(args) -> bool:
    """Capture baseline snapshot manually."""
    
    print("Capturing baseline snapshot...")
    
    snapshot = capture_baseline_snapshot()
    save_baseline_snapshot(snapshot)
    
    output_path = get_file_path(BASELINE_SNAPSHOT_FILE)
    
    print(f"\nBaseline snapshot captured: {output_path}")
    print(f"\nSummary:")
    print(f"  Timestamp: {snapshot['timestamp']}")
    print(f"  Total files: {snapshot['summary']['total_files']}")
    print(f"  Total directories: {snapshot['summary']['total_directories']}")
    
    print(f"\nFile types:")
    for ext, count in list(snapshot['summary']['file_types'].items())[:10]:
        print(f"    {ext}: {count}")
    if len(snapshot['summary']['file_types']) > 10:
        print(f"    ... and {len(snapshot['summary']['file_types']) - 10} more")
    
    print(f"\nGit status:")
    print(f"    Branch: {snapshot['git_status']['branch']}")
    print(f"    Commit: {snapshot['git_status']['last_commit_hash']}")
    
    # Show key files
    present = [k for k, v in snapshot['key_files_present'].items() if v]
    if present:
        print(f"\nKey files found: {', '.join(present)}")
    
    return True

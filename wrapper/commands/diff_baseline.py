"""
wrapper diff-baseline - Compare current repo state against baseline snapshot.

Shows what has changed since baseline was captured.
"""

from datetime import datetime
from typing import Set, List, Dict, Any

from wrapper.core.files import load_baseline_snapshot
from wrapper.core.paths import get_file_path, BASELINE_SNAPSHOT_FILE
from wrapper.commands.snapshot import capture_baseline_snapshot


def cmd_diff_baseline(args) -> bool:
    """Compare current repository against baseline snapshot."""
    
    # Load baseline
    baseline = load_baseline_snapshot()
    if baseline is None:
        print(f"Error: No baseline snapshot found.")
        print(f"Run 'wrapper snapshot' or 'wrapper verify' (first time) to create one.")
        return False
    
    baseline_time = baseline.get("timestamp", "unknown")
    print(f"Comparing against baseline from {baseline_time}")
    print()
    
    # Capture current state
    current = capture_baseline_snapshot()
    
    # Compare directories
    baseline_dirs = set(baseline.get("directories", []))
    current_dirs = set(current.get("directories", []))
    
    new_dirs = sorted(current_dirs - baseline_dirs)
    removed_dirs = sorted(baseline_dirs - current_dirs)
    
    # Compare files
    baseline_files = set(baseline.get("files", []))
    current_files = set(current.get("files", []))
    
    new_files = sorted(current_files - baseline_files)
    removed_files = sorted(baseline_files - current_files)
    
    # Compare file type counts
    baseline_types = baseline.get("summary", {}).get("file_types", {})
    current_types = current.get("summary", {}).get("file_types", {})
    
    # Check if anything changed
    has_changes = new_dirs or removed_dirs or new_files or removed_files
    
    if not has_changes:
        print("NO CHANGES DETECTED")
        print()
        print("Repository matches baseline snapshot.")
        return True
    
    print("CHANGES DETECTED:")
    print()
    
    # New files
    if new_files:
        print(f"New files ({len(new_files)}):")
        for f in new_files[:20]:
            print(f"  + {f}")
        if len(new_files) > 20:
            print(f"  ... and {len(new_files) - 20} more")
        print()
    
    # Removed files
    if removed_files:
        print(f"Removed files ({len(removed_files)}):")
        for f in removed_files[:20]:
            print(f"  - {f}")
        if len(removed_files) > 20:
            print(f"  ... and {len(removed_files) - 20} more")
        print()
    
    # New directories
    if new_dirs:
        print(f"New directories ({len(new_dirs)}):")
        for d in new_dirs[:10]:
            print(f"  + {d}/")
        if len(new_dirs) > 10:
            print(f"  ... and {len(new_dirs) - 10} more")
        print()
    
    # Removed directories
    if removed_dirs:
        print(f"Removed directories ({len(removed_dirs)}):")
        for d in removed_dirs[:10]:
            print(f"  - {d}/")
        if len(removed_dirs) > 10:
            print(f"  ... and {len(removed_dirs) - 10} more")
        print()
    
    # Summary
    baseline_file_count = baseline.get("summary", {}).get("total_files", 0)
    current_file_count = current.get("summary", {}).get("total_files", 0)
    baseline_dir_count = baseline.get("summary", {}).get("total_directories", 0)
    current_dir_count = current.get("summary", {}).get("total_directories", 0)
    
    file_diff = current_file_count - baseline_file_count
    dir_diff = current_dir_count - baseline_dir_count
    
    print("Summary:")
    file_change = f"+{file_diff}" if file_diff >= 0 else str(file_diff)
    dir_change = f"+{dir_diff}" if dir_diff >= 0 else str(dir_diff)
    print(f"  Files: {baseline_file_count} → {current_file_count} ({file_change})")
    print(f"  Directories: {baseline_dir_count} → {current_dir_count} ({dir_change})")
    
    # File type changes
    all_types = set(baseline_types.keys()) | set(current_types.keys())
    type_changes = []
    for ext in all_types:
        old_count = baseline_types.get(ext, 0)
        new_count = current_types.get(ext, 0)
        if old_count != new_count:
            diff = new_count - old_count
            type_changes.append((ext, old_count, new_count, diff))
    
    if type_changes:
        print()
        print("File type changes:")
        # Sort by absolute difference
        type_changes.sort(key=lambda x: -abs(x[3]))
        for ext, old, new, diff in type_changes[:5]:
            diff_str = f"+{diff}" if diff >= 0 else str(diff)
            print(f"  {ext}: {old} → {new} ({diff_str})")
    
    return True

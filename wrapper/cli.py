#!/usr/bin/env python3
"""
wrapper - Prompt Compiler + Verifier for Copilot-based coding.

A strict, boring CLI tool that:
1. Proposes next steps based on architecture
2. Compiles strict Copilot prompts
3. Verifies git diffs against constraints
4. Maintains explicit state
"""

import argparse
import sys
from pathlib import Path

from wrapper.commands.propose import cmd_propose
from wrapper.commands.compile import cmd_compile
from wrapper.commands.verify import cmd_verify
from wrapper.commands.accept import cmd_accept
from wrapper.commands.init import cmd_init
from wrapper.commands.sync_external import cmd_sync_external
from wrapper.commands.snapshot import cmd_snapshot
from wrapper.commands.diff_baseline import cmd_diff_baseline
from wrapper.commands.plan import cmd_plan_init, cmd_plan_status, cmd_plan_show
from wrapper.commands.test import cmd_test


def get_version():
    """Read version from VERSION file."""
    try:
        version_file = Path(__file__).parent.parent / "VERSION"
        return version_file.read_text(encoding='utf-8').strip()
    except:
        return "unknown"


def main():
    parser = argparse.ArgumentParser(
        prog="wrapper",
        description="AI-assisted development with architectural guardrails"
    )
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'wrapper v{get_version()}'
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize .wrapper directory with templates")
    init_parser.set_defaults(func=cmd_init)

    # propose command
    propose_parser = subparsers.add_parser("propose", help="Propose next step.yaml")
    propose_parser.add_argument(
        "--no-plan",
        action="store_false",
        dest="from_plan",
        help="Ignore implementation plan if it exists"
    )
    propose_parser.set_defaults(func=cmd_propose)

    # compile command
    compile_parser = subparsers.add_parser("compile", help="Compile copilot_prompt.txt and verify.md")
    compile_parser.set_defaults(func=cmd_compile)

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Verify git diff against constraints")
    verify_parser.add_argument(
        "--staged",
        action="store_true",
        help="Check only staged changes (default: all uncommitted)"
    )
    verify_parser.add_argument(
        "--check-logic",
        action="store_true",
        help="Verify implementation logic against features checklist"
    )
    verify_parser.set_defaults(func=cmd_verify)

    # accept command
    accept_parser = subparsers.add_parser("accept", help="Accept verified step into state")
    accept_parser.set_defaults(func=cmd_accept)

    # sync-external command
    sync_parser = subparsers.add_parser(
        "sync-external",
        help="Sync external_state.json from other repos"
    )
    sync_parser.add_argument(
        "--from",
        dest="from_paths",
        action="append",
        required=True,
        metavar="PATH",
        help="Path to another repo (can specify multiple times)"
    )
    sync_parser.set_defaults(func=cmd_sync_external)

    # snapshot command
    snapshot_parser = subparsers.add_parser(
        "snapshot",
        help="Capture baseline snapshot of repository (usually auto-captured)"
    )
    snapshot_parser.set_defaults(func=cmd_snapshot)

    # diff-baseline command
    diff_baseline_parser = subparsers.add_parser(
        "diff-baseline",
        help="Compare current repo state against baseline snapshot"
    )
    diff_baseline_parser.set_defaults(func=cmd_diff_baseline)

    # plan command (NEW)
    plan_parser = subparsers.add_parser("plan", help="Interactive implementation planning")
    plan_subparsers = plan_parser.add_subparsers(dest="plan_command")
    
    # plan init
    plan_init_parser = plan_subparsers.add_parser("init", help="Create implementation plan interactively")
    plan_init_parser.set_defaults(func=cmd_plan_init)
    
    # plan status
    plan_status_parser = plan_subparsers.add_parser("status", help="Show plan progress")
    plan_status_parser.set_defaults(func=cmd_plan_status)
    
    # plan show
    plan_show_parser = plan_subparsers.add_parser("show", help="Show plan visualization")
    plan_show_parser.set_defaults(func=cmd_plan_show)
    
    # Default to status if just "wrapper plan"
    plan_parser.set_defaults(func=cmd_plan_status)

    # test command (NEW)
    test_parser = subparsers.add_parser(
        "test",
        help="Test implemented features against plan"
    )
    test_parser.add_argument(
        "--step",
        help="Test specific step by ID",
        type=str
    )
    test_parser.set_defaults(func=cmd_test)

    args = parser.parse_args()
    
    try:
        result = args.func(args)
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

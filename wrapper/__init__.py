"""
wrapper - Prompt Compiler + Verifier for Copilot-based coding.

A strict, boring CLI tool that enforces architectural discipline.
"""

import os as _os

from wrapper.cli import main

# Read version from VERSION file at repo root to stay in sync with setup.py
_version_file = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "VERSION")
try:
    with open(_version_file, "r", encoding="utf-8") as _f:
        __version__ = _f.read().strip()
except FileNotFoundError:
    __version__ = "0.0.0"

__all__ = ["main"]

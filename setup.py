#!/usr/bin/env python3
"""
Setup script for wrapper CLI tool.
"""

from setuptools import setup, find_packages

# Read version from VERSION file
with open("VERSION", "r", encoding="utf-8") as f:
    version = f.read().strip()

setup(
    name="wrapper",
    version=version,
    description="AI-assisted development with architectural guardrails",
    author="Blink Deploy",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "PyYAML>=6.0",
    ],
    entry_points={
        "console_scripts": [
            "wrapper=wrapper:main",
        ],
    },
)

#!/usr/bin/env python3
"""
Setup script for wrapper CLI tool.
"""

from setuptools import setup, find_packages

setup(
    name="wrapper",
    version="0.1.0",
    description="Prompt Compiler + Verifier for Copilot-based coding",
    author="Your Name",
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

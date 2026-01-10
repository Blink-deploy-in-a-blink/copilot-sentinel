"""
wrapper init - Initialize .wrapper directory with templates.
"""

from pathlib import Path
from wrapper.core.paths import (
    ensure_wrapper_dir,
    get_file_path,
    ARCHITECTURE_FILE,
    REPO_YAML_FILE,
    CONFIG_FILE,
)


ARCHITECTURE_TEMPLATE = '''# Architecture: {repo_name}

## Overview

Describe the TARGET architecture for this repository.
This is future-facing - what the repo SHOULD look like.

## Components

List the main components and their responsibilities.

## Boundaries

### This repo MUST:
- (list responsibilities)

### This repo MUST NOT:
- (list forbidden things)

## File Structure

Describe expected file organization.

## Known Deviations

List any current deviations from target architecture that are acknowledged
and will be addressed later. The verifier will allow these.

- None (baseline clean)

## Integration Points

How this repo interacts with other repos.
'''

REPO_YAML_TEMPLATE = '''# Repository Configuration
# This file defines the role and constraints for this repository.

repo_name: {repo_name}
repo_role: |
  Describe the core purpose of this repository in 1-2 sentences.

# Hard constraints - things this repo must NEVER do
must_not:
  - example: expose HTTP APIs (if not an API repo)
  - example: contain UI logic (if not a UI repo)
  - example: directly access database (if using a service layer)

# Dependencies - other repos this one interacts with
depends_on: []
  # - repo: ui
  #   via: REST API
  # - repo: llm
  #   via: function calls
'''

CONFIG_TEMPLATE = '''# Wrapper Configuration
# LLM settings - environment variables take precedence

# LLM provider: deepseek, openai, or anthropic
llm_provider: deepseek

# API keys (prefer environment variables for security)
# deepseek_api_key: your-key-here
# openai_api_key: your-key-here
# anthropic_api_key: your-key-here

# Model overrides (optional)
# deepseek_model: deepseek-chat
# openai_model: gpt-4o
# anthropic_model: claude-sonnet-4-20250514
'''


def cmd_init(args) -> bool:
    """Initialize .wrapper directory with template files."""
    
    wrapper_dir = ensure_wrapper_dir()
    print(f"Initializing {wrapper_dir}/")
    
    # Infer repo name from directory
    repo_name = Path.cwd().name
    
    # Create architecture.md if missing
    arch_path = get_file_path(ARCHITECTURE_FILE)
    if arch_path.exists():
        print(f"  {ARCHITECTURE_FILE} already exists, skipping")
    else:
        arch_path.write_text(ARCHITECTURE_TEMPLATE.format(repo_name=repo_name))
        print(f"  Created {ARCHITECTURE_FILE}")
    
    # Create repo.yaml if missing
    repo_path = get_file_path(REPO_YAML_FILE)
    if repo_path.exists():
        print(f"  {REPO_YAML_FILE} already exists, skipping")
    else:
        repo_path.write_text(REPO_YAML_TEMPLATE.format(repo_name=repo_name))
        print(f"  Created {REPO_YAML_FILE}")
    
    # Create config.yaml if missing
    config_path = get_file_path(CONFIG_FILE)
    if config_path.exists():
        print(f"  {CONFIG_FILE} already exists, skipping")
    else:
        config_path.write_text(CONFIG_TEMPLATE)
        print(f"  Created {CONFIG_FILE}")
    
    print()
    print("Next steps:")
    print(f"  1. Edit {wrapper_dir}/{ARCHITECTURE_FILE} with your target architecture")
    print(f"  2. Edit {wrapper_dir}/{REPO_YAML_FILE} with repo constraints")
    print(f"  3. Set DEEPSEEK_API_KEY environment variable (or edit config.yaml)")
    print(f"  4. Run: wrapper propose")
    
    return True

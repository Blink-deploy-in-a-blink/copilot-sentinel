"""
wrapper init - Initialize .wrapper directory with templates.
"""

from pathlib import Path
from typing import Optional
from wrapper.core.paths import (
    ensure_wrapper_dir,
    get_file_path,
    ARCHITECTURE_FILE,
    REPO_YAML_FILE,
    CONFIG_FILE,
)
from wrapper.core.cli_helpers import ask_text, ask_yes_no
from wrapper.core.llm import get_llm_client


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
    
    # Check for --guided flag
    if hasattr(args, 'guided') and args.guided:
        return cmd_init_guided(args)
    
    # Original non-guided behavior
    return cmd_init_basic(args)


def cmd_init_basic(args) -> bool:
    """Initialize .wrapper directory with template files (non-guided)."""
    
    wrapper_dir = ensure_wrapper_dir()
    print(f"Initializing {wrapper_dir}/")
    
    # Infer repo name from directory
    repo_name = Path.cwd().name
    
    # Create architecture.md if missing
    arch_path = get_file_path(ARCHITECTURE_FILE)
    if arch_path.exists():
        print(f"  {ARCHITECTURE_FILE} already exists, skipping")
    else:
        arch_path.write_text(ARCHITECTURE_TEMPLATE.format(repo_name=repo_name), encoding='utf-8')
        print(f"  Created {ARCHITECTURE_FILE}")
    
    # Create repo.yaml if missing
    repo_path = get_file_path(REPO_YAML_FILE)
    if repo_path.exists():
        print(f"  {REPO_YAML_FILE} already exists, skipping")
    else:
        repo_path.write_text(REPO_YAML_TEMPLATE.format(repo_name=repo_name), encoding='utf-8')
        print(f"  Created {REPO_YAML_FILE}")
    
    # Create config.yaml if missing
    config_path = get_file_path(CONFIG_FILE)
    if config_path.exists():
        print(f"  {CONFIG_FILE} already exists, skipping")
    else:
        config_path.write_text(CONFIG_TEMPLATE, encoding='utf-8')
        print(f"  Created {CONFIG_FILE}")
    
    print()
    print("Next steps:")
    print(f"  1. Edit {wrapper_dir}/{ARCHITECTURE_FILE} with your target architecture")
    print(f"  2. Edit {wrapper_dir}/{REPO_YAML_FILE} with repo constraints")
    print(f"  3. Set DEEPSEEK_API_KEY environment variable (or edit config.yaml)")
    print(f"  4. Run: wrapper propose")
    
    return True


def cmd_init_guided(args) -> bool:
    """Guided initialization with LLM assistance."""
    
    wrapper_dir = ensure_wrapper_dir()
    repo_name = Path.cwd().name
    
    # Check if files already exist
    arch_path = get_file_path(ARCHITECTURE_FILE)
    repo_path = get_file_path(REPO_YAML_FILE)
    config_path = get_file_path(CONFIG_FILE)
    
    # Create config.yaml first if it doesn't exist
    if not config_path.exists():
        config_path.write_text(CONFIG_TEMPLATE, encoding='utf-8')
        print(f"✅ Created {CONFIG_FILE}")
        print()
    
    # Check if API key is configured (required for guided mode)
    try:
        llm = get_llm_client()
    except RuntimeError as e:
        print("❌ Guided mode requires an LLM API key to be configured.")
        print()
        print(str(e))
        print()
        print(f"After setting your API key, run: wrapper init --guided")
        return False
    
    if arch_path.exists() or repo_path.exists():
        print(f"⚠️  {ARCHITECTURE_FILE} or {REPO_YAML_FILE} already exist!")
        if not ask_yes_no("Overwrite existing files?", default=False):
            print("Aborted.")
            return False
    
    print("🤖 Guided Repository Setup")
    print("=" * 60)
    print("I'll ask questions about your repository and help generate")
    print(f"proper {ARCHITECTURE_FILE} and {REPO_YAML_FILE} files.")
    print()
    print("Tip: Be specific and detailed in your answers.")
    print("=" * 60)
    print()
    
    # Step 1: Gather user inputs
    print("📋 ARCHITECTURE QUESTIONS")
    print("-" * 60)
    
    answers = {}
    
    answers['purpose'] = ask_text(
        "1/7: What is the PRIMARY PURPOSE of this repository?\n"
        "    (What problem does it solve? What is its main goal?)"
    )
    
    answers['components'] = ask_text(
        "2/7: What are the MAIN COMPONENTS or modules?\n"
        "    (e.g., API server, database layer, CLI tool, etc.)"
    )
    
    answers['must_do'] = ask_text(
        "3/7: What are the CORE RESPONSIBILITIES this repo MUST handle?\n"
        "    (List the things this repo is responsible for)"
    )
    
    answers['must_not'] = ask_text(
        "4/7: What should this repo NEVER do?\n"
        "    (List forbidden actions or out-of-scope concerns)"
    )
    
    answers['integrations'] = ask_text(
        "5/7: How does this repo interact with OTHER SYSTEMS or repos?\n"
        "    (APIs, databases, external services, etc.)",
        optional=True
    )
    
    print()
    print("📋 REPOSITORY CONFIGURATION QUESTIONS")
    print("-" * 60)
    
    answers['role'] = ask_text(
        "6/7: Describe the repository's ROLE in 1-2 sentences\n"
        "    (A concise summary of what this repo does)"
    )
    
    answers['constraints'] = ask_text(
        "7/7: List HARD CONSTRAINTS (things this repo must NEVER do)\n"
        "    (Separate multiple items with commas, or press Enter to skip)",
        optional=True
    )
    
    # Step 2: Use LLM to format sections
    print()
    print("🤖 Processing your answers with AI...")
    print()
    
    try:
        formatted = {}
        formatted['overview'] = format_with_llm(llm, answers['purpose'], "overview")
        formatted['components'] = format_with_llm(llm, answers['components'], "components")
        formatted['must_do'] = format_with_llm(llm, answers['must_do'], "must_list")
        formatted['must_not'] = format_with_llm(llm, answers['must_not'], "must_not_list")
        formatted['integrations'] = format_with_llm(llm, answers['integrations'] or "No external integrations.", "integrations")
        formatted['role'] = format_with_llm(llm, answers['role'], "role")
        
        # Parse constraints for YAML
        if answers.get('constraints'):
            formatted['constraints_list'] = parse_comma_list(answers['constraints'])
        else:
            formatted['constraints_list'] = []
        
    except Exception as e:
        print(f"❌ Error calling LLM: {e}")
        print()
        print("Falling back to non-guided init...")
        return cmd_init_basic(args)
    
    # Step 3: Preview generated content
    print("✅ Generated content preview:")
    print()
    print("=" * 60)
    print(f"📄 {ARCHITECTURE_FILE}")
    print("=" * 60)
    print(build_architecture_content(formatted, repo_name, answers))
    print()
    print("=" * 60)
    print(f"📄 {REPO_YAML_FILE}")
    print("=" * 60)
    print(build_repo_yaml_content(formatted, repo_name, answers))
    print("=" * 60)
    print()
    
    # Step 4: Confirm
    if not ask_yes_no("Create files with this content?", default=True):
        print("Aborted. Run 'wrapper init --guided' again to retry.")
        return False
    
    # Step 5: Write files
    arch_path.write_text(build_architecture_content(formatted, repo_name, answers), encoding='utf-8')
    print(f"✅ Created {ARCHITECTURE_FILE}")
    
    repo_path.write_text(build_repo_yaml_content(formatted, repo_name, answers), encoding='utf-8')
    print(f"✅ Created {REPO_YAML_FILE}")
    
    # Config was already created at the beginning
    
    print()
    print("🎉 Setup complete!")
    print()
    print("Next steps:")
    print(f"  1. Review and refine {wrapper_dir}/{ARCHITECTURE_FILE}")
    print(f"  2. Review and refine {wrapper_dir}/{REPO_YAML_FILE}")
    print(f"  3. Run: wrapper propose")
    
    return True


def format_with_llm(llm, user_input: str, section_type: str) -> str:
    """Use LLM to format user input for a specific section."""
    
    prompt_templates = {
        "overview": (
            "Format this repository purpose into a clear, professional overview paragraph (2-4 sentences).\n\n"
            "CRITICAL: Format ONLY what the user provided. DO NOT add examples, suggestions, or invented content.\n"
            "Use ONLY the user's words and meaning.\n\n"
            "User input:\n{input}\n\n"
            "Output only the formatted paragraph, no extra commentary."
        ),
        "components": (
            "Format this into a clear bulleted list of components with their responsibilities. "
            "Use this format:\n"
            "- **Component Name**: Brief description of what it does\n\n"
            "CRITICAL: Format ONLY what the user provided. DO NOT add examples, suggestions, or invented components.\n"
            "Use ONLY the user's words and meaning.\n\n"
            "User input:\n{input}\n\n"
            "Output only the bulleted list, no extra commentary."
        ),
        "must_list": (
            "Format this into a clear bulleted list of core responsibilities. "
            "Each item should be a clear, actionable responsibility.\n\n"
            "CRITICAL: Format ONLY what the user provided. DO NOT add examples, suggestions, or invented responsibilities.\n"
            "Use ONLY the user's words and meaning.\n\n"
            "Input:\n{input}\n\n"
            "Output only the bulleted list with '- ' prefix, no extra commentary."
        ),
        "must_not_list": (
            "Format this into a clear bulleted list of forbidden actions or out-of-scope concerns. "
            "Each item should be a clear prohibition.\n\n"
            "CRITICAL: Format ONLY what the user provided. DO NOT add examples, suggestions, or invented prohibitions.\n"
            "Use ONLY the user's words and meaning.\n\n"
            "User input:\n{input}\n\n"
            "Output only the bulleted list with '- ' prefix, no extra commentary."
        ),
        "integrations": (
            "Format this into a clear description of how this repository integrates with external systems. "
            "Use bullet points if multiple integrations exist.\n\n"
            "CRITICAL: Format ONLY what the user provided. DO NOT add examples, suggestions, or invented integrations.\n"
            "Use ONLY the user's words and meaning.\n\n"
            "User input:\n{input}\n\n"
            "Output only the formatted text, no extra commentary."
        ),
        "role": (
            "Refine this repository role description to be clear and concise (1-2 sentences). "
            "Make it professional but keep the original meaning.\n\n"
            "CRITICAL: Format ONLY what the user provided. DO NOT add examples, suggestions, or invented content.\n"
            "Use ONLY the user's words and meaning.\n\n"
            "User input:\n{input}\n\n"
            "Output only the refined text, no extra commentary."
        ),
    }
    
    prompt = prompt_templates[section_type].format(input=user_input)
    response = llm.generate(prompt, "guided_init_helper")
    return response.strip()


def parse_comma_list(text: str) -> list:
    """Parse comma-separated text into a list of items."""
    if not text:
        return []
    items = [item.strip() for item in text.split(',')]
    return [item for item in items if item]


def build_architecture_content(formatted: dict, repo_name: str, raw_answers: dict = None) -> str:
    """Build the architecture.md content from formatted sections."""
    
    # Add raw answers as HTML comments for reference
    raw_section = ""
    if raw_answers:
        raw_section = "<!--\n"
        raw_section += "RAW USER ANSWERS (for reference if you need to regenerate):\n\n"
        raw_section += f"Purpose: {raw_answers.get('purpose', 'N/A')}\n\n"
        raw_section += f"Components: {raw_answers.get('components', 'N/A')}\n\n"
        raw_section += f"Must Do: {raw_answers.get('must_do', 'N/A')}\n\n"
        raw_section += f"Must Not: {raw_answers.get('must_not', 'N/A')}\n\n"
        raw_section += f"Integrations: {raw_answers.get('integrations', 'N/A')}\n"
        raw_section += "-->\n\n"
    
    return f'''{raw_section}# Architecture: {repo_name}

## Overview

{formatted['overview']}

## Components

{formatted['components']}

## Boundaries

### This repo MUST:
{formatted['must_do']}

### This repo MUST NOT:
{formatted['must_not']}

## File Structure

(To be documented as the project evolves)

## Known Deviations

List any current deviations from target architecture that are acknowledged
and will be addressed later. The verifier will allow these.

- None (baseline clean)

## Integration Points

{formatted['integrations']}
'''


def build_repo_yaml_content(formatted: dict, repo_name: str, raw_answers: dict = None) -> str:
    """Build the repo.yaml content from formatted sections."""
    
    # Build must_not list
    if formatted['constraints_list']:
        must_not_items = '\n'.join([f"  - {item}" for item in formatted['constraints_list']])
    else:
        must_not_items = "  # Add constraints as needed"
    
    # Add raw answers as YAML comments for reference
    raw_section = ""
    if raw_answers:
        raw_section = "# RAW USER ANSWERS (for reference if you need to regenerate):\n"
        raw_section += f"# Role: {raw_answers.get('role', 'N/A')}\n"
        raw_section += f"# Constraints: {raw_answers.get('constraints', 'N/A')}\n\n"
    
    return f'''{raw_section}# Repository Configuration
# This file defines the role and constraints for this repository.

repo_name: {repo_name}
repo_role: |
  {formatted['role']}

# Hard constraints - things this repo must NEVER do
must_not:
{must_not_items}

# Dependencies - other repos this one interacts with
depends_on: []
  # - repo: other-repo-name
  #   via: REST API / function calls / etc
'''


def cmd_init(args) -> bool:
    """Initialize .wrapper directory with template files."""
    
    # Check for --guided flag
    if hasattr(args, 'guided') and args.guided:
        return cmd_init_guided(args)
    
    # Original non-guided behavior
    return cmd_init_basic(args)

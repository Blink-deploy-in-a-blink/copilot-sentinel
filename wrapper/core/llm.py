"""
LLM client abstraction.

Supports pluggable LLM backends. Default: DeepSeek.
Configuration via environment variables or .wrapper/config.yaml.
Environment variables take precedence.
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Optional
from wrapper.core.files import load_config


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def generate(self, prompt: str, role: str) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The prompt to send
            role: One of "step_proposer", "prompt_compiler", "verifier"
        
        Returns:
            The LLM's response text
        """
        pass


# Shared system prompts for all LLM clients
SYSTEM_PROMPTS = {
    "step_proposer": (
        "You are a CONSERVATIVE architecture enforcer. "
        "You propose the SMALLEST, SAFEST next step. "
        "ALWAYS prefer verification over implementation. "
        "ALWAYS prefer cleanup over features. "
        "NEVER propose cross-repo changes. "
        "BLOCK feature work if dependencies are unverified. "
        "When in doubt, propose a verification step. "
        "Output ONLY valid YAML for a step definition. No explanations."
    ),
    "prompt_compiler": (
        "You are a Copilot prompt compiler. "
        "You generate strict, imperative prompts that enforce architectural constraints. "
        "Output ONLY the prompt text. No explanations or markdown."
    ),
    "verifier": (
        "You are a strict code verification assistant. "
        "You analyze git diffs against architectural constraints. "
        "Be STRICT. FAIL if any violation is found. "
        "Report violations clearly. Output structured analysis."
    ),
}


class DeepSeekClient(LLMClient):
    """DeepSeek API client."""
    
    API_URL = "https://api.deepseek.com/v1/chat/completions"
    
    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
    
    def generate(self, prompt: str, role: str) -> str:
        import urllib.request
        import urllib.error
        
        system = SYSTEM_PROMPTS.get(role, "You are a helpful assistant.")
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,  # Low temperature for consistency
            "max_tokens": 4096
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"DeepSeek API error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")


class OpenAIClient(LLMClient):
    """OpenAI API client."""
    
    API_URL = "https://api.openai.com/v1/chat/completions"
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
    
    def generate(self, prompt: str, role: str) -> str:
        import urllib.request
        import urllib.error
        
        system = SYSTEM_PROMPTS.get(role, "You are a helpful assistant.")
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 4096
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"OpenAI API error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")


class AnthropicClient(LLMClient):
    """Anthropic API client."""
    
    API_URL = "https://api.anthropic.com/v1/messages"
    
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
    
    def generate(self, prompt: str, role: str) -> str:
        import urllib.request
        import urllib.error
        
        system = SYSTEM_PROMPTS.get(role, "You are a helpful assistant.")
        
        payload = {
            "model": self.model,
            "max_tokens": 4096,
            "system": system,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }
        
        req = urllib.request.Request(
            self.API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result["content"][0]["text"]
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Anthropic API error {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error: {e.reason}")


def get_llm_client() -> LLMClient:
    """
    Get the configured LLM client.
    
    Priority:
    1. Environment variables (DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
    2. Config file (.wrapper/config.yaml)
    
    Returns:
        Configured LLMClient instance
    
    Raises:
        RuntimeError if no API key is configured
    """
    config = load_config()
    
    # Check environment variables first (they win)
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    # Fall back to config file
    if not deepseek_key:
        deepseek_key = config.get("deepseek_api_key")
    if not openai_key:
        openai_key = config.get("openai_api_key")
    if not anthropic_key:
        anthropic_key = config.get("anthropic_api_key")
    
    # Determine which provider to use
    provider = os.environ.get("LLM_PROVIDER") or config.get("llm_provider", "deepseek")
    
    if provider == "deepseek" and deepseek_key:
        model = config.get("deepseek_model", "deepseek-chat")
        return DeepSeekClient(deepseek_key, model)
    
    if provider == "openai" and openai_key:
        model = config.get("openai_model", "gpt-4o")
        return OpenAIClient(openai_key, model)
    
    if provider == "anthropic" and anthropic_key:
        model = config.get("anthropic_model", "claude-sonnet-4-20250514")
        return AnthropicClient(anthropic_key, model)
    
    # Auto-detect based on available keys
    if deepseek_key:
        return DeepSeekClient(deepseek_key)
    if openai_key:
        return OpenAIClient(openai_key)
    if anthropic_key:
        return AnthropicClient(anthropic_key)
    
    raise RuntimeError(
        "No LLM API key configured.\n"
        "Set one of:\n"
        "  - DEEPSEEK_API_KEY environment variable\n"
        "  - OPENAI_API_KEY environment variable\n"
        "  - ANTHROPIC_API_KEY environment variable\n"
        "Or add to .wrapper/config.yaml:\n"
        "  deepseek_api_key: your-key-here"
    )

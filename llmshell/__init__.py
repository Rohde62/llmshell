"""
LLMShell - A privacy-respecting Linux shell powered by local LLMs.

This package provides a command-line interface that translates natural language
instructions into bash commands using local Large Language Models.
"""

__version__ = "0.1.0"
__author__ = "Jakob Rohde"
__email__ = "jakob@example.com"
__description__ = "A privacy-respecting Linux shell that translates natural language to bash commands using local LLMs"

from .config import LLMShellConfig, load_config
from .core import ShellSession, start_interactive_shell
from .llm import LLMProvider, LLMResponse, OllamaProvider, create_llm_provider
from .safety import CommandRisk, DangerLevel, SafetyAnalyzer

__all__ = [
    "LLMShellConfig",
    "load_config",
    "LLMProvider",
    "OllamaProvider",
    "create_llm_provider",
    "LLMResponse",
    "ShellSession",
    "start_interactive_shell",
    "SafetyAnalyzer",
    "DangerLevel",
    "CommandRisk",
]

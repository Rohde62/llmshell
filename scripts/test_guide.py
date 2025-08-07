#!/usr/bin/env python3
"""Interactive test of model selection in the running shell."""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import llmshell
sys.path.insert(0, str(Path(__file__).parent.parent))

from llmshell.config import LLMShellConfig
from llmshell.core import start_interactive_shell
from llmshell.llm import create_llm_provider


async def test_model_commands():
    """Test model commands interactively."""
    print("🎯 LLMShell Model Testing Guide")
    print("=" * 50)
    print("\nTo test the model selection features, try these commands in LLMShell:")
    print("\n1. Check current model:")
    print("   .model")
    print("\n2. List available models:")
    print("   .models")
    print("\n3. Switch to a different model (example):")
    print("   .model deepseek-r1:8b")
    print("   .model gemma3:12b")
    print("\n4. Test fuzzy matching:")
    print("   .model llama3       # Should match llama3:latest")
    print("   .model deepseek     # Should suggest deepseek-r1:8b")
    print("\n5. Test help to see all commands:")
    print("   .help")
    print("\n6. Exit when done:")
    print("   .exit")
    print("\n" + "=" * 50)
    print("LLMShell is ready for testing! 🚀")


if __name__ == "__main__":
    asyncio.run(test_model_commands())

#!/usr/bin/env python3
"""Test fuzzy model matching functionality."""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import llmshell
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

from llmshell.config import LLMShellConfig
from llmshell.core import ShellSession
from llmshell.llm import create_llm_provider


async def test_fuzzy_matching():
    """Test fuzzy model name matching."""
    console = Console()

    console.print("🧪 Testing Fuzzy Model Name Matching\n", style="bold cyan")

    # Load configuration and create provider
    config = LLMShellConfig()
    provider = create_llm_provider(config.llm)
    session = ShellSession(config, provider)

    try:
        # Test various fuzzy matches
        test_cases = [
            "llama3",  # Should match "llama3:latest"
            "deepseek",  # Should match "deepseek-r1:8b"
            "gemma",  # Should match "gemma3:12b"
            "nonexistent",  # Should fail gracefully
        ]

        console.print("Available models:")
        await session.show_models()
        console.print()

        for test_name in test_cases:
            console.print(f"🔄 Testing switch to '{test_name}':")
            await session.switch_model(test_name)
            console.print()

    except Exception as e:
        console.print(f"❌ Test failed: {e}", style="red")
    finally:
        provider.close()


async def main():
    """Main test function."""
    try:
        await test_fuzzy_matching()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted")


if __name__ == "__main__":
    asyncio.run(main())

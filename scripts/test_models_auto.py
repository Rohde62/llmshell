#!/usr/bin/env python3
"""Automated test of model selection features."""

import asyncio
import subprocess
import sys
import time
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

from llmshell.config import LLMShellConfig
from llmshell.core import ShellSession
from llmshell.llm import create_llm_provider


async def automated_model_test():
    """Run automated tests of model functionality."""
    console = Console()

    console.print("🧪 Automated Model Selection Test", style="bold cyan")
    console.print("=" * 50)

    # Initialize the same way the CLI does
    config = LLMShellConfig()
    provider = create_llm_provider(config.llm)
    session = ShellSession(config, provider)

    try:
        # Test 1: Show current model
        console.print("\n🔍 Test 1: Current Model Configuration")
        session.show_current_model()

        # Test 2: List available models
        console.print("\n🔍 Test 2: Available Models")
        await session.show_models()

        # Test 3: Test model switching
        models = await provider.list_models()
        if len(models) > 1:
            # Find a different model to test
            current_model = config.llm.model
            test_model = None
            for model in models:
                if model != current_model:
                    test_model = model
                    break

            if test_model:
                console.print(f"\n🔄 Test 3: Switching to '{test_model}'")
                await session.switch_model(test_model)

                console.print("\n📋 Verifying switch:")
                session.show_current_model()

                console.print(f"\n🔄 Switching back to '{current_model}'")
                await session.switch_model(current_model)

        # Test 4: Fuzzy matching
        console.print("\n🔍 Test 4: Fuzzy Matching")
        console.print("Testing 'llama3' (should match 'llama3:latest')")
        await session.switch_model("llama3")

        console.print("\nTesting 'deepseek' (should suggest 'deepseek-r1:8b')")
        await session.switch_model("deepseek")

        console.print("\nTesting 'nonexistent' (should show error)")
        await session.switch_model("nonexistent")

        console.print("\n✅ All model tests completed!")

    except Exception as e:
        console.print(f"\n❌ Test failed: {e}", style="red")
        import traceback

        traceback.print_exc()
    finally:
        provider.close()


async def main():
    """Main test function."""
    try:
        await automated_model_test()
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted")


if __name__ == "__main__":
    asyncio.run(main())

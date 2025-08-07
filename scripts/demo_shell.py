#!/usr/bin/env python3
"""
Demo script to test LLMShell interactive functionality.
This demonstrates the core features without entering full interactive mode.
"""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import llmshell
sys.path.insert(0, str(Path(__file__).parent.parent))

from llmshell.config import load_config
from llmshell.core import ShellSession
from llmshell.llm import create_llm_provider, test_llm_connection


async def demo_shell_session():
    """Demonstrate the shell session functionality."""
    print("🚀 LLMShell Interactive Demo")
    print("=" * 50)

    # Load configuration
    try:
        config = load_config()
        print(f"📋 Using: {config.llm.provider} ({config.llm.model})")
        print(f"🔗 URL: {config.llm.base_url}")
        print()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return

    # Create LLM provider
    try:
        provider = create_llm_provider(config.llm)
    except Exception as e:
        print(f"❌ Failed to create LLM provider: {e}")
        return

    # Test connection
    print("🔌 Testing LLM connection...")
    if not await test_llm_connection(provider):
        print("❌ LLM connection failed.")
        provider.close()
        return

    print("✅ LLM connection successful!")
    print()

    # Create shell session
    session = ShellSession(config, provider)

    # Demo commands
    demo_commands = [
        "list all python files",
        "show current directory",
        "show disk usage",
        "ls -la",  # Direct command
        ".help",  # Special command
    ]

    print("🎯 Running Demo Commands:")
    print("-" * 30)

    for i, command in enumerate(demo_commands, 1):
        print(f"\n[{i}/{len(demo_commands)}] Demo: '{command}'")
        print("-" * 40)

        # Simulate user input processing
        try:
            # For this demo, we'll bypass the confirmation prompts
            original_confirm = config.execution.always_confirm
            config.execution.always_confirm = False

            # Process the command
            continue_session = await session.process_user_input(command)

            # Restore original setting
            config.execution.always_confirm = original_confirm

            if not continue_session:
                break

        except Exception as e:
            print(f"❌ Error processing '{command}': {e}")

    print("\n" + "=" * 50)
    print("✅ Demo completed!")
    print("\nTo start the full interactive shell, run: llmshell shell")

    provider.close()


def main():
    """Main demo function."""
    try:
        asyncio.run(demo_shell_session())
    except KeyboardInterrupt:
        print("\n👋 Demo cancelled!")
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    main()

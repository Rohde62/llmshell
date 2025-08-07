#!/usr/bin/env python3
"""Interactive demo of model selection functionality."""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import llmshell
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console
from rich.panel import Panel

from llmshell.config import LLMShellConfig
from llmshell.core import ShellSession
from llmshell.llm import create_llm_provider


async def demo_model_selection():
    """Interactive demo of model selection."""
    console = Console()

    # Welcome message
    welcome_panel = Panel(
        "🎯 LLMShell Model Selection Demo\n\n"
        "This demo shows the new model management features:\n"
        "• .models - List available models\n"
        "• .model - Show current model\n"
        "• .model <name> - Switch models\n\n"
        "We'll simulate the commands to show the functionality.",
        title="Model Selection Demo",
        border_style="cyan",
    )
    console.print(welcome_panel)

    # Load configuration and create provider
    config = LLMShellConfig()
    provider = create_llm_provider(config.llm)
    session = ShellSession(config, provider)

    try:
        console.print("\n🔍 Step 1: Checking current model configuration")
        session.show_current_model()

        console.print("\n🔍 Step 2: Listing all available models")
        await session.show_models()

        # Get available models for demo
        models = await provider.list_models()
        if len(models) > 1:
            # Find a different model to switch to
            current_model = config.llm.model
            demo_model = None
            for model in models:
                if model != current_model:
                    demo_model = model
                    break

            if demo_model:
                console.print(f"\n🔄 Step 3: Switching to model '{demo_model}'")
                await session.switch_model(demo_model)

                console.print("\n📋 Step 4: Verifying the change")
                session.show_current_model()

                console.print(
                    f"\n🔄 Step 5: Switching back to original model '{current_model}'"
                )
                await session.switch_model(current_model)
            else:
                console.print("\n⚠️  Only one model available, skipping switch demo")
        else:
            console.print("\n⚠️  Only one model available, skipping switch demo")

        console.print(
            "\n✅ Demo completed! These commands are now available in LLMShell:"
        )
        console.print("  • .models   - List all available models")
        console.print("  • .model    - Show current model info")
        console.print("  • .model <name> - Switch to a different model")

    except Exception as e:
        console.print(f"\n❌ Demo failed: {e}", style="red")
    finally:
        provider.close()


async def main():
    """Main demo function."""
    try:
        await demo_model_selection()
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Test script for model selection functionality."""

import asyncio
import sys
from pathlib import Path

# Add the parent directory to the path so we can import llmshell
sys.path.insert(0, str(Path(__file__).parent.parent))

from llmshell.config import LLMShellConfig
from llmshell.llm import create_llm_provider


async def test_model_functionality():
    """Test model listing and switching functionality."""
    print("🧪 Testing Model Management Functionality\n")

    # Load configuration
    config = LLMShellConfig()
    provider = create_llm_provider(config.llm)

    print(f"📋 Current Configuration:")
    print(f"  Provider: {config.llm.provider}")
    print(f"  Base URL: {config.llm.base_url}")
    print(f"  Model: {config.llm.model}")
    print(f"  Temperature: {config.llm.temperature}\n")

    # Test connection
    print("🔗 Testing LLM Connection...")
    if await provider.test_connection():
        print("✅ Connection successful\n")
    else:
        print("❌ Connection failed")
        provider.close()
        return

    # List available models
    print("📋 Available Models:")
    models = await provider.list_models()

    if not models:
        print("❌ No models found or unable to fetch models")
        provider.close()
        return

    current_model = config.llm.model
    for i, model in enumerate(models, 1):
        indicator = " ← current" if model == current_model else ""
        print(f"  {i}. {model}{indicator}")

    print(f"\n✅ Found {len(models)} available models")

    # Test model switching (if multiple models available)
    if len(models) > 1:
        # Find a different model to test switching
        test_model = None
        for model in models:
            if model != current_model:
                test_model = model
                break

        if test_model:
            print(f"\n🔄 Testing model switch to: {test_model}")
            old_model = provider.config.model
            provider.config.model = test_model

            if await provider.test_connection():
                print(f"✅ Successfully switched to {test_model}")

                # Test a simple translation
                print("🧪 Testing translation with new model...")
                response = await provider.translate("list files")
                if response.error:
                    print(f"❌ Translation error: {response.error}")
                else:
                    print(f"✅ Translation successful: {response.command}")

                # Switch back
                provider.config.model = old_model
                print(f"🔄 Switched back to original model: {old_model}")
            else:
                print(f"❌ Failed to connect to {test_model}")
                provider.config.model = old_model

    print("\n🎉 Model management tests completed!")
    provider.close()


async def main():
    """Main test function."""
    try:
        await test_model_functionality()
    except KeyboardInterrupt:
        print("\n\n👋 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

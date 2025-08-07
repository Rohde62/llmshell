#!/usr/bin/env python3
"""
Development script to verify installation and basic functionality.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, description: str):
    """Run a command and report results."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Success")
            if result.stdout.strip():
                print(f"   📄 Output: {result.stdout.strip()}")
        else:
            print(f"   ❌ Failed (exit code: {result.returncode})")
            if result.stderr.strip():
                print(f"   💥 Error: {result.stderr.strip()}")
        return result.returncode == 0
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False


def check_python_version():
    """Check Python version."""
    version = sys.version_info
    if version >= (3, 10):
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(
            f"❌ Python version {version.major}.{version.minor}.{version.micro} is too old (need 3.10+)"
        )
        return False


def check_ollama():
    """Check if Ollama is installed and running."""
    print("🔍 Checking Ollama...")

    # Check if ollama command exists
    if not run_command("which ollama", "Checking Ollama installation"):
        print("   💡 Install Ollama from: https://ollama.ai/")
        return False

    # Check if Ollama is running
    if not run_command(
        "curl -s http://localhost:11434/api/tags", "Checking Ollama service"
    ):
        print("   💡 Start Ollama with: ollama serve")
        return False

    # List available models
    run_command("ollama list", "Listing available models")
    return True


def main():
    """Main verification script."""
    print("🚀 LLMShell Development Environment Check")
    print("=" * 50)

    all_checks_passed = True

    # Check Python version
    if not check_python_version():
        all_checks_passed = False

    print()

    # Check if we can import the package
    try:
        import llmshell

        print(f"✅ LLMShell package imported successfully (v{llmshell.__version__})")
    except ImportError as e:
        print(f"❌ Failed to import LLMShell: {e}")
        print("   💡 Install with: pip install -e .")
        all_checks_passed = False

    print()

    # Check dependencies
    dependencies = ["click", "httpx", "rich", "pydantic", "yaml"]
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep} is available")
        except ImportError:
            print(f"❌ {dep} is missing")
            all_checks_passed = False

    print()

    # Check Ollama
    if not check_ollama():
        all_checks_passed = False

    print()

    # Test CLI
    if run_command("python -m llmshell.cli --help", "Testing CLI"):
        print("✅ CLI is working")
    else:
        print("❌ CLI test failed")
        all_checks_passed = False

    print()
    print("=" * 50)

    if all_checks_passed:
        print("🎉 All checks passed! You're ready to develop.")
        print("\nNext steps:")
        print("1. Initialize config: python -m llmshell.cli init")
        print("2. Test connection: python -m llmshell.cli test")
        print("3. Run prompt tests: python scripts/test_prompts.py")
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

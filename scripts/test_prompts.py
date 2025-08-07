#!/usr/bin/env python3
"""
Script to test LLM prompt templates and validate responses.
This helps ensure the LLM can reliably convert natural language to bash commands.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import llmshell
sys.path.insert(0, str(Path(__file__).parent.parent))

from llmshell.config import LLMConfig, load_config
from llmshell.llm import create_llm_provider, test_llm_connection

# Test cases for natural language to bash translation
TEST_CASES = [
    # File operations
    {
        "input": "list all files",
        "expected_commands": ["ls", "ls -la", "ls -l", "ls -a"],
        "category": "file_operations",
    },
    {
        "input": "list all hidden files",
        "expected_commands": ["ls -a", "ls -la", "ls -ld .*", "find . -name '.*'"],
        "category": "file_operations",
    },
    {
        "input": "show current directory",
        "expected_commands": ["pwd"],
        "category": "file_operations",
    },
    {
        "input": "change to home directory",
        "expected_commands": ["cd ~", "cd $HOME", "cd"],
        "category": "file_operations",
    },
    # File searching
    {
        "input": "find all python files",
        "expected_commands": [
            "find . -name '*.py'",
            'find . -name "*.py"',
            "find . -type f -name '*.py'",
        ],
        "category": "search",
    },
    {
        "input": "find files modified in the last 24 hours",
        "expected_commands": ["find . -mtime -1", "find . -type f -mtime -1"],
        "category": "search",
    },
    {
        "input": "search for text in files",
        "expected_commands": ["grep -r", "grep -rn", "find . -type f -exec grep"],
        "category": "search",
    },
    # System information
    {
        "input": "show disk usage",
        "expected_commands": ["df -h", "df", "du -h"],
        "category": "system",
    },
    {
        "input": "show running processes",
        "expected_commands": ["ps aux", "ps -ef", "ps"],
        "category": "system",
    },
    {
        "input": "show memory usage",
        "expected_commands": ["free -h", "free", "cat /proc/meminfo"],
        "category": "system",
    },
    # File permissions
    {
        "input": "make file executable",
        "expected_commands": ["chmod +x", "chmod 755"],
        "category": "permissions",
    },
    {
        "input": "change file owner to current user",
        "expected_commands": ["chown $USER", "chown $(whoami)"],
        "category": "permissions",
    },
    # Network
    {
        "input": "show network connections",
        "expected_commands": ["netstat", "ss", "netstat -tuln"],
        "category": "network",
    },
    {
        "input": "ping google",
        "expected_commands": ["ping google.com", "ping 8.8.8.8"],
        "category": "network",
    },
    # Complex commands
    {
        "input": "count lines in all python files",
        "expected_commands": [
            "find . -name '*.py' -exec wc -l {} +",
            "wc -l *.py",
            'find . -name "*.py" -exec grep -c',
            "grep -c",
        ],
        "category": "complex",
    },
    {
        "input": "show largest files in current directory",
        "expected_commands": [
            "ls -laSh",
            "du -sh * | sort -rh",
            "du -ah | sort -hr",
            "find . -type f -exec ls -lh {} + | sort -k5 -rh",
        ],
        "category": "complex",
    },
]


def validate_command(generated_command: str, expected_commands: list[str]) -> bool:
    """
    Validate if the generated command matches expected patterns.
    Returns True if the command contains any of the expected command patterns.
    """
    if not generated_command:
        return False

    generated_lower = generated_command.lower().strip()

    # Check if any expected command pattern is present
    for expected in expected_commands:
        if expected.lower() in generated_lower:
            return True

    # Additional validation for common alternative patterns
    # Handle quote differences (single vs double quotes)
    generated_normalized = generated_lower.replace('"', "'")
    for expected in expected_commands:
        expected_normalized = expected.lower().replace('"', "'")
        if expected_normalized in generated_normalized:
            return True

    # Special case validations for semantically equivalent commands
    if any("hidden" in cmd.lower() for cmd in expected_commands):
        # Accept various ways to list hidden files
        if any(
            pattern in generated_lower for pattern in ["ls -", "ls.*-a", "find.*\\."]
        ):
            return True

    if any(
        "count" in cmd.lower() and "lines" in cmd.lower() for cmd in expected_commands
    ):
        # Accept various ways to count lines
        if any(
            pattern in generated_lower for pattern in ["wc -l", "grep -c", "find.*wc"]
        ):
            return True

    if any(
        "largest" in cmd.lower() and "files" in cmd.lower() for cmd in expected_commands
    ):
        # Accept various ways to show largest files
        if any(
            pattern in generated_lower
            for pattern in ["du.*sort", "ls.*-s", "find.*size"]
        ):
            return True

    return False


async def test_single_prompt(provider, test_case: dict) -> dict:
    """Test a single prompt and return results."""
    result = {
        "input": test_case["input"],
        "category": test_case["category"],
        "expected": test_case["expected_commands"],
        "generated": "",
        "valid": False,
        "error": None,
    }

    try:
        response = await provider.translate(test_case["input"])

        if response.error:
            result["error"] = response.error
            return result

        result["generated"] = response.command
        result["valid"] = validate_command(
            response.command, test_case["expected_commands"]
        )

    except Exception as e:
        result["error"] = str(e)

    return result


async def run_prompt_tests():
    """Run all prompt tests and display results."""
    print("🧪 LLMShell Prompt Testing")
    print("=" * 50)

    # Load configuration
    try:
        config = load_config()
        print(f"📋 Using LLM: {config.llm.provider} ({config.llm.model})")
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
        print(
            "❌ LLM connection failed. Make sure Ollama is running and the model is available."
        )
        provider.close()
        return

    print("✅ LLM connection successful!")
    print()

    # Run tests
    results = []
    categories = {}

    print("🚀 Running prompt tests...")
    print()

    for i, test_case in enumerate(TEST_CASES, 1):
        print(f"[{i:2d}/{len(TEST_CASES)}] Testing: '{test_case['input']}'")

        result = await test_single_prompt(provider, test_case)
        results.append(result)

        # Track by category
        category = result["category"]
        if category not in categories:
            categories[category] = {"total": 0, "passed": 0}
        categories[category]["total"] += 1

        if result["error"]:
            print(f"        ❌ Error: {result['error']}")
        elif result["valid"]:
            print(f"        ✅ Generated: {result['generated']}")
            categories[category]["passed"] += 1
        else:
            print(f"        ❌ Generated: {result['generated']}")
            print(f"        Expected patterns: {', '.join(result['expected'])}")
        print()

    # Summary
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r["valid"] and not r["error"])

    print("📊 Test Summary")
    print("=" * 50)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success rate: {passed_tests/total_tests*100:.1f}%")
    print()

    # Category breakdown
    print("📈 Results by Category")
    print("-" * 30)
    for category, stats in categories.items():
        success_rate = stats["passed"] / stats["total"] * 100
        print(
            f"{category:15s}: {stats['passed']:2d}/{stats['total']:2d} ({success_rate:5.1f}%)"
        )

    # Failed tests details
    failed_tests = [r for r in results if not r["valid"] or r["error"]]
    if failed_tests:
        print()
        print("❌ Failed Tests Details")
        print("-" * 30)
        for result in failed_tests:
            print(f"Input: {result['input']}")
            if result["error"]:
                print(f"Error: {result['error']}")
            else:
                print(f"Generated: {result['generated']}")
                print(f"Expected: {', '.join(result['expected'])}")
            print()

    provider.close()


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Interactive mode for testing custom prompts
        async def interactive_mode():
            config = load_config()
            provider = create_llm_provider(config.llm)

            if not await test_llm_connection(provider):
                print("❌ LLM connection failed.")
                return

            print("🔍 Interactive Prompt Testing")
            print("Type 'quit' to exit.")
            print()

            while True:
                try:
                    user_input = input("Natural language: ").strip()
                    if user_input.lower() in ["quit", "exit", "q"]:
                        break

                    if not user_input:
                        continue

                    response = await provider.translate(user_input)
                    if response.error:
                        print(f"❌ Error: {response.error}")
                    else:
                        print(f"✅ Command: {response.command}")
                    print()

                except KeyboardInterrupt:
                    break

            provider.close()

        asyncio.run(interactive_mode())
    else:
        # Run standard test suite
        asyncio.run(run_prompt_tests())


if __name__ == "__main__":
    main()

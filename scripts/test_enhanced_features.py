#!/usr/bin/env python3
"""Test script for enhanced context and history features."""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import llmshell
sys.path.insert(0, str(Path(__file__).parent.parent))

from rich.console import Console

from llmshell.context import EnhancedContextAnalyzer, ProjectType
from llmshell.history import CommandType, HistoryEntry, HistoryManager


async def test_enhanced_features():
    """Test the enhanced context and history features."""
    console = Console()

    console.print("🧪 Testing Enhanced Context & History Features", style="bold cyan")
    console.print("=" * 60)

    # Test History Manager
    console.print("\n📊 Testing History Manager")
    with tempfile.TemporaryDirectory() as tmp_dir:
        history_manager = HistoryManager(Path(tmp_dir))

        # Add some test entries
        test_entries = [
            HistoryEntry(
                user_input="list python files",
                translated_command="find . -name '*.py'",
                command_type=CommandType.NATURAL.value,
                success=True,
                working_directory="/test/python-project",
                model_used="llama3:latest",
                project_context="python",
            ),
            HistoryEntry(
                user_input="git status",
                translated_command="git status",
                command_type=CommandType.DIRECT.value,
                success=True,
                working_directory="/test/python-project",
                model_used="llama3:latest",
                project_context="git",
            ),
            HistoryEntry(
                user_input="install package",
                translated_command="pip install requests",
                command_type=CommandType.NATURAL.value,
                success=True,
                working_directory="/test/python-project",
                model_used="llama3:latest",
                project_context="python",
            ),
        ]

        for entry in test_entries:
            history_manager.add_entry(entry)

        console.print("✅ Added test history entries")

        # Test search
        search_results = history_manager.search_history("python")
        console.print(f"✅ Search 'python': found {len(search_results)} results")

        # Test similar commands
        similar = history_manager.get_similar_commands("list files", limit=3)
        console.print(f"✅ Similar to 'list files': found {len(similar)} results")

        # Test stats
        stats = history_manager.get_command_stats()
        console.print(
            f"✅ Stats: {stats['total_commands']} total, {stats['success_rate']}% success rate"
        )

        # Test export
        export_file = Path(tmp_dir) / "test_export.json"
        if history_manager.export_history(export_file):
            console.print(f"✅ Exported history to {export_file}")

    # Test Context Analyzer
    console.print("\n🔍 Testing Context Analyzer")
    analyzer = EnhancedContextAnalyzer()

    # Test current directory (LLMShell project)
    current_dir = Path.cwd()
    context = analyzer.analyze_directory(current_dir)
    console.print(f"✅ Current directory analysis:")
    console.print(
        f"   Type: {context.project_type.value} (confidence: {context.confidence:.1%})"
    )
    console.print(f"   Language: {context.main_language}")
    console.print(f"   Package Manager: {context.package_manager}")
    console.print(f"   Key files: {', '.join(context.key_files[:3])}")

    # Test LLM context
    llm_context = analyzer.get_context_for_llm(current_dir)
    console.print(f"✅ LLM context keys: {list(llm_context.keys())}")

    # Test command suggestions
    if context.project_type != ProjectType.UNKNOWN:
        suggestions = analyzer.get_command_suggestions(context, "install dependencies")
        console.print(
            f"✅ Suggestions for 'install dependencies': {len(suggestions)} items"
        )
        for i, suggestion in enumerate(suggestions[:3], 1):
            console.print(f"   {i}. {suggestion}")

    # Test different project types by creating temporary directories
    console.print("\n📁 Testing Project Type Detection")

    test_projects = [
        ("python", ["requirements.txt", "main.py", "setup.py"]),
        ("nodejs", ["package.json", "index.js", "yarn.lock"]),
        ("rust", ["Cargo.toml", "src/main.rs"]),
        ("go", ["go.mod", "main.go"]),
        ("docker", ["Dockerfile", "docker-compose.yml"]),
        ("web", ["index.html", "webpack.config.js", "style.css"]),
    ]

    for project_name, files in test_projects:
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = Path(tmp_dir)

            # Create test files
            for file in files:
                if "/" in file:
                    # Create directory structure
                    file_path = test_dir / file
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    file_path.touch()
                else:
                    (test_dir / file).touch()

            # Analyze the test project
            test_context = analyzer.analyze_directory(test_dir)
            console.print(
                f"✅ {project_name.title()}: {test_context.project_type.value} "
                f"(confidence: {test_context.confidence:.1%})"
            )

    console.print(f"\n🎉 Enhanced features testing completed!")


async def main():
    """Main test function."""
    try:
        await test_enhanced_features()
    except KeyboardInterrupt:
        print("\n\n👋 Tests interrupted")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

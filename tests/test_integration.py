"""Integration tests for LLMShell end-to-end functionality."""

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llmshell.cli import main
from llmshell.config import LLMShellConfig
from llmshell.core import ShellSession, start_interactive_shell
from llmshell.history import CommandType
from llmshell.llm import LLMProvider, LLMResponse


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    @pytest.mark.asyncio
    async def test_complete_natural_language_workflow(self, shell_session):
        """Test complete workflow from natural language to execution."""
        # Mock user confirmation
        with patch("rich.prompt.Confirm.ask", return_value=True):
            # Process natural language input
            result = await shell_session.process_user_input("list all python files")

            assert result is True

            # Check that history was recorded
            recent_history = shell_session.history_manager.get_recent_entries(limit=1)
            assert len(recent_history) == 1
            assert recent_history[0].command_type == "natural"

    @pytest.mark.asyncio
    async def test_complete_direct_command_workflow(self, shell_session):
        """Test complete workflow for direct commands."""
        with patch("rich.prompt.Confirm.ask", return_value=True):
            result = await shell_session.process_user_input("echo 'test'")

            assert result is True

            # Check that history was recorded
            recent_history = shell_session.history_manager.get_recent_entries(limit=1)
            assert len(recent_history) == 1
            assert recent_history[0].command_type == "direct"

    def test_session_state_persistence(
        self, temp_dir, test_config, mock_llm_provider, monkeypatch
    ):
        """Test that session state persists across restarts."""
        monkeypatch.setenv("HOME", str(temp_dir))

        # Create first session and execute commands
        session1 = ShellSession(test_config, mock_llm_provider)
        session1.execute_command(
            "echo 'session1'", "test command 1", CommandType.DIRECT
        )

        # Get initial history count
        initial_stats = session1.history_manager.get_statistics()
        initial_count = initial_stats["total_commands"]

        # Create second session (simulating restart)
        session2 = ShellSession(test_config, mock_llm_provider)

        # Add another command
        session2.execute_command(
            "echo 'session2'", "test command 2", CommandType.DIRECT
        )

        # Check that history persists and accumulates
        final_stats = session2.history_manager.get_statistics()
        final_count = final_stats["total_commands"]

        assert final_count == initial_count + 1

    @pytest.mark.asyncio
    async def test_model_switching_workflow(self, shell_session):
        """Test complete model switching workflow."""
        # Check initial model
        initial_model = shell_session.llm_provider.config.model

        # Switch to different model
        await shell_session.switch_model("codellama:latest")

        # Verify model changed
        assert shell_session.llm_provider.config.model == "codellama:latest"

        # Test that new model works
        response = await shell_session.translate_command("list files")
        assert response.command is not None
        assert response.error is None

    def test_directory_navigation_workflow(self, shell_session, sample_project_dirs):
        """Test directory navigation and context updates."""
        python_dir = sample_project_dirs["python"]
        node_dir = sample_project_dirs["node"]

        # Start in Python directory
        shell_session.current_directory = python_dir
        shell_session._load_session_context()

        assert shell_session.current_project_context.project_type.value == "python"

        # Navigate to Node.js directory
        success, _, _ = shell_session.execute_command(f"cd {node_dir}")
        assert success is True

        # Context should update
        assert shell_session.current_project_context.project_type.value == "nodejs"

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, shell_session):
        """Test error recovery and handling workflow."""
        # Test LLM error recovery
        shell_session.llm_provider.translate.return_value = LLMResponse(
            command="", explanation="", error="Connection failed"
        )

        with patch("rich.prompt.Confirm.ask", return_value=True):
            result = await shell_session.process_user_input("list files")
            assert result is True  # Should continue despite error

        # Test command execution error recovery
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "Command failed"

            success, stdout, stderr = shell_session.execute_command("false")
            assert success is False
            assert "Command failed" in stderr

    def test_history_analysis_workflow(self, shell_session):
        """Test history analysis and insights workflow."""
        # Execute various commands to build history
        commands = [
            ("list python files", "find . -name '*.py'", CommandType.NATURAL),
            ("show disk usage", "df -h", CommandType.NATURAL),
            ("ls", "ls", CommandType.DIRECT),
            ("python script", "python main.py", CommandType.DIRECT),
        ]

        for user_input, command, cmd_type in commands:
            shell_session.execute_command(command, user_input, cmd_type)

        # Test history statistics
        stats = shell_session.history_manager.get_statistics()
        assert stats["total_commands"] == 4
        assert stats["natural_language_commands"] == 2
        assert stats["direct_commands"] == 2

        # Test history search
        python_results = shell_session.history_manager.search_history("python")
        assert len(python_results) == 2

    @pytest.mark.asyncio
    async def test_context_aware_suggestions_workflow(
        self, shell_session, sample_project_dirs
    ):
        """Test context-aware suggestion workflow."""
        python_dir = sample_project_dirs["python"]

        # Set up Python project context
        shell_session.current_directory = python_dir
        shell_session._load_session_context()

        # Get suggestions for testing
        suggestions = shell_session.context_analyzer.get_command_suggestions(
            shell_session.current_project_context, "testing"
        )

        assert len(suggestions) > 0
        assert any("pytest" in suggestion.lower() for suggestion in suggestions)

    def test_safety_analysis_workflow(self, shell_session):
        """Test safety analysis workflow."""
        dangerous_commands = [
            "rm -rf /",
            "dd if=/dev/zero of=/dev/sda",
            "chmod -R 000 /",
            ":(){ :|:& };:",
        ]

        for cmd in dangerous_commands:
            risk = shell_session.analyze_command_safety(cmd)
            assert risk.is_dangerous is True
            assert risk.level.value >= 3  # At least HIGH risk

    @pytest.mark.asyncio
    async def test_configuration_workflow(self, temp_dir, monkeypatch):
        """Test configuration loading and usage workflow."""
        monkeypatch.setenv("HOME", str(temp_dir))

        # Create custom config
        config_dir = temp_dir / ".llmshell"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"

        config_content = """
llm:
  model: "custom:model"
  temperature: 0.2
execution:
  safe_mode: false
  timeout: 60
"""
        config_file.write_text(config_content)

        # Load configuration
        from llmshell.config import load_config

        config = load_config()

        assert config.llm.model == "custom:model"
        assert config.llm.temperature == 0.2
        assert config.execution.safe_mode is False
        assert config.execution.timeout == 60


@pytest.mark.integration
class TestCLIIntegration:
    """Test CLI integration and argument parsing."""

    def test_cli_help_command(self):
        """Test CLI help command."""
        with patch("sys.argv", ["llmshell", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_cli_version_command(self):
        """Test CLI version command."""
        with patch("sys.argv", ["llmshell", "--version"]):
            with patch("click.echo") as mock_echo:
                with pytest.raises(SystemExit):
                    main()
                mock_echo.assert_called()

    def test_cli_config_validation(self, temp_dir, monkeypatch):
        """Test CLI configuration validation."""
        monkeypatch.setenv("HOME", str(temp_dir))

        # Test with invalid config
        config_dir = temp_dir / ".llmshell"
        config_dir.mkdir()
        config_file = config_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content:")

        with patch("sys.argv", ["llmshell"]):
            with pytest.raises(SystemExit):
                main()

    @pytest.mark.asyncio
    async def test_cli_interactive_mode(self, temp_dir, monkeypatch):
        """Test CLI interactive mode startup."""
        monkeypatch.setenv("HOME", str(temp_dir))

        # Mock the interactive shell to exit immediately
        with patch("llmshell.cli.start_interactive_shell") as mock_shell:
            mock_shell.return_value = None

            with patch("sys.argv", ["llmshell"]):
                # Should not raise exception
                main()

            mock_shell.assert_called_once()


@pytest.mark.integration
class TestPerformanceWorkflow:
    """Test performance-related workflows."""

    def test_large_history_performance(self, shell_session):
        """Test performance with large history."""
        # Add many history entries
        for i in range(1000):
            shell_session.execute_command(
                f"echo 'command {i}'", f"test command {i}", CommandType.DIRECT
            )

        # Test that operations still perform well
        import time

        # Test recent entries retrieval
        start_time = time.time()
        recent = shell_session.history_manager.get_recent_entries(limit=10)
        retrieval_time = time.time() - start_time

        assert len(recent) == 10
        assert retrieval_time < 1.0  # Should be fast

        # Test search performance
        start_time = time.time()
        results = shell_session.history_manager.search_history("command")
        search_time = time.time() - start_time

        assert len(results) > 0
        assert search_time < 2.0  # Should be reasonable

    def test_memory_usage_stability(self, shell_session):
        """Test memory usage stays stable."""
        import gc

        # Execute many commands
        for i in range(100):
            shell_session.execute_command(
                f"echo 'test {i}'", f"command {i}", CommandType.DIRECT
            )

            if i % 10 == 0:
                gc.collect()  # Force garbage collection

        # Test that in-memory history doesn't grow beyond limits
        assert len(shell_session.history) <= 50  # Should be capped at 50

        # Test that database operations remain efficient
        stats = shell_session.history_manager.get_statistics()
        assert stats["total_commands"] == 100

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, shell_session):
        """Test concurrent operations don't interfere."""
        # Run multiple translation tasks concurrently
        tasks = []
        for i in range(10):
            task = shell_session.translate_command(f"test command {i}")
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        assert len(results) == 10
        for result in results:
            assert result.error is None
            assert result.command is not None


@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_development_workflow(self, shell_session, sample_project_dirs):
        """Test typical development workflow."""
        python_dir = sample_project_dirs["python"]

        # Developer starts in project directory
        shell_session.current_directory = python_dir
        shell_session._load_session_context()

        # Common development commands
        dev_commands = [
            ("show project files", "natural"),
            ("run tests", "natural"),
            ("check git status", "natural"),
            ("git status", "direct"),
            ("python main.py", "direct"),
        ]

        with patch("rich.prompt.Confirm.ask", return_value=True):
            for command, cmd_type in dev_commands:
                if cmd_type == "natural":
                    result = await shell_session._handle_natural_language(command)
                else:
                    result = await shell_session._handle_direct_command(command)

                assert result is True

        # Check history shows development workflow
        stats = shell_session.history_manager.get_statistics()
        assert stats["total_commands"] == 5

    @pytest.mark.asyncio
    async def test_system_administration_workflow(self, shell_session):
        """Test system administration workflow."""
        admin_commands = [
            ("check disk space", "natural"),
            ("show running processes", "natural"),
            ("df -h", "direct"),
            ("ps aux", "direct"),
        ]

        with patch("rich.prompt.Confirm.ask", return_value=True):
            for command, cmd_type in admin_commands:
                if cmd_type == "natural":
                    result = await shell_session._handle_natural_language(command)
                else:
                    result = await shell_session._handle_direct_command(command)

                assert result is True

        # Verify system commands were executed
        recent_history = shell_session.history_manager.get_recent_entries(limit=4)
        assert len(recent_history) == 4

    def test_learning_and_improvement_workflow(self, shell_session):
        """Test that the system learns from user patterns."""
        # Execute similar commands multiple times
        similar_commands = [
            "list all python files",
            "find python files",
            "show me python files",
            "display python files",
        ]

        for cmd in similar_commands:
            shell_session.execute_command(
                "find . -name '*.py'", cmd, CommandType.NATURAL
            )

        # Search for similar commands
        similar = shell_session.history_manager.get_similar_commands("python files")
        assert len(similar) == 4

        # All should have similar translated commands
        translated_commands = [entry.translated_command for entry in similar]
        assert all("find" in cmd and "*.py" in cmd for cmd in translated_commands)

    @pytest.mark.asyncio
    async def test_error_recovery_and_learning(self, shell_session):
        """Test error recovery and learning from mistakes."""
        # Simulate a failed command followed by correction
        with patch("subprocess.run") as mock_run:
            # First command fails
            mock_run.return_value.returncode = 1
            mock_run.return_value.stdout = ""
            mock_run.return_value.stderr = "Command not found"

            success1, _, _ = shell_session.execute_command(
                "nonexistent_command", "run nonexistent", CommandType.NATURAL
            )
            assert success1 is False

            # Second command succeeds
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Success"
            mock_run.return_value.stderr = ""

            success2, _, _ = shell_session.execute_command(
                "echo 'fixed'", "corrected command", CommandType.NATURAL
            )
            assert success2 is True

        # Check that both attempts are recorded
        stats = shell_session.history_manager.get_statistics()
        assert stats["total_commands"] == 2
        assert stats["successful_commands"] == 1
        assert stats["success_rate"] == 50.0

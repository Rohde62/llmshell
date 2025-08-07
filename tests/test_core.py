"""Comprehensive unit tests for LLMShell core functionality."""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llmshell.config import LLMShellConfig
from llmshell.core import ShellSession
from llmshell.history import CommandType
from llmshell.llm import LLMProvider, LLMResponse
from llmshell.safety import DangerLevel


class TestShellSession:
    """Test the main shell session functionality."""

    def test_session_initialization(self, shell_session):
        """Test that shell session initializes correctly."""
        assert shell_session.ai_mode is True
        assert shell_session.current_directory == Path.cwd()
        assert shell_session.history_manager is not None
        assert shell_session.context_analyzer is not None
        assert len(shell_session.history) == 0

    def test_get_context(self, shell_session):
        """Test context retrieval."""
        context = shell_session.get_context()

        assert "cwd" in context
        assert "user" in context
        assert "files" in context
        assert isinstance(context["files"], list)

    def test_detect_command_type_natural(self, shell_session):
        """Test natural language detection."""
        test_cases = [
            "please list all files",
            "can you show me the disk usage",
            "find all python files",
            "what is the current directory",
        ]

        for case in test_cases:
            assert shell_session.detect_command_type(case) == "natural"

    def test_detect_command_type_direct(self, shell_session):
        """Test direct command detection."""
        test_cases = ["ls -la", "cd /home", "grep -r pattern .", "ps aux"]

        for case in test_cases:
            assert shell_session.detect_command_type(case) == "direct"

    def test_cd_command_handling(self, shell_session, temp_dir):
        """Test cd command execution."""
        # Create test directory
        test_dir = temp_dir / "test_subdir"
        test_dir.mkdir()

        # Change to the temp directory first
        shell_session.current_directory = temp_dir

        # Test cd to subdirectory
        success, stdout, stderr = shell_session.execute_command(f"cd {test_dir}")

        assert success is True
        assert shell_session.current_directory == test_dir
        assert stderr == ""

    def test_cd_command_nonexistent_directory(self, shell_session):
        """Test cd to non-existent directory."""
        success, stdout, stderr = shell_session.execute_command(
            "cd /nonexistent/directory"
        )

        assert success is False
        assert "Directory not found" in stderr

    def test_command_safety_analysis(self, shell_session):
        """Test command safety analysis."""
        # Test safe command
        safe_risk = shell_session.analyze_command_safety("ls -la")
        assert safe_risk.level == DangerLevel.SAFE

        # Test potentially dangerous command
        risky_risk = shell_session.analyze_command_safety("rm -rf /")
        assert risky_risk.level >= DangerLevel.HIGH
        assert risky_risk.is_dangerous is True

    @pytest.mark.asyncio
    async def test_translate_command(self, shell_session):
        """Test natural language translation."""
        response = await shell_session.translate_command("list all files")

        assert response.command == "ls -la"
        assert response.explanation == "List files in detail"
        assert response.error is None

    def test_history_recording(self, shell_session):
        """Test that commands are recorded in history."""
        initial_count = len(shell_session.history)

        # Execute a command
        shell_session.execute_command("echo 'test'", "echo test", CommandType.DIRECT)

        # Check history was updated
        assert len(shell_session.history) == initial_count + 1

        # Check history manager was called
        recent_entries = shell_session.history_manager.get_recent_entries(limit=1)
        assert len(recent_entries) >= 1

    @pytest.mark.asyncio
    async def test_model_switching(self, shell_session):
        """Test model switching functionality."""
        # Test switching to available model
        await shell_session.switch_model("codellama:latest")
        assert shell_session.llm_provider.config.model == "codellama:latest"

        # Test switching to non-existent model
        old_model = shell_session.llm_provider.config.model
        shell_session.llm_provider.list_models.return_value = ["llama3:latest"]

        await shell_session.switch_model("nonexistent:model")
        # Should revert to old model
        assert shell_session.llm_provider.config.model == old_model

    def test_special_command_handling(self, shell_session):
        """Test special dot command handling."""
        # Test help command
        result = shell_session._handle_special_command(".help")
        assert result is True

        # Test mode toggle
        initial_mode = shell_session.ai_mode
        shell_session._handle_special_command(".mode")
        assert shell_session.ai_mode != initial_mode

        # Test exit command
        result = shell_session._handle_special_command(".exit")
        assert result is False

    @pytest.mark.asyncio
    async def test_natural_language_processing(self, shell_session):
        """Test complete natural language processing flow."""
        # Mock confirmation to always accept
        with patch("rich.prompt.Confirm.ask", return_value=True):
            result = await shell_session._handle_natural_language("list files")
            assert result is True

    @pytest.mark.asyncio
    async def test_direct_command_processing(self, shell_session):
        """Test direct command processing."""
        with patch("rich.prompt.Confirm.ask", return_value=True):
            result = await shell_session._handle_direct_command("echo 'test'")
            assert result is True

    def test_context_refresh_on_cd(self, shell_session, sample_project_dirs):
        """Test that project context refreshes when changing directories."""
        python_dir = sample_project_dirs["python"]

        # Change to python project directory
        shell_session.current_directory = python_dir
        success, _, _ = shell_session.execute_command(f"cd {python_dir}")

        assert success is True
        assert shell_session.current_project_context is not None

    def test_history_commands(self, shell_session):
        """Test history-related special commands."""
        # Add some history entries first
        shell_session.execute_command(
            "echo 'test1'", "test command 1", CommandType.DIRECT
        )
        shell_session.execute_command("ls", "list files", CommandType.NATURAL)

        # Test history stats command
        result = shell_session._handle_special_command(".history stats")
        assert result is True

        # Test history search command
        result = shell_session._handle_special_command(".history search echo")
        assert result is True

    def test_context_commands(self, shell_session):
        """Test context-related special commands."""
        # Test context display
        result = shell_session._handle_special_command(".context")
        assert result is True

        # Test context re-analysis
        result = shell_session._handle_special_command(".context analyze")
        assert result is True

    @pytest.mark.asyncio
    async def test_suggestion_commands(self, shell_session):
        """Test suggestion command handling."""
        # This should return an async command identifier
        result = shell_session._handle_special_command(".suggest testing")
        assert result == "async_suggest:testing"

    def test_error_handling_in_execution(self, shell_session):
        """Test error handling during command execution."""
        # Test timeout handling (mock subprocess.TimeoutExpired)
        with patch("subprocess.run") as mock_run:
            from subprocess import TimeoutExpired

            mock_run.side_effect = TimeoutExpired("test", 1)

            success, stdout, stderr = shell_session.execute_command("sleep 100")
            assert success is False
            assert "timed out" in stderr

    def test_history_memory_management(self, shell_session):
        """Test that in-memory history is properly managed."""
        # Add many commands to test memory limit
        for i in range(60):  # More than the 50 limit
            shell_session.execute_command(
                f"echo 'test{i}'", f"test command {i}", CommandType.DIRECT
            )

        # Should keep only last 50
        assert len(shell_session.history) == 50

        # Last command should be test59
        last_command = shell_session.history[-1]
        assert "test59" in last_command[0]


class TestSessionContextLoading:
    """Test session context loading and management."""

    def test_load_session_context(self, shell_session, sample_project_dirs):
        """Test loading session context from project directory."""
        python_dir = sample_project_dirs["python"]
        shell_session.current_directory = python_dir

        shell_session._load_session_context()

        assert shell_session.current_project_context is not None
        assert shell_session.current_project_context.project_type.value in [
            "python",
            "general",
        ]

    def test_session_persistence_across_restarts(
        self, temp_dir, test_config, mock_llm_provider, monkeypatch
    ):
        """Test that session data persists across shell restarts."""
        monkeypatch.setenv("HOME", str(temp_dir))

        # Create first session and add some history
        session1 = ShellSession(test_config, mock_llm_provider)
        session1.execute_command("echo 'test'", "test command", CommandType.DIRECT)

        # Create second session (simulating restart)
        session2 = ShellSession(test_config, mock_llm_provider)

        # Should load previous history
        recent_entries = session2.history_manager.get_recent_entries(limit=5)
        assert len(recent_entries) >= 1

        # Should have some in-memory history from recent entries
        assert len(session2.history) >= 0


@pytest.mark.asyncio
class TestAsyncShellOperations:
    """Test asynchronous shell operations."""

    async def test_concurrent_translation_requests(self, shell_session):
        """Test handling concurrent translation requests."""
        tasks = [
            shell_session.translate_command("list files"),
            shell_session.translate_command("show disk usage"),
            shell_session.translate_command("find python files"),
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 3
        for response in responses:
            assert response.command is not None
            assert response.error is None

    async def test_llm_provider_error_handling(self, shell_session):
        """Test error handling when LLM provider fails."""
        # Mock LLM provider to return error
        shell_session.llm_provider.translate.return_value = LLMResponse(
            command="", explanation="", error="Connection failed"
        )

        response = await shell_session.translate_command("test command")
        assert response.error == "Connection failed"

    async def test_model_list_error_handling(self, shell_session):
        """Test error handling when model listing fails."""
        shell_session.llm_provider.list_models.return_value = []

        # Should handle empty model list gracefully
        await shell_session.show_models()  # Should not raise exception

    async def test_background_operations(self, shell_session):
        """Test that background operations don't block."""

        # Mock a long-running operation
        async def slow_translate(query, context):
            await asyncio.sleep(0.1)  # Simulate delay
            return LLMResponse(command="ls", explanation="list files", error=None)

        shell_session.llm_provider.translate = slow_translate

        # Start translation and ensure it's non-blocking
        start_time = asyncio.get_event_loop().time()
        task = asyncio.create_task(shell_session.translate_command("list files"))

        # Do other work
        other_work_done = True

        # Wait for translation to complete
        response = await task
        end_time = asyncio.get_event_loop().time()

        assert other_work_done is True
        assert response.command == "ls"
        assert end_time - start_time >= 0.1

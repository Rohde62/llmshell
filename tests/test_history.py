"""Unit tests for history management functionality."""

import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from llmshell.history import CommandType, HistoryEntry, HistoryManager


class TestHistoryManager:
    """Test the history manager functionality."""

    def test_initialization(self, history_manager):
        """Test history manager initializes correctly."""
        assert history_manager.db_path.exists()
        assert history_manager.db_path.name == "history.db"

    def test_add_entry(self, history_manager):
        """Test adding history entries."""
        entry = HistoryEntry(
            user_input="list files",
            translated_command="ls -la",
            command_type="natural",
            success=True,
            execution_time_ms=150,
            working_directory="/home/user",
            exit_code=0,
            model_used="llama3:latest",
            project_context="python",
        )

        # Add entry
        history_manager.add_entry(entry)

        # Verify it was added
        recent = history_manager.get_recent_entries(limit=1)
        assert len(recent) == 1
        assert recent[0].user_input == "list files"
        assert recent[0].translated_command == "ls -la"

    def test_get_recent_entries(self, history_manager):
        """Test retrieving recent entries."""
        # Add multiple entries
        for i in range(5):
            entry = HistoryEntry(
                user_input=f"command {i}",
                translated_command=f"cmd{i}",
                command_type="direct",
                success=True,
                execution_time_ms=100 + i,
                working_directory="/home/user",
                exit_code=0,
            )
            history_manager.add_entry(entry)

        # Get recent entries
        recent = history_manager.get_recent_entries(limit=3)
        assert len(recent) == 3

        # Should be in reverse chronological order (newest first)
        assert recent[0].user_input == "command 4"
        assert recent[1].user_input == "command 3"
        assert recent[2].user_input == "command 2"

    def test_search_history(self, history_manager):
        """Test searching through history."""
        # Add entries with different commands
        entries = [
            ("list python files", "find . -name '*.py'", "natural"),
            ("show disk usage", "df -h", "natural"),
            ("python script", "python main.py", "direct"),
            ("install package", "pip install requests", "direct"),
        ]

        for user_input, command, cmd_type in entries:
            entry = HistoryEntry(
                user_input=user_input,
                translated_command=command,
                command_type=cmd_type,
                success=True,
                execution_time_ms=100,
                working_directory="/home/user",
                exit_code=0,
            )
            history_manager.add_entry(entry)

        # Search for python-related commands
        python_results = history_manager.search_history("python")
        assert len(python_results) == 2

        # Search for specific command
        find_results = history_manager.search_history("find")
        assert len(find_results) == 1
        assert find_results[0].translated_command == "find . -name '*.py'"

    def test_get_similar_commands(self, history_manager):
        """Test finding similar commands."""
        # Add various file listing commands
        commands = [
            ("list files", "ls -la"),
            ("show files", "ls -l"),
            ("list directories", "ls -d */"),
            ("show disk usage", "df -h"),
            ("list processes", "ps aux"),
        ]

        for user_input, command in commands:
            entry = HistoryEntry(
                user_input=user_input,
                translated_command=command,
                command_type="natural",
                success=True,
                execution_time_ms=100,
                working_directory="/home/user",
                exit_code=0,
            )
            history_manager.add_entry(entry)

        # Find similar to "list"
        similar = history_manager.get_similar_commands("list", limit=3)
        assert len(similar) == 3

        # Should include list-related commands
        list_commands = [cmd.user_input for cmd in similar]
        assert any("list" in cmd for cmd in list_commands)

    def test_get_statistics(self, history_manager):
        """Test getting history statistics."""
        # Add entries with different success rates and types
        entries_data = [
            (True, "natural", 100),
            (True, "direct", 150),
            (False, "natural", 200),
            (True, "natural", 120),
            (False, "direct", 180),
        ]

        for success, cmd_type, exec_time in entries_data:
            entry = HistoryEntry(
                user_input="test command",
                translated_command="test cmd",
                command_type=cmd_type,
                success=success,
                execution_time_ms=exec_time,
                working_directory="/home/user",
                exit_code=0 if success else 1,
            )
            history_manager.add_entry(entry)

        stats = history_manager.get_statistics()

        assert stats["total_commands"] == 5
        assert stats["successful_commands"] == 3
        assert stats["success_rate"] == 60.0
        assert stats["avg_execution_time"] == 150.0  # (100+150+200+120+180)/5
        assert stats["natural_language_commands"] == 3
        assert stats["direct_commands"] == 2

    def test_export_history(self, history_manager, temp_dir):
        """Test exporting history to file."""
        # Add some entries
        for i in range(3):
            entry = HistoryEntry(
                user_input=f"command {i}",
                translated_command=f"cmd{i}",
                command_type="direct",
                success=True,
                execution_time_ms=100,
                working_directory="/home/user",
                exit_code=0,
            )
            history_manager.add_entry(entry)

        # Export to file
        export_file = temp_dir / "history_export.json"
        success = history_manager.export_history(export_file)

        assert success is True
        assert export_file.exists()

        # Check file content
        import json

        with open(export_file) as f:
            data = json.load(f)

        assert "metadata" in data
        assert "history" in data
        assert len(data["history"]) == 3
        assert data["history"][0]["user_input"] == "command 2"  # Newest first

    def test_clear_history(self, history_manager):
        """Test clearing all history."""
        # Add some entries
        for i in range(5):
            entry = HistoryEntry(
                user_input=f"command {i}",
                translated_command=f"cmd{i}",
                command_type="direct",
                success=True,
                execution_time_ms=100,
                working_directory="/home/user",
                exit_code=0,
            )
            history_manager.add_entry(entry)

        # Verify entries exist
        assert len(history_manager.get_recent_entries(limit=10)) == 5

        # Clear history
        cleared_count = history_manager.clear_history()
        assert cleared_count == 5

        # Verify history is empty
        assert len(history_manager.get_recent_entries(limit=10)) == 0

    def test_database_persistence(self, temp_dir, monkeypatch):
        """Test that data persists across manager instances."""
        monkeypatch.setenv("HOME", str(temp_dir))

        # Create first manager and add entry
        manager1 = HistoryManager()
        entry = HistoryEntry(
            user_input="persistent command",
            translated_command="persistent cmd",
            command_type="direct",
            success=True,
            execution_time_ms=100,
            working_directory="/home/user",
            exit_code=0,
        )
        manager1.add_entry(entry)

        # Create second manager (should read from same database)
        manager2 = HistoryManager()
        recent = manager2.get_recent_entries(limit=1)

        assert len(recent) == 1
        assert recent[0].user_input == "persistent command"

    def test_error_handling_invalid_export_path(self, history_manager):
        """Test error handling for invalid export paths."""
        # Try to export to invalid path
        invalid_path = Path("/invalid/nonexistent/path/export.json")
        success = history_manager.export_history(invalid_path)

        assert success is False

    def test_entries_with_special_characters(self, history_manager):
        """Test handling entries with special characters."""
        entry = HistoryEntry(
            user_input="find files with 'quotes' and unicode: 🚀",
            translated_command="find . -name '*quotes*'",
            command_type="natural",
            success=True,
            execution_time_ms=100,
            working_directory="/home/user",
            exit_code=0,
            error_message="",
            model_used="llama3:latest",
            project_context="general",
        )

        history_manager.add_entry(entry)

        # Verify it was stored correctly
        recent = history_manager.get_recent_entries(limit=1)
        assert len(recent) == 1
        assert "🚀" in recent[0].user_input
        assert "quotes" in recent[0].user_input

    def test_history_size_limits(self, history_manager):
        """Test behavior with large history."""
        # Add many entries to test performance
        entries_count = 100

        for i in range(entries_count):
            entry = HistoryEntry(
                user_input=f"bulk command {i}",
                translated_command=f"bulk cmd {i}",
                command_type="direct" if i % 2 == 0 else "natural",
                success=i % 3 != 0,  # Mix of success/failure
                execution_time_ms=100 + i,
                working_directory="/home/user",
                exit_code=0 if i % 3 != 0 else 1,
            )
            history_manager.add_entry(entry)

        # Test that retrieval still works efficiently
        recent = history_manager.get_recent_entries(limit=10)
        assert len(recent) == 10

        # Test search still works
        search_results = history_manager.search_history("bulk")
        assert len(search_results) > 0

        # Test statistics calculation
        stats = history_manager.get_statistics()
        assert stats["total_commands"] == entries_count

    def test_timestamp_ordering(self, history_manager):
        """Test that entries are properly ordered by timestamp."""
        # Add entries with slight delays to ensure different timestamps
        import time

        commands = ["first", "second", "third"]
        for cmd in commands:
            entry = HistoryEntry(
                user_input=cmd,
                translated_command=cmd,
                command_type="direct",
                success=True,
                execution_time_ms=100,
                working_directory="/home/user",
                exit_code=0,
            )
            history_manager.add_entry(entry)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Get all entries
        recent = history_manager.get_recent_entries(limit=3)

        # Should be in reverse chronological order
        assert recent[0].user_input == "third"
        assert recent[1].user_input == "second"
        assert recent[2].user_input == "first"

        # Verify timestamps are actually different and ordered
        timestamps = [entry.timestamp for entry in recent]
        assert timestamps == sorted(timestamps, reverse=True)


class TestHistoryEntry:
    """Test the HistoryEntry dataclass."""

    def test_history_entry_creation(self):
        """Test creating history entries."""
        entry = HistoryEntry(
            user_input="test command",
            translated_command="test cmd",
            command_type="direct",
            success=True,
            execution_time_ms=150,
            working_directory="/home/user",
            exit_code=0,
            error_message="",
            model_used="llama3:latest",
            project_context="python",
        )

        assert entry.user_input == "test command"
        assert entry.translated_command == "test cmd"
        assert entry.command_type == "direct"
        assert entry.success is True
        assert entry.execution_time_ms == 150
        assert entry.working_directory == "/home/user"
        assert entry.exit_code == 0
        assert entry.error_message == ""
        assert entry.model_used == "llama3:latest"
        assert entry.project_context == "python"

        # Timestamp should be automatically set
        assert entry.timestamp is not None
        assert isinstance(entry.timestamp, str)

    def test_history_entry_defaults(self):
        """Test history entry with default values."""
        entry = HistoryEntry(
            user_input="test",
            translated_command="test",
            command_type="direct",
            success=True,
            execution_time_ms=100,
            working_directory="/home/user",
            exit_code=0,
        )

        # Check defaults
        assert entry.error_message == ""
        assert entry.model_used == ""
        assert entry.project_context == ""

    def test_command_type_enum(self):
        """Test CommandType enum values."""
        assert CommandType.NATURAL.value == "natural"
        assert CommandType.DIRECT.value == "direct"
        assert CommandType.BUILTIN.value == "builtin"


@pytest.mark.integration
class TestHistoryIntegration:
    """Integration tests for history functionality."""

    def test_history_with_shell_session(self, shell_session):
        """Test history integration with shell session."""
        # Execute some commands
        shell_session.execute_command(
            "echo 'test1'", "test command 1", CommandType.DIRECT
        )
        shell_session.execute_command("ls", "list files", CommandType.NATURAL)

        # Check that history was recorded
        recent = shell_session.history_manager.get_recent_entries(limit=2)
        assert len(recent) == 2

        # Check that in-memory history is also updated
        assert len(shell_session.history) == 2

    def test_history_display_methods(self, history_manager):
        """Test history display methods don't crash."""
        # Add some test data
        for i in range(3):
            entry = HistoryEntry(
                user_input=f"command {i}",
                translated_command=f"cmd{i}",
                command_type="direct",
                success=i % 2 == 0,
                execution_time_ms=100 + i * 10,
                working_directory="/home/user",
                exit_code=0 if i % 2 == 0 else 1,
            )
            history_manager.add_entry(entry)

        # These should not raise exceptions
        try:
            history_manager.display_recent_history()
            history_manager.display_history_stats()
        except Exception as e:
            pytest.fail(f"Display methods should not raise exceptions: {e}")

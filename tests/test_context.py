"""Unit tests for enhanced context analysis functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from llmshell.context import (
    EnhancedContextAnalyzer,
    ProjectContext,
    ProjectType,
    detect_language_from_files,
)


class TestEnhancedContextAnalyzer:
    """Test the enhanced context analyzer."""

    def test_initialization(self, enhanced_context_analyzer):
        """Test analyzer initializes correctly."""
        assert isinstance(enhanced_context_analyzer, EnhancedContextAnalyzer)

    def test_detect_python_project(
        self, enhanced_context_analyzer, sample_project_dirs
    ):
        """Test Python project detection."""
        python_dir = sample_project_dirs["python"]
        context = enhanced_context_analyzer.analyze_directory(python_dir)

        assert context.project_type == ProjectType.PYTHON
        assert context.confidence >= 0.8
        assert context.main_language == "Python"
        assert context.package_manager in ["pip", "pipenv", "poetry"]
        assert "requests" in context.dependencies
        assert "click" in context.dependencies

    def test_detect_node_project(self, enhanced_context_analyzer, sample_project_dirs):
        """Test Node.js project detection."""
        node_dir = sample_project_dirs["node"]
        context = enhanced_context_analyzer.analyze_directory(node_dir)

        assert context.project_type == ProjectType.NODEJS
        assert context.confidence >= 0.8
        assert context.main_language == "JavaScript"
        assert context.package_manager == "npm"
        assert "express" in context.dependencies
        assert "react" in context.dependencies

    def test_detect_rust_project(self, enhanced_context_analyzer, sample_project_dirs):
        """Test Rust project detection."""
        rust_dir = sample_project_dirs["rust"]
        context = enhanced_context_analyzer.analyze_directory(rust_dir)

        assert context.project_type == ProjectType.RUST
        assert context.confidence >= 0.8
        assert context.main_language == "Rust"
        assert context.package_manager == "cargo"
        assert "serde" in context.dependencies
        assert "tokio" in context.dependencies

    def test_detect_go_project(self, enhanced_context_analyzer, sample_project_dirs):
        """Test Go project detection."""
        go_dir = sample_project_dirs["go"]
        context = enhanced_context_analyzer.analyze_directory(go_dir)

        assert context.project_type == ProjectType.GO
        assert context.confidence >= 0.8
        assert context.main_language == "Go"
        assert context.package_manager == "go mod"
        assert any("gin" in dep for dep in context.dependencies)

    def test_detect_docker_project(
        self, enhanced_context_analyzer, sample_project_dirs
    ):
        """Test Docker project detection."""
        docker_dir = sample_project_dirs["docker"]
        context = enhanced_context_analyzer.analyze_directory(docker_dir)

        assert context.project_type == ProjectType.DOCKER
        assert context.confidence >= 0.8
        assert "Dockerfile" in context.config_files
        assert "docker-compose.yml" in context.config_files

    def test_detect_git_info(self, enhanced_context_analyzer, sample_project_dirs):
        """Test Git information detection."""
        git_dir = sample_project_dirs["git"]

        # Mock git commands
        with patch("subprocess.run") as mock_run:
            # Mock git branch command
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "main"
            mock_run.return_value.stderr = ""

            context = enhanced_context_analyzer.analyze_directory(git_dir)

            assert context.git_branch == "main"

    def test_detect_general_project(self, enhanced_context_analyzer, temp_dir):
        """Test general project detection for unknown types."""
        # Create directory with no specific project files
        general_dir = temp_dir / "general_project"
        general_dir.mkdir()
        (general_dir / "README.md").write_text("# General Project")
        (general_dir / "data.txt").write_text("some data")

        context = enhanced_context_analyzer.analyze_directory(general_dir)

        assert context.project_type == ProjectType.GENERAL
        assert context.confidence < 0.8

    def test_get_context_for_llm(self, enhanced_context_analyzer, sample_project_dirs):
        """Test LLM context generation."""
        python_dir = sample_project_dirs["python"]
        context = enhanced_context_analyzer.get_context_for_llm(python_dir)

        assert "cwd" in context
        assert "user" in context
        assert "files" in context
        assert "project_type" in context
        assert "main_language" in context
        assert context["project_type"] == "python"

    def test_get_command_suggestions_python(
        self, enhanced_context_analyzer, sample_project_context
    ):
        """Test command suggestions for Python projects."""
        suggestions = enhanced_context_analyzer.get_command_suggestions(
            sample_project_context, "testing"
        )

        assert len(suggestions) > 0
        assert any("pytest" in suggestion.lower() for suggestion in suggestions)

    def test_get_command_suggestions_general(self, enhanced_context_analyzer):
        """Test command suggestions for general intents."""
        # Create a general project context
        general_context = ProjectContext(
            project_type=ProjectType.GENERAL, confidence=0.5
        )

        suggestions = enhanced_context_analyzer.get_command_suggestions(
            general_context, "files"
        )

        assert len(suggestions) > 0
        assert any("ls" in suggestion.lower() for suggestion in suggestions)

    def test_virtual_environment_detection(self, enhanced_context_analyzer, temp_dir):
        """Test virtual environment detection."""
        # Create Python project with virtual environment
        python_dir = temp_dir / "python_with_venv"
        python_dir.mkdir()
        (python_dir / "pyproject.toml").write_text("[project]\nname = 'test'")

        # Create virtual environment directories
        venv_dirs = ["venv", ".venv", "env"]
        for venv_dir in venv_dirs:
            venv_path = python_dir / venv_dir
            venv_path.mkdir()
            (venv_path / "bin" / "python").parent.mkdir(parents=True)
            (venv_path / "bin" / "python").write_text("#!/usr/bin/env python")

        context = enhanced_context_analyzer.analyze_directory(python_dir)

        assert context.virtual_env in venv_dirs

    def test_language_detection_from_files(self):
        """Test language detection from file extensions."""
        # Test Python files
        python_files = ["main.py", "utils.py", "test_main.py"]
        language = detect_language_from_files(python_files)
        assert language == "Python"

        # Test JavaScript files
        js_files = ["app.js", "utils.ts", "component.jsx"]
        language = detect_language_from_files(js_files)
        assert language == "JavaScript"

        # Test mixed files - should return most common
        mixed_files = ["main.py", "utils.py", "app.js"]
        language = detect_language_from_files(mixed_files)
        assert language == "Python"  # Python files are more

        # Test unknown files
        unknown_files = ["data.txt", "config.ini"]
        language = detect_language_from_files(unknown_files)
        assert language == "Unknown"

    def test_dependency_parsing_python(self, enhanced_context_analyzer, temp_dir):
        """Test Python dependency parsing from various files."""
        python_dir = temp_dir / "python_deps"
        python_dir.mkdir()

        # Test pyproject.toml parsing
        (python_dir / "pyproject.toml").write_text(
            """
[project]
dependencies = [
    "requests>=2.25.0",
    "click>=8.0.0",
    "pydantic[email]>=2.0.0"
]
"""
        )

        context = enhanced_context_analyzer.analyze_directory(python_dir)

        assert "requests" in context.dependencies
        assert "click" in context.dependencies
        assert "pydantic" in context.dependencies

    def test_dependency_parsing_nodejs(self, enhanced_context_analyzer, temp_dir):
        """Test Node.js dependency parsing."""
        node_dir = temp_dir / "node_deps"
        node_dir.mkdir()

        # Test package.json parsing
        (node_dir / "package.json").write_text(
            """
{
  "dependencies": {
    "express": "^4.18.0",
    "@types/node": "^18.0.0"
  },
  "devDependencies": {
    "typescript": "^4.9.0"
  }
}
"""
        )

        context = enhanced_context_analyzer.analyze_directory(node_dir)

        assert "express" in context.dependencies
        assert "@types/node" in context.dependencies
        assert "typescript" in context.dependencies

    def test_error_handling_invalid_json(self, enhanced_context_analyzer, temp_dir):
        """Test error handling for invalid JSON files."""
        node_dir = temp_dir / "invalid_json"
        node_dir.mkdir()

        # Create invalid package.json
        (node_dir / "package.json").write_text("{ invalid json content")

        # Should not crash
        context = enhanced_context_analyzer.analyze_directory(node_dir)
        assert context.project_type in [ProjectType.NODEJS, ProjectType.GENERAL]

    def test_error_handling_permission_denied(self, enhanced_context_analyzer):
        """Test error handling for permission denied scenarios."""
        # Try to analyze a directory we can't read
        restricted_path = Path("/root")  # Typically not readable by normal users

        # Should not crash
        context = enhanced_context_analyzer.analyze_directory(restricted_path)
        assert context.project_type == ProjectType.GENERAL
        assert context.confidence == 0.0

    def test_mixed_project_detection(self, enhanced_context_analyzer, temp_dir):
        """Test detection when multiple project types are present."""
        mixed_dir = temp_dir / "mixed_project"
        mixed_dir.mkdir()

        # Add both Python and Node.js files
        (mixed_dir / "pyproject.toml").write_text("[project]\nname = 'test'")
        (mixed_dir / "package.json").write_text('{"name": "test"}')
        (mixed_dir / "main.py").write_text("print('hello')")
        (mixed_dir / "app.js").write_text("console.log('hello');")

        context = enhanced_context_analyzer.analyze_directory(mixed_dir)

        # Should detect one of them (preferably the stronger indicator)
        assert context.project_type in [ProjectType.PYTHON, ProjectType.NODEJS]
        assert context.confidence > 0.5

    def test_entry_point_detection(
        self, enhanced_context_analyzer, sample_project_dirs
    ):
        """Test entry point detection for different project types."""
        python_dir = sample_project_dirs["python"]
        context = enhanced_context_analyzer.analyze_directory(python_dir)

        assert len(context.entry_points) > 0
        assert any("main.py" in entry for entry in context.entry_points)

    def test_config_file_detection(
        self, enhanced_context_analyzer, sample_project_dirs
    ):
        """Test configuration file detection."""
        python_dir = sample_project_dirs["python"]
        context = enhanced_context_analyzer.analyze_directory(python_dir)

        assert "pyproject.toml" in context.config_files
        assert "requirements.txt" in context.config_files

    def test_context_caching_behavior(
        self, enhanced_context_analyzer, sample_project_dirs
    ):
        """Test that context analysis can be cached effectively."""
        python_dir = sample_project_dirs["python"]

        # Analyze same directory multiple times
        context1 = enhanced_context_analyzer.analyze_directory(python_dir)
        context2 = enhanced_context_analyzer.analyze_directory(python_dir)

        # Results should be consistent
        assert context1.project_type == context2.project_type
        assert context1.confidence == context2.confidence
        assert context1.main_language == context2.main_language


class TestProjectContext:
    """Test the ProjectContext dataclass."""

    def test_project_context_creation(self):
        """Test creating project contexts."""
        context = ProjectContext(
            project_type=ProjectType.PYTHON,
            confidence=0.95,
            main_language="Python",
            package_manager="pip",
            dependencies=["requests", "click"],
            virtual_env="venv",
            git_branch="main",
            git_status="clean",
            config_files=["pyproject.toml"],
            entry_points=["main.py"],
        )

        assert context.project_type == ProjectType.PYTHON
        assert context.confidence == 0.95
        assert context.main_language == "Python"
        assert context.package_manager == "pip"
        assert "requests" in context.dependencies
        assert context.virtual_env == "venv"
        assert context.git_branch == "main"
        assert context.git_status == "clean"
        assert "pyproject.toml" in context.config_files
        assert "main.py" in context.entry_points

    def test_project_context_defaults(self):
        """Test project context with default values."""
        context = ProjectContext(project_type=ProjectType.GENERAL, confidence=0.5)

        assert context.main_language == "Unknown"
        assert context.package_manager == ""
        assert context.dependencies == []
        assert context.virtual_env == ""
        assert context.git_branch == ""
        assert context.git_status == ""
        assert context.config_files == []
        assert context.entry_points == []


class TestProjectType:
    """Test the ProjectType enum."""

    def test_project_type_values(self):
        """Test project type enum values."""
        assert ProjectType.PYTHON.value == "python"
        assert ProjectType.NODEJS.value == "nodejs"
        assert ProjectType.RUST.value == "rust"
        assert ProjectType.GO.value == "go"
        assert ProjectType.DOCKER.value == "docker"
        assert ProjectType.GIT.value == "git"
        assert ProjectType.GENERAL.value == "general"

    def test_project_type_from_string(self):
        """Test creating project types from strings."""
        assert ProjectType("python") == ProjectType.PYTHON
        assert ProjectType("nodejs") == ProjectType.NODEJS
        assert ProjectType("general") == ProjectType.GENERAL


@pytest.mark.integration
class TestContextIntegration:
    """Integration tests for context analysis."""

    def test_context_with_shell_session(self, shell_session, sample_project_dirs):
        """Test context integration with shell session."""
        python_dir = sample_project_dirs["python"]

        # Change to project directory
        shell_session.current_directory = python_dir
        shell_session._load_session_context()

        assert shell_session.current_project_context is not None
        assert shell_session.current_project_context.project_type == ProjectType.PYTHON

    def test_context_updates_on_directory_change(
        self, shell_session, sample_project_dirs
    ):
        """Test that context updates when changing directories."""
        python_dir = sample_project_dirs["python"]
        node_dir = sample_project_dirs["node"]

        # Start in Python directory
        shell_session.current_directory = python_dir
        shell_session._load_session_context()
        assert shell_session.current_project_context.project_type == ProjectType.PYTHON

        # Change to Node.js directory
        shell_session.current_directory = node_dir
        success, _, _ = shell_session._handle_cd_command(f"cd {node_dir}")

        assert success is True
        assert shell_session.current_project_context.project_type == ProjectType.NODEJS

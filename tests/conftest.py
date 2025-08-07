"""Pytest configuration and fixtures for LLMShell tests."""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import AsyncMock, MagicMock

import pytest

from llmshell.config import ExecutionConfig, LLMConfig, LLMShellConfig
from llmshell.context import EnhancedContextAnalyzer, ProjectContext, ProjectType
from llmshell.core import ShellSession
from llmshell.history import HistoryManager
from llmshell.llm import LLMProvider, LLMResponse


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_home_dir(temp_dir: Path) -> Path:
    """Create a mock home directory structure."""
    home_dir = temp_dir / "home" / "testuser"
    home_dir.mkdir(parents=True)

    # Create common directories
    (home_dir / ".llmshell").mkdir()
    (home_dir / "Documents").mkdir()
    (home_dir / "Downloads").mkdir()

    return home_dir


@pytest.fixture
def test_config() -> LLMShellConfig:
    """Create a test configuration."""
    return LLMShellConfig(
        llm=LLMConfig(
            provider="ollama",
            base_url="http://localhost:11434",
            model="llama3:latest",
            temperature=0.1,
            timeout=30,
        ),
        execution=ExecutionConfig(
            safe_mode=True, always_confirm=False, timeout=30, max_history=1000
        ),
    )


@pytest.fixture
def mock_llm_provider() -> LLMProvider:
    """Create a mock LLM provider."""
    mock_provider = MagicMock(spec=LLMProvider)
    mock_provider.config = LLMConfig(
        provider="ollama",
        base_url="http://localhost:11434",
        model="llama3:latest",
        temperature=0.1,
        timeout=30,
    )

    # Mock async methods
    mock_provider.translate = AsyncMock(
        return_value=LLMResponse(
            command="ls -la", explanation="List files in detail", error=None
        )
    )
    mock_provider.list_models = AsyncMock(
        return_value=["llama3:latest", "codellama:latest", "mistral:latest"]
    )
    mock_provider.test_connection = AsyncMock(return_value=True)
    mock_provider.close = MagicMock()

    return mock_provider


@pytest.fixture
def shell_session(
    test_config: LLMShellConfig,
    mock_llm_provider: LLMProvider,
    temp_dir: Path,
    monkeypatch,
) -> ShellSession:
    """Create a shell session for testing."""
    # Mock the home directory for history storage
    monkeypatch.setenv("HOME", str(temp_dir))

    session = ShellSession(test_config, mock_llm_provider)
    return session


@pytest.fixture
def history_manager(temp_dir: Path, monkeypatch) -> HistoryManager:
    """Create a history manager with temporary storage."""
    monkeypatch.setenv("HOME", str(temp_dir))
    return HistoryManager()


@pytest.fixture
def sample_project_dirs(temp_dir: Path) -> dict[str, Path]:
    """Create sample project directories for testing."""
    projects = {}

    # Python project
    python_dir = temp_dir / "python_project"
    python_dir.mkdir()
    (python_dir / "pyproject.toml").write_text(
        """
[project]
name = "test-project"
dependencies = ["requests", "click"]
"""
    )
    (python_dir / "src" / "main.py").parent.mkdir(parents=True)
    (python_dir / "src" / "main.py").write_text("print('hello')")
    (python_dir / "requirements.txt").write_text("requests>=2.25.0\nclick>=8.0.0")
    projects["python"] = python_dir

    # Node.js project
    node_dir = temp_dir / "node_project"
    node_dir.mkdir()
    (node_dir / "package.json").write_text(
        """
{
  "name": "test-app",
  "dependencies": {
    "express": "^4.18.0",
    "react": "^18.0.0"
  }
}
"""
    )
    (node_dir / "src" / "index.js").parent.mkdir(parents=True)
    (node_dir / "src" / "index.js").write_text("console.log('hello');")
    projects["node"] = node_dir

    # Rust project
    rust_dir = temp_dir / "rust_project"
    rust_dir.mkdir()
    (rust_dir / "Cargo.toml").write_text(
        """
[package]
name = "test-app"
version = "0.1.0"

[dependencies]
serde = "1.0"
tokio = "1.0"
"""
    )
    (rust_dir / "src" / "main.rs").parent.mkdir(parents=True)
    (rust_dir / "src" / "main.rs").write_text('fn main() { println!("Hello"); }')
    projects["rust"] = rust_dir

    # Go project
    go_dir = temp_dir / "go_project"
    go_dir.mkdir()
    (go_dir / "go.mod").write_text(
        """
module test-app

go 1.21

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/gorilla/mux v1.8.0
)
"""
    )
    (go_dir / "main.go").write_text('package main\n\nfunc main() { println("Hello") }')
    projects["go"] = go_dir

    # Docker project
    docker_dir = temp_dir / "docker_project"
    docker_dir.mkdir()
    (docker_dir / "Dockerfile").write_text(
        """
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "app.py"]
"""
    )
    (docker_dir / "docker-compose.yml").write_text(
        """
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
"""
    )
    projects["docker"] = docker_dir

    # Git repository
    git_dir = temp_dir / "git_project"
    git_dir.mkdir()
    (git_dir / ".git").mkdir()
    (git_dir / ".git" / "HEAD").write_text("ref: refs/heads/main")
    (git_dir / ".git" / "refs" / "heads").mkdir(parents=True)
    (git_dir / ".git" / "refs" / "heads" / "main").write_text("abc123def456")
    projects["git"] = git_dir

    return projects


@pytest.fixture
def enhanced_context_analyzer() -> EnhancedContextAnalyzer:
    """Create an enhanced context analyzer."""
    return EnhancedContextAnalyzer()


@pytest.fixture
def sample_project_context() -> ProjectContext:
    """Create a sample project context."""
    return ProjectContext(
        project_type=ProjectType.PYTHON,
        confidence=0.95,
        main_language="Python",
        package_manager="pip",
        dependencies=["requests", "click", "pytest"],
        virtual_env="venv",
        git_branch="main",
        git_status="clean",
        config_files=["pyproject.toml", "requirements.txt"],
        entry_points=["src/main.py"],
    )


@pytest.fixture(autouse=True)
def mock_subprocess(monkeypatch):
    """Mock subprocess calls to prevent actual command execution during tests."""
    import subprocess

    def mock_run(*args, **kwargs):
        """Mock subprocess.run to return safe test data."""
        result = MagicMock()
        result.returncode = 0
        result.stdout = "test output"
        result.stderr = ""
        return result

    monkeypatch.setattr(subprocess, "run", mock_run)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    """Clean environment variables for consistent testing."""
    # Remove environment variables that might affect tests
    env_vars_to_remove = [
        "LLMSHELL_CONFIG",
        "LLMSHELL_DEBUG",
        "OLLAMA_HOST",
    ]

    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)

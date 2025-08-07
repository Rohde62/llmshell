"""Tests for LLMShell configuration module."""

import tempfile
from pathlib import Path

import pytest
import yaml

from llmshell.config import (
    ExecutionConfig,
    LLMConfig,
    LLMShellConfig,
    LoggingConfig,
    create_default_config,
    load_config_file,
)


def test_llm_config_defaults():
    """Test LLMConfig default values."""
    config = LLMConfig()
    assert config.provider == "ollama"
    assert config.base_url == "http://localhost:11434"
    assert config.model == "llama3:latest"
    assert config.timeout == 30
    assert config.temperature == 0.1


def test_execution_config_defaults():
    """Test ExecutionConfig default values."""
    config = ExecutionConfig()
    assert config.always_confirm is True
    assert config.safe_mode is True
    assert config.timeout == 60
    assert "rm -rf" in config.dangerous_commands


def test_logging_config_defaults():
    """Test LoggingConfig default values."""
    config = LoggingConfig()
    assert config.level == "INFO"
    assert config.log_commands is True
    assert config.log_file is None


def test_main_config_defaults():
    """Test LLMShellConfig default values."""
    config = LLMShellConfig()
    assert isinstance(config.llm, LLMConfig)
    assert isinstance(config.execution, ExecutionConfig)
    assert isinstance(config.logging, LoggingConfig)


def test_load_config_file():
    """Test loading configuration from YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_data = {
            "llm": {"model": "test-model", "timeout": 60},
            "execution": {"safe_mode": False},
        }
        yaml.dump(config_data, f)
        f.flush()

        try:
            loaded = load_config_file(Path(f.name))
            assert loaded["llm"]["model"] == "test-model"
            assert loaded["llm"]["timeout"] == 60
            assert loaded["execution"]["safe_mode"] is False
        finally:
            Path(f.name).unlink()


def test_load_config_file_not_found():
    """Test loading non-existent config file returns empty dict."""
    result = load_config_file(Path("/nonexistent/file.yaml"))
    assert result == {}


def test_create_default_config():
    """Test creating default configuration file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        create_default_config(config_path)

        assert config_path.exists()

        # Load and verify content
        with open(config_path) as f:
            data = yaml.safe_load(f)

        assert data["llm"]["provider"] == "ollama"
        assert data["llm"]["model"] == "llama3"
        assert data["execution"]["safe_mode"] is True


def test_config_with_custom_values():
    """Test creating config with custom values."""
    config = LLMShellConfig(
        llm=LLMConfig(model="custom-model", timeout=120),
        execution=ExecutionConfig(safe_mode=False),
    )

    assert config.llm.model == "custom-model"
    assert config.llm.timeout == 120
    assert config.execution.safe_mode is False
    # Other values should remain default
    assert config.llm.provider == "ollama"

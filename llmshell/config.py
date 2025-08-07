"""Configuration management for LLMShell."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class LLMConfig(BaseModel):
    """Configuration for LLM integration."""

    provider: str = Field(
        default="ollama", description="LLM provider (ollama, llamacpp)"
    )
    base_url: str = Field(
        default="http://localhost:11434", description="Base URL for LLM API"
    )
    model: str = Field(default="llama3:latest", description="Model name to use")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    temperature: float = Field(default=0.1, description="Sampling temperature")
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens to generate"
    )


class ExecutionConfig(BaseModel):
    """Configuration for command execution."""

    always_confirm: bool = Field(
        default=True, description="Always require confirmation"
    )
    safe_mode: bool = Field(default=True, description="Enable safety checks")
    dangerous_commands: list[str] = Field(
        default_factory=lambda: [
            "rm -rf",
            "sudo rm",
            "mkfs",
            "dd if=",
            ":(){ :|:& };:",  # Fork bomb
            "chmod -R 777",
            "chown -R",
        ],
        description="Commands that require extra confirmation",
    )
    timeout: int = Field(default=60, description="Command execution timeout")


class LoggingConfig(BaseModel):
    """Configuration for logging."""

    level: str = Field(default="INFO", description="Log level")
    log_commands: bool = Field(default=True, description="Log executed commands")
    log_file: Optional[str] = Field(default=None, description="Log file path")


class LLMShellConfig(BaseSettings):
    """Main configuration class for LLMShell."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    class Config:
        env_prefix = "LLMSHELL_"
        env_nested_delimiter = "__"


def get_config_paths() -> list[Path]:
    """Get list of possible configuration file paths in order of preference."""
    paths = []

    # Current directory
    paths.append(Path.cwd() / "llmshell.yaml")
    paths.append(Path.cwd() / "llmshell.yml")

    # User config directory
    if xdg_config := os.getenv("XDG_CONFIG_HOME"):
        config_dir = Path(xdg_config) / "llmshell"
    else:
        config_dir = Path.home() / ".config" / "llmshell"

    paths.append(config_dir / "config.yaml")
    paths.append(config_dir / "config.yml")

    # User home directory
    paths.append(Path.home() / ".llmshell.yaml")
    paths.append(Path.home() / ".llmshell.yml")

    return paths


def load_config_file(path: Path) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    try:
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing config file {path}: {e}")


def load_config() -> LLMShellConfig:
    """Load configuration from files and environment variables."""
    config_data = {}

    # Load from config files (first found wins)
    for path in get_config_paths():
        if path.exists():
            config_data = load_config_file(path)
            break

    # Create config with file data and environment variables
    return LLMShellConfig(**config_data)


def create_default_config(path: Path) -> None:
    """Create a default configuration file."""
    path.parent.mkdir(parents=True, exist_ok=True)

    default_config = {
        "llm": {
            "provider": "ollama",
            "base_url": "http://localhost:11434",
            "model": "llama3",
            "timeout": 30,
            "temperature": 0.1,
        },
        "execution": {"always_confirm": True, "safe_mode": True, "timeout": 60},
        "logging": {"level": "INFO", "log_commands": True},
    }

    with open(path, "w") as f:
        yaml.dump(default_config, f, default_flow_style=False, indent=2)


if __name__ == "__main__":
    # Example usage
    config = load_config()
    print(f"Loaded config: {config}")

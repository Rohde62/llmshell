# LLMShell 🚀

**A privacy-respecting Linux shell that translates natural language to bash commands using local LLMs**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## ✨ Features

- 🤖 **Natural Language Interface**: Transform commands like "show me all python files" into `find . -name "*.py"`
- 🔒 **Privacy-First**: Uses local LLMs (Ollama) - your commands never leave your machine
- 🛡️ **Advanced Safety Analysis**: 5-tier risk assessment with intelligent confirmation prompts
- 📊 **Smart Context Awareness**: Automatically detects project types and provides relevant suggestions
- 📜 **Persistent History**: SQLite-backed command history with powerful search and analytics
- 🎯 **Model Management**: Easy switching between different LLM models with fuzzy matching
- ⚡ **Performance Optimized**: Efficient caching and background operations
- 🎨 **Beautiful Interface**: Rich terminal UI with syntax highlighting and progress indicators

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- [Ollama](https://ollama.ai) installed and running
- At least one language model (e.g., `ollama pull llama3`)

### Installation

#### Option 1: pipx (Recommended)
```bash
pipx install llmshell
```

#### Option 2: pip
```bash
pip install llmshell
```

#### Option 3: From Source
```bash
git clone https://github.com/jakobr-dev/llmshell.git
cd llmshell
pip install -e .
```

### First Run

```bash
llmshell
```

You'll be greeted with an interactive shell where you can use natural language:

```
🚀 LLMShell v0.1.0
Welcome to LLMShell! 🚀

Type natural language commands or use direct bash commands.
Type '.help' for help, '.exit' to quit.

🤖 [myproject]> list all python files
```

## 📖 Usage Guide

### Natural Language Commands

LLMShell excels at translating natural language into bash commands:

```bash
# File operations
"show me all python files" → find . -name "*.py"
"list files larger than 100MB" → find . -type f -size +100M
"count lines in all js files" → find . -name "*.js" -exec wc -l {} +

# System monitoring
"show disk usage" → df -h
"display running processes" → ps aux
"check memory usage" → free -h

# Development workflows
"run tests" → pytest (in Python projects)
"build project" → npm run build (in Node.js projects)
"check git status" → git status
```

### Direct Commands

You can also use LLMShell as a regular shell:

```bash
🤖 [myproject]> ls -la
💻 [myproject]> cd src/
💻 [src]> grep -r "TODO" .
```

### Built-in Commands

LLMShell provides several built-in commands for enhanced functionality:

#### Help and Information
- `.help` - Show comprehensive help
- `.context` - Display current project context
- `.pwd` - Show current directory

#### Mode Management
- `.mode` - Toggle between AI-powered and direct mode
- `.models` - List available LLM models
- `.model <name>` - Switch to a different model

#### History Management
- `.history` - Show recent command history
- `.history stats` - Display detailed statistics
- `.history search <term>` - Search command history
- `.history export <file>` - Export history to JSON
- `.history clear` - Clear all history

#### Context-Aware Features
- `.context analyze` - Re-analyze current directory
- `.suggest <intent>` - Get context-aware command suggestions

## 🎯 Advanced Features

### Project Context Detection

LLMShell automatically detects your project type and adapts suggestions accordingly:

- **Python Projects**: Detects virtual environments, dependencies from pyproject.toml/requirements.txt
- **Node.js Projects**: Reads package.json, suggests npm/yarn commands
- **Rust Projects**: Understands Cargo.toml, suggests cargo commands
- **Go Projects**: Detects go.mod, provides go-specific suggestions
- **Docker Projects**: Recognizes Dockerfiles and docker-compose files
- **Git Repositories**: Shows branch info and git status

### Safety Analysis

Commands are analyzed for potential risks with a 5-tier system:

- 🟢 **SAFE**: No risks detected
- 🟡 **LOW**: Minor risks, confirmation in safe mode
- 🟠 **MEDIUM**: Moderate risks, requires confirmation
- 🔴 **HIGH**: Significant risks, strong warning
- 💀 **CRITICAL**: Extremely dangerous, multiple confirmations required

### Smart Suggestions

Get context-aware command suggestions based on your project:

```bash
🤖 [python-project]> .suggest testing
💡 Suggestions for 'testing':
  1. pytest
  2. python -m pytest tests/
  3. pytest --cov=src

📜 From your history:
  1. pytest --verbose
```

### History Analytics

Powerful history system with SQLite backend:

```bash
🤖 [myproject]> .history stats
📊 Command History Statistics:
Total Commands: 1,247
Success Rate: 94.3%
Average Execution Time: 234ms
Most Used: git status (43 times)
Project Context: Python (67%), Node.js (23%), General (10%)
```

## 🔧 Configuration

LLMShell uses YAML configuration files located in `~/.llmshell/config.yaml`:

```yaml
llm:
  provider: "ollama"
  base_url: "http://localhost:11434"
  model: "llama3:latest"
  temperature: 0.1
  timeout: 30

execution:
  safe_mode: true
  always_confirm: false
  timeout: 30
  max_history: 1000
```

### Environment Variables

- `LLMSHELL_CONFIG`: Path to custom config file
- `OLLAMA_HOST`: Override Ollama server URL
- `LLMSHELL_DEBUG`: Enable debug logging

## 🛠️ Development

### Setting up Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run with coverage
pytest --cov=llmshell
```

### Project Structure

```
llmshell/
├── llmshell/           # Main package
│   ├── __init__.py
│   ├── cli.py          # CLI interface
│   ├── config.py       # Configuration management
│   ├── core.py         # Core shell logic
│   └── llm.py          # LLM integration
├── scripts/            # Development scripts
├── tests/              # Test suite
├── pyproject.toml      # Project configuration
└── README.md
```

## Roadmap

- [x] Project scaffolding and dependencies
- [x] Basic CLI loop with LLM translation
- [x] Safe execution with confirmations
- [x] Enhanced context awareness and project detection
- [x] Session history and context injection with SQLite backend
- [x] Advanced safety analysis with 5-tier risk assessment
- [x] Model management and fuzzy matching
- [x] Comprehensive testing framework
- [x] Production build system and CI/CD pipeline
- [x] Packaging and distribution
- [ ] 🚀 **v1.0.0 Release** - Ready for production use
- [ ] Community feedback and feature requests
- [ ] Performance optimizations and additional LLM provider support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run the test suite
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Security

LLMShell prioritizes security and privacy:
- All processing happens locally
- No network requests to external services
- Commands require explicit confirmation before execution
- Built-in detection of potentially dangerous operations

## Support

- Create an issue for bug reports or feature requests
- Check existing issues before creating new ones
- Include system information and error messages in bug reports

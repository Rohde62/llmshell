# Changelog

All notable changes to LLMShell will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Production Polish Complete**: Comprehensive testing framework with 99 tests
- **Enterprise Build System**: Multi-format distributions (wheel, sdist, AppImage, Debian, Homebrew)
- **CI/CD Pipeline**: GitHub Actions with automated testing, quality checks, and releases
- **Developer Experience**: Pre-commit hooks, tox configuration, advanced test runner
- **Code Quality**: Black/isort formatting, comprehensive linting and type checking
- **Documentation**: Production-grade README, CONTRIBUTING guidelines, comprehensive help

### Changed
- Upgraded to production-ready status with enterprise-grade infrastructure
- Enhanced testing coverage and reliability
- Improved build and distribution processes

### Fixed
- Resolved import dependencies and module structure issues
- Fixed test infrastructure and coverage reporting
- Corrected type annotations and code quality issues

## [0.1.0] - 2024-08-06

### Added
- Initial release of LLMShell
- Natural language to bash command translation using local LLMs
- Integration with Ollama for privacy-preserving AI inference
- Advanced safety analysis with 5-tier risk assessment system
- Intelligent context awareness and project type detection
- Persistent command history with SQLite backend
- Model management with fuzzy matching and switching
- Rich terminal interface with syntax highlighting
- Interactive shell with dual mode operation (AI-powered and direct)
- Comprehensive configuration system with YAML support
- Built-in help system and context-aware suggestions

### Core Features
- **Shell Session Management**: Interactive shell with command processing
- **LLM Integration**: Async Ollama API client with error handling
- **Safety Analysis**: Command risk assessment and confirmation prompts
- **History Management**: SQLite-backed persistent command history
- **Context Analysis**: Automatic project type detection and suggestions
- **Configuration**: Flexible YAML-based configuration system

### Supported Project Types
- Python (pyproject.toml, requirements.txt, virtual environments)
- Node.js (package.json, npm/yarn)
- Rust (Cargo.toml, cargo commands)
- Go (go.mod, go commands)
- Docker (Dockerfile, docker-compose)
- Git repositories (branch info, status)
- General projects (basic file operations)

### Safety Features
- 5-tier risk assessment (Safe, Low, Medium, High, Critical)
- Dangerous command detection and warnings
- Confirmation prompts based on risk level
- Safe mode with additional protections
- Command preview with syntax highlighting

### CLI Commands
- `.help` - Comprehensive help system
- `.mode` - Toggle between AI and direct modes
- `.models` - List and switch between available models
- `.history` - Command history management and search
- `.context` - Project context display and analysis
- `.suggest` - Context-aware command suggestions

### Technical Implementation
- Async/await for non-blocking operations
- SQLite database for persistent storage
- Rich terminal UI with progress indicators
- Comprehensive error handling and recovery
- Type hints and modern Python practices
- Extensive test coverage with pytest

### Dependencies
- Rich (terminal interface)
- Click (CLI framework)
- httpx (HTTP client)
- Pydantic (configuration)
- PyYAML (config files)
- jsonschema (validation)

[Unreleased]: https://github.com/jakobr-dev/llmshell/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jakobr-dev/llmshell/releases/tag/v0.1.0

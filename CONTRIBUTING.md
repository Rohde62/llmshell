# Contributing to LLMShell

Thank you for your interest in contributing to LLMShell! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/llmshell.git
   cd llmshell
   ```
3. **Set up development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -e ".[dev,test,build]"
   ```
4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
5. **Make your changes** and test them
6. **Submit a pull request**

## 🛠️ Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- [Ollama](https://ollama.ai) for testing LLM integration
- Basic familiarity with async Python and CLI development

### Installing Dependencies

```bash
# Install all development dependencies
pip install -e ".[dev,test,build]"

# Or install specific dependency groups
pip install -e ".[dev]"     # Development tools
pip install -e ".[test]"    # Testing tools
pip install -e ".[build]"   # Build and distribution tools
```

### Development Tools

The project uses several tools to maintain code quality:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Linting
- **MyPy**: Type checking
- **Pytest**: Testing framework
- **Pre-commit**: Git hooks for code quality

### Setting Up Pre-commit Hooks

```bash
pre-commit install
```

This will automatically run code quality checks before each commit.

## 🧪 Testing

### Running Tests

```bash
# Run all tests with coverage
python scripts/test_runner.py

# Run only unit tests
python scripts/test_runner.py --no-integration

# Run quick tests (unit tests + basic linting)
python scripts/test_runner.py --quick

# Run specific test files
pytest tests/test_core.py -v
pytest tests/test_history.py -v
```

### Test Categories

- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Benchmarks and memory usage tests

### Writing Tests

When adding new features or fixing bugs, please include tests:

```python
import pytest
from llmshell.core import ShellSession

def test_new_feature(shell_session):
    """Test description of what this tests."""
    # Arrange
    input_data = "test input"
    
    # Act
    result = shell_session.process_input(input_data)
    
    # Assert
    assert result.success is True
    assert "expected output" in result.output
```

### Test Fixtures

Use the provided fixtures in `tests/conftest.py`:

- `shell_session`: Configured ShellSession for testing
- `temp_dir`: Temporary directory for file operations
- `mock_llm_provider`: Mocked LLM provider
- `sample_project_dirs`: Pre-configured project directories

## 📝 Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line length**: 88 characters (Black default)
- **Type hints**: Required for all public functions
- **Docstrings**: Google style for all public classes and functions
- **Imports**: Sorted using isort

### Code Formatting

```bash
# Format code with Black
black llmshell/ tests/

# Sort imports with isort
isort llmshell/ tests/

# Check linting with Flake8
flake8 llmshell/ tests/

# Type checking with MyPy
mypy llmshell/
```

### Documentation Style

```python
def example_function(param1: str, param2: int) -> bool:
    """Brief description of the function.
    
    Longer description if needed. Explain the purpose,
    behavior, and any important details.
    
    Args:
        param1: Description of the first parameter.
        param2: Description of the second parameter.
        
    Returns:
        Description of the return value.
        
    Raises:
        ValueError: When parameter validation fails.
        RuntimeError: When operation cannot be completed.
    """
    pass
```

## 🏗️ Architecture Overview

### Core Components

```
llmshell/
├── cli.py          # Command-line interface and argument parsing
├── core.py         # Main shell session logic and command processing
├── llm.py          # LLM provider interface and Ollama integration
├── config.py       # Configuration management and validation
├── safety.py       # Command safety analysis and risk assessment
├── history.py      # Persistent command history with SQLite
└── context.py      # Project context detection and analysis
```

### Design Principles

1. **Privacy First**: All LLM processing happens locally
2. **Safety by Default**: Dangerous commands require confirmation
3. **Extensible**: Modular design for easy feature additions
4. **Performance**: Async operations and efficient caching
5. **User Experience**: Beautiful, intuitive interface

### Adding New Features

When adding features, consider:

1. **Does it align with the privacy-first principle?**
2. **How does it affect safety and security?**
3. **Is the API consistent with existing patterns?**
4. **Are there comprehensive tests?**
5. **Is the documentation updated?**

## 🐛 Bug Reports

When reporting bugs, please include:

1. **LLMShell version**: `llmshell --version`
2. **Python version**: `python --version`
3. **Operating system** and version
4. **Ollama version** and model being used
5. **Steps to reproduce** the issue
6. **Expected vs actual behavior**
7. **Error messages** or logs
8. **Configuration** (if relevant)

### Debug Information

Enable debug mode to get more detailed logs:

```bash
export LLMSHELL_DEBUG=1
llmshell
```

## 💡 Feature Requests

Before requesting a feature:

1. **Check existing issues** to avoid duplicates
2. **Explain the use case** and why it's needed
3. **Provide examples** of how it would work
4. **Consider privacy implications**
5. **Think about the user experience**

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally (`python scripts/test_runner.py`)
- [ ] Code is formatted (`black llmshell/ tests/`)
- [ ] Imports are sorted (`isort llmshell/ tests/`)
- [ ] Linting passes (`flake8 llmshell/ tests/`)
- [ ] Type checking passes (`mypy llmshell/`)
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for significant changes)

### Pull Request Process

1. **Create a clear title** describing the change
2. **Fill out the PR template** completely
3. **Link related issues** using "Fixes #123" syntax
4. **Add reviewers** if you know who should review
5. **Respond to feedback** promptly
6. **Keep the PR focused** - one feature/fix per PR

### PR Template

```markdown
## Description
Brief description of what this PR does.

## Changes
- List of changes made
- Use bullet points for clarity

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Documentation
- [ ] README updated (if needed)
- [ ] Docstrings added/updated
- [ ] CHANGELOG updated

## Related Issues
Fixes #123
Related to #456
```

## 🔄 Release Process

Releases are managed by maintainers and follow semantic versioning:

- **Patch** (0.1.1): Bug fixes, minor improvements
- **Minor** (0.2.0): New features, non-breaking changes
- **Major** (1.0.0): Breaking changes, major milestones

### Version Numbering

- Development: `0.x.y-dev`
- Release Candidates: `0.x.y-rc1`
- Stable Releases: `0.x.y`

## 🤝 Community Guidelines

### Code of Conduct

We follow the [Contributor Covenant](https://www.contributor-covenant.org/). Please be:

- **Respectful**: Treat all community members with respect
- **Inclusive**: Welcome newcomers and diverse perspectives
- **Collaborative**: Work together to improve the project
- **Constructive**: Provide helpful feedback and suggestions

### Communication Channels

- **Issues**: Bug reports and feature requests
- **Discussions**: General questions and community chat
- **Pull Requests**: Code review and development discussion

### Getting Help

If you need help:

1. Check the **documentation** first
2. Search **existing issues** for similar problems
3. Ask in **GitHub Discussions** for general questions
4. Create an **issue** for specific bugs or feature requests

## 🏆 Recognition

Contributors are recognized in several ways:

- **CONTRIBUTORS.md**: All contributors are listed
- **Release Notes**: Significant contributions are highlighted
- **GitHub**: Contributions are tracked and displayed

## 📚 Learning Resources

### Python Development
- [Python Official Documentation](https://docs.python.org/3/)
- [Real Python Tutorials](https://realpython.com/)
- [Async Programming Guide](https://docs.python.org/3/library/asyncio.html)

### Project-Specific
- [Click Documentation](https://click.palletsprojects.com/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Pydantic Documentation](https://pydantic.dev/)
- [Ollama Documentation](https://ollama.ai/docs)

### Testing
- [Pytest Documentation](https://pytest.org/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)

## 🎯 Current Priorities

Check the [GitHub Projects](https://github.com/jakobr-dev/llmshell/projects) for current development priorities and roadmap.

### Good First Issues

Look for issues labeled `good-first-issue` for newcomer-friendly contributions.

### Areas Needing Help

- Documentation improvements
- Test coverage expansion
- Performance optimizations
- New project type detection
- Additional safety analysis patterns

Thank you for contributing to LLMShell! 🚀

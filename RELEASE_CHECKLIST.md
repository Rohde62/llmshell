# 🚀 LLMShell Release Checklist

This checklist ensures a smooth and professional release process for LLMShell.

## 📋 Pre-Release Checklist

### ✅ Code Quality & Testing
- [ ] All tests pass (`python scripts/test_runner.py`)
- [ ] Code coverage is adequate (>80%)
- [ ] All code is formatted with Black and isort
- [ ] No critical linting errors (flake8, mypy)
- [ ] Documentation is up to date
- [ ] CHANGELOG.md is updated with new version

### ✅ Version Management
- [ ] Version bumped in `pyproject.toml`
- [ ] Version updated in `__init__.py`
- [ ] CHANGELOG.md has new version entry
- [ ] Release notes prepared

### ✅ Dependencies & Compatibility
- [ ] All dependencies are pinned appropriately
- [ ] Python version compatibility tested (3.10+)
- [ ] Ollama integration tested with latest version
- [ ] All optional dependencies work correctly

### ✅ Build & Distribution
- [ ] Clean build environment (`python scripts/release_prepare.py --clean`)
- [ ] Wheel and source distributions build successfully
- [ ] Package metadata is correct
- [ ] Long description renders correctly on PyPI

## 🏗️ Build Process

### 1. Automated Release Preparation
```bash
# Run comprehensive release preparation
python scripts/release_prepare.py

# Or skip tests if already validated
python scripts/release_prepare.py --skip-tests
```

### 2. Manual Verification
```bash
# Test local installation
pip install dist/*.whl

# Verify command works
llmshell --help

# Test in clean environment
docker run --rm -it python:3.10 bash
pip install /path/to/dist/*.whl
llmshell --version
```

### 3. Package Validation
```bash
# Check package integrity
twine check dist/*

# Test upload to TestPyPI
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ llmshell
```

## 🚀 Release Process

### 1. GitHub Release
1. Create new release on GitHub
2. Use version tag (e.g., `v0.1.0`)
3. Upload distribution files
4. Include release notes from CHANGELOG
5. Mark as pre-release if beta

### 2. PyPI Publication
```bash
# Upload to PyPI
twine upload dist/*

# Verify on PyPI
pip install llmshell
```

### 3. Documentation Updates
- [ ] Update README badges if needed
- [ ] Update documentation links
- [ ] Announce on relevant platforms

## 📝 Post-Release Checklist

### ✅ Verification
- [ ] PyPI package installs correctly
- [ ] GitHub release is accessible
- [ ] Documentation is updated
- [ ] All links work correctly

### ✅ Communication
- [ ] Update project README with new features
- [ ] Consider blog post or announcement
- [ ] Update any external documentation

### ✅ Next Version Preparation
- [ ] Create new branch for next version
- [ ] Update version numbers for development
- [ ] Add "Unreleased" section to CHANGELOG

## 🔧 Release Scripts & Tools

### Available Scripts
- `scripts/release_prepare.py` - Comprehensive release preparation
- `scripts/test_runner.py` - Full test suite execution
- `scripts/build.py` - Multi-format build system

### Required Tools
```bash
# Install release tools
pip install build twine

# Verify tools
python -m build --help
twine --help
```

## 🚨 Emergency Procedures

### Rollback Release
```bash
# Remove from PyPI (if critical issues)
# Contact PyPI support for removal

# Create hotfix release
git checkout v0.1.0
git checkout -b hotfix/v0.1.1
# Apply fixes
# Follow release process with new version
```

### Critical Issues
1. Document the issue immediately
2. Assess impact and urgency
3. Prepare hotfix if necessary
4. Communicate with users
5. Update documentation

## 📊 Release Metrics

Track these metrics for each release:
- Download counts
- Installation success rate
- User feedback and issues
- Performance benchmarks
- Test coverage improvements

## 🎯 Release Goals

### v0.1.0 Goals
- [x] Core functionality working
- [x] Production-ready infrastructure
- [x] Comprehensive testing
- [x] Professional documentation
- [ ] Public release and community feedback

### Future Releases
- Enhanced LLM provider support
- Performance optimizations
- Additional project type detection
- Community-requested features

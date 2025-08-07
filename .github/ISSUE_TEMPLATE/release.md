---
name: Release Tracking
about: Track progress for a new release
title: 'Release v[VERSION] - [RELEASE_NAME]'
labels: ['release', 'tracking']
assignees: ''
---

# 🚀 Release v[VERSION] - [RELEASE_NAME]

## 📋 Release Information
- **Version**: v[VERSION]
- **Target Date**: [DATE]
- **Release Type**: [Major/Minor/Patch]
- **Breaking Changes**: [Yes/No]

## ✅ Pre-Release Checklist

### Code Quality & Testing
- [ ] All tests pass (`python scripts/test_runner.py`)
- [ ] Code coverage >80%
- [ ] Code formatted (Black/isort)
- [ ] No critical linting errors
- [ ] Documentation updated
- [ ] CHANGELOG.md updated

### Version Management
- [ ] Version bumped in `pyproject.toml`
- [ ] Version updated in `__init__.py`
- [ ] CHANGELOG.md has new version entry
- [ ] Release notes prepared

### Build & Distribution
- [ ] Release preparation script passes (`python scripts/release_prepare.py`)
- [ ] Packages build successfully
- [ ] Package validation passes (`twine check`)
- [ ] TestPyPI upload successful

## 🏗️ Release Tasks

### GitHub Release
- [ ] Create release draft
- [ ] Upload distribution files
- [ ] Include release notes
- [ ] Tag created and pushed

### PyPI Publication
- [ ] Upload to PyPI
- [ ] Verify installation works
- [ ] Test basic functionality

### Documentation
- [ ] README updated
- [ ] Documentation links verified
- [ ] Installation instructions current

## 📝 Post-Release

### Verification
- [ ] PyPI package installs correctly
- [ ] GitHub release accessible
- [ ] All links functional

### Communication
- [ ] Project README reflects new features
- [ ] Announcement prepared (if applicable)

### Next Version
- [ ] Development branch updated
- [ ] Next version milestone created

## 📊 Release Notes

### New Features
- 

### Improvements
- 

### Bug Fixes
- 

### Breaking Changes
- 

## 🔗 Links
- [ ] [PyPI Package](https://pypi.org/project/llmshell/)
- [ ] [GitHub Release](https://github.com/jakobr-dev/llmshell/releases)
- [ ] [Documentation](https://github.com/jakobr-dev/llmshell#readme)

---
**Release Manager**: @[USERNAME]
**Review Required**: [ ] Code Review [ ] QA Testing [ ] Documentation Review

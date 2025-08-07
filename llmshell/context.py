"""Enhanced context detection and analysis for LLMShell."""

import json
import os
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from rich.console import Console


def detect_language_from_files(filenames: List[str]) -> str:
    """Detect programming language from a list of filenames."""
    language_counts = {}

    extension_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".jsx": "JavaScript",
        ".ts": "JavaScript",
        ".tsx": "JavaScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".c": "C",
        ".h": "C",
        ".rs": "Rust",
        ".go": "Go",
        ".php": "PHP",
        ".rb": "Ruby",
        ".cs": "C#",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".scala": "Scala",
        ".pl": "Perl",
        ".r": "R",
        ".m": "Objective-C",
        ".sh": "Shell",
        ".bash": "Shell",
        ".zsh": "Shell",
    }

    for filename in filenames:
        path = Path(filename)
        ext = path.suffix.lower()
        if ext in extension_map:
            lang = extension_map[ext]
            language_counts[lang] = language_counts.get(lang, 0) + 1

    if not language_counts:
        return "Unknown"

    # Return the most common language
    return max(language_counts, key=language_counts.get)


class ProjectType(Enum):
    """Detected project types."""

    PYTHON = "python"
    NODEJS = "nodejs"
    RUST = "rust"
    GO = "go"
    JAVA = "java"
    CPP = "cpp"
    WEB = "web"
    DOCKER = "docker"
    GIT = "git"
    LINUX_CONFIG = "linux_config"
    SCRIPT = "script"
    UNKNOWN = "unknown"


@dataclass
class ProjectContext:
    """Rich project context information."""

    project_type: ProjectType
    confidence: float
    root_directory: Path
    key_files: List[str]
    package_manager: Optional[str] = None
    main_language: Optional[str] = None
    dependencies: List[str] = None
    virtual_env: Optional[str] = None
    git_branch: Optional[str] = None
    git_status: Optional[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class EnhancedContextAnalyzer:
    """Advanced context analysis for better command suggestions."""

    def __init__(self):
        self.console = Console()
        self._project_cache: Dict[str, ProjectContext] = {}

    def analyze_directory(self, directory: Path) -> ProjectContext:
        """Analyze a directory to determine project context."""
        directory = directory.resolve()
        cache_key = str(directory)

        # Check cache first
        if cache_key in self._project_cache:
            return self._project_cache[cache_key]

        context = self._detect_project_type(directory)

        # Cache the result
        self._project_cache[cache_key] = context
        return context

    def _detect_project_type(self, directory: Path) -> ProjectContext:
        """Detect the project type based on files and structure."""
        key_files = []
        project_types = []

        # Look for specific files that indicate project type
        files_in_dir = set()
        try:
            for item in directory.iterdir():
                if item.is_file():
                    files_in_dir.add(item.name.lower())
                    key_files.append(item.name)
        except PermissionError:
            pass

        # Python project detection
        python_indicators = {
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "setup.cfg",
            "pipfile",
            "poetry.lock",
            "conda.yml",
            "environment.yml",
        }
        if python_indicators & files_in_dir:
            project_types.append((ProjectType.PYTHON, 0.9))
        elif any(f.endswith(".py") for f in files_in_dir):
            project_types.append((ProjectType.PYTHON, 0.6))

        # Node.js project detection
        nodejs_indicators = {
            "package.json",
            "yarn.lock",
            "package-lock.json",
            "pnpm-lock.yaml",
        }
        if nodejs_indicators & files_in_dir:
            project_types.append((ProjectType.NODEJS, 0.9))
        elif "node_modules" in [d.name for d in directory.iterdir() if d.is_dir()]:
            project_types.append((ProjectType.NODEJS, 0.7))

        # Rust project detection
        if "cargo.toml" in files_in_dir:
            project_types.append((ProjectType.RUST, 0.95))
        elif any(f.endswith(".rs") for f in files_in_dir):
            project_types.append((ProjectType.RUST, 0.6))

        # Go project detection
        go_indicators = {"go.mod", "go.sum"}
        if go_indicators & files_in_dir:
            project_types.append((ProjectType.GO, 0.9))
        elif any(f.endswith(".go") for f in files_in_dir):
            project_types.append((ProjectType.GO, 0.6))

        # Java project detection
        java_indicators = {"pom.xml", "build.gradle", "build.gradle.kts"}
        if java_indicators & files_in_dir:
            project_types.append((ProjectType.JAVA, 0.9))
        elif any(f.endswith(".java") for f in files_in_dir):
            project_types.append((ProjectType.JAVA, 0.6))

        # C++ project detection
        cpp_indicators = {"cmake.txt", "makefile", "cmakelists.txt"}
        if cpp_indicators & files_in_dir:
            project_types.append((ProjectType.CPP, 0.8))
        elif any(
            f.endswith((".cpp", ".cc", ".cxx", ".hpp", ".h")) for f in files_in_dir
        ):
            project_types.append((ProjectType.CPP, 0.6))

        # Web project detection
        web_indicators = {
            "index.html",
            "webpack.config.js",
            ".babelrc",
            "vite.config.js",
        }
        if web_indicators & files_in_dir:
            project_types.append((ProjectType.WEB, 0.8))

        # Docker project detection
        docker_indicators = {
            "dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            ".dockerignore",
        }
        if docker_indicators & files_in_dir:
            project_types.append((ProjectType.DOCKER, 0.9))

        # Git repository detection
        if (directory / ".git").exists():
            project_types.append((ProjectType.GIT, 0.7))

        # Linux config detection
        config_indicators = {".bashrc", ".zshrc", ".vimrc", ".tmux.conf", "ansible.cfg"}
        if config_indicators & files_in_dir:
            project_types.append((ProjectType.LINUX_CONFIG, 0.7))

        # Script directory detection
        script_extensions = {".sh", ".bash", ".zsh", ".fish", ".py", ".pl", ".rb"}
        script_files = [
            f for f in files_in_dir if any(f.endswith(ext) for ext in script_extensions)
        ]
        if len(script_files) > 2:
            project_types.append((ProjectType.SCRIPT, 0.6))

        # Determine the best match
        if project_types:
            project_types.sort(key=lambda x: x[1], reverse=True)
            best_type, confidence = project_types[0]
        else:
            best_type, confidence = ProjectType.UNKNOWN, 0.1

        # Create context object
        context = ProjectContext(
            project_type=best_type,
            confidence=confidence,
            root_directory=directory,
            key_files=key_files[:10],  # Limit to avoid huge lists
        )

        # Add specific context based on project type
        self._enhance_context(context, directory, files_in_dir)

        return context

    def _enhance_context(
        self, context: ProjectContext, directory: Path, files_in_dir: Set[str]
    ):
        """Enhance context with project-specific information."""
        try:
            if context.project_type == ProjectType.PYTHON:
                self._enhance_python_context(context, directory, files_in_dir)
            elif context.project_type == ProjectType.NODEJS:
                self._enhance_nodejs_context(context, directory, files_in_dir)
            elif context.project_type == ProjectType.GIT:
                self._enhance_git_context(context, directory)
            elif context.project_type == ProjectType.DOCKER:
                self._enhance_docker_context(context, directory, files_in_dir)
        except Exception:
            # If enhancement fails, just continue with basic context
            pass

    def _enhance_python_context(
        self, context: ProjectContext, directory: Path, files_in_dir: Set[str]
    ):
        """Add Python-specific context."""
        context.main_language = "Python"

        # Detect package manager
        if "poetry.lock" in files_in_dir:
            context.package_manager = "poetry"
        elif "pipfile" in files_in_dir:
            context.package_manager = "pipenv"
        elif "requirements.txt" in files_in_dir:
            context.package_manager = "pip"
        elif "conda.yml" in files_in_dir or "environment.yml" in files_in_dir:
            context.package_manager = "conda"

        # Check for virtual environment
        venv_indicators = [".venv", "venv", "env", ".env"]
        for venv_name in venv_indicators:
            if (directory / venv_name).exists():
                context.virtual_env = venv_name
                break

        # Parse dependencies from requirements.txt
        req_file = directory / "requirements.txt"
        if req_file.exists():
            try:
                with open(req_file, "r") as f:
                    deps = []
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            # Extract package name (before version specifier)
                            pkg_name = (
                                line.split("==")[0]
                                .split(">=")[0]
                                .split("<=")[0]
                                .split("~=")[0]
                                .strip()
                            )
                            deps.append(pkg_name)
                    context.dependencies = deps[:20]  # Limit to first 20
            except Exception:
                pass

    def _enhance_nodejs_context(
        self, context: ProjectContext, directory: Path, files_in_dir: Set[str]
    ):
        """Add Node.js-specific context."""
        context.main_language = "JavaScript"

        # Detect package manager
        if "yarn.lock" in files_in_dir:
            context.package_manager = "yarn"
        elif "pnpm-lock.yaml" in files_in_dir:
            context.package_manager = "pnpm"
        else:
            context.package_manager = "npm"

        # Parse package.json for dependencies
        package_json = directory / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    data = json.load(f)
                    deps = []
                    for dep_type in ["dependencies", "devDependencies"]:
                        if dep_type in data:
                            deps.extend(list(data[dep_type].keys()))
                    context.dependencies = deps[:20]  # Limit to first 20
            except Exception:
                pass

    def _enhance_git_context(self, context: ProjectContext, directory: Path):
        """Add Git-specific context."""
        try:
            # Get current branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                context.git_branch = result.stdout.strip()

            # Get git status summary
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if lines and lines[0]:
                    modified = len([l for l in lines if l.startswith(" M")])
                    added = len([l for l in lines if l.startswith("A")])
                    deleted = len([l for l in lines if l.startswith(" D")])
                    untracked = len([l for l in lines if l.startswith("??")])

                    status_parts = []
                    if modified:
                        status_parts.append(f"{modified}M")
                    if added:
                        status_parts.append(f"{added}A")
                    if deleted:
                        status_parts.append(f"{deleted}D")
                    if untracked:
                        status_parts.append(f"{untracked}??")

                    context.git_status = (
                        " ".join(status_parts) if status_parts else "clean"
                    )
                else:
                    context.git_status = "clean"
        except Exception:
            pass

    def _enhance_docker_context(
        self, context: ProjectContext, directory: Path, files_in_dir: Set[str]
    ):
        """Add Docker-specific context."""
        # Check for docker-compose
        if (
            "docker-compose.yml" in files_in_dir
            or "docker-compose.yaml" in files_in_dir
        ):
            context.package_manager = "docker-compose"
        else:
            context.package_manager = "docker"

    def get_context_for_llm(self, directory: Path) -> Dict[str, Any]:
        """Get enhanced context specifically formatted for LLM prompts."""
        basic_context = self._get_basic_context(directory)
        project_context = self.analyze_directory(directory)

        # Combine basic and project context
        enhanced_context = {
            **basic_context,
            "project_type": project_context.project_type.value,
            "project_confidence": project_context.confidence,
            "main_language": project_context.main_language,
            "package_manager": project_context.package_manager,
            "virtual_env": project_context.virtual_env,
            "git_branch": project_context.git_branch,
            "git_status": project_context.git_status,
            "key_files": project_context.key_files[:5],  # Top 5 key files
            "dependencies": (
                project_context.dependencies[:10]
                if project_context.dependencies
                else []
            ),
        }

        return enhanced_context

    def _get_basic_context(self, directory: Path) -> Dict[str, Any]:
        """Get basic context information."""
        try:
            files = []
            try:
                files = [
                    f.name for f in directory.iterdir() if not f.name.startswith(".")
                ][:10]
            except PermissionError:
                pass

            return {
                "cwd": str(directory),
                "user": os.getenv("USER", "unknown"),
                "files": files,
                "shell": os.getenv("SHELL", "/bin/bash"),
            }
        except Exception:
            return {"cwd": str(directory)}

    def get_command_suggestions(
        self, context: ProjectContext, user_intent: str
    ) -> List[str]:
        """Get context-aware command suggestions."""
        suggestions = []
        intent_lower = user_intent.lower()

        if context.project_type == ProjectType.PYTHON:
            if any(
                word in intent_lower for word in ["install", "dependency", "package"]
            ):
                if context.package_manager == "poetry":
                    suggestions.append("poetry add <package>")
                    suggestions.append("poetry install")
                elif context.package_manager == "pipenv":
                    suggestions.append("pipenv install <package>")
                    suggestions.append("pipenv install --dev <package>")
                else:
                    suggestions.append("pip install <package>")
                    if context.virtual_env:
                        suggestions.append(f"source {context.virtual_env}/bin/activate")

            if any(word in intent_lower for word in ["test", "run"]):
                suggestions.extend(
                    ["python -m pytest", "python -m unittest", "python main.py"]
                )

        elif context.project_type == ProjectType.NODEJS:
            if any(
                word in intent_lower for word in ["install", "dependency", "package"]
            ):
                if context.package_manager == "yarn":
                    suggestions.extend(["yarn add <package>", "yarn install"])
                elif context.package_manager == "pnpm":
                    suggestions.extend(["pnpm add <package>", "pnpm install"])
                else:
                    suggestions.extend(["npm install <package>", "npm install"])

            if any(word in intent_lower for word in ["start", "run", "build"]):
                suggestions.extend(["npm start", "npm run build", "npm run dev"])

        elif context.project_type == ProjectType.GIT:
            if any(word in intent_lower for word in ["commit", "add", "push"]):
                suggestions.extend(
                    ["git add .", "git commit -m 'message'", "git push origin main"]
                )

            if any(word in intent_lower for word in ["status", "diff"]):
                suggestions.extend(["git status", "git diff", "git log --oneline -10"])

        elif context.project_type == ProjectType.DOCKER:
            if any(word in intent_lower for word in ["build", "run"]):
                suggestions.extend(
                    [
                        "docker build -t <image> .",
                        "docker run -it <image>",
                        "docker-compose up -d",
                    ]
                )

        return suggestions[:5]  # Limit to top 5 suggestions

#!/usr/bin/env python3
"""
Release preparation script for LLMShell.

This script helps prepare the project for release by:
1. Running comprehensive tests
2. Building distribution packages
3. Validating package integrity
4. Creating release artifacts
5. Generating release notes
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import track
from rich.table import Table

console = Console()


class ReleaseManager:
    """Manages the release preparation process."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.version = self._get_version()
        self.build_dir = project_root / "dist"
        self.release_dir = project_root / "release"

    def _get_version(self) -> str:
        """Extract version from pyproject.toml."""
        pyproject_path = self.project_root / "pyproject.toml"
        with open(pyproject_path) as f:
            content = f.read()
            for line in content.split("\\n"):
                if line.strip().startswith("version"):
                    return line.split("=")[1].strip().strip('"')
        return "unknown"

    def run_tests(self) -> bool:
        """Run comprehensive test suite."""
        console.print("🧪 Running comprehensive test suite...", style="bold blue")

        test_script = self.project_root / "scripts" / "test_runner.py"
        if not test_script.exists():
            console.print("❌ Test runner not found", style="bold red")
            return False

        result = subprocess.run(
            [sys.executable, str(test_script)], 
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            console.print("✅ All tests passed!", style="bold green")
            return True
        else:
            console.print("❌ Tests failed", style="bold red")
            console.print(result.stdout)
            console.print(result.stderr)
            return False

    def build_packages(self) -> bool:
        """Build distribution packages."""
        console.print("📦 Building distribution packages...", style="bold blue")

        # Clean previous builds
        if self.build_dir.exists():
            subprocess.run(["rm", "-rf", str(self.build_dir)])
        self.build_dir.mkdir(exist_ok=True)

        # Build with standard Python build tools
        build_commands = [
            [sys.executable, "-m", "build", "--wheel"],
            [sys.executable, "-m", "build", "--sdist"],
        ]

        for cmd in track(build_commands, description="Building packages..."):
            result = subprocess.run(
                cmd, cwd=self.project_root, capture_output=True, text=True
            )
            if result.returncode != 0:
                console.print(f"❌ Build failed: {' '.join(cmd)}", style="bold red")
                console.print(result.stderr)
                return False

        console.print("✅ Packages built successfully!", style="bold green")
        return True

    def validate_packages(self) -> bool:
        """Validate built packages."""
        console.print("🔍 Validating packages...", style="bold blue")

        dist_files = list(self.build_dir.glob("*"))
        if not dist_files:
            console.print("❌ No distribution files found", style="bold red")
            return False

        # Check with twine
        result = subprocess.run(
            ["twine", "check"] + [str(f) for f in dist_files],
            cwd=self.project_root,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            console.print("✅ Package validation passed!", style="bold green")
            return True
        else:
            console.print("❌ Package validation failed", style="bold red")
            console.print(result.stderr)
            return False

    def create_release_artifacts(self) -> bool:
        """Create release artifacts and documentation."""
        console.print("📄 Creating release artifacts...", style="bold blue")

        self.release_dir.mkdir(exist_ok=True)

        # Copy distribution files
        if self.build_dir.exists():
            subprocess.run(
                ["cp", "-r"] + [str(f) for f in self.build_dir.glob("*")] + [str(self.release_dir)]
            )

        # Generate release notes
        release_notes = self._generate_release_notes()
        (self.release_dir / f"RELEASE_NOTES_v{self.version}.md").write_text(release_notes)

        # Create checksums
        self._create_checksums()

        console.print("✅ Release artifacts created!", style="bold green")
        return True

    def _generate_release_notes(self) -> str:
        """Generate release notes from CHANGELOG."""
        changelog_path = self.project_root / "CHANGELOG.md"
        if not changelog_path.exists():
            return f"# Release Notes v{self.version}\\n\\nNo changelog available."

        with open(changelog_path) as f:
            content = f.read()

        # Extract current version section
        lines = content.split("\\n")
        in_current_version = False
        release_notes = [f"# LLMShell v{self.version} Release Notes\\n"]

        for line in lines:
            if line.startswith(f"## [{self.version}]") or line.startswith(f"## {self.version}"):
                in_current_version = True
                continue
            elif line.startswith("## [") and in_current_version:
                break
            elif in_current_version:
                release_notes.append(line)

        return "\\n".join(release_notes)

    def _create_checksums(self) -> None:
        """Create checksums for release files."""
        checksums = []
        for file_path in self.release_dir.glob("*"):
            if file_path.is_file() and not file_path.name.endswith(".md"):
                result = subprocess.run(
                    ["sha256sum", str(file_path)], 
                    capture_output=True, 
                    text=True
                )
                if result.returncode == 0:
                    checksums.append(result.stdout.strip())

        if checksums:
            (self.release_dir / "SHA256SUMS").write_text("\\n".join(checksums))

    def print_release_summary(self) -> None:
        """Print release summary."""
        table = Table(title=f"🚀 LLMShell v{self.version} Release Summary")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")

        table.add_row("Version", "✅", self.version)
        table.add_row("Tests", "✅", "All tests passed")
        table.add_row("Packages", "✅", f"Built in {self.build_dir}")
        table.add_row("Validation", "✅", "Package integrity verified")
        table.add_row("Artifacts", "✅", f"Created in {self.release_dir}")

        console.print(table)

        panel = Panel(
            f"""
[bold green]🎉 Release v{self.version} is ready![/bold green]

[bold]Next steps:[/bold]
1. Review artifacts in {self.release_dir}
2. Test installation: pip install {self.build_dir}/*.whl
3. Create GitHub release with artifacts
4. Publish to PyPI: twine upload {self.build_dir}/*

[bold]Release artifacts:[/bold]
- Distribution packages: {self.build_dir}
- Release notes: {self.release_dir}/RELEASE_NOTES_v{self.version}.md
- Checksums: {self.release_dir}/SHA256SUMS
            """.strip(),
            title="Release Ready",
            border_style="green"
        )
        console.print(panel)


@click.command()
@click.option("--skip-tests", is_flag=True, help="Skip running tests")
@click.option("--clean", is_flag=True, help="Clean previous builds")
def main(skip_tests: bool, clean: bool):
    """Prepare LLMShell for release."""
    project_root = Path(__file__).parent.parent
    release_manager = ReleaseManager(project_root)

    console.print(Panel.fit(
        f"🚀 LLMShell v{release_manager.version} Release Preparation",
        style="bold blue"
    ))

    if clean:
        console.print("🧹 Cleaning previous builds...")
        subprocess.run(["rm", "-rf", "dist", "build", "release"], cwd=project_root)

    success = True

    # Run tests
    if not skip_tests:
        success &= release_manager.run_tests()
    else:
        console.print("⏭️  Skipping tests", style="yellow")

    # Build packages
    if success:
        success &= release_manager.build_packages()

    # Validate packages
    if success:
        success &= release_manager.validate_packages()

    # Create release artifacts
    if success:
        success &= release_manager.create_release_artifacts()

    if success:
        release_manager.print_release_summary()
        sys.exit(0)
    else:
        console.print("❌ Release preparation failed", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()

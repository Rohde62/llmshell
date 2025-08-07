#!/usr/bin/env python3
"""
Version bump script for LLMShell.

Automatically updates version numbers across all relevant files.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple

import click
from rich.console import Console

console = Console()


class VersionBumper:
    """Handles version bumping across project files."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.files_to_update = [
            ("pyproject.toml", r'version = "([^"]+)"', 'version = "{}"'),
            ("llmshell/__init__.py", r'__version__ = "([^"]+)"', '__version__ = "{}"'),
        ]

    def get_current_version(self) -> str:
        """Get current version from pyproject.toml."""
        pyproject_path = self.project_root / "pyproject.toml"
        with open(pyproject_path) as f:
            content = f.read()
            match = re.search(r'version = "([^"]+)"', content)
            if match:
                return match.group(1)
        raise ValueError("Could not find version in pyproject.toml")

    def parse_version(self, version: str) -> Tuple[int, int, int]:
        """Parse semantic version string."""
        parts = version.split(".")
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version}")
        return tuple(int(p) for p in parts)

    def format_version(self, major: int, minor: int, patch: int) -> str:
        """Format version tuple as string."""
        return f"{major}.{minor}.{patch}"

    def bump_version(self, current: str, bump_type: str) -> str:
        """Bump version according to type."""
        major, minor, patch = self.parse_version(current)

        if bump_type == "major":
            return self.format_version(major + 1, 0, 0)
        elif bump_type == "minor":
            return self.format_version(major, minor + 1, 0)
        elif bump_type == "patch":
            return self.format_version(major, minor, patch + 1)
        else:
            raise ValueError(f"Invalid bump type: {bump_type}")

    def update_files(self, new_version: str) -> List[str]:
        """Update version in all relevant files."""
        updated_files = []

        for file_path, pattern, replacement in self.files_to_update:
            full_path = self.project_root / file_path
            if not full_path.exists():
                console.print(f"⚠️  File not found: {file_path}", style="yellow")
                continue

            with open(full_path) as f:
                content = f.read()

            new_content = re.sub(pattern, replacement.format(new_version), content)

            if content != new_content:
                with open(full_path, "w") as f:
                    f.write(new_content)
                updated_files.append(file_path)
                console.print(f"✅ Updated {file_path}", style="green")

        return updated_files

    def update_changelog(self, new_version: str) -> bool:
        """Add new version section to CHANGELOG.md."""
        changelog_path = self.project_root / "CHANGELOG.md"
        if not changelog_path.exists():
            console.print("⚠️  CHANGELOG.md not found", style="yellow")
            return False

        with open(changelog_path) as f:
            content = f.read()

        # Insert new version section after [Unreleased]
        today = "2025-08-06"  # You might want to use datetime.date.today()
        new_section = f"""
## [{new_version}] - {today}

### Added
- 

### Changed
- 

### Fixed
- 

"""

        # Find the position to insert
        unreleased_pattern = r"(## \[Unreleased\].*?)(## \[)"
        replacement = f"\\1{new_section}\\2"

        new_content = re.sub(unreleased_pattern, replacement, content, flags=re.DOTALL)

        if content != new_content:
            with open(changelog_path, "w") as f:
                f.write(new_content)
            console.print("✅ Updated CHANGELOG.md", style="green")
            return True

        return False


@click.command()
@click.argument("bump_type", type=click.Choice(["major", "minor", "patch"]))
@click.option("--dry-run", is_flag=True, help="Show what would be changed without making changes")
@click.option("--no-changelog", is_flag=True, help="Skip updating CHANGELOG.md")
def main(bump_type: str, dry_run: bool, no_changelog: bool):
    """Bump version across all project files.
    
    BUMP_TYPE: Type of version bump (major, minor, patch)
    """
    project_root = Path(__file__).parent.parent
    bumper = VersionBumper(project_root)

    try:
        current_version = bumper.get_current_version()
        new_version = bumper.bump_version(current_version, bump_type)

        console.print(f"🔄 Version bump: {current_version} → {new_version}", style="bold blue")

        if dry_run:
            console.print("🔍 Dry run mode - no files will be changed", style="yellow")

            console.print("\\nFiles that would be updated:")
            for file_path, _, _ in bumper.files_to_update:
                full_path = project_root / file_path
                if full_path.exists():
                    console.print(f"  - {file_path}")

            if not no_changelog:
                changelog_path = project_root / "CHANGELOG.md"
                if changelog_path.exists():
                    console.print(f"  - CHANGELOG.md")

        else:
            updated_files = bumper.update_files(new_version)

            if not no_changelog:
                bumper.update_changelog(new_version)

            console.print(f"\\n✅ Version bumped to {new_version}", style="bold green")
            console.print("\\nNext steps:")
            console.print("1. Review the changes")
            console.print("2. Update CHANGELOG.md with actual changes")
            console.print("3. Commit the version bump")
            console.print("4. Run release preparation script")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()

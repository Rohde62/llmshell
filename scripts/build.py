#!/usr/bin/env python3
"""Production build script for LLMShell."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


class BuildManager:
    """Manages the build process for different distribution formats."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / "build"
        self.dist_dir = project_root / "dist"

        # Ensure build directories exist
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)

    def clean_build(self):
        """Clean previous build artifacts."""
        print("🧹 Cleaning previous builds...")

        # Remove build directories
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)

        # Remove Python cache
        for cache_dir in self.project_root.rglob("__pycache__"):
            shutil.rmtree(cache_dir)

        for cache_file in self.project_root.rglob("*.pyc"):
            cache_file.unlink()

        # Recreate directories
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)

        print("✅ Build environment cleaned")

    def build_wheel(self) -> Path:
        """Build Python wheel distribution."""
        print("🎡 Building Python wheel...")

        cmd = [sys.executable, "-m", "build", "--wheel"]
        result = subprocess.run(
            cmd, cwd=self.project_root, capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ Wheel build failed: {result.stderr}")
            raise BuildError(f"Wheel build failed: {result.stderr}")

        # Find the built wheel
        wheel_files = list(self.dist_dir.glob("*.whl"))
        if not wheel_files:
            raise BuildError("No wheel file found after build")

        wheel_path = wheel_files[0]
        print(f"✅ Wheel built: {wheel_path}")
        return wheel_path

    def build_sdist(self) -> Path:
        """Build source distribution."""
        print("📦 Building source distribution...")

        cmd = [sys.executable, "-m", "build", "--sdist"]
        result = subprocess.run(
            cmd, cwd=self.project_root, capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ Source distribution build failed: {result.stderr}")
            raise BuildError(f"Source distribution build failed: {result.stderr}")

        # Find the built tarball
        sdist_files = list(self.dist_dir.glob("*.tar.gz"))
        if not sdist_files:
            raise BuildError("No source distribution found after build")

        sdist_path = sdist_files[0]
        print(f"✅ Source distribution built: {sdist_path}")
        return sdist_path

    def create_appimage(self) -> Path:
        """Create AppImage for Linux distribution."""
        print("🖼️  Creating AppImage...")

        try:
            # Check if PyInstaller is available
            result = subprocess.run(
                [sys.executable, "-c", "import PyInstaller"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise ImportError("PyInstaller not available")
        except (ImportError, subprocess.CalledProcessError):
            print("❌ PyInstaller not installed. Install with: pip install pyinstaller")
            raise BuildError("PyInstaller required for AppImage creation")

        # Create PyInstaller spec file
        spec_content = """
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['llmshell/cli.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('llmshell/*.py', 'llmshell'),
    ],
    hiddenimports=[
        'llmshell.core',
        'llmshell.llm', 
        'llmshell.config',
        'llmshell.safety',
        'llmshell.history',
        'llmshell.context',
        'rich',
        'click',
        'httpx',
        'pydantic',
        'yaml',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='llmshell',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"""

        spec_file = self.build_dir / "llmshell.spec"
        spec_file.write_text(spec_content)

        # Run PyInstaller
        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            str(spec_file),
            "--distpath",
            str(self.dist_dir),
        ]
        result = subprocess.run(
            cmd, cwd=self.project_root, capture_output=True, text=True
        )

        if result.returncode != 0:
            print(f"❌ PyInstaller build failed: {result.stderr}")
            raise BuildError(f"PyInstaller build failed: {result.stderr}")

        binary_path = self.dist_dir / "llmshell"
        if not binary_path.exists():
            raise BuildError("PyInstaller binary not found")

        print(f"✅ Standalone binary created: {binary_path}")
        return binary_path

    def create_debian_package(self) -> Path:
        """Create Debian package."""
        print("📦 Creating Debian package...")

        # Create package structure
        pkg_dir = self.build_dir / "llmshell-deb"
        pkg_dir.mkdir(exist_ok=True)

        # DEBIAN control directory
        control_dir = pkg_dir / "DEBIAN"
        control_dir.mkdir(exist_ok=True)

        # Read version from pyproject.toml
        import tomllib

        with open(self.project_root / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        version = pyproject["project"]["version"]

        # Control file
        control_content = f"""Package: llmshell
Version: {version}
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.10), python3-pip
Maintainer: Jakob Rohde <jakob@example.com>
Description: AI-powered Linux shell that translates natural language to bash commands
 LLMShell is a privacy-respecting shell that uses local LLMs to translate
 natural language commands into bash commands, with enhanced safety analysis
 and intelligent context awareness.
"""
        (control_dir / "control").write_text(control_content)

        # Post-install script
        postinst_content = """#!/bin/bash
set -e

# Install LLMShell via pip
pip3 install --user llmshell

# Add to PATH if not already there
if ! grep -q "$HOME/.local/bin" "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

echo "LLMShell installed successfully!"
echo "Run 'llmshell' to get started."
"""
        postinst_file = control_dir / "postinst"
        postinst_file.write_text(postinst_content)
        postinst_file.chmod(0o755)

        # Pre-remove script
        prerm_content = """#!/bin/bash
set -e

# Uninstall LLMShell
pip3 uninstall -y llmshell 2>/dev/null || true
"""
        prerm_file = control_dir / "prerm"
        prerm_file.write_text(prerm_content)
        prerm_file.chmod(0o755)

        # Build the package
        deb_name = f"llmshell_{version}_all.deb"
        deb_path = self.dist_dir / deb_name

        cmd = ["dpkg-deb", "--build", str(pkg_dir), str(deb_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"❌ Debian package build failed: {result.stderr}")
            raise BuildError(f"Debian package build failed: {result.stderr}")

        print(f"✅ Debian package created: {deb_path}")
        return deb_path

    def create_homebrew_formula(self) -> Path:
        """Create Homebrew formula for macOS."""
        print("🍺 Creating Homebrew formula...")

        # Read version from pyproject.toml
        import tomllib

        with open(self.project_root / "pyproject.toml", "rb") as f:
            pyproject = tomllib.load(f)

        version = pyproject["project"]["version"]

        formula_content = f"""class Llmshell < Formula
  desc "AI-powered Linux shell that translates natural language to bash commands"
  homepage "https://github.com/jakobr-dev/llmshell"
  url "https://github.com/jakobr-dev/llmshell/archive/v{version}.tar.gz"
  license "MIT"
  head "https://github.com/jakobr-dev/llmshell.git", branch: "main"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    system bin/"llmshell", "--version"
  end
end
"""

        formula_path = self.dist_dir / "llmshell.rb"
        formula_path.write_text(formula_content)

        print(f"✅ Homebrew formula created: {formula_path}")
        return formula_path

    def run_tests_before_build(self):
        """Run comprehensive tests before building."""
        print("🧪 Running pre-build tests...")

        test_script = self.project_root / "scripts" / "test_runner.py"
        if not test_script.exists():
            print("⚠️  Test runner not found, skipping tests")
            return

        cmd = [sys.executable, str(test_script), "--quick"]
        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            raise BuildError("Tests failed - aborting build")

        print("✅ All tests passed")

    def validate_build(self, wheel_path: Path):
        """Validate the built package."""
        print("🔍 Validating build...")

        # Test wheel installation in temporary environment
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_venv = Path(temp_dir) / "test_env"

            # Create virtual environment
            subprocess.run([sys.executable, "-m", "venv", str(temp_venv)], check=True)

            # Install the wheel
            pip_path = temp_venv / "bin" / "pip"
            if not pip_path.exists():
                pip_path = temp_venv / "Scripts" / "pip.exe"  # Windows

            install_result = subprocess.run(
                [str(pip_path), "install", str(wheel_path)],
                capture_output=True,
                text=True,
            )

            if install_result.returncode != 0:
                raise BuildError(f"Wheel installation failed: {install_result.stderr}")

            # Test import
            python_path = temp_venv / "bin" / "python"
            if not python_path.exists():
                python_path = temp_venv / "Scripts" / "python.exe"  # Windows

            test_result = subprocess.run(
                [str(python_path), "-c", "import llmshell; print('Import successful')"],
                capture_output=True,
                text=True,
            )

            if test_result.returncode != 0:
                raise BuildError(f"Package import failed: {test_result.stderr}")

        print("✅ Build validation passed")

    def build_all(
        self, formats: list = None, run_tests: bool = True, validate: bool = True
    ):
        """Build all requested formats."""
        if formats is None:
            formats = ["wheel", "sdist"]

        print("🚀 Starting production build...")
        print(f"📋 Formats: {', '.join(formats)}")

        try:
            # Clean previous builds
            self.clean_build()

            # Run tests
            if run_tests:
                self.run_tests_before_build()

            built_artifacts = []

            # Build wheel
            if "wheel" in formats:
                wheel_path = self.build_wheel()
                built_artifacts.append(("wheel", wheel_path))

                if validate:
                    self.validate_build(wheel_path)

            # Build source distribution
            if "sdist" in formats:
                sdist_path = self.build_sdist()
                built_artifacts.append(("sdist", sdist_path))

            # Build AppImage
            if "appimage" in formats:
                try:
                    appimage_path = self.create_appimage()
                    built_artifacts.append(("appimage", appimage_path))
                except Exception as e:
                    print(f"⚠️  AppImage build failed: {e}")

            # Build Debian package
            if "deb" in formats:
                try:
                    deb_path = self.create_debian_package()
                    built_artifacts.append(("deb", deb_path))
                except Exception as e:
                    print(f"⚠️  Debian package build failed: {e}")

            # Create Homebrew formula
            if "homebrew" in formats:
                formula_path = self.create_homebrew_formula()
                built_artifacts.append(("homebrew", formula_path))

            # Summary
            print("\\n🎉 Build completed successfully!")
            print("📦 Built artifacts:")
            for format_name, path in built_artifacts:
                print(f"  {format_name:10} {path}")

            return built_artifacts

        except BuildError as e:
            print(f"\\n❌ Build failed: {e}")
            return []
        except Exception as e:
            print(f"\\n💥 Unexpected build error: {e}")
            return []


class BuildError(Exception):
    """Custom exception for build errors."""

    pass


def main():
    """Main entry point for build script."""
    parser = argparse.ArgumentParser(description="LLMShell Production Build")
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["wheel", "sdist", "appimage", "deb", "homebrew"],
        default=["wheel", "sdist"],
        help="Build formats to create",
    )
    parser.add_argument("--no-tests", action="store_true", help="Skip pre-build tests")
    parser.add_argument(
        "--no-validate", action="store_true", help="Skip build validation"
    )
    parser.add_argument(
        "--clean-only", action="store_true", help="Only clean build artifacts"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    builder = BuildManager(project_root)

    if args.clean_only:
        builder.clean_build()
        return

    artifacts = builder.build_all(
        formats=args.formats, run_tests=not args.no_tests, validate=not args.no_validate
    )

    success = len(artifacts) > 0
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

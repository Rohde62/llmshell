#!/usr/bin/env python3
"""Comprehensive test runner for LLMShell with detailed reporting."""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List


class TestRunner:
    """Advanced test runner with performance metrics and reporting."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {
            "timestamp": time.time(),
            "test_suites": {},
            "coverage": {},
            "performance": {},
            "summary": {},
        }

    def run_unit_tests(self) -> Dict[str, Any]:
        """Run unit tests with coverage."""
        print("🧪 Running unit tests...")

        unit_cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "-v",
            "-x",  # Stop on first failure for quick mode
            "--tb=short",
        ]

        start_time = time.time()
        result = subprocess.run(
            unit_cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        # Parse coverage data
        coverage_file = self.project_root / "coverage.json"
        coverage_data = {}
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)

        return {
            "exit_code": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "coverage": coverage_data,
        }

    def run_integration_tests(self) -> Dict[str, Any]:
        """Run integration tests."""
        print("🔗 Running integration tests...")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_integration.py",
            "-v",
            "-m",
            "integration",
            "--tb=short",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "exit_code": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance benchmarks."""
        print("⚡ Running performance tests...")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "-v",
            "-k",
            "performance",
            "--tb=short",
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=self.project_root
        )
        duration = time.time() - start_time

        return {
            "exit_code": result.returncode,
            "duration": duration,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    def run_linting(self) -> Dict[str, Any]:
        """Run code quality checks."""
        print("📝 Running code quality checks...")

        results = {}

        # Black formatting check
        black_result = subprocess.run(
            [sys.executable, "-m", "black", "--check", "llmshell/", "tests/"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
        )
        results["black"] = {
            "exit_code": black_result.returncode,
            "stdout": black_result.stdout,
            "stderr": black_result.stderr,
        }

        # isort import sorting check
        isort_result = subprocess.run(
            [sys.executable, "-m", "isort", "--check-only", "llmshell/", "tests/"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
        )
        results["isort"] = {
            "exit_code": isort_result.returncode,
            "stdout": isort_result.stdout,
            "stderr": isort_result.stderr,
        }

        # Flake8 linting
        flake8_result = subprocess.run(
            [sys.executable, "-m", "flake8", "llmshell/", "tests/"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
        )
        results["flake8"] = {
            "exit_code": flake8_result.returncode,
            "stdout": flake8_result.stdout,
            "stderr": flake8_result.stderr,
        }

        # MyPy type checking
        mypy_result = subprocess.run(
            [sys.executable, "-m", "mypy", "llmshell/"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
        )
        results["mypy"] = {
            "exit_code": mypy_result.returncode,
            "stdout": mypy_result.stdout,
            "stderr": mypy_result.stderr,
        }

        return results

    def run_security_scan(self) -> Dict[str, Any]:
        """Run security vulnerability scan."""
        print("🔒 Running security scan...")

        # Safety check for known vulnerabilities
        safety_result = subprocess.run(
            [sys.executable, "-m", "safety", "check", "--json"],
            capture_output=True,
            text=True,
            cwd=self.project_root,
        )

        return {
            "safety": {
                "exit_code": safety_result.returncode,
                "stdout": safety_result.stdout,
                "stderr": safety_result.stderr,
            }
        }

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        total_tests = 0
        passed_tests = 0
        total_duration = 0

        report = []
        report.append("=" * 80)
        report.append("🚀 LLMSHELL TEST REPORT")
        report.append("=" * 80)
        report.append("")

        # Test Results Summary
        for suite_name, suite_results in self.results["test_suites"].items():
            duration = suite_results.get("duration", 0)
            total_duration += duration

            if suite_results["exit_code"] == 0:
                status = "✅ PASSED"
                passed_tests += 1
            else:
                status = "❌ FAILED"

            total_tests += 1

            report.append(f"{suite_name:20} {status:10} ({duration:.2f}s)")

        report.append("")
        report.append(f"Total Duration: {total_duration:.2f}s")
        report.append(
            f"Success Rate: {passed_tests}/{total_tests} ({(passed_tests/total_tests*100):.1f}%)"
        )
        report.append("")

        # Coverage Summary
        if "coverage" in self.results and self.results["coverage"]:
            coverage_data = self.results["coverage"]
            if "totals" in coverage_data:
                total_coverage = coverage_data["totals"].get("percent_covered", 0)
                report.append(f"📊 Code Coverage: {total_coverage:.1f}%")
                report.append("")

        # Code Quality Summary
        if "linting" in self.results:
            report.append("📝 Code Quality:")
            linting = self.results["linting"]

            for tool, result in linting.items():
                status = "✅ PASSED" if result["exit_code"] == 0 else "❌ FAILED"
                report.append(f"  {tool:15} {status}")
            report.append("")

        # Performance Summary
        if "performance" in self.results and self.results["performance"]:
            report.append("⚡ Performance Tests:")
            perf = self.results["performance"]
            status = "✅ PASSED" if perf.get("exit_code", 1) == 0 else "❌ FAILED"
            report.append(
                f"  Benchmarks      {status} ({perf.get('duration', 0):.2f}s)"
            )
            report.append("")

        # Security Summary
        if "security" in self.results and self.results["security"]:
            report.append("🔒 Security Scan:")
            security = self.results["security"]
            if "safety" in security:
                safety_status = (
                    "✅ PASSED"
                    if security["safety"].get("exit_code", 1) == 0
                    else "❌ ISSUES FOUND"
                )
                report.append(f"  Vulnerability Scan  {safety_status}")
            report.append("")

        report.append("=" * 80)

        return "\\n".join(report)

    def run_all(
        self,
        include_integration: bool = True,
        include_performance: bool = True,
        include_security: bool = True,
    ) -> bool:
        """Run all test suites and generate report."""
        success = True

        # Unit tests (always run)
        unit_results = self.run_unit_tests()
        self.results["test_suites"]["Unit Tests"] = unit_results
        self.results["coverage"] = unit_results.get("coverage", {})
        success = success and (unit_results["exit_code"] == 0)

        # Integration tests
        if include_integration:
            integration_results = self.run_integration_tests()
            self.results["test_suites"]["Integration Tests"] = integration_results
            success = success and (integration_results["exit_code"] == 0)

        # Performance tests
        if include_performance:
            performance_results = self.run_performance_tests()
            self.results["test_suites"]["Performance Tests"] = performance_results
            self.results["performance"] = performance_results
            success = success and (performance_results["exit_code"] == 0)

        # Code quality checks
        linting_results = self.run_linting()
        self.results["linting"] = linting_results
        linting_success = all(
            result["exit_code"] == 0 for result in linting_results.values()
        )
        success = success and linting_success

        # Security scan
        if include_security:
            try:
                security_results = self.run_security_scan()
                self.results["security"] = security_results
                security_success = security_results["safety"]["exit_code"] == 0
                success = success and security_success
            except FileNotFoundError:
                print("⚠️  Safety not installed - skipping security scan")

        # Generate and display report
        report = self.generate_report()
        print(report)

        # Save detailed results
        results_file = self.project_root / "test-results.json"
        with open(results_file, "w") as f:
            json.dump(self.results, f, indent=2)

        print(f"\\n📄 Detailed results saved to: {results_file}")

        return success


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="LLMShell Test Runner")
    parser.add_argument(
        "--no-integration", action="store_true", help="Skip integration tests"
    )
    parser.add_argument(
        "--no-performance", action="store_true", help="Skip performance tests"
    )
    parser.add_argument("--no-security", action="store_true", help="Skip security scan")
    parser.add_argument(
        "--quick", action="store_true", help="Run only unit tests and basic linting"
    )

    args = parser.parse_args()

    project_root = Path(__file__).parent.parent
    runner = TestRunner(project_root)

    if args.quick:
        include_integration = False
        include_performance = False
        include_security = False
    else:
        include_integration = not args.no_integration
        include_performance = not args.no_performance
        include_security = not args.no_security

    success = runner.run_all(
        include_integration=include_integration,
        include_performance=include_performance,
        include_security=include_security,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

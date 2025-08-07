"""Advanced safety system for LLMShell command execution."""

import re
import shlex
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class DangerLevel(Enum):
    """Danger levels for commands."""

    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class CommandRisk:
    """Represents the risk assessment of a command."""

    def __init__(
        self,
        level: DangerLevel,
        reasons: List[str],
        suggestions: Optional[List[str]] = None,
    ):
        self.level = level
        self.reasons = reasons
        self.suggestions = suggestions or []

    @property
    def is_dangerous(self) -> bool:
        """Check if command is considered dangerous."""
        return self.level.value >= DangerLevel.MEDIUM.value

    @property
    def requires_confirmation(self) -> bool:
        """Check if command requires confirmation."""
        return self.level.value >= DangerLevel.LOW.value


class SafetyAnalyzer:
    """Advanced safety analyzer for shell commands."""

    def __init__(self):
        self.setup_rules()

    def setup_rules(self):
        """Setup dangerous command patterns and rules."""

        # Critical danger patterns - immediate system destruction
        self.critical_patterns = {
            r"rm\s+-rf\s+/": "Attempting to delete root filesystem",
            r":\(\)\{\s*:\|\:&\s*\};:": "Fork bomb attempt",
            r"dd\s+if=/dev/(zero|random)\s+of=/dev/[sh]d[a-z]": "Attempting to overwrite disk",
            r"mkfs\.\w+\s+/dev/[sh]d[a-z]": "Attempting to format disk",
            r"rm\s+-rf\s+\*": "Attempting to delete all files recursively",
            r"echo\s+.*>\s*/etc/(passwd|shadow|sudoers)": "Attempting to modify critical system files",
        }

        # High danger patterns - significant system impact
        self.high_patterns = {
            r"sudo\s+rm\s+-rf": "Recursive deletion with sudo privileges",
            r"chmod\s+-R\s+777\s+/": "Setting dangerous permissions on root",
            r"chown\s+-R\s+.*:/": "Changing ownership of system directories",
            r"killall\s+-9\s+(init|systemd|kernel)": "Attempting to kill critical system processes",
            r"(reboot|shutdown|halt)\s+(-f|--force)": "Forced system shutdown/reboot",
            r"iptables\s+-F": "Flushing firewall rules",
            r"history\s+-c": "Clearing command history",
            r"shred\s+.*": "Securely deleting files",
        }

        # Medium danger patterns - potential data loss or security issues
        self.medium_patterns = {
            r"rm\s+-rf\s+[^/\s]": "Recursive deletion",
            r"mv\s+.*\s+/dev/null": "Moving files to null device",
            r">\s*/etc/": "Redirecting output to system config files",
            r"chmod\s+[0-7]{3}\s+.*\.(sh|py|pl|rb)": "Changing executable permissions",
            r"find\s+.*-exec\s+rm": "Finding and deleting files",
            r"tar\s+.*--overwrite": "Overwriting files during extraction",
            r"wget\s+.*\|\s*(bash|sh)": "Downloading and executing remote scripts",
            r"curl\s+.*\|\s*(bash|sh)": "Downloading and executing remote scripts",
        }

        # Low danger patterns - potentially risky operations
        self.low_patterns = {
            r"rm\s+[^-]": "Deleting files",
            r"cp\s+.*\s+.*\.(conf|cfg|ini)": "Copying configuration files",
            r"mv\s+.*\.(conf|cfg|ini)": "Moving configuration files",
            r"nano\s+/etc/": "Editing system configuration",
            r"vi\s+/etc/": "Editing system configuration",
            r"chmod\s+\+x": "Making files executable",
            r"sudo\s+[^rm]": "Running command with sudo privileges",
        }

        # Safe command prefixes - these are generally safe
        self.safe_prefixes = {
            "ls",
            "cat",
            "less",
            "more",
            "head",
            "tail",
            "grep",
            "find",
            "locate",
            "ps",
            "top",
            "htop",
            "df",
            "du",
            "free",
            "uptime",
            "whoami",
            "pwd",
            "date",
            "cal",
            "history",
            "man",
            "info",
            "which",
            "whereis",
            "type",
            "echo",
            "printf",
            "wc",
            "sort",
            "uniq",
            "cut",
            "awk",
            "sed",
        }

        # Dangerous executables
        self.dangerous_executables = {
            "fdisk",
            "parted",
            "gparted",
            "mkfs",
            "fsck",
            "mount",
            "umount",
            "iptables",
            "ufw",
            "firewall-cmd",
            "systemctl",
            "service",
        }

        # Critical paths that should never be modified
        self.protected_paths = {
            "/",
            "/boot",
            "/etc",
            "/usr",
            "/var",
            "/sys",
            "/proc",
            "/dev/sda",
            "/dev/sdb",
            "/dev/nvme",
            "/dev/hd",
        }

    def analyze_command(
        self, command: str, context: Optional[Dict[str, Any]] = None
    ) -> CommandRisk:
        """Analyze a command and return risk assessment."""
        if not command.strip():
            return CommandRisk(DangerLevel.SAFE, [])

        # Normalize command
        command_lower = command.lower().strip()

        # Check for critical patterns
        for pattern, reason in self.critical_patterns.items():
            if re.search(pattern, command_lower):
                return CommandRisk(
                    DangerLevel.CRITICAL,
                    [reason],
                    [
                        "This command can cause irreversible system damage",
                        "Consider alternatives or seek expert help",
                    ],
                )

        # Check for high danger patterns
        reasons = []
        suggestions = []
        max_level = DangerLevel.SAFE

        for pattern, reason in self.high_patterns.items():
            if re.search(pattern, command_lower):
                reasons.append(reason)
                if DangerLevel.HIGH.value > max_level.value:
                    max_level = DangerLevel.HIGH
                suggestions.append(
                    "Double-check the target path and consider backing up first"
                )

        # Check for medium danger patterns
        for pattern, reason in self.medium_patterns.items():
            if re.search(pattern, command_lower):
                reasons.append(reason)
                if DangerLevel.MEDIUM.value > max_level.value:
                    max_level = DangerLevel.MEDIUM
                suggestions.append(
                    "Verify the operation is intended and paths are correct"
                )

        # Check for low danger patterns
        for pattern, reason in self.low_patterns.items():
            if re.search(pattern, command_lower):
                reasons.append(reason)
                if DangerLevel.LOW.value > max_level.value:
                    max_level = DangerLevel.LOW
                suggestions.append("Review the operation carefully")

        # Context-aware analysis
        if context:
            context_risks = self._analyze_context(command, context)
            reasons.extend(context_risks.reasons)
            suggestions.extend(context_risks.suggestions)
            if context_risks.level.value > max_level.value:
                max_level = context_risks.level

        # Analyze command structure
        structure_risk = self._analyze_structure(command)
        reasons.extend(structure_risk.reasons)
        suggestions.extend(structure_risk.suggestions)
        if structure_risk.level.value > max_level.value:
            max_level = structure_risk.level

        # Check if it's a safe command
        if max_level == DangerLevel.SAFE:
            try:
                parts = shlex.split(command)
                if parts and parts[0] in self.safe_prefixes:
                    return CommandRisk(DangerLevel.SAFE, ["Safe read-only operation"])
            except ValueError:
                pass

        return CommandRisk(max_level, reasons, list(set(suggestions)))

    def _analyze_context(self, command: str, context: Dict[str, Any]) -> CommandRisk:
        """Analyze command in context of current directory and files."""
        reasons = []
        suggestions = []
        level = DangerLevel.SAFE

        cwd = context.get("cwd", "")
        files = context.get("files", [])

        # Check if operating in system directories
        if cwd:
            cwd_path = Path(cwd)
            for protected in self.protected_paths:
                if str(cwd_path).startswith(protected) and protected != "/":
                    reasons.append(f"Operating in protected directory: {protected}")
                    if DangerLevel.MEDIUM.value > level.value:
                        level = DangerLevel.MEDIUM
                    suggestions.append(
                        "Be extra careful when modifying system directories"
                    )

        # Check for operations on important files
        if "rm" in command.lower() or "mv" in command.lower():
            important_files = [
                f
                for f in files
                if f.startswith(".")
                or f.endswith((".conf", ".cfg", ".ini", ".yaml", ".json"))
            ]
            if important_files:
                reasons.append("Command may affect configuration files")
                if DangerLevel.LOW.value > level.value:
                    level = DangerLevel.LOW
                suggestions.append("Backup important files before modification")

        return CommandRisk(level, reasons, suggestions)

    def _analyze_structure(self, command: str) -> CommandRisk:
        """Analyze command structure for risky patterns."""
        reasons = []
        suggestions = []
        level = DangerLevel.SAFE

        # Check for command chaining
        if any(op in command for op in ["&&", "||", ";"]):
            reasons.append("Command contains multiple operations")
            if DangerLevel.LOW.value > level.value:
                level = DangerLevel.LOW
            suggestions.append("Review each operation in the chain")

        # Check for redirection to important locations
        if re.search(r">\s*(/etc|/usr|/var)", command):
            reasons.append("Output redirection to system directories")
            if DangerLevel.MEDIUM.value > level.value:
                level = DangerLevel.MEDIUM
            suggestions.append("Ensure you have proper permissions and backup files")

        # Check for wildcards in dangerous contexts
        if re.search(r"rm\s+.*\*", command) or re.search(r"chmod\s+.*\*", command):
            reasons.append("Wildcard usage in potentially destructive command")
            if DangerLevel.MEDIUM.value > level.value:
                level = DangerLevel.MEDIUM
            suggestions.append(
                "Be specific about target files instead of using wildcards"
            )

        # Check for pipe to shell execution
        if re.search(r"\|\s*(bash|sh|zsh|fish)", command):
            reasons.append("Piping output to shell execution")
            if DangerLevel.HIGH.value > level.value:
                level = DangerLevel.HIGH
            suggestions.append("Verify the source and content before execution")

        # Check for dangerous executables
        try:
            parts = shlex.split(command)
            if parts:
                executable = parts[0].split("/")[-1]  # Get basename
                if executable in self.dangerous_executables:
                    reasons.append(
                        f"Using potentially dangerous executable: {executable}"
                    )
                    if DangerLevel.MEDIUM.value > level.value:
                        level = DangerLevel.MEDIUM
                    suggestions.append(
                        "Ensure you understand the implications of this command"
                    )
        except ValueError:
            # Malformed command
            reasons.append("Command has malformed syntax")
            if DangerLevel.LOW.value > level.value:
                level = DangerLevel.LOW
            suggestions.append("Check command syntax before execution")

        return CommandRisk(level, reasons, suggestions)

    def get_safety_tips(self, command: str) -> List[str]:
        """Get general safety tips for command execution."""
        tips = []

        if "rm" in command.lower():
            tips.extend(
                [
                    "Use 'ls' first to see what files will be affected",
                    "Consider using 'trash' command instead of 'rm' for recoverable deletion",
                    "Always double-check paths before deletion",
                ]
            )

        if "sudo" in command.lower():
            tips.extend(
                [
                    "Understand why sudo privileges are needed",
                    "Verify the command is from a trusted source",
                    "Consider if there's a non-privileged alternative",
                ]
            )

        if any(op in command for op in [">", ">>"]):
            tips.extend(
                [
                    "Backup the target file before overwriting",
                    "Use '>>' for appending instead of '>' for overwriting when appropriate",
                ]
            )

        return tips


def get_danger_level_color(level: DangerLevel) -> str:
    """Get Rich color for danger level."""
    colors = {
        DangerLevel.SAFE: "green",
        DangerLevel.LOW: "yellow",
        DangerLevel.MEDIUM: "orange3",
        DangerLevel.HIGH: "red",
        DangerLevel.CRITICAL: "bright_red",
    }
    return colors.get(level, "white")


def get_danger_level_emoji(level: DangerLevel) -> str:
    """Get emoji for danger level."""
    emojis = {
        DangerLevel.SAFE: "✅",
        DangerLevel.LOW: "⚠️",
        DangerLevel.MEDIUM: "🔶",
        DangerLevel.HIGH: "🚨",
        DangerLevel.CRITICAL: "💀",
    }
    return emojis.get(level, "❓")

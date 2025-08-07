"""Core shell logic for LLMShell."""

import os
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.syntax import Syntax
from rich.text import Text

from .config import LLMShellConfig
from .context import EnhancedContextAnalyzer, ProjectContext
from .history import CommandType, HistoryEntry, HistoryManager
from .llm import LLMProvider, LLMResponse
from .safety import (
    CommandRisk,
    DangerLevel,
    SafetyAnalyzer,
    get_danger_level_color,
    get_danger_level_emoji,
)


class ShellSession:
    """Main shell session handler with enhanced history and context."""

    def __init__(self, config: LLMShellConfig, llm_provider: LLMProvider):
        self.config = config
        self.llm_provider = llm_provider
        self.console = Console()
        self.history: List[str] = (
            []
        )  # Keep in-memory history for backward compatibility
        self.current_directory = Path.cwd()
        self.ai_mode = True
        self.safety_analyzer = SafetyAnalyzer()

        # Enhanced features
        self.history_manager = HistoryManager()
        self.context_analyzer = EnhancedContextAnalyzer()
        self.current_project_context: Optional[ProjectContext] = None

        # Load previous session history
        self._load_session_context()

    def _load_session_context(self):
        """Load context and recent history for the session."""
        # Analyze current directory context
        self.current_project_context = self.context_analyzer.analyze_directory(
            self.current_directory
        )

        # Load recent history into memory for quick access
        recent_entries = self.history_manager.get_recent_entries(limit=10)
        self.history = [
            (entry.user_input, entry.translated_command, entry.success)
            for entry in recent_entries
        ]

    def get_context(self) -> Dict[str, Any]:
        """Get current context for LLM prompts with enhanced information."""
        # Use enhanced context analyzer
        return self.context_analyzer.get_context_for_llm(self.current_directory)

    def analyze_command_safety(self, command: str) -> "CommandRisk":
        """Analyze command safety using advanced detection."""
        context = self.get_context()
        return self.safety_analyzer.analyze_command(command, context)

    def is_dangerous_command(self, command: str) -> bool:
        """Check if command is potentially dangerous (legacy method)."""
        risk = self.analyze_command_safety(command)
        return risk.is_dangerous

    def detect_command_type(self, user_input: str) -> str:
        """Detect if input is natural language or direct command."""
        # Simple heuristics to detect natural language vs commands
        natural_language_indicators = [
            "please",
            "can you",
            "how to",
            "show me",
            "find all",
            "list all",
            "what is",
            "where is",
            "count",
            "display",
            "get",
            "make",
        ]

        # If it starts with common shell commands, treat as direct command
        if user_input.strip().split()[0] in [
            "ls",
            "cd",
            "pwd",
            "grep",
            "find",
            "ps",
            "df",
            "free",
            "chmod",
            "chown",
            "mv",
            "cp",
            "rm",
            "mkdir",
            "rmdir",
        ]:
            return "direct"

        # If it contains natural language indicators, treat as natural language
        if any(
            indicator in user_input.lower() for indicator in natural_language_indicators
        ):
            return "natural"

        # If it's very short and doesn't contain spaces, likely a command
        if len(user_input.split()) <= 2 and not any(
            char in user_input for char in "?.,;"
        ):
            return "direct"

        # Default to natural language if in AI mode
        return "natural" if self.ai_mode else "direct"

    async def translate_command(self, natural_input: str) -> LLMResponse:
        """Translate natural language to bash command."""
        context = self.get_context()
        return await self.llm_provider.translate(natural_input, context)

    def execute_command(
        self,
        command: str,
        user_input: str = "",
        command_type: CommandType = CommandType.DIRECT,
    ) -> Tuple[bool, str, str]:
        """Execute a bash command and return (success, stdout, stderr) with history tracking."""
        start_time = time.time()

        try:
            # Handle built-in commands
            if command.strip().startswith("cd "):
                success, stdout, stderr = self._handle_cd_command(command)
                execution_time = int((time.time() - start_time) * 1000)

                # Record in history
                self._record_command_history(
                    user_input or command,
                    command,
                    command_type,
                    success,
                    execution_time,
                    0 if success else 1,
                    stderr,
                )

                return success, stdout, stderr

            # Execute external command
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.execution.timeout,
                cwd=self.current_directory,
            )

            execution_time = int((time.time() - start_time) * 1000)
            success = result.returncode == 0

            # Record in history
            self._record_command_history(
                user_input or command,
                command,
                command_type,
                success,
                execution_time,
                result.returncode,
                result.stderr,
            )

            return success, result.stdout, result.stderr

        except subprocess.TimeoutExpired:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = (
                f"Command timed out after {self.config.execution.timeout} seconds"
            )

            # Record timeout in history
            self._record_command_history(
                user_input or command,
                command,
                command_type,
                False,
                execution_time,
                -1,
                error_msg,
            )

            return False, "", error_msg
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            error_msg = f"Execution error: {str(e)}"

            # Record error in history
            self._record_command_history(
                user_input or command,
                command,
                command_type,
                False,
                execution_time,
                -1,
                error_msg,
            )

            return False, "", error_msg

    def _record_command_history(
        self,
        user_input: str,
        command: str,
        command_type: CommandType,
        success: bool,
        execution_time: int,
        exit_code: int,
        error_message: str = "",
    ):
        """Record command execution in history."""
        try:
            entry = HistoryEntry(
                user_input=user_input,
                translated_command=command,
                command_type=command_type.value,
                success=success,
                execution_time_ms=execution_time,
                working_directory=str(self.current_directory),
                exit_code=exit_code,
                error_message=error_message,
                model_used=self.llm_provider.config.model,
                project_context=(
                    self.current_project_context.project_type.value
                    if self.current_project_context
                    else ""
                ),
            )

            # Add to persistent history
            self.history_manager.add_entry(entry)

            # Add to in-memory history for backward compatibility
            self.history.append((user_input, command, success))

            # Keep only last 50 entries in memory
            if len(self.history) > 50:
                self.history = self.history[-50:]

        except Exception as e:
            # Don't let history recording break command execution
            self.console.print(
                f"Warning: Failed to record history: {e}", style="dim yellow"
            )

    def _handle_cd_command(self, command: str) -> Tuple[bool, str, str]:
        """Handle cd command specially to change session directory and refresh context."""
        try:
            parts = shlex.split(command)
            if len(parts) == 1:  # just "cd"
                target = Path.home()
            else:
                target_str = parts[1]
                if target_str == "~":
                    target = Path.home()
                elif target_str.startswith("~/"):
                    target = Path.home() / target_str[2:]
                else:
                    target = self.current_directory / target_str

            target = target.resolve()
            if target.exists() and target.is_dir():
                self.current_directory = target
                os.chdir(target)  # Also change the process directory

                # Refresh project context when changing directories
                self.current_project_context = self.context_analyzer.analyze_directory(
                    self.current_directory
                )

                return True, str(target), ""
            else:
                return False, "", f"Directory not found: {target}"

        except Exception as e:
            return False, "", f"cd error: {str(e)}"

    def display_command_preview(
        self,
        command: str,
        explanation: Optional[str] = None,
        risk: Optional[CommandRisk] = None,
    ):
        """Display command preview with syntax highlighting and safety information."""
        # Create syntax highlighted command
        syntax = Syntax(command, "bash", theme="monokai", line_numbers=False)

        # Determine panel title and style based on risk level
        if risk:
            emoji = get_danger_level_emoji(risk.level)
            level_name = risk.level.name.title()
            panel_title = f"{emoji} Generated Command ({level_name} Risk)"
            border_style = get_danger_level_color(risk.level)
        else:
            panel_title = "🤖 Generated Command"
            border_style = "blue"

        # Build panel content
        content_parts = []

        # Add explanation if provided
        if explanation:
            content_parts.append(Text(f"📝 {explanation}", style="dim"))
            content_parts.append(Text(""))  # Empty line

        # Add the command
        content_parts.append(syntax)

        # Add safety information if risk is provided
        if risk and (risk.reasons or risk.suggestions):
            content_parts.append(Text(""))  # Empty line

            if risk.reasons:
                content_parts.append(Text("⚠️  Safety Concerns:", style="bold yellow"))
                for reason in risk.reasons:
                    content_parts.append(Text(f"  • {reason}", style="yellow"))

            if risk.suggestions:
                content_parts.append(Text("💡 Suggestions:", style="bold cyan"))
                for suggestion in risk.suggestions:
                    content_parts.append(Text(f"  • {suggestion}", style="cyan"))

        # Create panel content
        if len(content_parts) == 1:
            panel_content = content_parts[0]
        else:
            from rich.console import Group

            panel_content = Group(*content_parts)

        panel = Panel(panel_content, title=panel_title, border_style=border_style)

        self.console.print(panel)

    def display_output(self, success: bool, stdout: str, stderr: str):
        """Display command execution output."""
        if stdout.strip():
            self.console.print(stdout, end="")

        if stderr.strip():
            error_text = Text(stderr, style="red")
            self.console.print(error_text, end="")

        if not success and not stderr.strip():
            self.console.print(Text("Command failed with no error output", style="red"))

    def show_help(self):
        """Show help information."""
        help_text = """
🚀 LLMShell Commands:

Natural Language Mode (AI-powered):
  "list all python files"     → find . -name "*.py"
  "show disk usage"           → df -h
  "make file executable"      → chmod +x <file>

Shell Commands:
  .help                       Show this help
  .mode                       Toggle between AI and direct mode
  .history                    Show command history  
  .clear                      Clear screen
  .exit or .quit              Exit LLMShell
  .pwd                        Show current directory
  .context                    Show current context info

Model Commands:
  .models                     List available models
  .model                      Show current model
  .model <name>               Switch to a different model

Enhanced History Commands:
  .history                    Show recent command history
  .history stats              Show detailed history statistics
  .history search <term>      Search command history
  .history export <file>      Export history to file
  .history clear              Clear all history

Context Commands:
  .context                    Show enhanced context information
  .context analyze            Re-analyze current directory
  .suggest <intent>           Get context-aware command suggestions

Direct Mode:
  Any bash command will be executed directly without AI translation

Tips:
  • Commands require confirmation in safe mode
  • Use Ctrl+C to cancel at any time
  • Dangerous commands require extra confirmation
  • History is automatically saved across sessions
        """

        panel = Panel(help_text.strip(), title="LLMShell Help", border_style="cyan")
        self.console.print(panel)

    def show_context(self):
        """Show enhanced context information."""
        context = self.get_context()

        # Basic context info
        context_text = f"""
Current Directory: {context.get('cwd', 'Unknown')}
User: {context.get('user', 'Unknown')}
Shell: {context.get('shell', 'Unknown')}
Files: {', '.join(context.get('files', [])[:5])}{'...' if len(context.get('files', [])) > 5 else ''}
Mode: {'AI-powered' if self.ai_mode else 'Direct bash'}
        """

        # Add project-specific context if available
        if (
            self.current_project_context
            and self.current_project_context.confidence > 0.5
        ):
            pc = self.current_project_context
            context_text += f"""
        
📁 Project Context:
Type: {pc.project_type.value.title()} (confidence: {pc.confidence:.1%})"""

            if pc.main_language:
                context_text += f"\nLanguage: {pc.main_language}"
            if pc.package_manager:
                context_text += f"\nPackage Manager: {pc.package_manager}"
            if pc.virtual_env:
                context_text += f"\nVirtual Environment: {pc.virtual_env}"
            if pc.git_branch:
                context_text += f"\nGit Branch: {pc.git_branch}"
                if pc.git_status:
                    context_text += f" ({pc.git_status})"
            if pc.dependencies:
                deps = ", ".join(pc.dependencies[:3])
                if len(pc.dependencies) > 3:
                    deps += f" (+{len(pc.dependencies)-3} more)"
                context_text += f"\nKey Dependencies: {deps}"

        panel = Panel(
            context_text.strip(), title="Enhanced Context", border_style="green"
        )
        self.console.print(panel)

    async def show_suggestions(self, intent: str):
        """Show context-aware command suggestions."""
        if not self.current_project_context:
            self.console.print(
                "No project context available for suggestions.", style="dim"
            )
            return

        suggestions = self.context_analyzer.get_command_suggestions(
            self.current_project_context, intent
        )

        if not suggestions:
            self.console.print(
                f"No specific suggestions for '{intent}' in this context.", style="dim"
            )
            return

        suggestion_text = f"💡 Suggestions for '{intent}':\n\n"
        for i, suggestion in enumerate(suggestions, 1):
            suggestion_text += f"  {i}. {suggestion}\n"

        # Also check history for similar commands
        similar_commands = self.history_manager.get_similar_commands(intent, limit=3)
        if similar_commands:
            suggestion_text += f"\n📜 From your history:\n"
            for i, entry in enumerate(similar_commands, 1):
                suggestion_text += f"  {i}. {entry.translated_command}\n"

        panel = Panel(
            suggestion_text.strip(),
            title=f"Context-Aware Suggestions - {self.current_project_context.project_type.value.title()} Project",
            border_style="cyan",
        )
        self.console.print(panel)

    def show_history(self):
        """Show command history."""
        if not self.history:
            self.console.print("No commands in history yet.", style="dim")
            return

        self.console.print("\n📜 Command History:", style="bold")
        for i, (original, command, success) in enumerate(self.history[-10:], 1):
            status = "✅" if success else "❌"
            self.console.print(f"{i:2d}. {status} {original}")
            if original != command:
                self.console.print(f"     → {command}", style="dim")

    async def show_models(self):
        """Show available models."""
        with self.console.status("🔍 Fetching available models..."):
            models = await self.llm_provider.list_models()

        if not models:
            self.console.print(
                "❌ No models found or unable to connect to LLM provider", style="red"
            )
            return

        current_model = self.llm_provider.config.model
        model_text = "📋 Available Models:\n\n"

        for model in models:
            if model == current_model:
                model_text += f"  • {model} ← [bold green]current[/bold green]\n"
            else:
                model_text += f"  • {model}\n"

        panel = Panel(model_text.strip(), title="LLM Models", border_style="cyan")
        self.console.print(panel)

    def show_current_model(self):
        """Show current model information."""
        current_model = self.llm_provider.config.model
        provider = self.llm_provider.config.provider
        base_url = self.llm_provider.config.base_url

        model_text = f"""
Provider: {provider}
Base URL: {base_url}
Current Model: {current_model}
Temperature: {self.llm_provider.config.temperature}
Timeout: {self.llm_provider.config.timeout}s
        """

        panel = Panel(
            model_text.strip(), title="Current Model Configuration", border_style="blue"
        )
        self.console.print(panel)

    async def switch_model(self, model_name: str):
        """Switch to a different model."""
        # Check if model is available
        with self.console.status("🔍 Checking model availability..."):
            available_models = await self.llm_provider.list_models()

        if not available_models:
            self.console.print("❌ Unable to fetch available models", style="red")
            return

        # Try exact match first
        if model_name in available_models:
            target_model = model_name
        else:
            # Try fuzzy matching (e.g., "llama3" matches "llama3:latest")
            target_model = None
            for model in available_models:
                if model.startswith(model_name + ":") or model.endswith(
                    ":" + model_name
                ):
                    target_model = model
                    break
                # Also check if the base name matches (remove tags)
                base_name = model.split(":")[0]
                if base_name == model_name:
                    target_model = model
                    break

            if not target_model:
                self.console.print(f"❌ Model '{model_name}' not found", style="red")
                # Show suggestions based on partial matches
                suggestions = [
                    m for m in available_models if model_name.lower() in m.lower()
                ]
                if suggestions:
                    self.console.print(
                        f"💡 Did you mean: {', '.join(suggestions[:3])}", style="cyan"
                    )
                else:
                    self.console.print(
                        f"Available models: {', '.join(available_models)}", style="dim"
                    )
                return

        # Update the model configuration
        old_model = self.llm_provider.config.model
        self.llm_provider.config.model = target_model

        # Test the new model
        with self.console.status(f"🧪 Testing model '{target_model}'..."):
            if await self.llm_provider.test_connection():
                self.console.print(
                    f"✅ Successfully switched to model: {target_model}", style="green"
                )
                if old_model != target_model:
                    self.console.print(f"Previous model: {old_model}", style="dim")
            else:
                # Revert on failure
                self.llm_provider.config.model = old_model
                self.console.print(
                    f"❌ Failed to connect to model '{target_model}', reverted to '{old_model}'",
                    style="red",
                )

    async def process_user_input(self, user_input: str) -> bool:
        """Process user input and return whether to continue the session."""
        user_input = user_input.strip()

        if not user_input:
            return True

        # Handle special commands
        if user_input.startswith("."):
            result = self._handle_special_command(user_input)

            # Handle async special commands
            if isinstance(result, str):
                if result == "async_models":
                    await self.show_models()
                    return True
                elif result.startswith("async_switch_model:"):
                    model_name = result.split(":", 1)[1]
                    await self.switch_model(model_name)
                    return True
                elif result.startswith("async_suggest:"):
                    intent = result.split(":", 1)[1]
                    await self.show_suggestions(intent)
                    return True

            return result

        # Determine command type
        command_type = self.detect_command_type(user_input)

        if command_type == "natural" and self.ai_mode:
            return await self._handle_natural_language(user_input)
        else:
            return await self._handle_direct_command(user_input)

    def _handle_special_command(self, command: str) -> bool:
        """Handle special dot commands with enhanced features."""
        command_lower = command.lower()
        parts = command.split()

        if command_lower in [".exit", ".quit", ".q"]:
            self.console.print("👋 Goodbye!", style="cyan")
            return False
        elif command_lower in [".help", ".h"]:
            self.show_help()
        elif command_lower == ".mode":
            self.ai_mode = not self.ai_mode
            mode = "AI-powered" if self.ai_mode else "Direct bash"
            self.console.print(f"Switched to {mode} mode", style="yellow")
        elif command_lower == ".clear":
            self.console.clear()
        elif command_lower == ".pwd":
            self.console.print(str(self.current_directory))

        # Enhanced history commands
        elif command_lower == ".history":
            self.history_manager.display_recent_history()
        elif command_lower == ".history stats":
            self.history_manager.display_history_stats()
        elif command_lower.startswith(".history search "):
            query = command[16:].strip()
            entries = self.history_manager.search_history(query)
            if entries:
                self.console.print(f"🔍 Found {len(entries)} matching commands:")
                for entry in entries[:10]:
                    timestamp = entry.timestamp[:10]  # Just the date
                    self.console.print(
                        f"  {timestamp}: {entry.user_input} → {entry.translated_command}"
                    )
            else:
                self.console.print(f"No commands found matching '{query}'", style="dim")
        elif command_lower.startswith(".history export "):
            filename = command[16:].strip()
            if self.history_manager.export_history(Path(filename)):
                self.console.print(f"✅ History exported to {filename}", style="green")
            else:
                self.console.print(
                    f"❌ Failed to export history to {filename}", style="red"
                )
        elif command_lower == ".history clear":
            if Confirm.ask(
                "Are you sure you want to clear all history?", default=False
            ):
                cleared = self.history_manager.clear_history()
                self.console.print(
                    f"✅ Cleared {cleared} history entries", style="green"
                )
                self.history = []  # Clear in-memory history too

        # Enhanced context commands
        elif command_lower == ".context":
            self.show_context()
        elif command_lower == ".context analyze":
            self.console.print("🔍 Re-analyzing directory context...")
            self.current_project_context = self.context_analyzer.analyze_directory(
                self.current_directory
            )
            self.show_context()
        elif command_lower.startswith(".suggest "):
            intent = command[9:].strip()
            return f"async_suggest:{intent}"

        # Model commands (keep existing)
        elif command_lower == ".models":
            return "async_models"
        elif command_lower == ".model":
            self.show_current_model()
        elif command_lower.startswith(".model "):
            model_name = command[7:].strip()
            return f"async_switch_model:{model_name}"

        else:
            self.console.print(
                f"Unknown command: {command}. Type .help for help.", style="red"
            )

        return True

    async def _handle_natural_language(self, user_input: str) -> bool:
        """Handle natural language input."""
        # Translate to command
        with self.console.status("🤖 Thinking..."):
            response = await self.translate_command(user_input)

        if response.error:
            self.console.print(f"❌ Translation error: {response.error}", style="red")
            return True

        if not response.command.strip():
            self.console.print("❌ No command generated", style="red")
            return True

        # Analyze command safety
        risk = self.analyze_command_safety(response.command)

        # Display command preview with safety information
        self.display_command_preview(response.command, response.explanation, risk)

        # Handle confirmation based on risk level
        if self.config.execution.always_confirm or risk.requires_confirmation:
            # Show risk-appropriate warnings
            if risk.level == DangerLevel.CRITICAL:
                self.console.print(
                    "💀 CRITICAL WARNING: This command is extremely dangerous!",
                    style="bold bright_red",
                )
                self.console.print(
                    "This command could cause irreversible system damage!", style="red"
                )
                if not Confirm.ask(
                    "Type 'I understand the risks' to continue", default=False
                ):
                    self.console.print("Command cancelled for safety.", style="yellow")
                    return True
                if not Confirm.ask(
                    "Are you absolutely certain you want to proceed?", default=False
                ):
                    self.console.print("Command cancelled.", style="yellow")
                    return True

            elif risk.level == DangerLevel.HIGH:
                self.console.print(
                    "🚨 HIGH RISK: This command could cause significant damage!",
                    style="bold red",
                )
                if not Confirm.ask(
                    "Are you sure you want to execute this high-risk command?",
                    default=False,
                ):
                    self.console.print("Command cancelled.", style="yellow")
                    return True

            elif risk.level == DangerLevel.MEDIUM:
                self.console.print(
                    "🔶 MODERATE RISK: This command requires careful consideration.",
                    style="bold orange3",
                )
                if not Confirm.ask(
                    "Proceed with this potentially risky command?", default=True
                ):
                    self.console.print("Command cancelled.", style="yellow")
                    return True

            elif risk.level == DangerLevel.LOW:
                if not Confirm.ask("Execute this command?", default=True):
                    self.console.print("Command cancelled.", style="yellow")
                    return True

            else:  # SAFE
                if self.config.execution.always_confirm:
                    if not Confirm.ask("Execute this command?", default=True):
                        self.console.print("Command cancelled.", style="yellow")
                        return True

        # Show safety tips if available
        tips = self.safety_analyzer.get_safety_tips(response.command)
        if tips:
            self.console.print("💡 Safety Tips:", style="bold cyan")
            for tip in tips:
                self.console.print(f"  • {tip}", style="cyan")
            self.console.print("")  # Empty line

        # Execute command
        success, stdout, stderr = self.execute_command(
            response.command, user_input, CommandType.NATURAL
        )

        # Display output
        self.display_output(success, stdout, stderr)

        return True

    async def _handle_direct_command(self, command: str) -> bool:
        """Handle direct command input."""
        # Analyze command safety
        risk = self.analyze_command_safety(command)

        # Check for dangerous commands in safe mode
        if self.config.execution.safe_mode and risk.requires_confirmation:
            # Display risk information for direct commands too
            if risk.level >= DangerLevel.MEDIUM:
                emoji = get_danger_level_emoji(risk.level)
                level_name = risk.level.name.title()
                color = get_danger_level_color(risk.level)

                self.console.print(
                    f"{emoji} {level_name} Risk Command Detected!",
                    style=f"bold {color}",
                )

                if risk.reasons:
                    self.console.print("⚠️  Safety Concerns:", style="bold yellow")
                    for reason in risk.reasons:
                        self.console.print(f"  • {reason}", style="yellow")

                if risk.suggestions:
                    self.console.print("💡 Suggestions:", style="bold cyan")
                    for suggestion in risk.suggestions:
                        self.console.print(f"  • {suggestion}", style="cyan")

                self.console.print()  # Empty line

            # Risk-based confirmation
            if risk.level == DangerLevel.CRITICAL:
                self.console.print(
                    "💀 CRITICAL WARNING: This command is extremely dangerous!",
                    style="bold bright_red",
                )
                if not Confirm.ask(
                    "Are you absolutely certain you want to proceed?", default=False
                ):
                    self.console.print("Command cancelled for safety.", style="yellow")
                    return True
            elif risk.level == DangerLevel.HIGH:
                self.console.print(
                    "🚨 HIGH RISK: This command could cause significant damage!",
                    style="bold red",
                )
                if not Confirm.ask(
                    "Are you sure you want to execute this high-risk command?",
                    default=False,
                ):
                    self.console.print("Command cancelled.", style="yellow")
                    return True
            elif risk.level == DangerLevel.MEDIUM:
                if not Confirm.ask(
                    "Proceed with this potentially risky command?", default=False
                ):
                    self.console.print("Command cancelled.", style="yellow")
                    return True
            else:  # LOW risk
                if not Confirm.ask(
                    "Are you sure you want to execute this command?", default=True
                ):
                    self.console.print("Command cancelled.", style="yellow")
                    return True

        # Execute command
        success, stdout, stderr = self.execute_command(
            command, command, CommandType.DIRECT
        )

        # Display output
        self.display_output(success, stdout, stderr)

        return True


async def start_interactive_shell(config: LLMShellConfig, llm_provider: LLMProvider):
    """Start the interactive shell session."""
    console = Console()

    # Welcome message
    welcome_panel = Panel(
        "Welcome to LLMShell! 🚀\n\n"
        "Type natural language commands or use direct bash commands.\n"
        "Type '.help' for help, '.exit' to quit.\n\n"
        f"Mode: {'AI-powered' if True else 'Direct bash'}\n"
        f"Safe mode: {'Enabled' if config.execution.safe_mode else 'Disabled'}",
        title="LLMShell v0.1.0",
        border_style="blue",
    )
    console.print(welcome_panel)

    session = ShellSession(config, llm_provider)

    try:
        while True:
            try:
                # Get current directory for prompt
                cwd = (
                    session.current_directory.name
                    if session.current_directory.name
                    else str(session.current_directory)
                )
                mode_indicator = "🤖" if session.ai_mode else "💻"

                prompt_text = f"{mode_indicator} [{cwd}]"
                user_input = Prompt.ask(prompt_text, default="")

                if not await session.process_user_input(user_input):
                    break

            except KeyboardInterrupt:
                console.print("\n👋 Goodbye! (Ctrl+C pressed)", style="cyan")
                break
            except EOFError:
                console.print("\n👋 Goodbye! (EOF)", style="cyan")
                break

    except Exception as e:
        console.print(f"❌ Unexpected error: {e}", style="red")
    finally:
        llm_provider.close()

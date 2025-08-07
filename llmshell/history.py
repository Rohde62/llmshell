"""Enhanced history management for LLMShell."""

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class CommandType(Enum):
    """Type of command executed."""

    NATURAL = "natural"
    DIRECT = "direct"
    SPECIAL = "special"


@dataclass
class HistoryEntry:
    """A single history entry with rich metadata."""

    id: Optional[int] = None
    timestamp: str = ""
    user_input: str = ""
    translated_command: str = ""
    command_type: str = ""
    success: bool = False
    execution_time_ms: int = 0
    working_directory: str = ""
    exit_code: int = 0
    error_message: str = ""
    model_used: str = ""
    session_id: str = ""
    project_context: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class HistoryManager:
    """Enhanced history management with persistence and analytics."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path.home() / ".llmshell"
        self.data_dir.mkdir(exist_ok=True)

        self.db_path = self.data_dir / "history.db"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.console = Console()

        self._init_database()

    def _init_database(self):
        """Initialize the SQLite database for history storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    user_input TEXT NOT NULL,
                    translated_command TEXT NOT NULL,
                    command_type TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    execution_time_ms INTEGER DEFAULT 0,
                    working_directory TEXT NOT NULL,
                    exit_code INTEGER DEFAULT 0,
                    error_message TEXT DEFAULT '',
                    model_used TEXT DEFAULT '',
                    session_id TEXT NOT NULL,
                    project_context TEXT DEFAULT ''
                )
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_timestamp ON command_history(timestamp)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_session ON command_history(session_id)
            """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_success ON command_history(success)
            """
            )

    def add_entry(self, entry: HistoryEntry) -> int:
        """Add a new history entry and return its ID."""
        entry.session_id = self.session_id

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO command_history (
                    timestamp, user_input, translated_command, command_type,
                    success, execution_time_ms, working_directory, exit_code,
                    error_message, model_used, session_id, project_context
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    entry.timestamp,
                    entry.user_input,
                    entry.translated_command,
                    entry.command_type,
                    entry.success,
                    entry.execution_time_ms,
                    entry.working_directory,
                    entry.exit_code,
                    entry.error_message,
                    entry.model_used,
                    entry.session_id,
                    entry.project_context,
                ),
            )
            entry.id = cursor.lastrowid
            return entry.id

    def get_recent_entries(self, limit: int = 50) -> List[HistoryEntry]:
        """Get recent history entries."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM command_history 
                ORDER BY timestamp DESC 
                LIMIT ?
            """,
                (limit,),
            )

            entries = []
            for row in cursor.fetchall():
                entry = HistoryEntry(**dict(row))
                entries.append(entry)

            return entries

    def get_session_history(
        self, session_id: Optional[str] = None
    ) -> List[HistoryEntry]:
        """Get history for a specific session."""
        session_id = session_id or self.session_id

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM command_history 
                WHERE session_id = ?
                ORDER BY timestamp ASC
            """,
                (session_id,),
            )

            entries = []
            for row in cursor.fetchall():
                entry = HistoryEntry(**dict(row))
                entries.append(entry)

            return entries

    def search_history(self, query: str, limit: int = 20) -> List[HistoryEntry]:
        """Search history by command content."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT * FROM command_history 
                WHERE user_input LIKE ? OR translated_command LIKE ?
                ORDER BY timestamp DESC 
                LIMIT ?
            """,
                (f"%{query}%", f"%{query}%", limit),
            )

            entries = []
            for row in cursor.fetchall():
                entry = HistoryEntry(**dict(row))
                entries.append(entry)

            return entries

    def get_command_stats(self) -> Dict[str, Any]:
        """Get statistics about command usage."""
        with sqlite3.connect(self.db_path) as conn:
            # Total commands
            total = conn.execute("SELECT COUNT(*) FROM command_history").fetchone()[0]

            # Success rate
            successful = conn.execute(
                "SELECT COUNT(*) FROM command_history WHERE success = 1"
            ).fetchone()[0]
            success_rate = (successful / total * 100) if total > 0 else 0

            # Command types
            type_stats = {}
            cursor = conn.execute(
                "SELECT command_type, COUNT(*) FROM command_history GROUP BY command_type"
            )
            for row in cursor.fetchall():
                type_stats[row[0]] = row[1]

            # Most used commands
            cursor = conn.execute(
                """
                SELECT translated_command, COUNT(*) as count 
                FROM command_history 
                WHERE command_type != 'special'
                GROUP BY translated_command 
                ORDER BY count DESC 
                LIMIT 10
            """
            )
            popular_commands = [
                {"command": row[0], "count": row[1]} for row in cursor.fetchall()
            ]

            # Recent activity (last 7 days)
            cursor = conn.execute(
                """
                SELECT DATE(timestamp) as date, COUNT(*) as count
                FROM command_history 
                WHERE timestamp >= datetime('now', '-7 days')
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
            """
            )
            recent_activity = [
                {"date": row[0], "count": row[1]} for row in cursor.fetchall()
            ]

            return {
                "total_commands": total,
                "success_rate": round(success_rate, 1),
                "command_types": type_stats,
                "popular_commands": popular_commands,
                "recent_activity": recent_activity,
            }

    def get_similar_commands(
        self, user_input: str, limit: int = 5
    ) -> List[HistoryEntry]:
        """Find similar commands based on user input."""
        # Simple similarity: look for commands with shared words
        words = user_input.lower().split()
        if not words:
            return []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            # Build a query that looks for any of the words
            query_parts = []
            params = []
            for word in words:
                if len(word) > 2:  # Skip very short words
                    query_parts.append(
                        "(user_input LIKE ? OR translated_command LIKE ?)"
                    )
                    params.extend([f"%{word}%", f"%{word}%"])

            if not query_parts:
                return []

            query = f"""
                SELECT *, 
                       (SELECT COUNT(*) FROM command_history ch2 
                        WHERE ch2.translated_command = command_history.translated_command 
                        AND ch2.success = 1) as usage_count
                FROM command_history 
                WHERE ({' OR '.join(query_parts)})
                AND success = 1
                AND command_type != 'special'
                ORDER BY usage_count DESC, timestamp DESC
                LIMIT ?
            """
            params.append(limit)

            cursor = conn.execute(query, params)
            entries = []
            for row in cursor.fetchall():
                entry = HistoryEntry(
                    **{k: v for k, v in dict(row).items() if k != "usage_count"}
                )
                entries.append(entry)

            return entries

    def export_history(self, output_file: Path, format: str = "json") -> bool:
        """Export history to file."""
        try:
            entries = self.get_recent_entries(limit=10000)  # Export all recent

            if format == "json":
                data = [asdict(entry) for entry in entries]
                with open(output_file, "w") as f:
                    json.dump(data, f, indent=2)
            elif format == "csv":
                import csv

                with open(output_file, "w", newline="") as f:
                    if entries:
                        writer = csv.DictWriter(f, fieldnames=asdict(entries[0]).keys())
                        writer.writeheader()
                        for entry in entries:
                            writer.writerow(asdict(entry))
            else:
                return False

            return True
        except Exception:
            return False

    def clear_history(self, older_than_days: Optional[int] = None) -> int:
        """Clear history, optionally only entries older than specified days."""
        with sqlite3.connect(self.db_path) as conn:
            if older_than_days:
                cursor = conn.execute(
                    """
                    DELETE FROM command_history 
                    WHERE timestamp < datetime('now', '-' || ? || ' days')
                """,
                    (older_than_days,),
                )
            else:
                cursor = conn.execute("DELETE FROM command_history")

            return cursor.rowcount

    def display_history_stats(self):
        """Display formatted history statistics."""
        stats = self.get_command_stats()

        # Main stats panel
        stats_text = f"""
Total Commands: {stats['total_commands']}
Success Rate: {stats['success_rate']}%
Current Session: {self.session_id}

Command Types:"""

        for cmd_type, count in stats["command_types"].items():
            percentage = (
                (count / stats["total_commands"] * 100)
                if stats["total_commands"] > 0
                else 0
            )
            stats_text += f"\n  • {cmd_type.title()}: {count} ({percentage:.1f}%)"

        panel = Panel(
            stats_text.strip(), title="📊 History Statistics", border_style="cyan"
        )
        self.console.print(panel)

        # Popular commands table
        if stats["popular_commands"]:
            table = Table(title="🔥 Most Used Commands")
            table.add_column("Command", style="cyan")
            table.add_column("Count", justify="right", style="yellow")

            for cmd in stats["popular_commands"][:5]:
                table.add_row(
                    (
                        cmd["command"][:50] + "..."
                        if len(cmd["command"]) > 50
                        else cmd["command"]
                    ),
                    str(cmd["count"]),
                )

            self.console.print(table)

    def display_recent_history(self, limit: int = 10):
        """Display recent history with formatting."""
        entries = self.get_recent_entries(limit)

        if not entries:
            self.console.print("No history entries found.", style="dim")
            return

        table = Table(title=f"📜 Recent History (Last {len(entries)} commands)")
        table.add_column("#", width=3)
        table.add_column("Time", width=8)
        table.add_column("Input", style="cyan")
        table.add_column("Command", style="green")
        table.add_column("Status", width=6)

        for i, entry in enumerate(reversed(entries), 1):
            timestamp = datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
            time_str = timestamp.strftime("%H:%M:%S")
            status = "✅" if entry.success else "❌"

            # Truncate long inputs/commands
            input_display = (
                entry.user_input[:30] + "..."
                if len(entry.user_input) > 30
                else entry.user_input
            )
            cmd_display = (
                entry.translated_command[:40] + "..."
                if len(entry.translated_command) > 40
                else entry.translated_command
            )

            table.add_row(str(i), time_str, input_display, cmd_display, status)

        self.console.print(table)

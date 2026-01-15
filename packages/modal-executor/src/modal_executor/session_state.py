"""SQLite-backed session state management for Claude CLI wrapper.

This module provides persistent conversation state across stateless Claude CLI calls.
Each session gets its own SQLite database stored on the Modal Volume.

Architecture:
- One .db file per session in /mnt/state/sessions/<session-id>.db
- Stores conversation history (last 10 messages for context)
- Tracks modified files across agent turns
- Survives sandbox restarts via Modal Volume persistence
"""

import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class SessionState:
    """SQLite-backed persistent state for Claude CLI wrapper.

    Each session maintains:
    - Conversation history (role + content + timestamp)
    - Modified files tracking
    - Persistent across sandbox restarts

    Example:
        state = SessionState(session_id="pr-123")
        state.add_exchange("Fix the bug", "I fixed it by...")
        context = state.build_context_prompt("What did you change?")
    """

    session_id: str
    db_path: Path = field(init=False)
    _conn: Optional[sqlite3.Connection] = field(init=False, repr=False, default=None)

    def __post_init__(self):
        # Store session DB in Modal Volume: /mnt/state/sessions/<session-id>.db
        self.db_path = Path(f"/mnt/state/sessions/{self.session_id}.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(str(self.db_path))
        self._init_schema()

    def _init_schema(self):
        """Create tables if they don't exist."""
        if self._conn is None:
            raise RuntimeError("Database connection not initialized")

        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL
            )
        """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS files_modified (
                path TEXT PRIMARY KEY,
                timestamp REAL NOT NULL
            )
        """
        )
        self._conn.commit()

    def build_context_prompt(self, new_prompt: str) -> str:
        """Combine last 5 exchanges into single prompt for continuity.

        Args:
            new_prompt: The new user prompt to append

        Returns:
            Context-enriched prompt with conversation history

        Example:
            Previous conversation:
            user: Fix the auth bug
            assistant: I fixed it in auth.py
            user: Add tests
        """
        if self._conn is None:
            raise RuntimeError("Database connection not initialized")

        cursor = self._conn.execute(
            """
            SELECT role, content FROM conversation
            ORDER BY id DESC LIMIT 10
        """
        )
        history = list(reversed(cursor.fetchall()))  # Oldest first

        if not history:
            # No history, just return the prompt as-is
            return new_prompt

        context = "Previous conversation:\n"
        for role, content in history:
            context += f"{role}: {content}\n"
        context += f"\nUser: {new_prompt}\n"
        return context

    def add_exchange(self, user: str, assistant: str):
        """Store conversation turn.

        Args:
            user: User's prompt
            assistant: Assistant's response
        """
        if self._conn is None:
            raise RuntimeError("Database connection not initialized")

        ts = time.time()
        self._conn.execute(
            "INSERT INTO conversation (role, content, timestamp) VALUES (?, ?, ?)",
            ("user", user, ts),
        )
        self._conn.execute(
            "INSERT INTO conversation (role, content, timestamp) VALUES (?, ?, ?)",
            ("assistant", assistant, ts),
        )
        self._conn.commit()

    def mark_file_modified(self, path: str):
        """Track modified files across turns.

        Args:
            path: File path that was modified
        """
        if self._conn is None:
            raise RuntimeError("Database connection not initialized")

        self._conn.execute(
            "INSERT OR REPLACE INTO files_modified (path, timestamp) VALUES (?, ?)",
            (path, time.time()),
        )
        self._conn.commit()

    def get_modified_files(self) -> list[str]:
        """Get list of all modified files in this session.

        Returns:
            List of file paths that have been modified
        """
        if self._conn is None:
            raise RuntimeError("Database connection not initialized")

        cursor = self._conn.execute(
            "SELECT path FROM files_modified ORDER BY timestamp DESC"
        )
        return [row[0] for row in cursor.fetchall()]

    def close(self):
        """Close database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __del__(self):
        """Ensure connection is closed on garbage collection."""
        self.close()

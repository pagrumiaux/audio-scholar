"""Database connection management for AudioScholar.

This module provides:
- SQLite connection creation with proper settings
- Database initialization (schema creation)
- Connection context manager
"""

import sqlite3
from pathlib import Path
from typing import Optional, Union

# Path to schema.sql (relative to this file)
SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection(
    db_path: Union[str, Path] = ":memory:",
    timeout: int = 30,
    wal_mode: bool = True,
) -> sqlite3.Connection:
    """Create a database connection with proper settings.

    Args:
        db_path: Path to SQLite database file, or ":memory:" for in-memory.
        timeout: Connection timeout in seconds.
        wal_mode: Enable Write-Ahead Logging for better concurrency.

    Returns:
        Configured SQLite connection.
    """
    # Convert to string for sqlite3
    if isinstance(db_path, Path):
        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_path = str(db_path)

    conn = sqlite3.connect(db_path, timeout=timeout)

    # Enable foreign keys (off by default in SQLite)
    conn.execute("PRAGMA foreign_keys = ON")

    # Enable WAL mode for better concurrency (except for :memory:)
    if wal_mode and db_path != ":memory:":
        conn.execute("PRAGMA journal_mode = WAL")

    # Return rows as sqlite3.Row for dict-like access
    conn.row_factory = sqlite3.Row

    return conn


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize database schema.

    Creates all tables, indexes, and triggers defined in schema.sql.
    Safe to call multiple times (uses IF NOT EXISTS).

    Args:
        conn: Database connection.
    """
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)
    conn.commit()


def init_db_from_path(
    db_path: Union[str, Path],
    timeout: int = 30,
    wal_mode: bool = True,
) -> sqlite3.Connection:
    """Create and initialize a new database.

    Convenience function that creates a connection and initializes the schema.

    Args:
        db_path: Path to SQLite database file.
        timeout: Connection timeout in seconds.
        wal_mode: Enable Write-Ahead Logging.

    Returns:
        Initialized database connection.
    """
    conn = get_connection(db_path, timeout=timeout, wal_mode=wal_mode)
    init_db(conn)
    return conn

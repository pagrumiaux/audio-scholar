"""Tests for database connection management."""

import sqlite3

import pytest

from audio_scholar.db.connection import get_connection, init_db


class TestGetConnection:
    """Tests for get_connection function."""

    def test_creates_in_memory_database(self):
        """Can create in-memory database."""
        conn = get_connection(":memory:")

        assert conn is not None
        assert isinstance(conn, sqlite3.Connection)
        conn.close()

    def test_foreign_keys_enabled(self):
        """Foreign keys are enabled by default."""
        conn = get_connection(":memory:")

        result = conn.execute("PRAGMA foreign_keys").fetchone()

        assert result[0] == 1
        conn.close()

    def test_row_factory_set(self):
        """Row factory is set for dict-like access."""
        conn = get_connection(":memory:")
        conn.execute("CREATE TABLE test (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'test')")

        row = conn.execute("SELECT * FROM test").fetchone()

        # Can access by column name
        assert row["id"] == 1
        assert row["name"] == "test"
        conn.close()

    def test_creates_parent_directories(self, tmp_path):
        """Creates parent directories for database file."""
        db_path = tmp_path / "nested" / "dir" / "test.db"

        conn = get_connection(db_path)

        assert db_path.parent.exists()
        conn.close()


class TestInitDb:
    """Tests for init_db function."""

    def test_creates_all_tables(self, db_connection):
        """All expected tables are created."""
        tables = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        table_names = [t["name"] for t in tables]

        expected = [
            "authors",
            "citations",
            "conversations",
            "paper_authors",
            "papers",
            "processing_log",
            "queries",
            "venues",
        ]

        for table in expected:
            assert table in table_names, f"Missing table: {table}"

    def test_creates_indexes(self, db_connection):
        """Expected indexes are created."""
        indexes = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
        ).fetchall()
        index_names = [i["name"] for i in indexes]

        # Check a few key indexes
        assert "idx_papers_status" in index_names
        assert "idx_papers_venue" in index_names
        assert "idx_authors_normalized" in index_names

    def test_safe_to_call_multiple_times(self, db_connection):
        """Calling init_db multiple times doesn't error."""
        # Already initialized in fixture, call again
        init_db(db_connection)
        init_db(db_connection)

        # Should still work
        tables = db_connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        assert len(tables) > 0

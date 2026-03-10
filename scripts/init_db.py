#!/usr/bin/env python3
"""Initialize the AudioScholar database.

This script creates the database file and all tables.
Safe to run multiple times (uses IF NOT EXISTS).

Usage:
    python scripts/init_db.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio_scholar.config import load_config
from audio_scholar.db.connection import init_db_from_path
from audio_scholar.logging import setup_logging, get_logger


def main():
    """Initialize the database."""
    # Load configuration
    config = load_config()

    # Setup logging
    setup_logging(config)
    logger = get_logger(__name__)

    db_path = config.paths.database
    logger.info(f"Initializing database at: {db_path}")

    # Create database and tables
    conn = init_db_from_path(
        db_path,
        timeout=config.database.timeout,
        wal_mode=config.database.wal_mode,
    )

    # Verify tables were created
    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = [t["name"] for t in tables]

    logger.info(f"Created tables: {table_names}")

    # Also seed with default venues
    from audio_scholar.db.crud import insert_venue, get_venue_by_name
    from audio_scholar.db.models import Venue

    default_venues = [
        Venue(name="ISMIR", type="conference", url="https://ismir.net"),
        Venue(name="ICASSP", type="conference", url="https://ieeexplore.ieee.org"),
        Venue(name="INTERSPEECH", type="conference", url="https://www.interspeech.org"),
        Venue(name="DAFx", type="conference", url="https://www.dafx.de"),
        Venue(name="WASPAA", type="conference", url="https://www.waspaa.com"),
        Venue(name="arXiv", type="preprint", url="https://arxiv.org"),
        Venue(name="IEEE TASLP", type="journal", url="https://ieeexplore.ieee.org"),
    ]

    for venue in default_venues:
        existing = get_venue_by_name(conn, venue.name)
        if not existing:
            insert_venue(conn, venue)
            logger.info(f"Added venue: {venue.name}")

    conn.close()
    logger.info("Database initialization complete!")


if __name__ == "__main__":
    main()

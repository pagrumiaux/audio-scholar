#!/usr/bin/env python3
"""Refresh citation counts for all papers.

This script recalculates citation_count for every paper
based on the citations table.

Usage:
    python scripts/refresh_citations.py
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from audio_scholar.config import load_config
from audio_scholar.db.connection import get_connection
from audio_scholar.db.crud import refresh_citation_counts
from audio_scholar.logging import setup_logging, get_logger


def main():
    """Refresh citation counts."""
    # Load configuration
    config = load_config()

    # Setup logging
    setup_logging(config)
    logger = get_logger(__name__)

    db_path = config.paths.database
    logger.info(f"Connecting to database: {db_path}")

    conn = get_connection(db_path)

    logger.info("Refreshing citation counts...")
    updated = refresh_citation_counts(conn)

    logger.info(f"Updated {updated} papers")
    conn.close()


if __name__ == "__main__":
    main()

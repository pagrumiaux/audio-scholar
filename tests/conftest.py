"""Pytest configuration and shared fixtures."""

import pytest

from audio_scholar.db.connection import get_connection, init_db
from audio_scholar.db.models import Author, Paper, Venue


@pytest.fixture
def db_connection():
    """Fresh in-memory database for each test."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def sample_venue():
    """Sample venue data."""
    return Venue(
        name="ISMIR",
        type="conference",
        url="https://ismir.net",
    )


@pytest.fixture
def sample_author():
    """Sample author data."""
    return Author(
        name="Pierre-Amaury Caron",
        affiliations=["MIT", "Stanford"],
    )


@pytest.fixture
def sample_paper():
    """Sample paper data."""
    return Paper(
        title="Audio Event Detection with Latent Clustering",
        abstract="We propose a method for detecting audio events using latent space clustering.",
        year=2023,
        arxiv_id="2301.12345",
    )


@pytest.fixture
def sample_paper_with_venue(sample_venue):
    """Sample paper with venue ID set."""
    return Paper(
        title="Deep Learning for Music Information Retrieval",
        abstract="A comprehensive survey of deep learning methods in MIR.",
        year=2024,
        doi="10.1109/TASLP.2024.1234567",
        venue_id=1,  # Assumes venue inserted first
    )


@pytest.fixture
def config_yaml_content():
    """Minimal valid config.yaml content."""
    return """
paths:
  database: "db/test.db"
  chroma: "db/chroma"
  pdfs: "data/pdfs"
  raw: "data/raw"
  logs: "logs"
"""

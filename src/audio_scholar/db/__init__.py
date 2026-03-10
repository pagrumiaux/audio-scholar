"""Database module for AudioScholar."""

from audio_scholar.db.connection import get_connection, init_db
from audio_scholar.db.models import (
    Author,
    Citation,
    Conversation,
    Paper,
    PaperAuthor,
    ProcessingLog,
    Query,
    Venue,
)

__all__ = [
    "get_connection",
    "init_db",
    "Author",
    "Citation",
    "Conversation",
    "Paper",
    "PaperAuthor",
    "ProcessingLog",
    "Query",
    "Venue",
]

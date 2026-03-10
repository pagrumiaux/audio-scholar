"""CRUD operations for AudioScholar database.

This module provides Create, Read, Update, Delete operations for all entities.
All functions take a database connection as the first argument.
"""

import sqlite3
from datetime import datetime
from typing import List, Optional

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


# =============================================================================
# Exceptions
# =============================================================================

class DuplicateError(Exception):
    """Raised when trying to insert a duplicate record."""
    pass


class NotFoundError(Exception):
    """Raised when a record is not found."""
    pass


# =============================================================================
# Venue CRUD
# =============================================================================

def insert_venue(conn: sqlite3.Connection, venue: Venue) -> int:
    """Insert a new venue.

    Args:
        conn: Database connection.
        venue: Venue to insert.

    Returns:
        ID of the inserted venue.

    Raises:
        DuplicateError: If venue name already exists.
    """
    try:
        cursor = conn.execute(
            """
            INSERT INTO venues (name, type, url)
            VALUES (?, ?, ?)
            """,
            (venue.name, venue.type, venue.url),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint" in str(e):
            raise DuplicateError(f"Venue already exists: {venue.name}")
        raise


def get_venue(conn: sqlite3.Connection, venue_id: int) -> Optional[Venue]:
    """Get a venue by ID.

    Args:
        conn: Database connection.
        venue_id: Venue ID.

    Returns:
        Venue if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM venues WHERE id = ?", (venue_id,)
    ).fetchone()

    if row is None:
        return None

    return Venue(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        url=row["url"],
        created_at=row["created_at"],
    )


def get_venue_by_name(conn: sqlite3.Connection, name: str) -> Optional[Venue]:
    """Get a venue by name.

    Args:
        conn: Database connection.
        name: Venue name.

    Returns:
        Venue if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM venues WHERE name = ?", (name,)
    ).fetchone()

    if row is None:
        return None

    return Venue(
        id=row["id"],
        name=row["name"],
        type=row["type"],
        url=row["url"],
        created_at=row["created_at"],
    )


def list_venues(conn: sqlite3.Connection) -> List[Venue]:
    """List all venues.

    Args:
        conn: Database connection.

    Returns:
        List of all venues.
    """
    rows = conn.execute("SELECT * FROM venues ORDER BY name").fetchall()
    return [
        Venue(
            id=row["id"],
            name=row["name"],
            type=row["type"],
            url=row["url"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


# =============================================================================
# Author CRUD
# =============================================================================

def insert_author(conn: sqlite3.Connection, author: Author) -> int:
    """Insert a new author.

    Args:
        conn: Database connection.
        author: Author to insert.

    Returns:
        ID of the inserted author.

    Raises:
        DuplicateError: If author (normalized name) already exists.
    """
    try:
        cursor = conn.execute(
            """
            INSERT INTO authors (name, name_normalized, affiliations)
            VALUES (?, ?, ?)
            """,
            (author.name, author.name_normalized, author.affiliations_json),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint" in str(e):
            raise DuplicateError(f"Author already exists: {author.name_normalized}")
        raise


def get_author(conn: sqlite3.Connection, author_id: int) -> Optional[Author]:
    """Get an author by ID.

    Args:
        conn: Database connection.
        author_id: Author ID.

    Returns:
        Author if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM authors WHERE id = ?", (author_id,)
    ).fetchone()

    if row is None:
        return None

    return Author(
        id=row["id"],
        name=row["name"],
        name_normalized=row["name_normalized"],
        affiliations=Author.affiliations_from_json(row["affiliations"]),
        created_at=row["created_at"],
    )


def get_author_by_name(
    conn: sqlite3.Connection, name_normalized: str
) -> Optional[Author]:
    """Get an author by normalized name.

    Args:
        conn: Database connection.
        name_normalized: Normalized author name (lowercase).

    Returns:
        Author if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM authors WHERE name_normalized = ?", (name_normalized,)
    ).fetchone()

    if row is None:
        return None

    return Author(
        id=row["id"],
        name=row["name"],
        name_normalized=row["name_normalized"],
        affiliations=Author.affiliations_from_json(row["affiliations"]),
        created_at=row["created_at"],
    )


def get_or_create_author(conn: sqlite3.Connection, author: Author) -> int:
    """Get existing author or create new one.

    Args:
        conn: Database connection.
        author: Author data.

    Returns:
        Author ID (existing or newly created).
    """
    existing = get_author_by_name(conn, author.name_normalized)
    if existing:
        return existing.id
    return insert_author(conn, author)


def update_author_affiliations(
    conn: sqlite3.Connection, author_id: int, affiliations: List[str]
) -> None:
    """Update author affiliations.

    Args:
        conn: Database connection.
        author_id: Author ID.
        affiliations: New affiliations list.
    """
    import json
    conn.execute(
        "UPDATE authors SET affiliations = ? WHERE id = ?",
        (json.dumps(affiliations), author_id),
    )
    conn.commit()


# =============================================================================
# Paper CRUD
# =============================================================================

def insert_paper(
    conn: sqlite3.Connection,
    paper: Paper,
    authors: Optional[List[Author]] = None,
) -> int:
    """Insert a new paper with optional authors.

    Args:
        conn: Database connection.
        paper: Paper to insert.
        authors: Optional list of authors (will be linked).

    Returns:
        ID of the inserted paper.

    Raises:
        DuplicateError: If paper (arxiv_id or doi) already exists.
    """
    try:
        cursor = conn.execute(
            """
            INSERT INTO papers (
                title, abstract, full_text, venue_id, year,
                arxiv_id, doi, pdf_url, pdf_path, status,
                citation_count, embedding_model, embedded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                paper.title,
                paper.abstract,
                paper.full_text,
                paper.venue_id,
                paper.year,
                paper.arxiv_id,
                paper.doi,
                paper.pdf_url,
                paper.pdf_path,
                paper.status,
                paper.citation_count,
                paper.embedding_model,
                paper.embedded_at,
            ),
        )
        paper_id = cursor.lastrowid

        # Link authors if provided
        if authors:
            for position, author in enumerate(authors, start=1):
                author_id = get_or_create_author(conn, author)
                conn.execute(
                    """
                    INSERT INTO paper_authors (paper_id, author_id, position)
                    VALUES (?, ?, ?)
                    """,
                    (paper_id, author_id, position),
                )

        conn.commit()
        return paper_id

    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint" in str(e):
            if "arxiv_id" in str(e):
                raise DuplicateError(f"Paper with arxiv_id already exists: {paper.arxiv_id}")
            elif "doi" in str(e):
                raise DuplicateError(f"Paper with doi already exists: {paper.doi}")
            raise DuplicateError(f"Paper already exists: {e}")
        raise


def get_paper(conn: sqlite3.Connection, paper_id: int) -> Optional[Paper]:
    """Get a paper by ID.

    Args:
        conn: Database connection.
        paper_id: Paper ID.

    Returns:
        Paper if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM papers WHERE id = ?", (paper_id,)
    ).fetchone()

    if row is None:
        return None

    return _row_to_paper(row)


def get_paper_by_arxiv_id(
    conn: sqlite3.Connection, arxiv_id: str
) -> Optional[Paper]:
    """Get a paper by arXiv ID.

    Args:
        conn: Database connection.
        arxiv_id: ArXiv ID (e.g., "2301.12345").

    Returns:
        Paper if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM papers WHERE arxiv_id = ?", (arxiv_id,)
    ).fetchone()

    if row is None:
        return None

    return _row_to_paper(row)


def get_paper_by_doi(conn: sqlite3.Connection, doi: str) -> Optional[Paper]:
    """Get a paper by DOI.

    Args:
        conn: Database connection.
        doi: DOI string.

    Returns:
        Paper if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM papers WHERE doi = ?", (doi,)
    ).fetchone()

    if row is None:
        return None

    return _row_to_paper(row)


def get_paper_with_authors(
    conn: sqlite3.Connection, paper_id: int
) -> Optional[Paper]:
    """Get a paper with its authors populated.

    Args:
        conn: Database connection.
        paper_id: Paper ID.

    Returns:
        Paper with authors list populated, None if not found.
    """
    paper = get_paper(conn, paper_id)
    if paper is None:
        return None

    paper.authors = get_paper_authors(conn, paper_id)
    return paper


def get_paper_authors(conn: sqlite3.Connection, paper_id: int) -> List[Author]:
    """Get all authors of a paper in order.

    Args:
        conn: Database connection.
        paper_id: Paper ID.

    Returns:
        List of authors ordered by position.
    """
    rows = conn.execute(
        """
        SELECT a.* FROM authors a
        JOIN paper_authors pa ON a.id = pa.author_id
        WHERE pa.paper_id = ?
        ORDER BY pa.position
        """,
        (paper_id,),
    ).fetchall()

    return [
        Author(
            id=row["id"],
            name=row["name"],
            name_normalized=row["name_normalized"],
            affiliations=Author.affiliations_from_json(row["affiliations"]),
            created_at=row["created_at"],
        )
        for row in rows
    ]


def update_paper_status(
    conn: sqlite3.Connection, paper_id: int, status: str
) -> None:
    """Update paper processing status.

    Args:
        conn: Database connection.
        paper_id: Paper ID.
        status: New status.
    """
    conn.execute(
        "UPDATE papers SET status = ? WHERE id = ?",
        (status, paper_id),
    )
    conn.commit()


def update_paper_full_text(
    conn: sqlite3.Connection, paper_id: int, full_text: str
) -> None:
    """Update paper full text after extraction.

    Args:
        conn: Database connection.
        paper_id: Paper ID.
        full_text: Extracted text content.
    """
    conn.execute(
        "UPDATE papers SET full_text = ?, status = 'extracted' WHERE id = ?",
        (full_text, paper_id),
    )
    conn.commit()


def update_paper_embedding(
    conn: sqlite3.Connection,
    paper_id: int,
    embedding_model: str,
) -> None:
    """Mark paper as embedded.

    Args:
        conn: Database connection.
        paper_id: Paper ID.
        embedding_model: Model used for embedding.
    """
    conn.execute(
        """
        UPDATE papers
        SET embedding_model = ?, embedded_at = CURRENT_TIMESTAMP, status = 'ready'
        WHERE id = ?
        """,
        (embedding_model, paper_id),
    )
    conn.commit()


def list_papers_by_status(
    conn: sqlite3.Connection, status: str, limit: int = 100
) -> List[Paper]:
    """List papers with a given status.

    Args:
        conn: Database connection.
        status: Status to filter by.
        limit: Maximum number of papers to return.

    Returns:
        List of papers with the given status.
    """
    rows = conn.execute(
        "SELECT * FROM papers WHERE status = ? ORDER BY created_at LIMIT ?",
        (status, limit),
    ).fetchall()

    return [_row_to_paper(row) for row in rows]


def list_papers_by_author(
    conn: sqlite3.Connection, author_id: int
) -> List[Paper]:
    """List all papers by an author.

    Args:
        conn: Database connection.
        author_id: Author ID.

    Returns:
        List of papers by the author.
    """
    rows = conn.execute(
        """
        SELECT p.* FROM papers p
        JOIN paper_authors pa ON p.id = pa.paper_id
        WHERE pa.author_id = ?
        ORDER BY p.year DESC
        """,
        (author_id,),
    ).fetchall()

    return [_row_to_paper(row) for row in rows]


def delete_paper(conn: sqlite3.Connection, paper_id: int) -> bool:
    """Delete a paper.

    Args:
        conn: Database connection.
        paper_id: Paper ID.

    Returns:
        True if paper was deleted, False if not found.
    """
    cursor = conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    conn.commit()
    return cursor.rowcount > 0


def _row_to_paper(row: sqlite3.Row) -> Paper:
    """Convert a database row to a Paper object."""
    return Paper(
        id=row["id"],
        title=row["title"],
        abstract=row["abstract"],
        full_text=row["full_text"],
        venue_id=row["venue_id"],
        year=row["year"],
        arxiv_id=row["arxiv_id"],
        doi=row["doi"],
        pdf_url=row["pdf_url"],
        pdf_path=row["pdf_path"],
        status=row["status"],
        citation_count=row["citation_count"],
        embedding_model=row["embedding_model"],
        embedded_at=row["embedded_at"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# =============================================================================
# Citation CRUD
# =============================================================================

def insert_citation(
    conn: sqlite3.Connection, citing_paper_id: int, cited_paper_id: int
) -> None:
    """Insert a citation link.

    Args:
        conn: Database connection.
        citing_paper_id: ID of the paper that cites.
        cited_paper_id: ID of the paper being cited.

    Raises:
        DuplicateError: If citation already exists.
    """
    try:
        conn.execute(
            """
            INSERT INTO citations (citing_paper_id, cited_paper_id)
            VALUES (?, ?)
            """,
            (citing_paper_id, cited_paper_id),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise DuplicateError(
            f"Citation already exists: {citing_paper_id} -> {cited_paper_id}"
        )


def get_papers_cited_by(
    conn: sqlite3.Connection, paper_id: int
) -> List[Paper]:
    """Get papers cited by a given paper.

    Args:
        conn: Database connection.
        paper_id: Paper ID.

    Returns:
        List of cited papers.
    """
    rows = conn.execute(
        """
        SELECT p.* FROM papers p
        JOIN citations c ON p.id = c.cited_paper_id
        WHERE c.citing_paper_id = ?
        """,
        (paper_id,),
    ).fetchall()

    return [_row_to_paper(row) for row in rows]


def get_papers_citing(conn: sqlite3.Connection, paper_id: int) -> List[Paper]:
    """Get papers that cite a given paper.

    Args:
        conn: Database connection.
        paper_id: Paper ID.

    Returns:
        List of papers that cite this paper.
    """
    rows = conn.execute(
        """
        SELECT p.* FROM papers p
        JOIN citations c ON p.id = c.citing_paper_id
        WHERE c.cited_paper_id = ?
        """,
        (paper_id,),
    ).fetchall()

    return [_row_to_paper(row) for row in rows]


def refresh_citation_counts(conn: sqlite3.Connection) -> int:
    """Refresh citation_count for all papers.

    Args:
        conn: Database connection.

    Returns:
        Number of papers updated.
    """
    cursor = conn.execute(
        """
        UPDATE papers
        SET citation_count = (
            SELECT COUNT(*) FROM citations WHERE cited_paper_id = papers.id
        )
        """
    )
    conn.commit()
    return cursor.rowcount


# =============================================================================
# Conversation CRUD
# =============================================================================

def insert_conversation(
    conn: sqlite3.Connection, title: Optional[str] = None
) -> int:
    """Create a new conversation.

    Args:
        conn: Database connection.
        title: Optional conversation title.

    Returns:
        ID of the created conversation.
    """
    cursor = conn.execute(
        "INSERT INTO conversations (title) VALUES (?)",
        (title,),
    )
    conn.commit()
    return cursor.lastrowid


def get_conversation(
    conn: sqlite3.Connection, conversation_id: int
) -> Optional[Conversation]:
    """Get a conversation by ID.

    Args:
        conn: Database connection.
        conversation_id: Conversation ID.

    Returns:
        Conversation if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM conversations WHERE id = ?", (conversation_id,)
    ).fetchone()

    if row is None:
        return None

    return Conversation(
        id=row["id"],
        title=row["title"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_conversation_with_queries(
    conn: sqlite3.Connection, conversation_id: int
) -> Optional[Conversation]:
    """Get a conversation with all its queries.

    Args:
        conn: Database connection.
        conversation_id: Conversation ID.

    Returns:
        Conversation with queries populated, None if not found.
    """
    conversation = get_conversation(conn, conversation_id)
    if conversation is None:
        return None

    conversation.queries = list_queries_by_conversation(conn, conversation_id)
    return conversation


def list_conversations(
    conn: sqlite3.Connection, limit: int = 50
) -> List[Conversation]:
    """List recent conversations.

    Args:
        conn: Database connection.
        limit: Maximum number to return.

    Returns:
        List of conversations, most recent first.
    """
    rows = conn.execute(
        "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    ).fetchall()

    return [
        Conversation(
            id=row["id"],
            title=row["title"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        for row in rows
    ]


# =============================================================================
# Query CRUD
# =============================================================================

def insert_query(conn: sqlite3.Connection, query: Query) -> int:
    """Insert a new query.

    Args:
        conn: Database connection.
        query: Query to insert.

    Returns:
        ID of the inserted query.
    """
    cursor = conn.execute(
        """
        INSERT INTO queries (
            conversation_id, query_text, response_text,
            retrieved_ids, model_used, latency_ms
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            query.conversation_id,
            query.query_text,
            query.response_text,
            query.retrieved_ids_json,
            query.model_used,
            query.latency_ms,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_query(conn: sqlite3.Connection, query_id: int) -> Optional[Query]:
    """Get a query by ID.

    Args:
        conn: Database connection.
        query_id: Query ID.

    Returns:
        Query if found, None otherwise.
    """
    row = conn.execute(
        "SELECT * FROM queries WHERE id = ?", (query_id,)
    ).fetchone()

    if row is None:
        return None

    return Query(
        id=row["id"],
        conversation_id=row["conversation_id"],
        query_text=row["query_text"],
        response_text=row["response_text"],
        retrieved_ids=Query.retrieved_ids_from_json(row["retrieved_ids"]),
        model_used=row["model_used"],
        latency_ms=row["latency_ms"],
        created_at=row["created_at"],
    )


def list_queries_by_conversation(
    conn: sqlite3.Connection, conversation_id: int
) -> List[Query]:
    """List all queries in a conversation.

    Args:
        conn: Database connection.
        conversation_id: Conversation ID.

    Returns:
        List of queries in order.
    """
    rows = conn.execute(
        "SELECT * FROM queries WHERE conversation_id = ? ORDER BY created_at",
        (conversation_id,),
    ).fetchall()

    return [
        Query(
            id=row["id"],
            conversation_id=row["conversation_id"],
            query_text=row["query_text"],
            response_text=row["response_text"],
            retrieved_ids=Query.retrieved_ids_from_json(row["retrieved_ids"]),
            model_used=row["model_used"],
            latency_ms=row["latency_ms"],
            created_at=row["created_at"],
        )
        for row in rows
    ]


# =============================================================================
# Processing Log CRUD
# =============================================================================

def insert_processing_log(
    conn: sqlite3.Connection, log: ProcessingLog
) -> int:
    """Insert a processing log entry.

    Args:
        conn: Database connection.
        log: ProcessingLog to insert.

    Returns:
        ID of the inserted log entry.
    """
    cursor = conn.execute(
        """
        INSERT INTO processing_log (paper_id, stage, status, message)
        VALUES (?, ?, ?, ?)
        """,
        (log.paper_id, log.stage, log.status, log.message),
    )
    conn.commit()
    return cursor.lastrowid


def list_processing_logs_for_paper(
    conn: sqlite3.Connection, paper_id: int
) -> List[ProcessingLog]:
    """List all processing logs for a paper.

    Args:
        conn: Database connection.
        paper_id: Paper ID.

    Returns:
        List of log entries in order.
    """
    rows = conn.execute(
        "SELECT * FROM processing_log WHERE paper_id = ? ORDER BY created_at",
        (paper_id,),
    ).fetchall()

    return [
        ProcessingLog(
            id=row["id"],
            paper_id=row["paper_id"],
            stage=row["stage"],
            status=row["status"],
            message=row["message"],
            created_at=row["created_at"],
        )
        for row in rows
    ]

"""Tests for CRUD operations."""

import pytest

from audio_scholar.db import crud
from audio_scholar.db.models import (
    Author,
    Conversation,
    Paper,
    ProcessingLog,
    Query,
    Venue,
)


class TestVenueCrud:
    """Tests for venue CRUD operations."""

    def test_insert_and_get_venue(self, db_connection, sample_venue):
        """Insert a venue and retrieve it."""
        venue_id = crud.insert_venue(db_connection, sample_venue)

        retrieved = crud.get_venue(db_connection, venue_id)

        assert retrieved is not None
        assert retrieved.name == sample_venue.name
        assert retrieved.type == sample_venue.type
        assert retrieved.url == sample_venue.url

    def test_get_venue_by_name(self, db_connection, sample_venue):
        """Retrieve venue by name."""
        crud.insert_venue(db_connection, sample_venue)

        retrieved = crud.get_venue_by_name(db_connection, sample_venue.name)

        assert retrieved is not None
        assert retrieved.name == sample_venue.name

    def test_get_nonexistent_venue(self, db_connection):
        """Getting missing venue returns None."""
        result = crud.get_venue(db_connection, venue_id=99999)

        assert result is None

    def test_insert_duplicate_venue(self, db_connection, sample_venue):
        """Duplicate venue name raises DuplicateError."""
        crud.insert_venue(db_connection, sample_venue)

        with pytest.raises(crud.DuplicateError):
            crud.insert_venue(db_connection, sample_venue)

    def test_list_venues(self, db_connection):
        """List all venues."""
        venues = [
            Venue(name="A Conference", type="conference"),
            Venue(name="B Journal", type="journal"),
        ]
        for v in venues:
            crud.insert_venue(db_connection, v)

        result = crud.list_venues(db_connection)

        assert len(result) == 2
        # Should be ordered by name
        assert result[0].name == "A Conference"
        assert result[1].name == "B Journal"


class TestAuthorCrud:
    """Tests for author CRUD operations."""

    def test_insert_and_get_author(self, db_connection, sample_author):
        """Insert an author and retrieve it."""
        author_id = crud.insert_author(db_connection, sample_author)

        retrieved = crud.get_author(db_connection, author_id)

        assert retrieved is not None
        assert retrieved.name == sample_author.name
        assert retrieved.name_normalized == sample_author.name_normalized
        assert retrieved.affiliations == sample_author.affiliations

    def test_get_author_by_name(self, db_connection, sample_author):
        """Retrieve author by normalized name."""
        crud.insert_author(db_connection, sample_author)

        retrieved = crud.get_author_by_name(
            db_connection, sample_author.name_normalized
        )

        assert retrieved is not None
        assert retrieved.name == sample_author.name

    def test_insert_duplicate_author(self, db_connection, sample_author):
        """Duplicate author raises DuplicateError."""
        crud.insert_author(db_connection, sample_author)

        with pytest.raises(crud.DuplicateError):
            crud.insert_author(db_connection, sample_author)

    def test_get_or_create_author_creates(self, db_connection, sample_author):
        """get_or_create_author creates new author."""
        author_id = crud.get_or_create_author(db_connection, sample_author)

        retrieved = crud.get_author(db_connection, author_id)
        assert retrieved is not None
        assert retrieved.name == sample_author.name

    def test_get_or_create_author_gets_existing(self, db_connection, sample_author):
        """get_or_create_author returns existing author."""
        original_id = crud.insert_author(db_connection, sample_author)

        returned_id = crud.get_or_create_author(db_connection, sample_author)

        assert returned_id == original_id

    def test_update_author_affiliations(self, db_connection, sample_author):
        """Update author affiliations."""
        author_id = crud.insert_author(db_connection, sample_author)
        new_affiliations = ["Google", "DeepMind"]

        crud.update_author_affiliations(db_connection, author_id, new_affiliations)

        retrieved = crud.get_author(db_connection, author_id)
        assert retrieved.affiliations == new_affiliations


class TestPaperCrud:
    """Tests for paper CRUD operations."""

    def test_insert_and_get_paper(self, db_connection, sample_paper):
        """Insert a paper and retrieve it."""
        paper_id = crud.insert_paper(db_connection, sample_paper)

        retrieved = crud.get_paper(db_connection, paper_id)

        assert retrieved is not None
        assert retrieved.title == sample_paper.title
        assert retrieved.abstract == sample_paper.abstract
        assert retrieved.arxiv_id == sample_paper.arxiv_id

    def test_get_paper_by_arxiv_id(self, db_connection, sample_paper):
        """Retrieve paper by arXiv ID."""
        crud.insert_paper(db_connection, sample_paper)

        retrieved = crud.get_paper_by_arxiv_id(db_connection, sample_paper.arxiv_id)

        assert retrieved is not None
        assert retrieved.title == sample_paper.title

    def test_get_paper_by_doi(self, db_connection):
        """Retrieve paper by DOI."""
        paper = Paper(title="Test", doi="10.1000/test")
        crud.insert_paper(db_connection, paper)

        retrieved = crud.get_paper_by_doi(db_connection, "10.1000/test")

        assert retrieved is not None
        assert retrieved.title == "Test"

    def test_get_nonexistent_paper(self, db_connection):
        """Getting missing paper returns None."""
        result = crud.get_paper(db_connection, paper_id=99999)

        assert result is None

    def test_insert_duplicate_arxiv_id(self, db_connection, sample_paper):
        """Duplicate arxiv_id raises DuplicateError."""
        crud.insert_paper(db_connection, sample_paper)

        with pytest.raises(crud.DuplicateError, match="arxiv_id"):
            crud.insert_paper(db_connection, sample_paper)

    def test_insert_paper_with_authors(self, db_connection, sample_paper, sample_author):
        """Paper insertion creates author links."""
        paper_id = crud.insert_paper(
            db_connection,
            sample_paper,
            authors=[sample_author],
        )

        authors = crud.get_paper_authors(db_connection, paper_id)

        assert len(authors) == 1
        assert authors[0].name == sample_author.name

    def test_insert_paper_with_multiple_authors(self, db_connection, sample_paper):
        """Paper with multiple authors preserves order."""
        authors = [
            Author(name="First Author"),
            Author(name="Second Author"),
            Author(name="Third Author"),
        ]
        paper_id = crud.insert_paper(db_connection, sample_paper, authors=authors)

        retrieved_authors = crud.get_paper_authors(db_connection, paper_id)

        assert len(retrieved_authors) == 3
        assert retrieved_authors[0].name == "First Author"
        assert retrieved_authors[1].name == "Second Author"
        assert retrieved_authors[2].name == "Third Author"

    def test_get_paper_with_authors(self, db_connection, sample_paper, sample_author):
        """get_paper_with_authors populates authors list."""
        paper_id = crud.insert_paper(
            db_connection,
            sample_paper,
            authors=[sample_author],
        )

        retrieved = crud.get_paper_with_authors(db_connection, paper_id)

        assert retrieved is not None
        assert len(retrieved.authors) == 1
        assert retrieved.authors[0].name == sample_author.name

    def test_update_paper_status(self, db_connection, sample_paper):
        """Update paper status."""
        paper_id = crud.insert_paper(db_connection, sample_paper)

        crud.update_paper_status(db_connection, paper_id, "downloaded")

        retrieved = crud.get_paper(db_connection, paper_id)
        assert retrieved.status == "downloaded"

    def test_update_paper_full_text(self, db_connection, sample_paper):
        """Update paper full text."""
        paper_id = crud.insert_paper(db_connection, sample_paper)

        crud.update_paper_full_text(db_connection, paper_id, "Full paper text here")

        retrieved = crud.get_paper(db_connection, paper_id)
        assert retrieved.full_text == "Full paper text here"
        assert retrieved.status == "extracted"

    def test_update_paper_embedding(self, db_connection, sample_paper):
        """Mark paper as embedded."""
        paper_id = crud.insert_paper(db_connection, sample_paper)

        crud.update_paper_embedding(db_connection, paper_id, "all-MiniLM-L6-v2")

        retrieved = crud.get_paper(db_connection, paper_id)
        assert retrieved.embedding_model == "all-MiniLM-L6-v2"
        assert retrieved.embedded_at is not None
        assert retrieved.status == "ready"

    def test_list_papers_by_status(self, db_connection):
        """List papers by status."""
        papers = [
            Paper(title="Paper 1", arxiv_id="1"),
            Paper(title="Paper 2", arxiv_id="2"),
            Paper(title="Paper 3", arxiv_id="3"),
        ]
        for p in papers:
            crud.insert_paper(db_connection, p)

        # Update one to different status
        crud.update_paper_status(db_connection, 2, "downloaded")

        pending = crud.list_papers_by_status(db_connection, "pending")
        downloaded = crud.list_papers_by_status(db_connection, "downloaded")

        assert len(pending) == 2
        assert len(downloaded) == 1

    def test_list_papers_by_author(self, db_connection, sample_author):
        """List papers by author."""
        papers = [
            Paper(title="Paper 1", arxiv_id="1", year=2023),
            Paper(title="Paper 2", arxiv_id="2", year=2024),
        ]
        for p in papers:
            crud.insert_paper(db_connection, p, authors=[sample_author])

        # Add a paper without this author
        crud.insert_paper(db_connection, Paper(title="Other", arxiv_id="3"))

        author = crud.get_author_by_name(db_connection, sample_author.name_normalized)
        result = crud.list_papers_by_author(db_connection, author.id)

        assert len(result) == 2
        # Should be ordered by year desc
        assert result[0].year == 2024
        assert result[1].year == 2023

    def test_delete_paper(self, db_connection, sample_paper):
        """Delete a paper."""
        paper_id = crud.insert_paper(db_connection, sample_paper)

        result = crud.delete_paper(db_connection, paper_id)

        assert result is True
        assert crud.get_paper(db_connection, paper_id) is None

    def test_delete_nonexistent_paper(self, db_connection):
        """Deleting nonexistent paper returns False."""
        result = crud.delete_paper(db_connection, 99999)

        assert result is False


class TestCitationCrud:
    """Tests for citation CRUD operations."""

    def test_insert_citation(self, db_connection):
        """Insert a citation link."""
        paper1_id = crud.insert_paper(db_connection, Paper(title="Paper 1", arxiv_id="1"))
        paper2_id = crud.insert_paper(db_connection, Paper(title="Paper 2", arxiv_id="2"))

        crud.insert_citation(db_connection, paper1_id, paper2_id)

        cited = crud.get_papers_cited_by(db_connection, paper1_id)
        assert len(cited) == 1
        assert cited[0].id == paper2_id

    def test_insert_duplicate_citation(self, db_connection):
        """Duplicate citation raises DuplicateError."""
        paper1_id = crud.insert_paper(db_connection, Paper(title="Paper 1", arxiv_id="1"))
        paper2_id = crud.insert_paper(db_connection, Paper(title="Paper 2", arxiv_id="2"))

        crud.insert_citation(db_connection, paper1_id, paper2_id)

        with pytest.raises(crud.DuplicateError):
            crud.insert_citation(db_connection, paper1_id, paper2_id)

    def test_get_papers_citing(self, db_connection):
        """Get papers that cite a given paper."""
        paper1_id = crud.insert_paper(db_connection, Paper(title="Paper 1", arxiv_id="1"))
        paper2_id = crud.insert_paper(db_connection, Paper(title="Paper 2", arxiv_id="2"))
        paper3_id = crud.insert_paper(db_connection, Paper(title="Paper 3", arxiv_id="3"))

        # Paper 2 and 3 cite Paper 1
        crud.insert_citation(db_connection, paper2_id, paper1_id)
        crud.insert_citation(db_connection, paper3_id, paper1_id)

        citing = crud.get_papers_citing(db_connection, paper1_id)

        assert len(citing) == 2

    def test_refresh_citation_counts(self, db_connection):
        """Refresh citation counts for all papers."""
        paper1_id = crud.insert_paper(db_connection, Paper(title="Paper 1", arxiv_id="1"))
        paper2_id = crud.insert_paper(db_connection, Paper(title="Paper 2", arxiv_id="2"))
        paper3_id = crud.insert_paper(db_connection, Paper(title="Paper 3", arxiv_id="3"))

        # Paper 2 and 3 cite Paper 1
        crud.insert_citation(db_connection, paper2_id, paper1_id)
        crud.insert_citation(db_connection, paper3_id, paper1_id)
        # Paper 3 also cites Paper 2
        crud.insert_citation(db_connection, paper3_id, paper2_id)

        crud.refresh_citation_counts(db_connection)

        paper1 = crud.get_paper(db_connection, paper1_id)
        paper2 = crud.get_paper(db_connection, paper2_id)
        paper3 = crud.get_paper(db_connection, paper3_id)

        assert paper1.citation_count == 2
        assert paper2.citation_count == 1
        assert paper3.citation_count == 0


class TestConversationCrud:
    """Tests for conversation CRUD operations."""

    def test_insert_and_get_conversation(self, db_connection):
        """Insert and retrieve a conversation."""
        conv_id = crud.insert_conversation(db_connection, title="Test Chat")

        retrieved = crud.get_conversation(db_connection, conv_id)

        assert retrieved is not None
        assert retrieved.title == "Test Chat"

    def test_list_conversations(self, db_connection):
        """List conversations."""
        crud.insert_conversation(db_connection, title="First")
        crud.insert_conversation(db_connection, title="Second")

        result = crud.list_conversations(db_connection)

        assert len(result) == 2
        titles = {c.title for c in result}
        assert titles == {"First", "Second"}


class TestQueryCrud:
    """Tests for query CRUD operations."""

    def test_insert_and_get_query(self, db_connection):
        """Insert and retrieve a query."""
        conv_id = crud.insert_conversation(db_connection)
        query = Query(
            conversation_id=conv_id,
            query_text="What is audio ML?",
            response_text="Audio ML is...",
            retrieved_ids=[1, 2, 3],
            model_used="llama3.1:8b",
            latency_ms=1500,
        )

        query_id = crud.insert_query(db_connection, query)

        retrieved = crud.get_query(db_connection, query_id)

        assert retrieved is not None
        assert retrieved.query_text == "What is audio ML?"
        assert retrieved.response_text == "Audio ML is..."
        assert retrieved.retrieved_ids == [1, 2, 3]

    def test_list_queries_by_conversation(self, db_connection):
        """List queries in a conversation."""
        conv_id = crud.insert_conversation(db_connection)

        for i in range(3):
            query = Query(conversation_id=conv_id, query_text=f"Query {i}")
            crud.insert_query(db_connection, query)

        result = crud.list_queries_by_conversation(db_connection, conv_id)

        assert len(result) == 3

    def test_get_conversation_with_queries(self, db_connection):
        """Get conversation with queries populated."""
        conv_id = crud.insert_conversation(db_connection, title="Test")
        query = Query(conversation_id=conv_id, query_text="Test query")
        crud.insert_query(db_connection, query)

        result = crud.get_conversation_with_queries(db_connection, conv_id)

        assert result is not None
        assert len(result.queries) == 1
        assert result.queries[0].query_text == "Test query"


class TestProcessingLogCrud:
    """Tests for processing log CRUD operations."""

    def test_insert_and_list_logs(self, db_connection, sample_paper):
        """Insert and list processing logs."""
        paper_id = crud.insert_paper(db_connection, sample_paper)

        log1 = ProcessingLog(paper_id=paper_id, stage="download", status="success")
        log2 = ProcessingLog(
            paper_id=paper_id, stage="extract", status="failed", message="PDF corrupted"
        )

        crud.insert_processing_log(db_connection, log1)
        crud.insert_processing_log(db_connection, log2)

        logs = crud.list_processing_logs_for_paper(db_connection, paper_id)

        assert len(logs) == 2
        assert logs[0].stage == "download"
        assert logs[1].stage == "extract"
        assert logs[1].message == "PDF corrupted"

"""Tests for data models."""

import pytest

from audio_scholar.db.models import Author, Paper, Query, Venue


class TestAuthor:
    """Tests for Author model."""

    def test_name_normalized_auto_generated(self):
        """name_normalized is auto-generated from name."""
        author = Author(name="Pierre-Amaury Caron")

        assert author.name_normalized == "pierre-amaury caron"

    def test_name_normalized_not_overwritten(self):
        """Explicit name_normalized is preserved."""
        author = Author(name="P.A. Caron", name_normalized="pierre-amaury caron")

        assert author.name_normalized == "pierre-amaury caron"

    def test_affiliations_json_serialization(self):
        """Affiliations serialize to JSON."""
        author = Author(name="Test", affiliations=["MIT", "Stanford"])

        json_str = author.affiliations_json

        assert json_str == '["MIT", "Stanford"]'

    def test_affiliations_json_deserialization(self):
        """Affiliations deserialize from JSON."""
        affiliations = Author.affiliations_from_json('["MIT", "Stanford"]')

        assert affiliations == ["MIT", "Stanford"]

    def test_affiliations_from_json_handles_none(self):
        """Handles None input gracefully."""
        affiliations = Author.affiliations_from_json(None)

        assert affiliations == []

    def test_affiliations_from_json_handles_empty(self):
        """Handles empty string gracefully."""
        affiliations = Author.affiliations_from_json("")

        assert affiliations == []


class TestQuery:
    """Tests for Query model."""

    def test_retrieved_ids_json_serialization(self):
        """retrieved_ids serialize to JSON."""
        query = Query(query_text="test", retrieved_ids=[1, 2, 3])

        json_str = query.retrieved_ids_json

        assert json_str == "[1, 2, 3]"

    def test_retrieved_ids_json_deserialization(self):
        """retrieved_ids deserialize from JSON."""
        ids = Query.retrieved_ids_from_json("[1, 2, 3]")

        assert ids == [1, 2, 3]

    def test_retrieved_ids_from_json_handles_none(self):
        """Handles None input gracefully."""
        ids = Query.retrieved_ids_from_json(None)

        assert ids == []


class TestVenue:
    """Tests for Venue model."""

    def test_default_type(self):
        """Default venue type is conference."""
        venue = Venue(name="Test")

        assert venue.type == "conference"


class TestPaper:
    """Tests for Paper model."""

    def test_default_status(self):
        """Default paper status is pending."""
        paper = Paper(title="Test")

        assert paper.status == "pending"

    def test_default_citation_count(self):
        """Default citation count is 0."""
        paper = Paper(title="Test")

        assert paper.citation_count == 0

    def test_authors_list_initially_empty(self):
        """Authors list starts empty."""
        paper = Paper(title="Test")

        assert paper.authors == []

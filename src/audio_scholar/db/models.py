"""Data models for AudioScholar.

Dataclasses representing database entities. These provide:
- Type safety
- Easy serialization/deserialization
- Clear documentation of fields
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
import json


# =============================================================================
# Core Models
# =============================================================================

@dataclass
class Venue:
    """A publication venue (conference, journal, or preprint server)."""
    id: Optional[int] = None
    name: str = ""
    type: str = "conference"  # conference, journal, preprint
    url: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class Author:
    """A paper author."""
    id: Optional[int] = None
    name: str = ""
    name_normalized: str = ""
    affiliations: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Normalize name if not provided."""
        if not self.name_normalized and self.name:
            self.name_normalized = self.name.lower().strip()

    @property
    def affiliations_json(self) -> str:
        """Serialize affiliations to JSON string."""
        return json.dumps(self.affiliations)

    @classmethod
    def affiliations_from_json(cls, json_str: Optional[str]) -> List[str]:
        """Deserialize affiliations from JSON string."""
        if not json_str:
            return []
        return json.loads(json_str)


@dataclass
class Paper:
    """A research paper."""
    id: Optional[int] = None
    title: str = ""
    abstract: Optional[str] = None
    full_text: Optional[str] = None
    venue_id: Optional[int] = None
    year: Optional[int] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    pdf_url: Optional[str] = None
    pdf_path: Optional[str] = None
    status: str = "pending"
    citation_count: int = 0
    embedding_model: Optional[str] = None
    embedded_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Non-database fields (populated by joins)
    authors: List["Author"] = field(default_factory=list)
    venue: Optional[Venue] = None


@dataclass
class PaperAuthor:
    """Link between a paper and an author with position."""
    paper_id: int = 0
    author_id: int = 0
    position: int = 1  # 1 = first author


@dataclass
class Citation:
    """A citation link between two papers."""
    citing_paper_id: int = 0
    cited_paper_id: int = 0
    created_at: Optional[datetime] = None


# =============================================================================
# RAG / Conversation Models
# =============================================================================

@dataclass
class Conversation:
    """A chat conversation session."""
    id: Optional[int] = None
    title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Non-database field
    queries: List["Query"] = field(default_factory=list)


@dataclass
class Query:
    """A single query within a conversation."""
    id: Optional[int] = None
    conversation_id: Optional[int] = None
    query_text: str = ""
    response_text: Optional[str] = None
    retrieved_ids: List[int] = field(default_factory=list)
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    created_at: Optional[datetime] = None

    @property
    def retrieved_ids_json(self) -> str:
        """Serialize retrieved_ids to JSON string."""
        return json.dumps(self.retrieved_ids)

    @classmethod
    def retrieved_ids_from_json(cls, json_str: Optional[str]) -> List[int]:
        """Deserialize retrieved_ids from JSON string."""
        if not json_str:
            return []
        return json.loads(json_str)


# =============================================================================
# Processing Models
# =============================================================================

@dataclass
class ProcessingLog:
    """A log entry for paper processing stages."""
    id: Optional[int] = None
    paper_id: int = 0
    stage: str = ""  # download, extract, parse, embed
    status: str = ""  # success, failed
    message: Optional[str] = None
    created_at: Optional[datetime] = None

-- AudioScholar Database Schema
-- SQLite database for storing research papers, authors, and RAG queries

-- =============================================================================
-- Core Tables
-- =============================================================================

-- Venues (conferences, journals)
CREATE TABLE IF NOT EXISTS venues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    type TEXT NOT NULL CHECK (type IN ('conference', 'journal', 'preprint')),
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Authors
CREATE TABLE IF NOT EXISTS authors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    name_normalized TEXT NOT NULL UNIQUE,
    affiliations TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Papers
CREATE TABLE IF NOT EXISTS papers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    abstract TEXT,
    full_text TEXT,
    venue_id INTEGER REFERENCES venues(id),
    year INTEGER,
    arxiv_id TEXT UNIQUE,
    doi TEXT UNIQUE,
    pdf_url TEXT,
    pdf_path TEXT,
    status TEXT DEFAULT 'pending' CHECK (
        status IN ('pending', 'downloading', 'downloaded', 'extracting',
                   'extracted', 'embedding', 'ready', 'failed')
    ),
    citation_count INTEGER DEFAULT 0,
    embedding_model TEXT,
    embedded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Paper-Author relationship (many-to-many)
CREATE TABLE IF NOT EXISTS paper_authors (
    paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    author_id INTEGER NOT NULL REFERENCES authors(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,  -- 1 = first author, 2 = second, etc.
    PRIMARY KEY (paper_id, author_id)
);

-- Citations (paper-to-paper references)
CREATE TABLE IF NOT EXISTS citations (
    citing_paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    cited_paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (citing_paper_id, cited_paper_id)
);

-- =============================================================================
-- RAG / Conversation Tables
-- =============================================================================

-- Conversations (chat sessions)
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Queries (individual questions within a conversation)
CREATE TABLE IF NOT EXISTS queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    query_text TEXT NOT NULL,
    response_text TEXT,
    retrieved_ids TEXT,  -- JSON array of paper IDs
    model_used TEXT,
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Processing / Debug Tables
-- =============================================================================

-- Processing log (for debugging failures)
CREATE TABLE IF NOT EXISTS processing_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
    stage TEXT NOT NULL CHECK (
        stage IN ('download', 'extract', 'parse', 'embed')
    ),
    status TEXT NOT NULL CHECK (status IN ('success', 'failed')),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- Papers indexes
CREATE INDEX IF NOT EXISTS idx_papers_status ON papers(status);
CREATE INDEX IF NOT EXISTS idx_papers_venue ON papers(venue_id);
CREATE INDEX IF NOT EXISTS idx_papers_year ON papers(year);
CREATE INDEX IF NOT EXISTS idx_papers_embedded ON papers(embedding_model)
    WHERE embedding_model IS NOT NULL;

-- Authors indexes
CREATE INDEX IF NOT EXISTS idx_authors_normalized ON authors(name_normalized);

-- Paper-Authors indexes
CREATE INDEX IF NOT EXISTS idx_paper_authors_author ON paper_authors(author_id);

-- Citations indexes
CREATE INDEX IF NOT EXISTS idx_citations_cited ON citations(cited_paper_id);

-- Queries indexes
CREATE INDEX IF NOT EXISTS idx_queries_conversation ON queries(conversation_id);

-- Processing log indexes
CREATE INDEX IF NOT EXISTS idx_processing_log_paper ON processing_log(paper_id);

-- =============================================================================
-- Triggers
-- =============================================================================

-- Update papers.updated_at on any update
CREATE TRIGGER IF NOT EXISTS update_papers_timestamp
    AFTER UPDATE ON papers
    FOR EACH ROW
BEGIN
    UPDATE papers SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

-- Update conversations.updated_at when a query is added
CREATE TRIGGER IF NOT EXISTS update_conversation_timestamp
    AFTER INSERT ON queries
    FOR EACH ROW
BEGIN
    UPDATE conversations SET updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.conversation_id;
END;

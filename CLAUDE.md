# AudioScholar - Development Guide

## Project Overview

AudioScholar is a retrieval-augmented generation (RAG) system for conversational search over 15,000+ audio machine learning research papers. Researchers ask natural language questions and receive synthesized answers with accurate citations.

**Goal:** Replace Google Scholar for domain-specific audio ML research by enabling conversational interaction with curated academic literature.

**Target users:** Audio ML researchers and engineers

**Example query:**
> "I'm working on audio event detection. Are there papers about latent space clustering to better classify events with similar semantics?"

**Expected output:** Synthesized answer from 8-10 relevant papers, with citations and follow-up capability.

---

## Technical Stack

### Core Technologies
- **Python 3.10+** - Primary language
- **SQLite** - Local database (sufficient for 15k papers)
- **sentence-transformers** - Text embeddings for semantic search
- **ChromaDB** - Vector database (migrate to FAISS if too slow)
- **Ollama + Llama 3.1 8B** - Local LLM inference
- **PyMuPDF or Nougat** - PDF text extraction (test both)

### Key Libraries
- PyTorch, numpy, pandas - ML/data
- PyYAML - Configuration
- tqdm - Progress bars
- pytest - Testing

---

## Performance Targets & Constraints

### Storage
- PDFs: ~30GB (15k papers)
- Database: ~10GB (full text)
- Embeddings: ~1.2GB
- **Total: ~41GB** (well within 8TB available)

### Processing
- Initial processing: 4-6 days continuous (15k papers)
- Query latency: 25-65 seconds acceptable
- Peak RAM: ~12GB (fits in 16GB)

### Hardware Constraints
- **Windows PC** - use pathlib for cross-platform paths
- **16GB RAM** - can't load huge models
- **RTX 2060** - moderate GPU, good for inference
- **8TB storage** - plenty of space

### Project Constraints
- **Local-first** - avoid paid APIs when possible
- **Learning project** - prioritize clarity over optimization
- **Portfolio quality** - clean code, good documentation

---

## Development Phases

### Phase 0: Project Setup (Week 1) ← START HERE
**Goal:** Foundation and infrastructure

**Key deliverables:**
- Project structure (src/, db/, data/, tests/)
- SQLite database schema (papers, embeddings, venues, queries, conversations)
- Configuration system (YAML-based)
- Logging system
- Basic CRUD operations for database
- README, requirements.txt, .gitignore

**Technical decisions to make:**
- Database schema design (which tables? what fields?)
- Directory structure organization
- Configuration format and loading approach
- Error handling strategy

### Phase 1: PDF Processing Pipeline (Weeks 2-3)
**Goal:** Reliably extract full text from PDFs

**Key deliverables:**
- PDF download module
- Text extraction (test Nougat vs PyMuPDF)
- Extraction validation and quality checks
- Store full_text in database
- Handle failures gracefully

**Technical decisions to make:**
- Nougat vs PyMuPDF vs hybrid approach?
- How to validate extraction quality?
- How to handle extraction failures?
- Batch processing strategy?

### Phase 2: Historical Data Scraping (Weeks 3-5)
**Goal:** Collect 15,000 papers from conferences and arXiv

**Key deliverables:**
- Scrapers for: ISMIR (~3k), ICASSP (~5k), arXiv (~4k), others (~3k)
- Rate limiting and respectful scraping
- Metadata extraction (authors, dates, venues)
- Queue papers for processing
- Progress tracking

**Technical decisions to make:**
- How to handle institutional access requirements?
- Scraping vs API usage?
- How to handle rate limits?
- Duplicate detection strategy?

### Phase 3: Embedding & Indexing (Week 6)
**Goal:** Create vector index for semantic search

**Key deliverables:**
- Generate embeddings for all papers (title + abstract + intro)
- Store in ChromaDB
- Retrieval functions (semantic search)
- Quality evaluation (test queries)

**Technical decisions to make:**
- Which embedding model? (all-MiniLM-L6-v2 vs all-mpnet-base-v2)
- What text to embed? (abstract only vs full text?)
- Whole-paper vs section-based chunking?
- How to measure retrieval quality?

### Phase 4: Basic RAG Implementation (Weeks 7-8) ← MVP!
**Goal:** Answer questions with citations

**Key deliverables:**
- Query → embedding → vector search pipeline
- LLM context building from retrieved papers
- Citation generation
- CLI interface for asking questions
- Conversation history

**Technical decisions to make:**
- How many papers to retrieve?
- How to build LLM context?
- Prompt engineering for citations
- How to handle follow-up questions?

### Phase 5: Advanced Features (Weeks 9-12)
**Goal:** Multi-stage retrieval and better UX

**Key deliverables:**
- Multi-stage retrieval (broad → narrow → rank)
- Conversational interface with history
- Query refinement capabilities
- Better ranking algorithms

**Technical decisions to make:**
- Re-ranking strategy?
- How to maintain conversation context?
- Query expansion techniques?

### Phase 6: WaveWatch Integration (Week 13)
**Goal:** Connect weekly paper monitoring

**Key deliverables:**
- WaveWatch → AudioScholar pipeline
- Quality filtering (author overlap, venue prestige, citations)
- Incremental processing (weekly updates)
- Duplicate prevention

**Technical decisions to make:**
- Quality filtering thresholds?
- How to detect duplicate papers?
- Incremental vs full reprocessing?

### Phase 7: Optimization & Polish (Weeks 14-15)
**Goal:** Production-ready system

**Key deliverables:**
- Performance tuning (ChromaDB → FAISS if needed)
- UI improvements (rich CLI or web interface?)
- Query caching
- Documentation

**Technical decisions to make:**
- When to migrate to FAISS?
- CLI vs web interface?
- Caching strategy?

**Total timeline:** 15 weeks (~3.5 months)

---

## Code Quality Standards

### Required Practices

**Type hints everywhere:**
```python
def insert_paper(paper_data: dict) -> int:
    """Insert a new paper."""
    pass
```

**Google-style docstrings:**
```python
def retrieve_papers(query: str, k: int = 10) -> List[dict]:
    """Retrieve papers using semantic search.
    
    Args:
        query: Natural language query
        k: Number of papers to retrieve
        
    Returns:
        List of paper dictionaries with scores
    """
```

**Proper error handling:**
```python
try:
    result = operation()
except SpecificError as e:
    logger.error(f"Failed: {e}")
    return None  # Graceful degradation
```

**Use logging, not print:**
```python
logger = logging.getLogger(__name__)
logger.info("Processing started")
logger.error(f"Failed: {error}")
```

**Path handling with pathlib:**
```python
from pathlib import Path

pdf_dir = Path("data/pdfs")
pdf_path = pdf_dir / f"{paper_id}.pdf"
```

---

## Common Pitfalls

1. **Windows path issues** - Always use pathlib, never string concatenation
2. **SQLite concurrency** - Serialize writes, use connection pools
3. **Hardcoded paths** - Everything in config.yaml
4. **Memory leaks** - Close connections, use context managers
5. **Token limits** - Don't exceed LLM context window
6. **Rate limiting** - Respect API quotas (arXiv: 1 req/3sec)

---

## Development Philosophy

### For Each Phase

- **Think first, code second** - Propose approach before implementing
- **Start simple** - MVP first, then enhance
- **Test incrementally** - Don't wait until the end
- **Document decisions** - Explain *why* in comments
- **Ask when uncertain** - Clarify before assuming

### Quality Principles

1. **Clarity > cleverness** - Readable code beats terse code
2. **Modular design** - Separate concerns, small functions
3. **Fail gracefully** - Log errors, don't crash
4. **Reproducible** - Seed randomness, log configs
5. **Portfolio-ready** - This showcases your skills

---

## Questions to Ask (Per Phase)

When starting each phase, consider:

1. **What's the MVP?** - Minimum needed to validate the approach?
2. **What are the trade-offs?** - Speed vs accuracy? Simple vs flexible?
3. **How to test?** - What validates this works?
4. **What can fail?** - How to handle errors gracefully?
5. **Is it documented?** - Will future-you understand this?

---

## User Context

**PA (Pierre-Amaury):**
- ML Research Engineer, audio deep learning specialist
- Background: PhD spatial audio, postdoc bandwidth extension
- Strong: PyTorch/audio ML | Moderate: Python | Learning: NLP/RAG
- Wants to understand *how* RAG works, not just build it
- Values clean, educational code over premature optimization

---

## Current Phase

**Phase 0 - Project Setup**

Start by proposing:
1. Database schema (which tables? what fields?)
2. Project structure (how to organize code?)
3. Configuration approach (what goes in config?)
4. Testing strategy (how to validate?)

Then implement incrementally, testing each component.

---

**Remember:** This is a learning project. Propose approaches, explain trade-offs, ask questions. Let's build something you understand deeply, not just something that works.

Ready to start Phase 0? Propose your approach!

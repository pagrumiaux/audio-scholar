# AudioScholar

A retrieval-augmented generation (RAG) system for conversational search over audio machine learning research papers.

## Overview

AudioScholar enables researchers to ask natural language questions about audio ML research and receive synthesized answers with accurate citations from a curated database of 15,000+ papers.

**Example query:**
> "I'm working on audio event detection. Are there papers about latent space clustering to better classify events with similar semantics?"

## Project Status

**Current Phase:** Phase 0 - Project Setup (Complete)

## Setup

### Prerequisites

- Python 3.10+
- SQLite (included with Python)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd audio-scholar

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize the database
python scripts/init_db.py
```

### Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
audio-scholar/
├── src/audio_scholar/     # Main source code
│   ├── config.py          # Configuration loading
│   ├── logging.py         # Logging setup
│   └── db/                # Database layer
│       ├── schema.sql     # Table definitions
│       ├── connection.py  # Connection management
│       ├── models.py      # Data models
│       └── crud.py        # CRUD operations
├── data/                  # Data storage
│   ├── pdfs/              # Downloaded PDFs
│   └── raw/               # Raw scraped data
├── db/                    # Database files
├── logs/                  # Application logs
├── tests/                 # Test suite
├── scripts/               # Utility scripts
│   ├── init_db.py         # Initialize database
│   └── refresh_citations.py
└── config.yaml            # Configuration file
```

## Configuration

Edit `config.yaml` to customize paths, logging, and processing settings.

## Development Phases

1. **Phase 0:** Project Setup (Complete)
2. **Phase 1:** PDF Processing Pipeline
3. **Phase 2:** Historical Data Scraping
4. **Phase 3:** Embedding & Indexing
5. **Phase 4:** Basic RAG Implementation
6. **Phase 5:** Advanced Features
7. **Phase 6:** WaveWatch Integration
8. **Phase 7:** Optimization & Polish

## License

[To be determined]

# AudioScholar

A retrieval-augmented generation system for conversational search over audio machine learning research papers.

## Overview

AudioScholar enables researchers/engineers to ask natural language questions about audio ML research and receive synthesized answers with accurate citations from a curated database of 15,000+ papers.

## Installation

```bash

# Install dependencies
pip install -e .[all]

# Initialize the database
python scripts/init_db.py
```

## Configuration

Edit `config.yaml` to customize paths, logging, and processing settings.

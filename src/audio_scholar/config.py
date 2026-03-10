"""Configuration loading and validation for AudioScholar.

This module provides a typed configuration system that:
- Loads settings from config.yaml
- Validates all values (fails on unknown keys)
- Provides sensible defaults
- Resolves relative paths to absolute paths
"""

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Optional, Set

import yaml


# =============================================================================
# Configuration Dataclasses
# =============================================================================

@dataclass
class PathsConfig:
    """Paths configuration."""
    database: Path
    chroma: Path
    pdfs: Path
    raw: Path
    logs: Path


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    file: str = "audio_scholar.log"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    timeout: int = 30
    wal_mode: bool = True


@dataclass
class ScraperConfig:
    """Single scraper configuration."""
    rate_limit: float = 1.0
    max_retries: int = 3


@dataclass
class ScrapingConfig:
    """All scrapers configuration."""
    arxiv: ScraperConfig = field(default_factory=lambda: ScraperConfig(rate_limit=3.0))
    ismir: ScraperConfig = field(default_factory=ScraperConfig)
    icassp: ScraperConfig = field(default_factory=ScraperConfig)


@dataclass
class PdfConfig:
    """PDF processing configuration."""
    extractor: str = "pymupdf"
    download_timeout: int = 60
    max_file_size_mb: int = 50


@dataclass
class EmbeddingsConfig:
    """Embeddings configuration."""
    model: str = "all-MiniLM-L6-v2"
    batch_size: int = 32
    device: str = "auto"


@dataclass
class LlmConfig:
    """LLM configuration."""
    provider: str = "ollama"
    model: str = "llama3.1:8b"
    endpoint: str = "http://localhost:11434"
    context_length: int = 8192
    temperature: float = 0.7


@dataclass
class RagConfig:
    """RAG configuration."""
    top_k: int = 10
    min_similarity: float = 0.5


@dataclass
class Config:
    """Main configuration container."""
    paths: PathsConfig
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    scraping: ScrapingConfig = field(default_factory=ScrapingConfig)
    pdf: PdfConfig = field(default_factory=PdfConfig)
    embeddings: EmbeddingsConfig = field(default_factory=EmbeddingsConfig)
    llm: LlmConfig = field(default_factory=LlmConfig)
    rag: RagConfig = field(default_factory=RagConfig)

    # Internal: project root for path resolution
    _project_root: Path = field(default=None, repr=False)


# =============================================================================
# Configuration Loading
# =============================================================================

def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml. If None, searches upward
                     from current directory for config.yaml.

    Returns:
        Validated Config object with resolved paths.

    Raises:
        FileNotFoundError: If config file not found.
        ValueError: If config validation fails.
    """
    if config_path is None:
        config_path = _find_config_file()
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    project_root = config_path.parent

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    config = _parse_config(raw, project_root)
    _validate_config(config)

    return config


def _find_config_file() -> Path:
    """Search upward from current directory for config.yaml."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        candidate = parent / "config.yaml"
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "config.yaml not found in current directory or any parent directory"
    )


# =============================================================================
# Parsing
# =============================================================================

def _parse_config(raw: dict, project_root: Path) -> Config:
    """Parse raw YAML dict into Config dataclass."""

    # Check for unknown top-level keys
    known_keys = {"paths", "logging", "database", "scraping", "pdf",
                  "embeddings", "llm", "rag"}
    _check_unknown_keys(raw, known_keys, "root")

    # Parse paths (required)
    if "paths" not in raw:
        raise ValueError("Missing required section: 'paths'")
    paths = _parse_paths(raw["paths"], project_root)

    # Parse optional sections with defaults
    logging_config = _parse_logging(raw.get("logging", {}))
    database_config = _parse_database(raw.get("database", {}))
    scraping_config = _parse_scraping(raw.get("scraping", {}))
    pdf_config = _parse_pdf(raw.get("pdf", {}))
    embeddings_config = _parse_embeddings(raw.get("embeddings", {}))
    llm_config = _parse_llm(raw.get("llm", {}))
    rag_config = _parse_rag(raw.get("rag", {}))

    return Config(
        paths=paths,
        logging=logging_config,
        database=database_config,
        scraping=scraping_config,
        pdf=pdf_config,
        embeddings=embeddings_config,
        llm=llm_config,
        rag=rag_config,
        _project_root=project_root,
    )


def _check_unknown_keys(data: dict, known: Set[str], context: str) -> None:
    """Raise ValueError if unknown keys are present."""
    if not isinstance(data, dict):
        return
    unknown = set(data.keys()) - known
    if unknown:
        raise ValueError(f"Unknown keys in {context}: {unknown}")


def _parse_paths(raw: dict, project_root: Path) -> PathsConfig:
    """Parse paths section."""
    known_keys = {"database", "chroma", "pdfs", "raw", "logs"}
    _check_unknown_keys(raw, known_keys, "paths")

    required = ["database", "chroma", "pdfs", "raw", "logs"]
    for key in required:
        if key not in raw:
            raise ValueError(f"Missing required path: 'paths.{key}'")

    def resolve_path(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = project_root / path
        return path

    return PathsConfig(
        database=resolve_path(raw["database"]),
        chroma=resolve_path(raw["chroma"]),
        pdfs=resolve_path(raw["pdfs"]),
        raw=resolve_path(raw["raw"]),
        logs=resolve_path(raw["logs"]),
    )


def _parse_logging(raw: dict) -> LoggingConfig:
    """Parse logging section."""
    known_keys = {"level", "format", "file"}
    _check_unknown_keys(raw, known_keys, "logging")

    return LoggingConfig(
        level=raw.get("level", LoggingConfig.level),
        format=raw.get("format", LoggingConfig.format),
        file=raw.get("file", LoggingConfig.file),
    )


def _parse_database(raw: dict) -> DatabaseConfig:
    """Parse database section."""
    known_keys = {"timeout", "wal_mode"}
    _check_unknown_keys(raw, known_keys, "database")

    return DatabaseConfig(
        timeout=raw.get("timeout", DatabaseConfig.timeout),
        wal_mode=raw.get("wal_mode", DatabaseConfig.wal_mode),
    )


def _parse_scraper(raw: dict, context: str) -> ScraperConfig:
    """Parse a single scraper config."""
    known_keys = {"rate_limit", "max_retries"}
    _check_unknown_keys(raw, known_keys, context)

    return ScraperConfig(
        rate_limit=raw.get("rate_limit", ScraperConfig.rate_limit),
        max_retries=raw.get("max_retries", ScraperConfig.max_retries),
    )


def _parse_scraping(raw: dict) -> ScrapingConfig:
    """Parse scraping section."""
    known_keys = {"arxiv", "ismir", "icassp"}
    _check_unknown_keys(raw, known_keys, "scraping")

    return ScrapingConfig(
        arxiv=_parse_scraper(raw.get("arxiv", {}), "scraping.arxiv"),
        ismir=_parse_scraper(raw.get("ismir", {}), "scraping.ismir"),
        icassp=_parse_scraper(raw.get("icassp", {}), "scraping.icassp"),
    )


def _parse_pdf(raw: dict) -> PdfConfig:
    """Parse pdf section."""
    known_keys = {"extractor", "download_timeout", "max_file_size_mb"}
    _check_unknown_keys(raw, known_keys, "pdf")

    return PdfConfig(
        extractor=raw.get("extractor", PdfConfig.extractor),
        download_timeout=raw.get("download_timeout", PdfConfig.download_timeout),
        max_file_size_mb=raw.get("max_file_size_mb", PdfConfig.max_file_size_mb),
    )


def _parse_embeddings(raw: dict) -> EmbeddingsConfig:
    """Parse embeddings section."""
    known_keys = {"model", "batch_size", "device"}
    _check_unknown_keys(raw, known_keys, "embeddings")

    return EmbeddingsConfig(
        model=raw.get("model", EmbeddingsConfig.model),
        batch_size=raw.get("batch_size", EmbeddingsConfig.batch_size),
        device=raw.get("device", EmbeddingsConfig.device),
    )


def _parse_llm(raw: dict) -> LlmConfig:
    """Parse llm section."""
    known_keys = {"provider", "model", "endpoint", "context_length", "temperature"}
    _check_unknown_keys(raw, known_keys, "llm")

    return LlmConfig(
        provider=raw.get("provider", LlmConfig.provider),
        model=raw.get("model", LlmConfig.model),
        endpoint=raw.get("endpoint", LlmConfig.endpoint),
        context_length=raw.get("context_length", LlmConfig.context_length),
        temperature=raw.get("temperature", LlmConfig.temperature),
    )


def _parse_rag(raw: dict) -> RagConfig:
    """Parse rag section."""
    known_keys = {"top_k", "min_similarity"}
    _check_unknown_keys(raw, known_keys, "rag")

    return RagConfig(
        top_k=raw.get("top_k", RagConfig.top_k),
        min_similarity=raw.get("min_similarity", RagConfig.min_similarity),
    )


# =============================================================================
# Validation
# =============================================================================

def _validate_config(config: Config) -> None:
    """Validate configuration values."""

    # Validate logging level
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    if config.logging.level.upper() not in valid_levels:
        raise ValueError(
            f"Invalid logging level: '{config.logging.level}'. "
            f"Must be one of: {valid_levels}"
        )

    # Validate PDF extractor
    valid_extractors = {"pymupdf", "nougat"}
    if config.pdf.extractor not in valid_extractors:
        raise ValueError(
            f"Invalid PDF extractor: '{config.pdf.extractor}'. "
            f"Must be one of: {valid_extractors}"
        )

    # Validate embeddings device
    valid_devices = {"auto", "cpu", "cuda"}
    if config.embeddings.device not in valid_devices:
        raise ValueError(
            f"Invalid embeddings device: '{config.embeddings.device}'. "
            f"Must be one of: {valid_devices}"
        )

    # Validate numeric ranges
    if config.database.timeout <= 0:
        raise ValueError("database.timeout must be positive")

    if config.pdf.download_timeout <= 0:
        raise ValueError("pdf.download_timeout must be positive")

    if config.pdf.max_file_size_mb <= 0:
        raise ValueError("pdf.max_file_size_mb must be positive")

    if config.embeddings.batch_size <= 0:
        raise ValueError("embeddings.batch_size must be positive")

    if config.llm.context_length <= 0:
        raise ValueError("llm.context_length must be positive")

    if not (0.0 <= config.llm.temperature <= 2.0):
        raise ValueError("llm.temperature must be between 0.0 and 2.0")

    if config.rag.top_k <= 0:
        raise ValueError("rag.top_k must be positive")

    if not (0.0 <= config.rag.min_similarity <= 1.0):
        raise ValueError("rag.min_similarity must be between 0.0 and 1.0")

    for scraper_name in ["arxiv", "ismir", "icassp"]:
        scraper = getattr(config.scraping, scraper_name)
        if scraper.rate_limit <= 0:
            raise ValueError(f"scraping.{scraper_name}.rate_limit must be positive")
        if scraper.max_retries < 0:
            raise ValueError(f"scraping.{scraper_name}.max_retries must be non-negative")

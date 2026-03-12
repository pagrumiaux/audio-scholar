"""Configuration loading and validation."""

from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Optional, Set

import yaml


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


def load_config(config_path: Optional[Path] = None) -> Config:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config.yaml. If None, searches upward
                     from current directory for config.yaml.

    Returns:
        Validated Config object with resolved paths.
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    project_root = config_path.parent

    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    config = _parse_config(raw, project_root)
    _validate_config(config)

    return config



def _parse_config(raw: dict, project_root: Path) -> Config:
    """Parse raw YAML dict into Config dataclass."""

    # Check for unknown keys
    known_keys = {"paths", "logging", "database", "scraping", "pdf",
                  "embeddings", "llm", "rag"}
    _check_unknown_keys(raw, known_keys, "root")

    # Parse paths (special handling for path resolution)
    if "paths" not in raw:
        raise ValueError("Missing required section: 'paths'")
    paths = _parse_paths(raw["paths"], project_root)

    # Parse optional sections with defaults
    scraping_config = _parse_scraping(raw.get("scraping", {}))

    return Config(
        paths=paths,
        logging=_parse_section(raw.get("logging", {}), LoggingConfig, "logging"),
        database=_parse_section(raw.get("database", {}), DatabaseConfig, "database"),
        scraping=scraping_config,
        pdf=_parse_section(raw.get("pdf", {}), PdfConfig, "pdf"),
        embeddings=_parse_section(raw.get("embeddings", {}), EmbeddingsConfig, "embeddings"),
        llm=_parse_section(raw.get("llm", {}), LlmConfig, "llm"),
        rag=_parse_section(raw.get("rag", {}), RagConfig, "rag"),
        _project_root=project_root,
    )


def _check_unknown_keys(data: dict, known: Set[str], context: str) -> None:
    """Raise ValueError if unknown keys are present."""
    if not isinstance(data, dict):
        return
    unknown = set(data.keys()) - known
    if unknown:
        raise ValueError(f"Unknown keys in {context}: {unknown}")


def _parse_section(raw: dict, cls: type, context: str):
    """Parse a config section into a dataclass using its field definitions."""
    # Check for unknown keys
    known_keys = {f.name for f in fields(cls)}
    _check_unknown_keys(raw, known_keys, context)
    
    # Only pass keys present in raw; dataclass defaults handle the rest
    kwargs = {k: v for k, v in raw.items() if k in known_keys}
    return cls(**kwargs)


def _parse_paths(raw: dict, project_root: Path) -> PathsConfig:
    """Parse paths section."""
    # Check for unknown keys
    known_keys = {"database", "chroma", "pdfs", "raw", "logs"}
    _check_unknown_keys(raw, known_keys, "paths")

    # Check for required keys
    required = ["database", "chroma", "pdfs", "raw", "logs"]
    for key in required:
        if key not in raw:
            raise ValueError(f"Missing required path: 'paths.{key}'")

    def resolve_path(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = project_root / path
        return path

    # Return config
    return PathsConfig(
        database=resolve_path(raw["database"]),
        chroma=resolve_path(raw["chroma"]),
        pdfs=resolve_path(raw["pdfs"]),
        raw=resolve_path(raw["raw"]),
        logs=resolve_path(raw["logs"]),
    )


def _parse_scraping(raw: dict) -> ScrapingConfig:
    """Parse scraping section (nested structure needs special handling)."""
    # Check for unknown keys
    known_keys = {"arxiv", "ismir", "icassp"}
    _check_unknown_keys(raw, known_keys, "scraping")

    # Return config
    return ScrapingConfig(
        arxiv=_parse_section(raw.get("arxiv", {}), ScraperConfig, "scraping.arxiv"),
        ismir=_parse_section(raw.get("ismir", {}), ScraperConfig, "scraping.ismir"),
        icassp=_parse_section(raw.get("icassp", {}), ScraperConfig, "scraping.icassp"),
    )


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

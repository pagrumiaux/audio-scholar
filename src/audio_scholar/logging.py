"""Logging setup."""

import logging
import sys

from audio_scholar.config import Config


def setup_logging(config: Config) -> logging.Logger:
    """Configure logging for the application.

    Args:
        config: Application configuration.

    Returns:
        Root logger for the audio_scholar package.
    """
    # Get the root logger for our package
    logger = logging.getLogger("audio_scholar")
    logger.handlers.clear()

    # Set level
    level = getattr(logging, config.logging.level.upper())
    logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(config.logging.format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_dir = config.paths.logs
    if log_dir:
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / config.logging.file
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except OSError as e:
            logger.warning(f"Could not create log file: {e}")

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Module name (typically __name__).

    Returns:
        Logger instance.
    """
    # Ensure the name is under our package namespace
    if not name.startswith("audio_scholar"):
        name = f"audio_scholar.{name}"
    return logging.getLogger(name)

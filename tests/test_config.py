"""Tests for configuration loading and validation."""

import pytest
from pathlib import Path

from audio_scholar.config import load_config


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_valid_config(self, tmp_path, config_yaml_content):
        """Config loads successfully with valid YAML."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml_content)

        config = load_config(config_file)

        assert config.paths.database == tmp_path / "db/test.db"
        assert config.paths.chroma == tmp_path / "db/chroma"

    def test_defaults_applied(self, tmp_path, config_yaml_content):
        """Missing optional values use defaults."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml_content)

        config = load_config(config_file)

        # Check defaults
        assert config.logging.level == "INFO"
        assert config.database.timeout == 30
        assert config.database.wal_mode is True
        assert config.rag.top_k == 10
        assert config.embeddings.model == "all-MiniLM-L6-v2"

    def test_missing_config_file(self, tmp_path):
        """Raises FileNotFoundError for missing config."""
        config_file = tmp_path / "nonexistent.yaml"

        with pytest.raises(FileNotFoundError):
            load_config(config_file)

    def test_missing_paths_section(self, tmp_path):
        """Raises ValueError when paths section is missing."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("logging:\n  level: DEBUG\n")

        with pytest.raises(ValueError, match="Missing required section"):
            load_config(config_file)

    def test_missing_required_path(self, tmp_path):
        """Raises ValueError when required path is missing."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
paths:
  database: "db/test.db"
  # Missing other required paths
""")

        with pytest.raises(ValueError, match="Missing required path"):
            load_config(config_file)

    def test_unknown_top_level_key(self, tmp_path, config_yaml_content):
        """Raises ValueError for unknown top-level keys."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml_content + "\nunknown_key: value\n")

        with pytest.raises(ValueError, match="Unknown keys"):
            load_config(config_file)

    def test_unknown_nested_key(self, tmp_path):
        """Raises ValueError for unknown nested keys."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text("""
paths:
  database: "db/test.db"
  chroma: "db/chroma"
  pdfs: "data/pdfs"
  raw: "data/raw"
  logs: "logs"
  unknown_path: "somewhere"
""")

        with pytest.raises(ValueError, match="Unknown keys"):
            load_config(config_file)

    def test_invalid_logging_level(self, tmp_path, config_yaml_content):
        """Raises ValueError for invalid logging level."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml_content + "\nlogging:\n  level: INVALID\n")

        with pytest.raises(ValueError, match="Invalid logging level"):
            load_config(config_file)

    def test_invalid_pdf_extractor(self, tmp_path, config_yaml_content):
        """Raises ValueError for invalid PDF extractor."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml_content + "\npdf:\n  extractor: invalid\n")

        with pytest.raises(ValueError, match="Invalid PDF extractor"):
            load_config(config_file)

    def test_invalid_embeddings_device(self, tmp_path, config_yaml_content):
        """Raises ValueError for invalid embeddings device."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml_content + "\nembeddings:\n  device: gpu\n")

        with pytest.raises(ValueError, match="Invalid embeddings device"):
            load_config(config_file)

    def test_negative_timeout(self, tmp_path, config_yaml_content):
        """Raises ValueError for negative timeout."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml_content + "\ndatabase:\n  timeout: -1\n")

        with pytest.raises(ValueError, match="must be positive"):
            load_config(config_file)

    def test_temperature_out_of_range(self, tmp_path, config_yaml_content):
        """Raises ValueError for temperature out of range."""
        config_file = tmp_path / "config.yaml"
        config_file.write_text(config_yaml_content + "\nllm:\n  temperature: 3.0\n")

        with pytest.raises(ValueError, match="temperature must be between"):
            load_config(config_file)

    def test_paths_resolved_relative_to_config(self, tmp_path, config_yaml_content):
        """Relative paths are resolved relative to config file location."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        config_file = subdir / "config.yaml"
        config_file.write_text(config_yaml_content)

        config = load_config(config_file)

        # Paths should be relative to subdir, not cwd
        assert config.paths.database == subdir / "db/test.db"

    def test_absolute_paths_preserved(self, tmp_path):
        """Absolute paths are not modified."""
        config_file = tmp_path / "config.yaml"
        # Use forward slashes for cross-platform compatibility in YAML
        abs_path = str(tmp_path / "absolute" / "db.sqlite").replace("\\", "/")
        config_file.write_text(f"""
paths:
  database: "{abs_path}"
  chroma: "db/chroma"
  pdfs: "data/pdfs"
  raw: "data/raw"
  logs: "logs"
""")

        config = load_config(config_file)

        assert config.paths.database == Path(abs_path)

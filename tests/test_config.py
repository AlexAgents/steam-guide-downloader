"""Tests for configuration"""

import pytest
import sys
import os
import json
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import AppConfig, AVAILABLE_THEMES


class TestAppConfigDefaults:
    """Default configuration values"""

    def test_default_language(self):
        c = AppConfig()
        assert c.language == "en"

    def test_default_theme(self):
        c = AppConfig()
        assert c.theme in AVAILABLE_THEMES

    def test_default_timeout(self):
        c = AppConfig()
        assert c.timeout == 15

    def test_default_retries(self):
        c = AppConfig()
        assert c.max_retries == 3

    def test_default_pdf_false(self):
        c = AppConfig()
        assert c.convert_to_pdf is False


class TestAppConfigValidation:
    """Config field validation"""

    def test_invalid_language_falls_back(self):
        c = AppConfig(language="fr")
        assert c.language == "en"

    def test_invalid_theme_falls_back(self):
        c = AppConfig(theme="nonexistent")
        assert c.theme in AVAILABLE_THEMES

    def test_negative_timeout_falls_back(self):
        c = AppConfig(timeout=0)
        assert c.timeout == 15

    def test_negative_retries_falls_back(self):
        c = AppConfig(max_retries=-1)
        assert c.max_retries == 3

    def test_valid_ru_language(self):
        c = AppConfig(language="ru")
        assert c.language == "ru"

    def test_valid_en_language(self):
        c = AppConfig(language="en")
        assert c.language == "en"


class TestAppConfigSaveLoad:
    """Config save/load cycle"""

    def test_save_and_load(self, tmp_path, monkeypatch):
        config_file = str(tmp_path / "settings.json")
        monkeypatch.setattr(
            "app.config.get_config_path",
            lambda: config_file
        )

        original = AppConfig(language="ru", theme="dark", timeout=30)
        original.save()

        assert os.path.isfile(config_file)

        loaded = AppConfig.load()
        assert loaded.language == "ru"
        assert loaded.theme == "dark"
        assert loaded.timeout == 30

    def test_load_missing_file(self, tmp_path, monkeypatch):
        config_file = str(tmp_path / "nonexistent.json")
        monkeypatch.setattr(
            "app.config.get_config_path",
            lambda: config_file
        )

        loaded = AppConfig.load()
        assert loaded.language == "en"
        assert loaded.timeout == 15

    def test_load_corrupted_json(self, tmp_path, monkeypatch):
        config_file = str(tmp_path / "broken.json")
        monkeypatch.setattr(
            "app.config.get_config_path",
            lambda: config_file
        )

        with open(config_file, "w") as f:
            f.write("{broken json!!!")

        loaded = AppConfig.load()
        assert loaded.language == "en"

    def test_load_ignores_unknown_fields(self, tmp_path, monkeypatch):
        config_file = str(tmp_path / "extra.json")
        monkeypatch.setattr(
            "app.config.get_config_path",
            lambda: config_file
        )

        data = {"language": "ru", "unknown_field": "value", "foo": 42}
        with open(config_file, "w") as f:
            json.dump(data, f)

        loaded = AppConfig.load()
        assert loaded.language == "ru"
        assert not hasattr(loaded, "unknown_field")
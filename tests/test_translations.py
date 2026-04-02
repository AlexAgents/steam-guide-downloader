"""Tests for translation system"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.translations import get_text, TRANSLATIONS


class TestTranslationKeys:
    """All keys exist in both languages"""

    def test_same_keys(self):
        en_keys = set(TRANSLATIONS["en"].keys())
        ru_keys = set(TRANSLATIONS["ru"].keys())
        missing_in_ru = en_keys - ru_keys
        missing_in_en = ru_keys - en_keys
        assert not missing_in_ru, f"Missing in RU: {missing_in_ru}"
        assert not missing_in_en, f"Missing in EN: {missing_in_en}"

    def test_no_empty_values_en(self):
        for key, value in TRANSLATIONS["en"].items():
            assert value, f"Empty EN value for key '{key}'"

    def test_no_empty_values_ru(self):
        for key, value in TRANSLATIONS["ru"].items():
            assert value, f"Empty RU value for key '{key}'"


class TestGetText:
    """get_text function behavior"""

    def test_en_basic(self):
        r = get_text("en", "btn_download")
        assert r
        assert isinstance(r, str)

    def test_ru_basic(self):
        r = get_text("ru", "btn_download")
        assert r
        assert isinstance(r, str)

    def test_unknown_lang_falls_back_to_en(self):
        r = get_text("xx", "btn_download")
        assert r == get_text("en", "btn_download")

    def test_unknown_key_returns_key(self):
        r = get_text("en", "nonexistent_key_12345")
        assert r == "nonexistent_key_12345"

    def test_format_args(self):
        r = get_text("en", "log_start", "https://example.com")
        assert "https://example.com" in r

    def test_format_numeric(self):
        r = get_text("en", "log_sections_found", 5)
        assert "5" in r

    def test_format_args_ru(self):
        r = get_text("ru", "err_access", 403)
        assert "403" in r

    def test_format_bad_args_no_crash(self):
        r = get_text("en", "btn_download", "extra", "args")
        assert isinstance(r, str)


class TestTranslationContent:
    """Content quality checks"""

    def test_window_title_en(self):
        assert "Steam" in get_text("en", "window_title")

    def test_window_title_ru(self):
        assert "Steam" in get_text("ru", "window_title")

    def test_error_messages_not_identical(self):
        en = get_text("en", "err_no_url")
        ru = get_text("ru", "err_no_url")
        assert en != ru
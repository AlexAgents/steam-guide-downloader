"""Tests for utility functions"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils import clean_filename, validate_save_path


class TestCleanFilename:
    """Filename sanitization"""

    def test_normal(self):
        assert clean_filename("My Guide") == "My Guide"

    def test_preserves_unicode(self):
        assert clean_filename("Руководство по игре") == "Руководство по игре"

    def test_removes_special(self):
        r = clean_filename('Test: "guide" <3>')
        assert ':' not in r
        assert '"' not in r
        assert '<' not in r
        assert '>' not in r

    def test_removes_slashes(self):
        r = clean_filename("path/to\\file")
        assert '/' not in r
        assert '\\' not in r

    def test_removes_pipe(self):
        r = clean_filename("choice A | choice B")
        assert '|' not in r

    def test_removes_question_asterisk(self):
        r = clean_filename("what? file*.txt")
        assert '?' not in r
        assert '*' not in r

    def test_empty(self):
        assert clean_filename("") == ""

    def test_none_like(self):
        assert clean_filename("") == ""

    def test_whitespace_only(self):
        assert clean_filename("   ") == ""

    def test_long_name(self):
        result = clean_filename("A" * 300)
        assert len(result) <= 200

    def test_strips_trailing_dots(self):
        result = clean_filename("test...")
        assert not result.endswith(".")

    def test_strips_trailing_spaces(self):
        result = clean_filename("test   ")
        assert not result.endswith(" ")

    def test_collapses_spaces(self):
        result = clean_filename("hello    world")
        assert result == "hello world"

    def test_control_characters(self):
        result = clean_filename("test\x00\x01\x1f\x7ffile")
        assert '\x00' not in result
        assert '\x7f' not in result


class TestValidateSavePath:
    """Save path validation"""

    def test_valid_existing(self, tmp_path):
        ok, result = validate_save_path(str(tmp_path))
        assert ok
        assert result == str(tmp_path)

    def test_empty(self):
        ok, _ = validate_save_path("")
        assert not ok

    def test_whitespace(self):
        ok, _ = validate_save_path("   ")
        assert not ok

    def test_creatable(self, tmp_path):
        new_dir = str(tmp_path / "new_folder")
        ok, result = validate_save_path(new_dir)
        assert ok
        assert os.path.isdir(result)

    def test_nested_creatable(self, tmp_path):
        deep = str(tmp_path / "a" / "b" / "c")
        ok, result = validate_save_path(deep)
        assert ok
        assert os.path.isdir(result)

    def test_normalizes_path(self, tmp_path):
        weird = str(tmp_path) + os.sep + "." + os.sep + "sub"
        ok, result = validate_save_path(weird)
        assert ok
        assert ".." not in result or os.sep + "." + os.sep not in result

    def test_expands_user(self):
        ok, result = validate_save_path("~/test_sgd_temp")
        if ok:
            assert "~" not in result
            # Cleanup
            try:
                os.rmdir(result)
            except OSError:
                pass

    @pytest.mark.skipif(os.name != 'nt', reason="Windows only")
    def test_invalid_windows_chars(self):
        ok, _ = validate_save_path('C:\\test<>file')
        assert not ok
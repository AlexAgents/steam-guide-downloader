"""Tests for URL validation"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.network import URLValidator


class TestURLValidatorBasic:
    """Basic URL validation"""

    def test_valid_full_url(self):
        ok, r = URLValidator.validate(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=123456"
        )
        assert ok
        assert "id=123456" in r

    def test_valid_with_www(self):
        ok, r = URLValidator.validate(
            "https://www.steamcommunity.com/sharedfiles/filedetails/?id=789"
        )
        assert ok
        assert "id=789" in r

    def test_auto_https(self):
        ok, r = URLValidator.validate(
            "steamcommunity.com/sharedfiles/filedetails/?id=456"
        )
        assert ok
        assert r.startswith("https://")
        assert "id=456" in r

    def test_http_to_https(self):
        ok, r = URLValidator.validate(
            "http://steamcommunity.com/sharedfiles/filedetails/?id=111"
        )
        assert ok
        assert r.startswith("https://")

    def test_normalized_output(self):
        ok, r = URLValidator.validate(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=42&other=param"
        )
        assert ok
        assert r == "https://steamcommunity.com/sharedfiles/filedetails/?id=42"


class TestURLValidatorInvalid:
    """Invalid URL rejection"""

    def test_empty(self):
        ok, _ = URLValidator.validate("")
        assert not ok

    def test_none_like(self):
        ok, _ = URLValidator.validate("   ")
        assert not ok

    def test_wrong_host(self):
        ok, _ = URLValidator.validate("https://google.com/something")
        assert not ok

    def test_wrong_path(self):
        ok, _ = URLValidator.validate(
            "https://steamcommunity.com/profiles/12345"
        )
        assert not ok

    def test_no_id(self):
        ok, _ = URLValidator.validate(
            "https://steamcommunity.com/sharedfiles/filedetails/"
        )
        assert not ok

    def test_empty_id(self):
        ok, _ = URLValidator.validate(
            "https://steamcommunity.com/sharedfiles/filedetails/?id="
        )
        assert not ok

    def test_non_numeric_id(self):
        ok, _ = URLValidator.validate(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=abc"
        )
        assert not ok

    def test_random_text(self):
        ok, _ = URLValidator.validate("not a url at all")
        assert not ok

    def test_partial_url(self):
        ok, _ = URLValidator.validate("steamcommunity.com")
        assert not ok


class TestURLValidatorExtractID:
    """Guide ID extraction"""

    def test_extract_valid(self):
        gid = URLValidator.extract_guide_id(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=42"
        )
        assert gid == "42"

    def test_extract_large_id(self):
        gid = URLValidator.extract_guide_id(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=2999999999"
        )
        assert gid == "2999999999"

    def test_extract_from_any_url(self):
        """extract_guide_id is a simple helper that extracts ?id= param
        from any URL regardless of host — this is by design."""
        gid = URLValidator.extract_guide_id(
            "https://google.com/?id=42"
        )
        assert gid == "42"

    def test_extract_none_no_id(self):
        gid = URLValidator.extract_guide_id(
            "https://steamcommunity.com/sharedfiles/filedetails/"
        )
        assert gid is None

    def test_extract_none_non_numeric(self):
        gid = URLValidator.extract_guide_id(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=hello"
        )
        assert gid is None

    def test_extract_none_no_query(self):
        gid = URLValidator.extract_guide_id(
            "https://steamcommunity.com"
        )
        assert gid is None

    def test_extract_none_empty(self):
        gid = URLValidator.extract_guide_id("")
        assert gid is None

    def test_extract_with_extra_params(self):
        gid = URLValidator.extract_guide_id(
            "https://steamcommunity.com/sharedfiles/filedetails/?id=777&lang=en"
        )
        assert gid == "777"
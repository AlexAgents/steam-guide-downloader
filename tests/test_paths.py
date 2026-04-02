"""Tests for path resolution"""

import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.paths import (
    get_base_dir, get_app_dir, get_data_dir,
    get_themes_dir, get_assets_dir,
    get_config_path, get_log_path, get_session_logs_dir
)


class TestBasePaths:
    """Base directory resolution"""

    def test_base_dir_exists(self):
        d = get_base_dir()
        assert os.path.isdir(d)

    def test_app_dir_exists(self):
        d = get_app_dir()
        assert os.path.isdir(d)

    def test_base_dir_has_app(self):
        d = get_base_dir()
        assert os.path.isdir(os.path.join(d, "app"))

    def test_base_dir_has_themes(self):
        d = get_base_dir()
        assert os.path.isdir(os.path.join(d, "themes"))


class TestDataDir:
    """Data directory (.cfg/)"""

    def test_data_dir_created(self):
        d = get_data_dir()
        assert os.path.isdir(d)
        assert d.endswith(".cfg")

    def test_config_in_data_dir(self):
        p = get_config_path()
        assert ".cfg" in p
        assert p.endswith("settings.json")

    def test_log_in_data_dir(self):
        p = get_log_path()
        assert ".cfg" in p
        assert p.endswith("downloader.log")

    def test_session_logs_dir_created(self):
        d = get_session_logs_dir()
        assert os.path.isdir(d)
        assert "logs" in d


class TestResourcePaths:
    """Resource directory resolution"""

    def test_themes_dir(self):
        d = get_themes_dir()
        assert "themes" in d

    def test_assets_dir(self):
        d = get_assets_dir()
        assert "assets" in d
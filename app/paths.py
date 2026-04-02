# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""
Path resolution — works in dev mode and in PyInstaller EXE
"""

import os
import sys

_APP_DATA_DIR = ".cfg"


def get_base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_app_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_dir() -> str:
    """Directory for all app runtime data (config, logs, etc.)
    Located next to the executable or project root as .cfg/"""
    d = os.path.join(get_app_dir(), _APP_DATA_DIR)
    os.makedirs(d, exist_ok=True)
    return d


def get_resource_path(relative_path: str) -> str:
    return os.path.join(get_base_dir(), relative_path)


def get_themes_dir() -> str:
    return get_resource_path("themes")


def get_assets_dir() -> str:
    return get_resource_path("assets")


def get_config_path() -> str:
    return os.path.join(get_data_dir(), "settings.json")


def get_log_path() -> str:
    return os.path.join(get_data_dir(), "downloader.log")


def get_session_logs_dir() -> str:
    d = os.path.join(get_data_dir(), "logs")
    os.makedirs(d, exist_ok=True)
    return d
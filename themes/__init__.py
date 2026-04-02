# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""Theme manager — light & dark themes"""

import os
import logging

from app.paths import get_themes_dir

logger = logging.getLogger(__name__)

_ALLOWED = ("light", "dark")


def load_theme(name: str) -> str:
    """Load QSS theme file by name."""
    if name not in _ALLOWED:
        name = "dark"
    p = os.path.join(get_themes_dir(), f"{name}.qss")
    if not os.path.isfile(p):
        logger.warning(f"Theme file not found: {p}")
        return ""
    try:
        with open(p, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        logger.error(f"Failed to load theme '{name}': {e}")
        return ""


def get_available_themes() -> list[str]:
    """Return list of available theme names."""
    return list(_ALLOWED)
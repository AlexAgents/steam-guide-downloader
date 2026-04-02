# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""Application configuration"""

import os
import json
import logging
import functools
import random
from dataclasses import dataclass, field, asdict

from app.paths import get_config_path, get_app_dir

logger = logging.getLogger(__name__)

# ── Dynamic User-Agent ──
_CHROME_VERSIONS = list(range(120, 138))
_OS_VARIANTS = [
    "Windows NT 10.0; Win64; x64",
    "Windows NT 11.0; Win64; x64",
    "Macintosh; Intel Mac OS X 10_15_7",
    "X11; Linux x86_64",
]


def _generate_user_agent() -> str:
    """Generate a realistic randomized User-Agent string."""
    try:
        chrome_ver = random.choice(_CHROME_VERSIONS)
        os_variant = random.choice(_OS_VARIANTS)
        return (
            f"Mozilla/5.0 ({os_variant}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Chrome/{chrome_ver}.0.0.0 Safari/537.36"
        )
    except Exception:
        return _DEFAULT_USER_AGENT


_DEFAULT_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/131.0.0.0 Safari/537.36'
)


def get_headers() -> dict:
    """Return request headers with dynamic User-Agent."""
    ua = _generate_user_agent()
    return {
        'User-Agent': ua,
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    }


# Keep a static reference for modules that import HEADERS directly
HEADERS = get_headers()


@functools.lru_cache(maxsize=1)
def has_pillow() -> bool:
    try:
        from PIL import Image
        return True
    except ImportError:
        return False


AVAILABLE_THEMES = ["light", "dark"]


def _get_available_memory_mb() -> int:
    """Return available system memory in MB. Falls back to 1024 MB."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return int(mem.available / (1024 * 1024))
    except ImportError:
        pass
    try:
        import os as _os
        if hasattr(_os, 'sysconf'):
            pages = _os.sysconf('SC_AVPHYS_PAGES')
            page_size = _os.sysconf('SC_PAGE_SIZE')
            if pages > 0 and page_size > 0:
                return int((pages * page_size) / (1024 * 1024))
    except (ValueError, OSError):
        pass
    try:
        import ctypes
        if os.name == 'nt':
            kernel32 = ctypes.windll.kernel32

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            if kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return int(stat.ullAvailPhys / (1024 * 1024))
    except Exception:
        pass
    return 1024


def compute_image_cache_limit() -> int:
    """Compute max image cache size based on available memory."""
    avail = _get_available_memory_mb()
    limit = max(50, min(int(avail * 0.10), 500))
    return limit


@dataclass
class AppConfig:
    language: str = "en"
    save_dir: str = field(
        default_factory=lambda: os.path.join(get_app_dir(), "Steam_Manuals")
    )
    theme: str = "dark"
    timeout: int = 15
    max_retries: int = 3
    retry_backoff: float = 0.5
    max_image_size_mb: int = 50
    max_image_width_inches: float = 6.0
    cell_image_width_inches: float = 1.8
    convert_to_pdf: bool = False
    save_images: bool = False
    image_cache_limit_mb: int = field(
        default_factory=compute_image_cache_limit
    )
    pdf_timeout: int = 300
    max_page_size_mb: int = 50

    def __post_init__(self):
        if self.language not in ("en", "ru"):
            logger.warning(
                f"Invalid language '{self.language}', falling back to 'en'"
            )
            self.language = "en"
        if self.timeout < 1:
            logger.warning(
                f"Invalid timeout {self.timeout}, falling back to 15"
            )
            self.timeout = 15
        if self.max_retries < 0:
            logger.warning(
                f"Invalid max_retries {self.max_retries}, falling back to 3"
            )
            self.max_retries = 3
        if self.theme not in AVAILABLE_THEMES:
            logger.warning(
                f"Invalid theme '{self.theme}', falling back to 'dark'"
            )
            self.theme = "dark"
        if self.image_cache_limit_mb < 10:
            logger.warning(
                f"Image cache limit too low ({self.image_cache_limit_mb}), "
                f"falling back to 50"
            )
            self.image_cache_limit_mb = 50
        if self.pdf_timeout < 60:
            logger.warning(
                f"PDF timeout too low ({self.pdf_timeout}), "
                f"falling back to 300"
            )
            self.pdf_timeout = 300
        if self.max_page_size_mb < 1:
            self.max_page_size_mb = 50

    @classmethod
    def load(cls) -> 'AppConfig':
        config_path = get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                known = {f for f in cls.__dataclass_fields__}
                filtered = {k: v for k, v in data.items() if k in known}
                # Migrate old theme name
                if filtered.get("theme") == "steam":
                    filtered["theme"] = "dark"
                config = cls(**filtered)
                logger.info(f"Config loaded: {config_path}")
                return config
            except (json.JSONDecodeError, TypeError, OSError) as e:
                logger.warning(f"Config error: {e}")
        return cls()

    def save(self):
        config_path = get_config_path()
        tmp_path = config_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, config_path)
        except OSError as e:
            logger.error(f"Save error: {e}")
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass
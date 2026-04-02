# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""Network layer"""

import logging
import threading
from collections import OrderedDict
from io import BytesIO
from urllib.parse import urlparse, parse_qs
from typing import Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config import get_headers, has_pillow, AppConfig

logger = logging.getLogger(__name__)


class URLValidator:
    VALID_HOSTS = frozenset({
        'steamcommunity.com', 'www.steamcommunity.com'
    })
    REQUIRED_PATH = '/sharedfiles/filedetails/'

    @classmethod
    def validate(cls, url: str) -> Tuple[bool, str]:
        if not url or not url.strip():
            return False, "URL is empty"

        url = url.strip()
        protocol_changed = False

        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            protocol_changed = True
        elif url.startswith('http://'):
            protocol_changed = True

        try:
            parsed = urlparse(url)
        except ValueError:
            return False, "Invalid URL format"

        hostname = parsed.hostname
        if not hostname or hostname not in cls.VALID_HOSTS:
            return False, f"Host '{hostname}' is not steamcommunity.com"

        if cls.REQUIRED_PATH not in (parsed.path or ''):
            return False, "URL is not a Steam guide link"

        params = parse_qs(parsed.query)
        ids = params.get('id', [])
        if not ids or not ids[0]:
            return False, "Guide ID not found in URL"

        guide_id = ids[0]
        if not guide_id.isdigit():
            return False, f"Invalid guide ID: '{guide_id}'"

        normalized = (
            f"https://steamcommunity.com/sharedfiles/"
            f"filedetails/?id={guide_id}"
        )

        if protocol_changed:
            logger.info(
                f"URL protocol normalized to HTTPS for id={guide_id}"
            )

        return True, normalized

    @classmethod
    def extract_guide_id(cls, url: str) -> Optional[str]:
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            ids = params.get('id', [])
            if ids and ids[0].isdigit():
                return ids[0]
        except (ValueError, IndexError):
            pass
        return None


def create_session(config: AppConfig) -> requests.Session:
    session = requests.Session()
    session.headers.update(get_headers())
    retry_strategy = Retry(
        total=config.max_retries,
        backoff_factor=config.retry_backoff,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


class ImageCache:
    """LRU image cache with both count and byte-size limits.
    Uses OrderedDict for O(1) LRU operations."""

    def __init__(self, max_count: int = 100,
                 max_bytes: int = 200 * 1024 * 1024):
        self._cache: OrderedDict[str, bytes] = OrderedDict()
        self._max_count = max_count
        self._max_bytes = max_bytes
        self._total_bytes = 0
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def get(self, url: str) -> Optional[BytesIO]:
        with self._lock:
            if url in self._cache:
                self._hits += 1
                self._cache.move_to_end(url)
                return BytesIO(self._cache[url])
            self._misses += 1
            return None

    def put(self, url: str, data: BytesIO):
        with self._lock:
            if url in self._cache:
                return

            data.seek(0)
            raw = data.read()
            data.seek(0)
            item_size = len(raw)

            # Evict until within limits
            while (
                (len(self._cache) >= self._max_count
                 or self._total_bytes + item_size > self._max_bytes)
                and self._cache
            ):
                _, evicted = self._cache.popitem(last=False)
                self._total_bytes -= len(evicted)

            self._cache[url] = raw
            self._total_bytes += item_size

    def clear(self):
        with self._lock:
            self._cache.clear()
            self._total_bytes = 0

    def expand_limit(self, additional_mb: int = 50):
        """Expand cache byte limit dynamically."""
        with self._lock:
            self._max_bytes += additional_mb * 1024 * 1024
            logger.info(
                f"Image cache expanded to "
                f"{self._max_bytes / 1024 / 1024:.0f} MB"
            )

    @property
    def stats(self) -> str:
        with self._lock:
            total = self._hits + self._misses
            rate = (self._hits / total * 100) if total > 0 else 0
            size_mb = self._total_bytes / (1024 * 1024)
            limit_mb = self._max_bytes / (1024 * 1024)
            return (
                f"Cache: {len(self._cache)} items "
                f"({size_mb:.1f}/{limit_mb:.0f} MB), "
                f"hits={self._hits}, miss={self._misses}, "
                f"rate={rate:.0f}%"
            )

    @property
    def is_near_limit(self) -> bool:
        """Check if cache is using more than 80% of its byte limit."""
        with self._lock:
            return self._total_bytes > self._max_bytes * 0.8


def _validate_image_header(data: BytesIO) -> bool:
    """Quick check image magic bytes without Pillow."""
    data.seek(0)
    header = data.read(12)
    data.seek(0)
    if len(header) < 2:
        return False
    if header[:8] == b'\x89PNG\r\n\x1a\n':
        return True
    if header[:2] == b'\xff\xd8':
        return True
    if header[:4] == b'GIF8':
        return True
    if len(header) >= 12 and header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return True
    if header[:2] == b'BM':
        return True
    return False


def download_image(url, session=None, config=None, cache=None):
    """Download image with streaming, size limits, and cache support."""
    if not url or not url.startswith('http'):
        return None

    if config is None:
        config = AppConfig()

    if cache is not None:
        cached = cache.get(url)
        if cached:
            return cached

    req_session = session or requests
    max_size = config.max_image_size_mb * 1024 * 1024
    response = None

    try:
        response = req_session.get(
            url, headers=get_headers(), stream=True, timeout=config.timeout
        )
        response.raise_for_status()

        content_type = response.headers.get('content-type', '')
        if 'image' not in content_type and 'octet-stream' not in content_type:
            return None

        content_length = response.headers.get('content-length')
        if content_length:
            try:
                if int(content_length) > max_size:
                    logger.warning(
                        f"Image too large ({int(content_length)} bytes), "
                        f"limit={max_size}: {url[:80]}"
                    )
                    return None
            except ValueError:
                pass

        # Stream download with size limit
        chunks = []
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            downloaded += len(chunk)
            if downloaded > max_size:
                logger.warning(
                    f"Image exceeded size limit during download: "
                    f"{url[:80]}"
                )
                return None
            chunks.append(chunk)

        if downloaded == 0:
            return None

        data = BytesIO(b"".join(chunks))

        # Validate image header (works without Pillow)
        if not _validate_image_header(data):
            logger.debug(f"Invalid image header: {url[:60]}")
            return None

        # Additional Pillow verification if available
        if has_pillow():
            try:
                from PIL import Image
                img = Image.open(data)
                img.verify()
                data.seek(0)
            except Exception:
                logger.debug(f"Pillow verification failed: {url[:60]}")
                data.seek(0)
                # Don't reject — header was valid, let docx handle it

        if cache is not None:
            if cache.is_near_limit:
                cache.expand_limit(50)
            cache.put(url, data)
            data.seek(0)

        return data

    except (requests.Timeout, requests.HTTPError,
            requests.ConnectionError, requests.RequestException):
        pass
    except Exception as e:
        logger.error(f"Image download error {url[:60]}: {e}")
    finally:
        if response is not None:
            try:
                response.close()
            except Exception:
                pass
    return None
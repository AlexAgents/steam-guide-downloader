# Steam Guide Downloader
# Copyright (c) 2025-2026 AlexAgents
# Licensed under the MIT License. See LICENSE file in the project root.

"""
Image saver — saves guide images to a separate folder in original quality.
"""

import os
import re
import logging
from datetime import datetime
from urllib.parse import urlparse, unquote
from typing import Optional

import requests

from app.config import get_headers, AppConfig

logger = logging.getLogger(__name__)


def _sanitize_filename(name: str) -> str:
    """Clean filename for filesystem safety."""
    name = unquote(name)
    name = re.sub(r'[\\/*?:"<>|]', '_', name)
    name = re.sub(r'[\x00-\x1f\x7f]', '', name)
    name = re.sub(r'\.\.', '_', name)  # prevent path traversal
    name = re.sub(r'_+', '_', name)
    name = name.strip('. _')
    if not name:
        name = "image"
    return name[:150]


def _extract_filename(url: str, index: int) -> str:
    """Extract a meaningful filename from URL, with fallback to index."""
    try:
        parsed = urlparse(url)
        path = parsed.path
        basename = os.path.basename(path)
        if basename and '.' in basename:
            name, ext = os.path.splitext(basename)
            ext = ext.lower()
            if ext not in (
                '.jpg', '.jpeg', '.png', '.gif',
                '.webp', '.bmp', '.svg'
            ):
                ext = '.jpg'
            return _sanitize_filename(name) + ext
    except Exception:
        pass
    return f"image_{index:03d}.jpg"


def _detect_extension(data: bytes, fallback: str = ".jpg") -> str:
    """Detect image format from magic bytes."""
    if len(data) < 12:
        return fallback
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return ".png"
    if data[:2] == b'\xff\xd8':
        return ".jpg"
    if data[:4] == b'GIF8':
        return ".gif"
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return ".webp"
    if data[:2] == b'BM':
        return ".bmp"
    return fallback


def _make_images_folder_name(guide_title: str) -> str:
    """Create folder name: IMG_{safe_title} or IMG_{timestamp}."""
    if not guide_title:
        return f"IMG_{datetime.now():%Y%m%d_%H%M%S}"

    safe = re.sub(r'[\\/*?:"<>|]', '_', guide_title)
    safe = re.sub(r'[\x00-\x1f\x7f]', '', safe)
    safe = re.sub(r'_+', '_', safe)
    safe = safe.strip('. _')

    if len(safe) < 2 or len(safe) > 80:
        return f"IMG_{datetime.now():%Y%m%d_%H%M%S}"

    alnum_count = sum(1 for c in safe if c.isalnum())
    if alnum_count < len(safe) * 0.3:
        return f"IMG_{datetime.now():%Y%m%d_%H%M%S}"

    return f"IMG_{safe}"


class ImageSaver:
    """Collects image URLs during parsing, saves them after DOCX is built."""

    def __init__(self, save_dir: str, guide_title: str,
                 config: AppConfig = None, session=None):
        self.config = config or AppConfig()
        self.session = session
        self._urls: list[str] = []
        self._seen: set[str] = set()
        folder_name = _make_images_folder_name(guide_title)
        self.images_dir = os.path.join(save_dir, folder_name)

    def register(self, url: str):
        """Register an image URL for later saving. Deduplicates."""
        if not url or not url.startswith('http'):
            return
        if url not in self._seen:
            self._seen.add(url)
            self._urls.append(url)

    @property
    def count(self) -> int:
        return len(self._urls)

    def save_all(self, log_func=None, cancel_check=None) -> int:
        """Download and save all registered images."""
        if not self._urls:
            return 0

        if log_func is None:
            log_func = lambda msg: None

        os.makedirs(self.images_dir, exist_ok=True)
        # Normalize for path traversal checks
        safe_base = os.path.abspath(self.images_dir)

        log_func(f"Saving images to: {self.images_dir}")

        req_session = self.session or requests
        saved = 0
        max_size = self.config.max_image_size_mb * 1024 * 1024

        for i, url in enumerate(self._urls):
            if cancel_check and cancel_check():
                break

            response = None
            try:
                response = req_session.get(
                    url, headers=get_headers(), stream=True,
                    timeout=self.config.timeout
                )
                response.raise_for_status()

                content_type = response.headers.get('content-type', '')
                if ('image' not in content_type
                        and 'octet-stream' not in content_type):
                    continue

                chunks = []
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    downloaded += len(chunk)
                    if downloaded > max_size:
                        break
                    chunks.append(chunk)

                if downloaded > max_size or downloaded == 0:
                    continue

                data = b"".join(chunks)

                filename = _extract_filename(url, i + 1)
                name_part, ext_part = os.path.splitext(filename)

                real_ext = _detect_extension(data, ext_part)
                if real_ext != ext_part:
                    filename = name_part + real_ext

                filepath = os.path.join(self.images_dir, filename)

                # Path traversal protection
                filepath = os.path.abspath(os.path.normpath(filepath))
                if os.path.commonpath([safe_base, filepath]) != safe_base:
                    logger.warning(
                        f"Path traversal blocked: {filename}"
                    )
                    continue

                counter = 1

                while os.path.exists(filepath):
                    filepath = os.path.join(
                        self.images_dir,
                        f"{name_part}_{counter}{real_ext}"
                    )
                    filepath = os.path.abspath(os.path.normpath(filepath))
                    counter += 1

                with open(filepath, 'wb') as f:
                    f.write(data)

                saved += 1
                logger.debug(
                    f"Saved image: {os.path.basename(filepath)}"
                )

            except (requests.Timeout, requests.ConnectionError):
                continue
            except Exception as e:
                logger.warning(
                    f"Failed to save image {url[:60]}: {e}"
                )
                continue
            finally:
                if response is not None:
                    try:
                        response.close()
                    except Exception:
                        pass

        return saved
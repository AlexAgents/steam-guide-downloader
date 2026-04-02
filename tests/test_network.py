"""Tests for network utilities (offline)"""

import pytest
import sys
import os
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.network import ImageCache


class TestImageCache:
    """Image cache behavior"""

    def test_empty_cache_returns_none(self):
        cache = ImageCache(max_count=10)
        assert cache.get("http://example.com/img.png") is None

    def test_put_and_get(self):
        cache = ImageCache(max_count=10)
        data = BytesIO(b"fake image data")
        cache.put("http://example.com/img.png", data)
        result = cache.get("http://example.com/img.png")
        assert result is not None
        assert result.read() == b"fake image data"

    def test_get_returns_copy(self):
        cache = ImageCache(max_count=10)
        data = BytesIO(b"test")
        cache.put("http://example.com/a.png", data)
        r1 = cache.get("http://example.com/a.png")
        r2 = cache.get("http://example.com/a.png")
        assert r1 is not r2
        assert r1.read() == r2.read()

    def test_eviction(self):
        cache = ImageCache(max_count=2, max_bytes=1024 * 1024)
        cache.put("http://a.com/1.png", BytesIO(b"1"))
        cache.put("http://a.com/2.png", BytesIO(b"2"))
        cache.put("http://a.com/3.png", BytesIO(b"3"))
        assert cache.get("http://a.com/1.png") is None
        assert cache.get("http://a.com/2.png") is not None
        assert cache.get("http://a.com/3.png") is not None

    def test_byte_limit_eviction(self):
        # max_bytes=10 means only ~10 bytes total
        cache = ImageCache(max_count=100, max_bytes=10)
        cache.put("http://a.com/1.png", BytesIO(b"12345"))  # 5 bytes
        cache.put("http://a.com/2.png", BytesIO(b"67890"))  # 5 bytes
        cache.put("http://a.com/3.png", BytesIO(b"abcde"))  # 5 bytes, evicts 1
        assert cache.get("http://a.com/1.png") is None
        assert cache.get("http://a.com/3.png") is not None

    def test_duplicate_put(self):
        cache = ImageCache(max_count=10)
        cache.put("http://a.com/x.png", BytesIO(b"first"))
        cache.put("http://a.com/x.png", BytesIO(b"second"))
        result = cache.get("http://a.com/x.png")
        assert result.read() == b"first"

    def test_clear(self):
        cache = ImageCache(max_count=10)
        cache.put("http://a.com/1.png", BytesIO(b"1"))
        cache.put("http://a.com/2.png", BytesIO(b"2"))
        cache.clear()
        assert cache.get("http://a.com/1.png") is None
        assert cache.get("http://a.com/2.png") is None

    def test_stats(self):
        cache = ImageCache(max_count=10)
        cache.put("http://a.com/1.png", BytesIO(b"1"))
        cache.get("http://a.com/1.png")
        cache.get("http://a.com/miss.png")
        stats = cache.stats
        assert "hits=1" in stats
        assert "miss=1" in stats

    def test_lru_order(self):
        cache = ImageCache(max_count=2, max_bytes=1024 * 1024)
        cache.put("http://a.com/1.png", BytesIO(b"1"))
        cache.put("http://a.com/2.png", BytesIO(b"2"))
        # Access 1, making 2 the oldest
        cache.get("http://a.com/1.png")
        # Add 3, should evict 2
        cache.put("http://a.com/3.png", BytesIO(b"3"))
        assert cache.get("http://a.com/1.png") is not None
        assert cache.get("http://a.com/2.png") is None
        assert cache.get("http://a.com/3.png") is not None

    def test_expand_limit(self):
        cache = ImageCache(max_count=100, max_bytes=100)
        cache.expand_limit(1)  # +1 MB
        # After expand, limit should be 100 + 1MB
        assert cache._max_bytes == 100 + 1 * 1024 * 1024

    def test_is_near_limit(self):
        cache = ImageCache(max_count=100, max_bytes=100)
        assert not cache.is_near_limit
        cache.put("http://a.com/big.png", BytesIO(b"x" * 85))
        assert cache.is_near_limit
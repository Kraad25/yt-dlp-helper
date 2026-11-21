import os
import io
import hashlib
import threading
import urllib.request
from urllib.parse import urlparse
from pathlib import Path
from typing import Callable
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageOps

from core.paths import user_data_dir
from core.job_logger import JobLogger

TOTAL_CACHE_MAX_BYTES = 50 * 1024 * 1024  # 50 MB
MAX_WORKERS = 4

log = JobLogger("thumbnail")

class ThumbnailService:
    def __init__(self, width: int = 160, height: int = 90):
        self._width = width
        self._height = height

        cache_dir = user_data_dir() / "config" / "thumbnail_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir = cache_dir

        self._pool = ThreadPoolExecutor(max_workers=MAX_WORKERS)
        self._lock = threading.Lock()
        self._waiting: dict[str, list[Callable]] = {}

        self._trim_cache()

    # Public Methods
    def fetch_async(self, url: str, on_ready: Callable):    
        if not url:
            on_ready(None)
            return

        with self._lock:
            if url in self._waiting:
                self._waiting[url].append(on_ready)
                return
            self._waiting[url] = [on_ready]

        self._pool.submit(self._fetch_and_resize, url)

    # Private Methods
    def _fetch_and_resize(self, url: str):
        image = None
        try:
            image = self._load_from_cache(url)
            if image is None:
                image = self._download(url)
                self._save_to_cache(url, image)
            image = ImageOps.fit(image, (self._width, self._height))
        except Exception as e:
            log.warning('Thumbnail Failed Url:%s Error:"%s"', url, e)
            image = None

        with self._lock:
            callbacks = self._waiting.pop(url, [])

        for callback in callbacks:
            try:
                callback(image)
            except Exception as e:
                log.exception('Thumbnail Callback Crashed Url:%s Error:"%s"', url, e)

    def _cache_path(self, url: str) -> Path:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{key}.jpg"

    def _load_from_cache(self, url: str):
        path = self._cache_path(url)
        if not path.exists():
            return None
        try:            
            image = Image.open(path).convert("RGB")
            os.utime(path)
            return image
        except Exception as e:
            log.warning('Thumbnail Cache Unreadable, re-downloading File:%s Error:"%s"', path.name, e)
            return None

    def _download(self, url: str):
        if urlparse(url).scheme != "https":
            raise ValueError("Only https thumbnails are allowed")
        with urllib.request.urlopen(url, timeout=5) as response:
            raw = response.read()
        return Image.open(io.BytesIO(raw)).convert("RGB")

    def _save_to_cache(self, url: str, image):
        try:
            image.save(self._cache_path(url), format="JPEG")
        except Exception as e:
            log.warning('Thumbnail Not Cached Url:%s Error:"%s"', url, e)

    def _trim_cache(self):
        removed = 0
        try:
            files = [(p, p.stat()) for p in self._cache_dir.glob("*.jpg")]
            total = sum(stat.st_size for _, stat in files)
            for path, stat in sorted(files, key=lambda item: item[1].st_mtime):
                if total <= TOTAL_CACHE_MAX_BYTES:
                    break

                path.unlink(missing_ok=True)
                total -= stat.st_size
                removed += 1

        except OSError as e:
            log.warning('Thumbnail Cache Trim Failed Error:"%s"', e)
            return

        if removed:
            log.info("Thumbnail Cache Trimmed Removed=%s", removed)
import io
import hashlib
import threading
import urllib.request
from pathlib import Path
from typing import Callable

from PIL import Image

from core.paths import user_data_dir

class ThumbnailService:
    def __init__(self, width: int = 160, height: int = 90):
        self._width = width
        self._height = height

        cache_dir = user_data_dir() / "config" / "thumbnail_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir = cache_dir

    # Public Methods
    def fetch_async(self, url: str, widget: object, on_ready: Callable):
        if not url:
            return
        thread = threading.Thread(
            target=self._fetch_and_resize,
            args=(url, widget, on_ready),
            daemon=True,
        )
        thread.start()

    # Private Methods
    def _fetch_and_resize(self, url: str, widget: object, on_ready: Callable):
        try:
            image = self._load_from_cache(url)
            if image is None:
                image = self._download(url)
                self._save_to_cache(url, image)

            image = image.resize((self._width, self._height))
            on_ready(image)
        except Exception:
            on_ready(image)

    def _cache_path(self, url: str) -> Path:
        key = hashlib.sha256(url.encode("utf-8")).hexdigest()
        return self._cache_dir / f"{key}.jpg"

    def _load_from_cache(self, url: str):
        path = self._cache_path(url)
        if not path.exists():
            return None
        try:
            return Image.open(path).convert("RGB")
        except Exception:
            return None

    def _download(self, url: str):
        with urllib.request.urlopen(url, timeout=5) as response:
            raw = response.read()
        return Image.open(io.BytesIO(raw)).convert("RGB")

    def _save_to_cache(self, url: str, image):
        try:
            image.save(self._cache_path(url), format="JPEG")
        except Exception:
            pass
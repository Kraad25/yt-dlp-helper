import sys
import io
import hashlib
import threading
import urllib.request
from pathlib import Path
from typing import Callable

from PIL import Image

def _get_app_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent  # service/ -> root

class ThumbnailService:
    def __init__(self, width: int = 160, height: int = 90):
        self._width = width
        self._height = height

        app_root = _get_app_root()
        cache_dir = app_root / "config" / "thumbnail_cache"
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
            widget.after(0, lambda: on_ready(image))
        except Exception:
            widget.after(0, lambda: on_ready(None))

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
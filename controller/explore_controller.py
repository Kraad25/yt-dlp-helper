import sys
import threading
from pathlib import Path
from typing import Callable

from model.youtube_model import YoutubeModel
from service.thumbnail_service import ThumbnailService
from controller.download_controller import DownloadController


def _get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def _get_ffmpeg_dir(app_root) -> Path:
    if getattr(sys, "frozen", False):
        return app_root / "_internal" / "ffmpeg"
    return app_root / "ffmpeg"


class ExploreController:
    def __init__(self, download_controller: DownloadController):
        app_root = _get_app_root()
        ffmpeg_dir = _get_ffmpeg_dir(app_root)

        self._youtube_model = YoutubeModel(ffmpeg_dir)
        self._thumbnail_service = ThumbnailService()
        self._download_controller = download_controller

    # Public Methods
    def search(self, query: str, on_results: Callable, on_error: Callable = None):        
        thread = threading.Thread(target=self._run_search, args=(query, on_results, on_error), daemon=True)
        thread.start()

    def browse_channel(self, channel_url: str, on_ready: Callable, on_error: Callable = None):        
        thread = threading.Thread(
            target=self._run_browse_channel, args=(channel_url, on_ready, on_error), daemon=True
        )
        thread.start()

    def browse_section(self, section_url: str, on_ready: Callable, on_error: Callable = None):
        thread = threading.Thread(
            target=self._run_browse_section, args=(section_url, on_ready, on_error), daemon=True
        )
        thread.start()

    def get_thumbnail(self, thumbnail_url: str, widget: object, on_ready: Callable):
        self._thumbnail_service.fetch_async(thumbnail_url, widget, on_ready)

    def download(
        self,
        url: str,
        mode: str,
        quality: str,
        path: str,
        update_status: Callable,
        enable_download: Callable = lambda enabled: None,
        enable_cancel: Callable = lambda enabled: None,
        update_progress: Callable = lambda value: None,
    ):
        data = {"url": url, "mode": mode, "quality": quality}
        # Explore results don't have their own encoder picker (yet)
        self._download_controller.download_requested(
            data,
            path,
            "CPU",
            enable_download,
            enable_cancel,
            update_progress,
            update_status,
        )

    # Private Methods
    def _run_search(self, query: str, on_results: Callable, on_error: Callable):
        try:
            results = self._youtube_model.search_videos(query)
            on_results(results)
        except Exception as e:
            if on_error:
                on_error(str(e))

    def _run_browse_channel(self, channel_url: str, on_ready: Callable, on_error: Callable):
        try:
            sections = self._youtube_model.get_channel_sections(channel_url)
            on_ready(sections)
        except Exception as e:
            if on_error:
                on_error(str(e))

    def _run_browse_section(self, section_url: str, on_ready: Callable, on_error: Callable):
        try:
            items = self._youtube_model.get_section_contents(section_url)
            on_ready(items)
        except Exception as e:
            if on_error:
                on_error(str(e))
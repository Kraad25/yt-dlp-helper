import sys
import threading
from pathlib import Path
from typing import Callable

from model.youtube_model import YoutubeModel, SECTION_INDEX_LIMIT
from controller.download_controller import DownloadController

from service.thumbnail_service import ThumbnailService
from service.search_page_service import SearchPageService

from concurrent.futures import ThreadPoolExecutor

def _get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def _get_ffmpeg_dir(app_root) -> Path:
    if getattr(sys, "frozen", False):
        return app_root / "_internal" / "ffmpeg"
    return app_root / "ffmpeg"

SECTION_BATCH_SIZE = 20

class ExploreController:
    def __init__(self, download_controller: DownloadController):
        app_root = _get_app_root()
        ffmpeg_dir = _get_ffmpeg_dir(app_root)

        self._youtube_model = YoutubeModel(ffmpeg_dir)
        self._search_pager = SearchPageService(fetch=self._youtube_model.search_videos)
        self._thumbnail_service = ThumbnailService()
        self._download_controller = download_controller

        self._section_url = ""
        self._section_offset = 0

        self._cover_pool = ThreadPoolExecutor(max_workers=6)
        self._cover_cache: dict[str, str] = {}

    # Public Methods
    def search(self, query: str, on_results: Callable, on_error: Callable = None):        
        thread = threading.Thread(target=self._run_search, args=(query, on_results, on_error), daemon=True)
        thread.start()

    def show_more_search(self, on_results: Callable, on_error: Callable = None):
        thread = threading.Thread(target=self._run_show_more_search, args=(on_results, on_error), daemon=True)
        thread.start()

    def browse_channel(self, channel_url: str, on_ready: Callable, on_error: Callable = None):        
        thread = threading.Thread(
            target=self._run_browse_channel, args=(channel_url, on_ready, on_error), daemon=True
        )
        thread.start()

    def browse_section(self, section_url: str, on_ready: Callable, on_error: Callable = None):
        self._section_url = section_url
        self._section_offset = 0
        self._start_section_fetch(on_ready, on_error)

    def show_more_section(self, on_ready: Callable, on_error: Callable = None):
        self._start_section_fetch(on_ready, on_error)

    def get_thumbnail(self, thumbnail_url: str, widget: object, on_ready: Callable):
        self._thumbnail_service.fetch_async(thumbnail_url, widget, on_ready)

    def list_section(self, section_url: str, on_ready: Callable, on_error: Callable = None):
        thread = threading.Thread(
            target=self._run_list_section, args=(section_url, on_ready, on_error), daemon=True
        )
        thread.start()

    def get_playlist_cover(self, playlist_url: str, on_ready: Callable):
        cached = self._cover_cache.get(playlist_url)
        if cached:
            on_ready(cached)
            return

        def task():
            cover = self._youtube_model.get_playlist_cover(playlist_url)
            if cover:
                self._cover_cache[playlist_url] = cover
            on_ready(cover)

        self._cover_pool.submit(task)

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
            batch = self._search_pager.start(query)
            on_results(batch, self._search_pager.has_more())
        except Exception as e:
            if on_error:
                on_error(str(e))

    def _run_list_section(self, section_url: str, on_ready: Callable, on_error: Callable):
        try:
            items = self._youtube_model.get_section_index(section_url)
            truncated = len(items) >= SECTION_INDEX_LIMIT
            on_ready(items, truncated)
        except Exception as e:
            if on_error:
                on_error(str(e))

    def _start_section_fetch(self, on_ready: Callable, on_error: Callable):
        thread = threading.Thread(
            target=self._run_browse_section,
            args=(self._section_url, self._section_offset, on_ready, on_error),
            daemon=True,
        )
        thread.start()

    def _run_browse_section(self, section_url: str, offset: int, on_ready: Callable, on_error: Callable):
        try:
            items = self._youtube_model.get_section_contents(
                section_url, limit=SECTION_BATCH_SIZE, offset=offset
            )
            if section_url != self._section_url:
                return  # user switched tabs while this was loading
            self._section_offset = offset + SECTION_BATCH_SIZE
            on_ready(items, len(items) >= SECTION_BATCH_SIZE)
        except Exception as e:
            if on_error:
                on_error(str(e))

    def _run_show_more_search(self, on_results: Callable, on_error: Callable):
        try:
            batch = self._search_pager.next_page()
            on_results(batch, self._search_pager.has_more())
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
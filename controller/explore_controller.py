import os
import threading
from typing import Callable

from controller.download_controller import DownloadController

from model.watcher_db_model import initilize_database
from model.validators import WatcherValidator

from service.youtube_service import YoutubeService, SECTION_INDEX_LIMIT
from service.thumbnail_service import ThumbnailService
from service.search_page_service import SearchPageService
from service.database_service import add_watch_with_items, is_watching, get_active_or_paused_watch_list

from core.paths import ffmpeg_directory

from concurrent.futures import ThreadPoolExecutor

SECTION_BATCH_SIZE = 20

class ExploreController:
    def __init__(self, download_controller: DownloadController):
        ffmpeg_dir = ffmpeg_directory()

        initilize_database()

        self._youtube_service = YoutubeService(ffmpeg_dir)
        self._thumbnail_service = ThumbnailService()
        self._validator = WatcherValidator
        self._download_controller = download_controller

        self._section_url = ""
        self._section_offset = 0
        self._search_pager: SearchPageService | None = None
        self._active_cancel = threading.Event()
        self._pending_watch: dict | None = None
        self._pending_items: list[dict] = []

        self._cover_pool = ThreadPoolExecutor(max_workers=6)
        self._cover_cache: dict[str, str] = {}

    # Public Methods
    def search(self, query: str, on_results: Callable, on_error: Callable = None):
        cancel = self._begin_request()
        self._search_pager = SearchPageService(fetch=self._youtube_service.search_videos)
        thread = threading.Thread(target=self._run_search, args=(query, self._search_pager, cancel, on_results, on_error), daemon=True)
        thread.start()

    def show_more_search(self, on_results: Callable, on_error: Callable = None):
        cancel = self._begin_request()
        thread = threading.Thread(target=self._run_show_more_search, args=(self._search_pager, cancel, on_results, on_error), daemon=True)
        thread.start()

    def browse_channel(self, channel_url: str, on_ready: Callable, on_error: Callable = None):    
        cancel = self._begin_request()    
        thread = threading.Thread(
            target=self._run_browse_channel, args=(channel_url, cancel, on_ready, on_error), daemon=True
        )
        thread.start()

    def browse_section(self, section_url: str, on_ready: Callable, on_error: Callable = None):
        cancel = self._begin_request()

        self._section_url = section_url
        self._section_offset = 0
        self._start_section_fetch(cancel, on_ready, on_error)

    def show_more_section(self, on_ready: Callable, on_error: Callable = None):
        cancel = self._begin_request()
        self._start_section_fetch(cancel, on_ready, on_error)

    def cancel_active_request(self):
        self._active_cancel.set()

    def get_thumbnail(self, thumbnail_url: str, widget: object, on_ready: Callable):
        self._thumbnail_service.fetch_async(thumbnail_url, widget, on_ready)    

    def get_playlist_cover(self, playlist_url: str, on_ready: Callable):
        cached = self._cover_cache.get(playlist_url)
        if cached:
            on_ready(cached)
            return

        def task():
            cover = self._youtube_service.get_playlist_cover(playlist_url)
            if cover:
                self._cover_cache[playlist_url] = cover
            on_ready(cover)

        self._cover_pool.submit(task)

    
    def start_watch(self, section_name, destination, auto_download, poll_interval, on_ready: Callable, on_error: Callable = None):
        self._pending_watch = {
            "section_url": self._section_url,
            "section_name": section_name,
            "destination_path": destination,
            "auto_download": auto_download,
            "poll_interval": poll_interval or WatcherValidator.MIN_POLL_INTERVAL,
        }

        self._pending_items = []

        threading.Thread(
            target=self._run_list_section,
            args=(self._section_url, on_ready, on_error),
            daemon=True,
        ).start()

    def finish_watch(self, ticked_ids: set) -> str | None:
        if not self._pending_watch:
            return "Nothing to save"

        for item in self._pending_items:
            item["status"] = "queued" if item["id"] in ticked_ids else "ignored"

        error = self._save_watch(self._pending_watch, self._pending_items)

        self._pending_watch = None
        self._pending_items = []

        return error

    def get_watches(self, is_active: bool) -> list[dict]:
        return get_active_or_paused_watch_list(is_active)

    def download(
        self,
        url: str,
        mode: str,
        quality: str,
        path: str,
        encoder: str,
        update_status: Callable,
        enable_download: Callable = lambda enabled: None,
        enable_cancel: Callable = lambda enabled: None,
        update_progress: Callable = lambda value: None,
    ):
        data = {"url": url, "mode": mode, "quality": quality}
        return self._download_controller.download_requested(
            data,
            path,
            encoder,
            enable_download,
            enable_cancel,
            update_progress,
            update_status,
        )

    # Private Methods
    def _begin_request(self) -> threading.Event:
        self._active_cancel.set()
        self._active_cancel = threading.Event()
        return self._active_cancel

    def _run_search(self, query: str, pager, cancel, on_results: Callable, on_error: Callable):
        try:
            batch = pager.start(query)
            has_more = pager.has_more()
        except Exception as e:
            if not cancel.is_set() and on_error:
                on_error(str(e))
            return
        
        if cancel.is_set():
            return
        
        on_results(batch, has_more)


    def _run_list_section(self, section_url: str, on_ready: Callable, on_error: Callable):
        try:
            items = self._youtube_service.get_section_index(section_url)
            self._pending_items = items
            truncated = len(items) >= SECTION_INDEX_LIMIT
            on_ready(items, truncated)
        except Exception as e:
            if on_error:
                on_error(str(e))

    def _start_section_fetch(self, cancel, on_ready: Callable, on_error: Callable):
        thread = threading.Thread(
            target=self._run_browse_section,
            args=(self._section_url, self._section_offset, cancel, on_ready, on_error),
            daemon=True,
        )
        thread.start()

    def _run_browse_section(self, section_url: str, offset: int, cancel, on_ready: Callable, on_error: Callable):
        try:
            items = self._youtube_service.get_section_contents(
                section_url, limit=SECTION_BATCH_SIZE, offset=offset
            )
        except Exception as e:
            if not cancel.is_set() and on_error:
                on_error(str(e))
            return

        if cancel.is_set():
            return
        
        self._section_offset = offset + SECTION_BATCH_SIZE
        on_ready(items, len(items) >= SECTION_BATCH_SIZE)

    def _run_show_more_search(self, pager, cancel, on_results: Callable, on_error: Callable):
        try:
            batch = pager.next_page()
            has_more = pager.has_more()
        except Exception as e:
            if not cancel.is_set() and on_error:
                on_error(str(e))
            return

        if cancel.is_set():
            pager.return_batch(batch)
            return

        on_results(batch, has_more)

    def _run_browse_channel(self, channel_url: str, cancel, on_ready: Callable, on_error: Callable):
        try:
            sections = self._youtube_service.get_channel_sections(channel_url)
        except Exception as e:
            if not cancel.is_set() and on_error:
                on_error(str(e))
            return

        if cancel.is_set():
            return
        
        on_ready(sections)

    def _save_watch(self, section_info: dict, items: list[dict]) -> str | None:
        error = self._validator.validate(section_info)
        if error:
            return error

        if is_watching(section_info["section_url"]):
            return "Already in your watch list"

        info = {**section_info, "poll_interval": int(section_info["poll_interval"])}

        try:
            os.makedirs(info["destination_path"], exist_ok=True)
        except OSError as e:
            return f"Couldn't create the folder: {e}"

        if not add_watch_with_items(info, items):
            return "Already in your watch list"
        return None
import os
import threading
from typing import Callable

from controller.download_controller import DownloadController
from controller.settings_controller import EncoderScope

from model.validators import WatcherValidator

from service.youtube_service import YoutubeService, SECTION_INDEX_LIMIT
from service.thumbnail_service import ThumbnailService
from service.search_page_service import SearchPageService
from service.error_service import ErrorHandlingService
from service.database_service import (
    add_watch_with_items, is_watching, get_active_or_paused_watch_list,
    ITEM_STATUS_IGNORED, ITEM_STATUS_QUEUED,
)

from core.paths import ffmpeg_directory
from core.job_logger import JobLogger

from concurrent.futures import ThreadPoolExecutor

SECTION_BATCH_SIZE = 20
cover_log = JobLogger("cover")
search_log = JobLogger("search")
section_log = JobLogger("section")

class ExploreController:
    def __init__(self, download_controller: DownloadController):
        ffmpeg_dir = ffmpeg_directory()

        self._youtube_service = YoutubeService(ffmpeg_dir)
        self._thumbnail_service = ThumbnailService()
        self._validator = WatcherValidator
        self._download_controller = download_controller
        self._error = ErrorHandlingService()

        self._section_url = ""
        self._section_offset = 0
        self._search_pager: SearchPageService | None = None
        self._active_stale = threading.Event()
        self._pending_watch: dict | None = None
        self._pending_items: list[dict] = []

        self._cover_pool = ThreadPoolExecutor(max_workers=6)
        self._cover_cache: dict[str, str] = {}

    # Public Methods
    def search(self, query: str, on_results: Callable, on_error: Callable = None):
        stale = self._begin_request()
        self._search_pager = SearchPageService(fetch=self._youtube_service.search_videos)
        thread = threading.Thread(target=self._run_search, args=(query, self._search_pager, stale, on_results, on_error), daemon=True)
        thread.start()

    def show_more_search(self, on_results: Callable, on_error: Callable = None):
        stale = self._begin_request()
        thread = threading.Thread(target=self._run_show_more_search, args=(self._search_pager, stale, on_results, on_error), daemon=True)
        thread.start()

    def browse_channel(self, channel_url: str, on_ready: Callable, on_error: Callable = None):    
        stale = self._begin_request()    
        thread = threading.Thread(
            target=self._run_browse_channel, args=(channel_url, stale, on_ready, on_error), daemon=True
        )
        thread.start()

    def browse_section(self, section_url: str, on_ready: Callable, on_error: Callable = None):
        stale = self._begin_request()

        self._section_url = section_url
        self._section_offset = 0
        self._start_section_fetch(stale, on_ready, on_error)

    def show_more_section(self, on_ready: Callable, on_error: Callable = None):
        stale = self._begin_request()
        self._start_section_fetch(stale, on_ready, on_error)

    def mark_requests_stale(self):
        self._active_stale.set()

    def get_thumbnail(self, thumbnail_url: str, on_ready: Callable):
        self._thumbnail_service.fetch_async(thumbnail_url, on_ready)    

    def get_playlist_cover(self, playlist_url: str, on_ready: Callable):
        cached = self._cover_cache.get(playlist_url)
        if cached:
            on_ready(cached)
            return

        def task():
            try:
                cover = self._youtube_service.get_playlist_cover(playlist_url)
            except Exception as e:
                cover_log.warning('Playlist Cover Failed Url:%s Error:"%s"', playlist_url, e)
                cover = None

            if cover:
                self._cover_cache[playlist_url] = cover

            try:
                on_ready(cover)
            except Exception as e:
                cover_log.error('Playlist Cover Callback Crashed Url:%s Error:"%s"', playlist_url, e)

        self._cover_pool.submit(task)

    
    def start_watch(self, section_name, destination, auto_download, poll_interval, on_ready: Callable, on_error: Callable = None):
        if is_watching(self._section_url):
            return "Already in your watch list"
        
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
            item["status"] = ITEM_STATUS_QUEUED if item["id"] in ticked_ids else ITEM_STATUS_IGNORED

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
        update_status: Callable,
        enable_download: Callable = lambda enabled: None,
        enable_cancel: Callable = lambda enabled: None,
        update_progress: Callable = lambda value: None,
        kind: str = "ex",
    ):
        data = {"url": url, "mode": mode, "quality": quality}
        return self._download_controller.download_requested(
            data,
            path,
            EncoderScope.EXPLORE,
            enable_download,
            enable_cancel,
            update_progress,
            update_status,
            kind
        )

    # Private Methods
    def _begin_request(self) -> threading.Event:
        self._active_stale.set()
        self._active_stale = threading.Event()
        return self._active_stale

    def _run_search(self, query: str, pager, stale, on_results: Callable, on_error: Callable):
        search_log.info('Search Start Query:"%s"', query)
        try:
            batch = pager.start(query)
            has_more = pager.has_more()
        except Exception as e:
            self._report_request_error(search_log, "Search", e, stale, on_error)
            return
        
        if stale.is_set():
            search_log.info("Search Dropped, newer request replaced it Count:%s", len(batch))
            return

        search_log.info("Search Done Results:%s HasMore:%s", len(batch), has_more)
        on_results(batch, has_more)


    def _run_list_section(self, section_url: str, on_ready: Callable, on_error: Callable):
        section_log.info('List Section Start Url:"%s"', section_url)
        try:
            items = self._youtube_service.get_section_index(section_url)            
        except Exception as e:
            self._report_request_error(section_log, "List Section", e, None, on_error)
            return

        self._pending_items = items
        truncated = len(items) >= SECTION_INDEX_LIMIT
        section_log.info("List Section Done Items:%s Truncated:%s", len(items), truncated)
        on_ready(items, truncated)

    def _start_section_fetch(self, stale, on_ready: Callable, on_error: Callable):
        thread = threading.Thread(
            target=self._run_browse_section,
            args=(self._section_url, self._section_offset, stale, on_ready, on_error),
            daemon=True,
        )
        thread.start()

    def _run_browse_section(self, section_url: str, offset: int, stale, on_ready: Callable, on_error: Callable):
        section_log.info('Section Start Url:"%s" Offset:%s', section_url, offset)
        try:
            items = self._youtube_service.get_section_contents(
                section_url, limit=SECTION_BATCH_SIZE, offset=offset
            )
        except Exception as e:
            self._report_request_error(section_log, "Section", e, stale, on_error)
            return

        if stale.is_set():
            section_log.info("Section Dropped, newer request replaced it Count:%s", len(items))
            return
        
        self._section_offset = offset + SECTION_BATCH_SIZE
        has_more = len(items) >= SECTION_BATCH_SIZE
        section_log.info("Section Done Items:%s HasMore:%s", len(items), has_more)
        on_ready(items, has_more)

    def _run_show_more_search(self, pager, stale, on_results: Callable, on_error: Callable):
        search_log.info("Show More Start")
        try:
            batch = pager.next_page()
            has_more = pager.has_more()
        except Exception as e:
            self._report_request_error(search_log, "Show More", e, stale, on_error)
            return

        if stale.is_set():
            pager.return_batch(batch)
            search_log.info("Show More Dropped, batch returned Count:%s", len(batch))
            return

        search_log.info("Show More Done Results:%s HasMore:%s", len(batch), has_more)
        on_results(batch, has_more)

    def _run_browse_channel(self, channel_url: str, stale, on_ready: Callable, on_error: Callable):
        section_log.info('Channel Start Url:"%s"', channel_url)
        try:
            sections = self._youtube_service.get_channel_sections(channel_url)
        except Exception as e:
            self._report_request_error(section_log, "Channel", e, stale, on_error)
            return

        if stale.is_set():
            section_log.info("Channel Dropped, newer request replaced it")
            return

        section_log.info("Channel Done Tabs:%s", len(sections))
        on_ready(sections)

    def _save_watch(self, section_info: dict, items: list[dict]) -> str | None:
        error = self._validator.validate(section_info)
        if error:
            return error

        info = {**section_info, "poll_interval": int(section_info["poll_interval"])}

        try:
            os.makedirs(info["destination_path"], exist_ok=True)
        except OSError as e:
            return f"Couldn't create the folder: {e}"

        if not add_watch_with_items(info, items):
            return "Couldn't save to your watch list"
        return None

    def _report_request_error(self, log, action: str, e: Exception, stale, on_error):
        if stale is not None and stale.is_set():
            log.info('%s Failed After Newer Request, not shown Error:"%s"', action, e)
            return

        shown = self._error.classify_error(error=e)
        log.error('%s Failed Raw Error:"%s" Show Error="%s"', action, e, shown)
        if on_error:
            on_error(shown)
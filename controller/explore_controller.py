import os
import threading
from typing import Callable

from controller.download_controller import DownloadController
from controller.settings_controller import EncoderScope, SettingsController

from model.validators import WatcherValidator

from service.youtube_service import YoutubeService, SECTION_INDEX_LIMIT
from service.thumbnail_service import ThumbnailService
from service.search_page_service import SearchPageService
from service.error_service import ErrorHandlingService
from service.download_queue_service import DownloadQueue
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
watch_log = JobLogger("watch")

class ExploreController:
    def __init__(self, download_controller: DownloadController, settings_controller: SettingsController):
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

        self._finished_count = 0
        self._finished_lock = threading.Lock()
        self._on_queue_update: Callable | None = None

        self._queue = DownloadQueue(
            download_workers=settings_controller.get_parallel_downloads(),
            transcode_workers=settings_controller.get_parallel_transcodes(),
            queue_limit=settings_controller.get_queue_limit(),
            run_download=self._run_download_job,
            run_transcode=self._run_transcode_job,
            on_skipped=self._on_job_skipped,
            on_queue_update=self._send_queue_update,
        )
        self._queue.start_workers()

    # Public Methods
    def set_on_queue_update_callback(self, callback: Callable):
        self._on_queue_update = callback

    def get_queue_status(self):
        status = self._queue.counts()
        with self._finished_lock:
            finished = self._finished_count

        return {
            "downloading": status["downloading"],
            "waiting": status["waiting"],
            "transcoding": status["transcoding"] + status["waiting_transcode"],
            "finished": finished,
        }

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
            watch_log.info('Section Already In Watch List Url:"%s"', self._section_url)
            return "Already in your watch list"
        
        self._pending_watch = {
            "section_url": self._section_url,
            "section_name": section_name,
            "destination_path": destination,
            "auto_download": auto_download,
            "poll_interval": poll_interval or WatcherValidator.MIN_POLL_INTERVAL,
        }

        self._pending_items = []

        watch_log.info(
            'Adding Section To Watch List Name:"%s" Url:"%s" AutoDownload:%s Interval:%s',
            section_name, self._section_url, auto_download, self._pending_watch["poll_interval"],
        )

        threading.Thread(
            target=self._run_list_section,
            args=(self._section_url, on_ready, on_error),
            daemon=True,
        ).start()

    def finish_watch(self, ticked_ids: set) -> str | None:
        if not self._pending_watch:
            watch_log.warning("Save Skipped, no section pending")
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
        kind: str = "ex",
    ) -> bool:
        data = {"url": url, "mode": mode, "quality": quality}
        job = self._download_controller.create_job(
            data,
            path,
            EncoderScope.EXPLORE,
            lambda enabled: None, # No enable download
            lambda enabled: None, # No enable cancel
            lambda value: None, # No update progress            
            update_status,
            kind
        )

        if not job:
            return False

        job.on_status = lambda message: None
        self._reset_finished_if_idle()
        
        if not self._queue.add_job(job):
            job.log.warning("Queue Full, job refused")
            update_status("Queue is full, try again later")
            return False

        update_status("Added to download queue")
        return True
    
    # Private Methods
    def _begin_request(self) -> threading.Event:
        self._active_stale.set()
        self._active_stale = threading.Event()
        return self._active_stale

    def _run_download_job(self, job):
        if self._download_controller.run_download(job):
            self._queue.handover_to_transcode(job)
        else:
            self._add_finished()

    def _run_transcode_job(self, job):
        self._download_controller.run_transcode(job)
        self._add_finished()

    def _on_job_skipped(self, job):
        job.log.info("Job Skipped, cancelled while waiting")
        self._add_finished()

    def _add_finished(self):
        with self._finished_lock:
            self._finished_count += 1

    def _reset_finished_if_idle(self):
        counts = self._queue.counts()
        if not any(counts.values()):
            with self._finished_lock:
                self._finished_count = 0

    def _send_queue_update(self):
        if self._on_queue_update:
            self._on_queue_update()

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
        section_log.info('Loading Full Section For Watch List Url:"%s"', section_url)
        try:
            items = self._youtube_service.get_section_index(section_url)            
        except Exception as e:
            self._report_request_error(section_log, "Loading Full Section For Watch List", e, None, on_error)
            return

        self._pending_items = items
        truncated = len(items) >= SECTION_INDEX_LIMIT
        section_log.info("Full Section Loaded Items:%s Truncated:%s", len(items), truncated)
        on_ready(items, truncated)

    def _start_section_fetch(self, stale, on_ready: Callable, on_error: Callable):
        thread = threading.Thread(
            target=self._run_browse_section,
            args=(self._section_url, self._section_offset, stale, on_ready, on_error),
            daemon=True,
        )
        thread.start()

    def _run_browse_section(self, section_url: str, offset: int, stale, on_ready: Callable, on_error: Callable):
        section_log.info('Loading Section Items Url:"%s" Offset:%s', section_url, offset)
        try:
            items = self._youtube_service.get_section_contents(
                section_url, limit=SECTION_BATCH_SIZE, offset=offset
            )
        except Exception as e:
            self._report_request_error(section_log, "Loading Section Items", e, stale, on_error)
            return

        if stale.is_set():
            section_log.info("Section Items Dropped, newer request replaced it Count:%s", len(items))
            return
        
        self._section_offset = offset + SECTION_BATCH_SIZE
        has_more = len(items) >= SECTION_BATCH_SIZE
        section_log.info("Section Items Loaded Count:%s HasMore:%s", len(items), has_more)
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
        section_log.info('Loading Channel Sections Url:"%s"', channel_url)
        try:
            sections = self._youtube_service.get_channel_sections(channel_url)
        except Exception as e:
            self._report_request_error(section_log, "Loading Channel Sections", e, stale, on_error)
            return

        if stale.is_set():
            section_log.info("Channel Sections Dropped, newer request replaced it")
            return

        section_log.info("Channel Sections Loaded Count:%s", len(sections))
        on_ready(sections)

    def _save_watch(self, section_info: dict, items: list[dict]) -> str | None:
        error = self._validator.validate(section_info)
        if error:
            watch_log.info('Section Not Saved, invalid input Shown:"%s"', error)
            return error

        info = {**section_info, "poll_interval": int(section_info["poll_interval"])}

        try:
            os.makedirs(info["destination_path"], exist_ok=True)
        except OSError as e:
            watch_log.warning('Section Not Saved, couldn\'t create folder Path:"%s" Error:"%s"', info["destination_path"], e)
            return f"Couldn't create the folder: {e}"

        if not add_watch_with_items(info, items):
            watch_log.error('Section Not Saved, database write failed Name:"%s" Items:%s', info["section_name"], len(items))
            return "Couldn't save to your watch list"
        
        queued = sum(1 for item in items if item["status"] == ITEM_STATUS_QUEUED)
        watch_log.info('Section Saved To Watch List Name:"%s" Items:%s Queued:%s', info["section_name"], len(items), queued)
        return None

    def _report_request_error(self, log, action: str, e: Exception, stale, on_error):
        if stale is not None and stale.is_set():
            log.info('%s Failed After Newer Request, not shown Error:"%s"', action, e)
            return

        shown = self._error.classify_error(error=e)
        log.error('%s Failed Raw Error:"%s" Show Error="%s"', action, e, shown)
        if on_error:
            on_error(shown)
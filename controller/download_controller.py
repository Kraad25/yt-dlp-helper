import os
import glob
import time
import gc
import threading
from dataclasses import dataclass, field
from typing import Callable

from yt_dlp.utils import DownloadCancelled, sanitize_filename
from urllib.parse import urlparse, parse_qs

from model.validators import DownloadValidator

from service.youtube_service import YoutubeService
from service.error_service import ErrorHandlingService
from service.video_processing_service import VideoProcessingService

from core.paths import ffmpeg_directory

@dataclass
class DownloadJob:
    url: str
    mode: str
    quality: str
    out_dir: str
    encoder: str

    on_status: Callable[[str], None]
    on_progress: Callable[[int], None] = lambda percent: None
    on_download_enabled: Callable[[bool], None] = lambda enabled: None
    on_cancel_enabled: Callable[[bool], None] = lambda enabled: None

    cancel: threading.Event = field(default_factory=threading.Event)
    partial_files: set = field(default_factory=set)

class DownloadController:    
    def __init__(self):
        self._ffmpeg_dir = ffmpeg_directory()
        
        self._youtube_service = YoutubeService(self._ffmpeg_dir)
        self._video_processor = VideoProcessingService(self._ffmpeg_dir)
        self._error = ErrorHandlingService()

    # Public Methods
    def download_requested(
            self, 
            data: dict, 
            path: str,
            encoder: str, 
            enable_download: Callable,
            enable_cancel: Callable,
            update_progress: Callable, 
            update_status: Callable
    ) -> DownloadJob | None:

        job = DownloadJob(
            url=data.get("url", ""),
            mode=data.get("mode", ""),
            quality=data.get("quality", ""),
            out_dir=path,
            encoder=encoder,
            on_status=update_status,
            on_progress=update_progress,
            on_download_enabled=enable_download,
            on_cancel_enabled=enable_cancel,
        )

        if not self._validate_data(job):
            return None

        job.on_download_enabled(False)
        job.on_cancel_enabled(True)
        job.on_progress(0)
        job.on_status("Downloading")

        target = self._run_video_download if job.mode == "mp4" else self._run_audio_download
        threading.Thread(target=target, args=(job,), daemon=True).start()
        return job

    def cancel_download(self, job: DownloadJob):
        job.cancel.set()
        job.on_status("Cancellation requested.....")

    # Private Methods
    def _validate_data(self, job: DownloadJob) -> bool:
        custom_error_msg = DownloadValidator.validate(job.url, job.mode)
        if custom_error_msg:            
            job.on_status(custom_error_msg)
            return False
        return True
    
    def _run_audio_download(self, job: DownloadJob):
        try:
            url = self._normalize_url(job.url)
            folder_path = self._resolve_target_dir(url, job.out_dir)

            downloaded_files = self._youtube_service.audio_download(
                url=url,
                out_dir=folder_path,
                quality=job.quality,
                progress_hook=lambda data: self._progress_hook(job, data),
            )

            if not job.cancel.is_set():
                saved = [file for file in downloaded_files if os.path.exists(file)]
                if saved:
                    job.on_status("Done")
                else:
                    job.on_status("Download failed, nothing was saved")

        except Exception as e:
            if not job.cancel.is_set():
                self._report_error(e, job)

        finally:
            self._finish_job(job)

    def _run_video_download(self, job: DownloadJob):
        try:
            url = self._normalize_url(job.url)
            folder_path = self._resolve_target_dir(url, job.out_dir)

            downloaded_files = self._youtube_service.video_download(
                url=url,
                out_dir=folder_path,
                quality=job.quality,
                progress_hook=lambda data: self._progress_hook(job, data),
            )

            if not job.cancel.is_set():
                saved = [file for file in downloaded_files if os.path.exists(file)]

                if not saved:
                    job.on_status("Download failed, nothing was saved")
                else:
                    for i, file in enumerate(saved, 1):
                        job.on_status(f"Transcoding {i}/{len(saved)} ...")
                        self._video_processor.transcode(file, job.encoder)

                    job.on_status(f"Done: {len(saved)} item downloaded")

        except Exception as e:
            if not job.cancel.is_set():
                self._report_error(e, job)

        finally:
            self._finish_job(job)

    def _finish_job(self, job: DownloadJob):
        if job.cancel.is_set():
            self._cleanup_partial_files(job)
            job.on_status("Download cancelled")
        job.on_cancel_enabled(False)
        job.on_download_enabled(True)

    def _progress_hook(self, job: DownloadJob, data: dict):
        if data['status'] == 'downloading':
            temp = data.get('tmpfilename')
            if temp:
                job.partial_files.add(temp)

            total = data.get('total_bytes') or data.get('total_bytes_estimate', 1)
            downloaded = data.get('downloaded_bytes', 0)
            percent = int((downloaded / total) * 100)

            job.on_progress(percent)
            job.on_status(f"Downloading: {percent}%")

            if job.cancel.is_set():
                job.on_cancel_enabled(False)
                raise DownloadCancelled("Download cancelled by user")

        elif data['status'] == 'finished':
            job.on_status("Processing file...")

    def _resolve_target_dir(self, url: str, base_dir: str) -> str:
        try:
            info = self._youtube_service.get_url_info(url)
            if not info.get("is_playlist"):
                return base_dir

            name = sanitize_filename(info.get("title") or "").strip(" .")
            if not name:
                return base_dir

            path = os.path.join(base_dir, name)
            os.makedirs(path, exist_ok=True)
            return path.replace("\\", "/")

        except Exception:
            return base_dir

    def _cleanup_partial_files(self, job: DownloadJob):
        gc.collect()
        for temp in job.partial_files:
            base = temp[:-5] if temp.endswith(".part") else temp
            targets = [
                temp,
                base + ".ytdl",
                *glob.glob(glob.escape(temp) + "-Frag*"),
            ]
            for path in targets:
                self._remove_with_retry(path)

        job.partial_files.clear()

    def _remove_with_retry(self, path: str, attempts: int = 5, delay: float = 0.5):
        for _ in range(attempts):
            try:
                if os.path.exists(path):
                    os.remove(path)
                return
            except PermissionError:
                time.sleep(delay)
            except Exception:
                return

    def _normalize_url(self, url: str) -> str:
        query = parse_qs(urlparse(url).query)
        list_id = (query.get("list") or [""])[0]
        if list_id.startswith(("OLAK5uy", "PL")):
            return f"https://www.youtube.com/playlist?list={list_id}"
        return url

    def _report_error(self, e: Exception, job: DownloadJob):
        error = self._error.classify_error(error=e)
        job.on_status(error)
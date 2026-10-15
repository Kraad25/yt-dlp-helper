import os
import sys
import glob
import time
import gc
import threading
from typing import Callable
from pathlib import Path

from yt_dlp.utils import DownloadCancelled, sanitize_filename
from urllib.parse import urlparse, parse_qs

from model.validators import DownloadValidator
from model.youtube_model import YoutubeModel
from service.error_service import ErrorHandlingService
from service.video_processing_service import VideoProcessingService

def _get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent

def _get_ffmpeg_dir(app_root) -> Path:
    if getattr(sys, "frozen", False):
        return app_root / "_internal" / "ffmpeg"
    return app_root / "ffmpeg"

class DownloadController:    
    def __init__(self):
        app_root = _get_app_root()
        self._ffmpeg_dir = _get_ffmpeg_dir(app_root)
        
        self._youtube_model = YoutubeModel(self._ffmpeg_dir)
        self._video_processor = VideoProcessingService(self._ffmpeg_dir)
        self._error = ErrorHandlingService()

        self._enable_download: Callable = None
        self._enable_cancel: Callable = None
        self._update_progress: Callable = None
        self._update_status: Callable = None
        self._cancel_flag = threading.Event()
        self._encoder = "CPU"

        self._partial_files: set[str] = set()

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
    ):

        self._set_callbacks(enable_download, enable_cancel, update_progress, update_status)
        self._enable_download(False)
        self._enable_cancel(True)
        self._encoder = encoder

        url = data.get("url", "")
        mode = data.get("mode", "")
        quality = data.get("quality", "")

        self._partial_files.clear()

        if not self._validate_data(url, mode):
            self._enable_cancel(False)
            self._enable_download(True)
            return

        if mode == 'mp4':
            self._request_video_download(url, path, quality)
        else:
            self._request_audio_download(url, path, quality)    

        self._update_progress(0)
        self._update_status("Downloading")

    def cancel_download(self):
        self._cancel_flag.set()
        if self._update_status:
            self._update_status("Cancellation requested.....")

    # Private Methods
    def _set_callbacks(
            self, 
            enable_download: Callable,
            enable_cancel: Callable, 
            update_progress: Callable, 
            update_status: Callable
    ):
        self._enable_download: Callable = enable_download
        self._enable_cancel: Callable = enable_cancel
        self._update_progress: Callable = update_progress
        self._update_status: Callable = update_status

    def _validate_data(self, url: str, mode: str):
        error_msg = DownloadValidator.validate(url, mode)
        if error_msg:
            self._error.handle_error(update_status=self._update_status, custom_msg=error_msg)
            return False
        return True
        
    def _request_audio_download(self, url: str, folderPath: str, quality: str):
        thread = threading.Thread(target=self._run_audio_download, args=(url, folderPath, quality), daemon=True)
        thread.start()

    def _request_video_download(self, url: str, folderPath: str, quality: str):
        thread = threading.Thread(target=self._run_video_download,args=(url, folderPath, quality),daemon=True)
        thread.start()
    
    def _run_audio_download(self, url: str, folderPath: str, quality: str):
        try:
            url = self._normalize_url(url)
            folderPath = self._resolve_target_dir(url, folderPath)

            downloaded_files = self._youtube_model.audio_download(url=url, 
                                             out_dir=folderPath, 
                                             quality=quality, 
                                             progress_hook = self._progress_hook
                                            )

            if not self._cancel_flag.is_set():
                saved = [file for file in downloaded_files if os.path.exists(file)]
                if saved:
                    self._update_status("Done")
                else:
                    self._update_status("Download failed, nothing was saved")

        except Exception as e:
            if not self._cancel_flag.is_set():
                self._error.handle_error(update_status=self._update_status, error=e)

        finally:
            if self._cancel_flag.is_set():
                self._cleanup_partial_files()
                self._update_status("Download cancelled")
            self._cancel_flag.clear()
            self._enable_cancel(False)
            self._enable_download(True)

    def _run_video_download(self, url: str, folderPath: str, quality: str):
        try:
            url = self._normalize_url(url)
            folderPath = self._resolve_target_dir(url, folderPath)

            downloaded_files = self._youtube_model.video_download(
                                                url=url,
                                                out_dir=folderPath,
                                                quality=quality,
                                                progress_hook = self._progress_hook
                                            )

            if not self._cancel_flag.is_set():                
                saved = [file for file in downloaded_files if os.path.exists(file)]

                if not saved:
                    self._update_status("Download failed, nothing was saved")
                else:
                    for i, file in enumerate(saved, 1):
                        self._update_status(f"Transcoding {i}/{len(saved)} ...")
                        self._video_processor.transcode(file, self._encoder)

                    self._update_status(f"Done: {len(saved)} item downloaded")
            
        except Exception as e:
            if not self._cancel_flag.is_set():
                self._error.handle_error(update_status=self._update_status, error=e)

        finally:
            if self._cancel_flag.is_set():
                self._cleanup_partial_files()
                self._update_status("Download cancelled")
            self._cancel_flag.clear()
            self._enable_cancel(False)
            self._enable_download(True)

    def _progress_hook(self, data: dict):        
        if data['status'] == 'downloading':
            temp = data.get('tmpfilename')
            if temp:
                self._partial_files.add(temp)
                
            total = data.get('total_bytes') or data.get('total_bytes_estimate', 1)
            downloaded = data.get('downloaded_bytes', 0)
            percent = int((downloaded / total) * 100)

            self._update_progress(percent)
            self._update_status(f"Downloading: {percent}%")

            if self._cancel_flag.is_set():
                self._enable_cancel(False)
                raise DownloadCancelled("Download cancelled by user")
        
        elif data['status'] == 'finished':
            self._update_status("Processing file...")

    def _resolve_target_dir(self, url: str, base_dir: str) -> str:
        try:
            info = self._youtube_model.get_url_info(url)
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

    def _cleanup_partial_files(self):
        gc.collect()
        for temp in self._partial_files:
            base = temp[:-5] if temp.endswith(".part") else temp
            targets = [
                temp,
                base + ".ytdl",
                *glob.glob(glob.escape(temp) + "-Frag*"),
            ]
            for path in targets:
                self._remove_with_retry(path)

        self._partial_files.clear()

    def _remove_with_retry(self, path: str, attempts: int = 5, delay: float = 0.5):
        for _ in range(attempts):
            try:
                if os.path.exists(path):
                    os.remove(path)
                return
            except PermissionError as e:
                time.sleep(delay)
            except Exception as e:
                return

    def _normalize_url(self, url: str) -> str:
        query = parse_qs(urlparse(url).query)
        list_id = (query.get("list") or [""])[0]
        if list_id.startswith(("OLAK5uy", "PL")):
            return f"https://www.youtube.com/playlist?list={list_id}"
        return url
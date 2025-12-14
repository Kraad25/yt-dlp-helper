import os
import sys
import threading
from typing import Callable
from pathlib import Path

from model.validators import DownloadValidator
from model.youtube_model import YoutubeModel
from service.error_service import ErrorHandlingService
from service.video_processing_service import VideoProcessingService


def _get_app_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

class DownloadController:    
    def __init__(self):
        app_root = _get_app_root()
        self._ffmpeg_dir = app_root / "ffmpeg"
        
        self._youtube_model = YoutubeModel(self._ffmpeg_dir)
        self._video_processor = VideoProcessingService(self._ffmpeg_dir)
        self._error = ErrorHandlingService()

        self._enable_download: Callable = None
        self._enable_cancel: Callable = None
        self._update_progress: Callable = None
        self._update_status: Callable = None
        self._cancel_flag = threading.Event()
        self._expected_filename = None
        self._encoder = "CPU"

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

        if not self._validate_data(url, mode):
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
            self._youtube_model.audio_download(url=url, 
                                             out_dir=folderPath, 
                                             quality=quality, 
                                             progress_hook = self._progress_hook
                                            )
            self._update_status("Done")

        except Exception as e:
            if self._cancel_flag.is_set():
                self._cleanup_partial_files()
            self._error.handle_error(update_status=self._update_status, error=e)
        finally:
            self._cancel_flag.clear()
            self._enable_download(True)

    def _run_video_download(self, url: str, folderPath: str, quality: str):
        try:
            downloaded_file = self._youtube_model.video_download(
                url=url,
                out_dir=folderPath,
                quality=quality,
                progress_hook = self._progress_hook
            )
            if downloaded_file and not self._cancel_flag.is_set():
                self._update_status("Transcoding video...")
                self._video_processor.transcode(downloaded_file,self._encoder)
            self._update_status("Done")
            
        except Exception as e:
            if self._cancel_flag.is_set():
                self._cleanup_partial_files()
            self._error.handle_error(update_status=self._update_status, error=e)
        finally:
            self._cancel_flag.clear()
            self._enable_download(True)

    def _progress_hook(self, d: dict):        
        if d['status'] == 'downloading':
            if 'filename' in d:
                self._expected_filename = d['filename']
                
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            percent = int((downloaded / total) * 100)

            self._update_progress(percent)
            self._update_status(f"Downloading: {percent}%")

            if self._cancel_flag.is_set():
                self._enable_cancel(False)
                raise Exception("Download cancelled by user")
        
        elif d['status'] == 'finished':
            self._update_status("Processing file...")

    def _cleanup_partial_files(self):
        if not self._expected_filename:
            return
        
        part_file = self._expected_filename + ".part"
        
        try:
            if os.path.exists(part_file):
                os.remove(part_file)
        except Exception as e:
            self._error.handle_error(
                update_status = self._update_status,
                custom_msg = f"Warning: Could not delete temp file: {e}"   
            )
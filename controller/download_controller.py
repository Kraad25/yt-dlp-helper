import os
import threading
from typing import Callable

from model.validators import DownloadValidator
from model.youtube_model import YoutubeModel
from service.error_service import ErrorHandlingService

class DownloadController:    
    def __init__(self):
        self.youtube_model = YoutubeModel()
        self.validator = DownloadValidator()
        self.error = ErrorHandlingService()

        self._enable_download: Callable = None
        self._update_progress: Callable = None
        self._update_status: Callable = None
        self._cancel_flag = threading.Event()
        self._expected_filename = None

    # Public Methods
    def download_requested(self, data: dict, path: str,
                           enable_download: Callable, update_progress: Callable, update_status: Callable):

        self._set_callbacks(enable_download, update_progress, update_status)
        enable_download(False)

        url = data.get("url", "")
        folder = data.get("folder", "")
        mode = data.get("mode", "")
        quality = data.get("quality", "")

        if not self._validate_data(url, folder, mode):
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
    def _set_callbacks(self, enable_download: Callable, update_progress: Callable, update_status: Callable):
        self._enable_download: Callable = enable_download
        self._update_progress: Callable = update_progress
        self._update_status: Callable = update_status

    def _validate_data(self, url: str, folder: str, mode: str):
        error_msg = self.validator.validate(url, folder, mode)
        if error_msg:
            self.error.handle_error(update_status=self._update_status, custom_msg=error_msg)
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
            self.youtube_model.audio_download(url=url, 
                                             out_dir=folderPath, 
                                             quality=quality, 
                                             progress_hook = self._progress_hook
                                            )
            self._update_status("Done")

        except Exception as e:
            if self._cancel_flag.is_set():
                self._cleanup_partial_files()
            self.error.handle_error(update_status=self._update_status, error=e)
        finally:
            self._cancel_flag.clear()
            self._enable_download(True)

    def _run_video_download(self, url: str, folderPath: str, quality: str):
        try:
            self.youtube_model.video_download(
                url=url,
                out_dir=folderPath,
                quality=quality,
                progress_hook = self._progress_hook
            )
            self._update_status("Done")
            
        except Exception as e:
            if self._cancel_flag.is_set():
                self._cleanup_partial_files()
            self.error.handle_error(update_status=self._update_status, error=e)
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
            print(f"Warning: Could not delete temp file: {e}")
import threading
from typing import Callable

from model.validators import DownloadValidator
from model.youtube_model import YoutubeModel

class DownloadController:    
    def __init__(self):
        self.youtube_model = YoutubeModel()
        self.validator = DownloadValidator()

        self._enable_download: Callable = None
        self._update_progress: Callable = None
        self._update_status: Callable = None

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
    
    # Private Methods
    def _set_callbacks(self, enable_download: Callable, update_progress: Callable, update_status: Callable):
        self._enable_download: Callable = enable_download
        self._update_progress: Callable = update_progress
        self._update_status: Callable = update_status

    def _validate_data(self, url: str, folder: str, mode: str):
        error_msg = self.validator.validate(url, folder, mode)
        if error_msg:
            self._update_status(error_msg)
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
            self._show_error(e)
        
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
            self._show_error(e)
        
        self._enable_download(True)

    def _progress_hook(self, d: dict):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            percent = int((downloaded / total) * 100)

            self._update_progress(percent)
            self._update_status(f"Downloading: {percent}%")
        
        elif d['status'] == 'finished':
            self._update_status("Processing file...")

    def _show_error(self, error):
        error_msg = str(error).lower()
        if "not a valid url" in error_msg:
            error_msg = "Not a Valid URL"
        else:
            error_msg = str(error) if str(error) else "Unknown error occurred"
        self._update_status(f"Error: {error_msg}")
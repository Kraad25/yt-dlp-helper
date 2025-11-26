import threading
from typing import Callable

from model.validators import DownloadValidator
from model.youtube_model import YoutubeModel

class DownloadController:    
    def __init__(self):
        self.youtubeModel = YoutubeModel()
        self.validator = DownloadValidator()

        self.__threads = []

    def download_requested(self, data: dict, path: str,
                           enable_download: Callable, update_progress: Callable, update_status: Callable):
        
        enable_download(False)

        url = data.get("url", "")
        folder = data.get("folder", "")
        mode = data.get("mode", "")
        quality = data.get("quality", "")

        if not self._validate_data(url, folder, mode, update_status):
            enable_download(True)
            return

        if mode == 'mp4':
            self._request_video_download(url, path, quality, enable_download, update_progress, update_status)
        else:
            self._request_audio_download(url, path, quality, enable_download, update_progress, update_status)    

        update_progress(0)
        update_status("Downloading")
    
    def _validate_data(self, url: str, folder: str, mode: str, update_status: Callable):
        error_msg = self.validator.validate(url, folder, mode)
        if error_msg:
            update_status(error_msg)
            return False
        return True
        
    def _request_audio_download(self, url: str, folderPath: str, quality: str, 
                                enable_download: Callable, 
                                update_progress: Callable, 
                                update_status: Callable):
        thread = threading.Thread(target=self._run_audio_download, 
                                  args=(url, folderPath, quality, enable_download, 
                                        update_progress, update_status), 
                                  daemon=True
                                )
        thread.start()
        self.__threads.append(thread)

    def _request_video_download(self, url: str, folderPath: str, quality: str, 
                                enable_download: Callable, 
                                update_progress: Callable, 
                                update_status: Callable):
        thread = threading.Thread(target=self._run_video_download, 
                                  args=(url, folderPath, quality, enable_download, update_progress, update_status), 
                                  daemon=True
                                )
        thread.start()
        self.__threads.append(thread)
    
    def _run_audio_download(self, url: str, folderPath: str, quality: str, 
                            enable_download: Callable, 
                            update_progress: Callable, 
                            update_status: Callable):
        try:
            self.youtubeModel.audio_download(url=url, 
                                             out_dir=folderPath, 
                                             quality=quality, 
                                             progress_hook = lambda d: self._progress_hook(d, update_progress, update_status)
                                            )
            update_status("Done")

        except Exception as e:
            self._show_error(e, update_status)
        
        enable_download(True)

    def _run_video_download(self, url: str, folderPath: str, quality: str,
                            enable_download: Callable, 
                            update_progress: Callable, 
                            update_status: Callable):
        try:
            self.youtubeModel.video_download(
                url=url,
                out_dir=folderPath,
                quality=quality,
                progress_hook = lambda d: self._progress_hook(d, update_progress, update_status)
            )
            update_status("Done")
            
        except Exception as e:
            self._show_error(e, update_status)
        
        enable_download(True)


    def _progress_hook(self, d: dict, progress: Callable, status: Callable):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            percent = int((downloaded / total) * 100)

            progress(percent)
            status(f"Downloading: {percent}%")
        
        elif d['status'] == 'finished':
            status("Processing file...")

    def _show_error(self, error, update_status: Callable):
        error_msg = str(error).lower()
        if "not a valid url" in error_msg:
            error_msg = "Not a Valid URL"
        else:
            error_msg = str(error) if str(error) else "Unknown error occurred"
        update_status(f"Error: {error_msg}")
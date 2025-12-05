import os
import threading
from typing import Callable

from model.validators import DownloadValidator
from model.youtube_model import YoutubeModel
from service.error_service import ErrorHandlingService

class DownloadController:    
    def __init__(self):
        self.__youtube_model = YoutubeModel()
        self.__error = ErrorHandlingService()

        self.__enable_download: Callable = None
        self.__update_progress: Callable = None
        self.__update_status: Callable = None
        self.__cancel_flag = threading.Event()
        self.__expected_filename = None

    # Public Methods
    def download_requested(
            self, 
            data: dict, 
            path: str, 
            enable_download: Callable, 
            update_progress: Callable, 
            update_status: Callable
    ):

        self.__set_callbacks(enable_download, update_progress, update_status)
        enable_download(False)

        url = data.get("url", "")
        mode = data.get("mode", "")
        quality = data.get("quality", "")

        if not self.__validate_data(url, mode):
            self.__enable_download(True)
            return

        if mode == 'mp4':
            self.__request_video_download(url, path, quality)
        else:
            self.__request_audio_download(url, path, quality)    

        self.__update_progress(0)
        self.__update_status("Downloading")

    def cancel_download(self):
        self.__cancel_flag.set()
        if self.__update_status:
            self.__update_status("Cancellation requested.....")

    # Private Methods
    def __set_callbacks(self, enable_download: Callable, update_progress: Callable, update_status: Callable):
        self.__enable_download: Callable = enable_download
        self.__update_progress: Callable = update_progress
        self.__update_status: Callable = update_status

    def __validate_data(self, url: str, mode: str):
        error_msg = DownloadValidator.validate(url, mode)
        if error_msg:
            self.__error.handle_error(update_status=self.__update_status, custom_msg=error_msg)
            return False
        return True
        
    def __request_audio_download(self, url: str, folderPath: str, quality: str):
        thread = threading.Thread(target=self.__run_audio_download, args=(url, folderPath, quality), daemon=True)
        thread.start()

    def __request_video_download(self, url: str, folderPath: str, quality: str):
        thread = threading.Thread(target=self.__run_video_download,args=(url, folderPath, quality),daemon=True)
        thread.start()
    
    def __run_audio_download(self, url: str, folderPath: str, quality: str):
        try:
            self.__youtube_model.audio_download(url=url, 
                                             out_dir=folderPath, 
                                             quality=quality, 
                                             progress_hook = self.__progress_hook
                                            )
            self.__update_status("Done")

        except Exception as e:
            if self.__cancel_flag.is_set():
                self.__cleanup_partial_files()
            self.__error.handle_error(update_status=self.__update_status, error=e)
        finally:
            self.__cancel_flag.clear()
            self.__enable_download(True)

    def __run_video_download(self, url: str, folderPath: str, quality: str):
        try:
            self.__youtube_model.video_download(
                url=url,
                out_dir=folderPath,
                quality=quality,
                progress_hook = self.__progress_hook
            )
            self.__update_status("Done")
            
        except Exception as e:
            if self.__cancel_flag.is_set():
                self.__cleanup_partial_files()
            self.__error.handle_error(update_status=self.__update_status, error=e)
        finally:
            self.__cancel_flag.clear()
            self.__enable_download(True)

    def __progress_hook(self, d: dict):        
        if d['status'] == 'downloading':
            if 'filename' in d:
                self.__expected_filename = d['filename']
                
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            percent = int((downloaded / total) * 100)

            self.__update_progress(percent)
            self.__update_status(f"Downloading: {percent}%")

            if self.__cancel_flag.is_set():
                raise Exception("Download cancelled by user")
        
        elif d['status'] == 'finished':
            self.__update_status("Processing file...")

    def __cleanup_partial_files(self):
        if not self.__expected_filename:
            return
        
        part_file = self.__expected_filename + ".part"
        
        try:
            if os.path.exists(part_file):
                os.remove(part_file)
        except Exception as e:
            print(f"Warning: Could not delete temp file: {e}")
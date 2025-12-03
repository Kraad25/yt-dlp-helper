import os
import threading
from typing import Callable

from service.file_service import FileRenamer
from service.error_service import ErrorHandlingService

from model.metadata_model import MetadataModel

from enum import IntEnum
class FilenameFormat(IntEnum):
    TITLE_ARTIST = 1
    TITLE_ALBUM = 2
    TITLE_ONLY = 3

class MetadataService:
    def __init__(self, metadata_model: MetadataModel, error_handler: ErrorHandlingService):
        self._model = metadata_model
        self._error = error_handler
        self._video_threads: list[threading.Thread] = []

    # Public Methods
    def reset(self):
        self._video_threads.clear()

    def get_title(self, mode: str, file_path: str) -> str:
        if mode == "mp3":
            return self._model.get_audio_title(file_path=file_path)
        return self._model.get_video_title(file_path=file_path)
    
    def set_metadata_for_file(
        self, mode: str, 
        file_path: str, title: str,
        artist: str, 
        album: str, 
        file_name: str, 
        update_status: Callable
    ):
        if mode == "mp3":
            ok = self._model.set_audio_metadata(file_path, title, artist, album)
            if not ok:
                update_status(f"Failed to save metadata for {file_name}")
        else:
            self._request_video_metadata_change(file_path, title, artist, album, update_status)

    def wait_for_all_video_operations(self):
        for thread in self._video_threads:
            thread.join()
        self._video_threads.clear()

    def rename_files(
        self,
        mode: str,
        folder_path: str,
        files: list[str],
        artist: str,
        album: str,
        filename_format: int,
        update_status: Callable,
    ) -> bool:
        for filename in files:
            file_path = os.path.join(folder_path, filename)
            title = self.get_title(mode, file_path)

            if not title or not title.strip():
                update_status(f"Skipped: {filename} (no title)")
                continue

            if filename_format == FilenameFormat.TITLE_ARTIST and artist:
                new_name = f"{title} - {artist}.{mode}"
            elif filename_format == FilenameFormat.TITLE_ALBUM and album:
                new_name = f"{title} - {album}.{mode}"
            elif filename_format == FilenameFormat.TITLE_ONLY:
                new_name = f"{title}.{mode}"
            else:
                continue

            FileRenamer.rename_file(file_path, new_name, folder_path, update_status)

        return True

    # Private Methods
    def _request_video_metadata_change(
        self,
        file_path: str,
        title: str,
        artist: str,
        album: str,
        update_status: Callable,
    ):
        thread = threading.Thread(
            target=self._change_video_metadata,
            args=(file_path, title, artist, album, update_status),
            daemon=True,
        )
        thread.start()
        self._video_threads.append(thread)

    def _change_video_metadata(
        self,
        file_path: str,
        title: str,
        artist: str,
        album: str,
        update_status: Callable,
    ):
        try:
            self._model.set_video_metadata(file_path, title, artist, album)
        except Exception as e:
            self._error.handle_error(update_status, error=e)
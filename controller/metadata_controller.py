import os
import threading

from typing import Callable
from model.validators import FolderValidator
from model.metadata_model import MetadataModel

from service.file_service import FileRenamer
from service.error_service import ErrorHandlingService

from enum import IntEnum
class FilenameFormat(IntEnum):
    TITLE_ARTIST = 1
    TITLE_ALBUM = 2
    TITLE_ONLY = 3

class MetadataController:
    def __init__(self):
        self.metadata_model = MetadataModel()
        self.metadata_editing_folder = FolderValidator()
        self.error = ErrorHandlingService()

        self._files = []
        self._current_index = 0        
        self._folder_path = ""
        self._mode = ""
        self._video_threads = []

        self._artist: str = None
        self._album: str = None
        self._set_title: Callable = None
        self._update_status: Callable = None
        self._enable_next: Callable = None
        self._enable_back: Callable = None
        
    # Public Methods
    def editing_requested(self, files: list, data: dict,
                          set_title: Callable, show_wizard: Callable, update_status: Callable, 
                          enable_next: Callable, enable_back: Callable):
        
        folder_path = data.get("folder_path", "")
        artist = data.get("artist", "")
        album = data.get("album", "")
        mode = data.get("mode", "")

        self._files = files
        self._artist = artist
        self._album = album
        self._folder_path = folder_path
        self._mode = mode
        self._current_index = 0
        
        self._set_callbacks(set_title, enable_next, enable_back, update_status)

        if not self._validate_folder(self._folder_path, self._files):
            return
        show_wizard()

        file_name, file_path = self._get_current_file_info()

        title = self._get_title(file_path)
        self._set_title(title if title else "")  
        self._update_status(f"Editing: {file_name}")

        self._enable_back(False)
        self._enable_next(len(self._files)>1)

    def on_next(self, given_title: str):
        file_name, file_path = self._get_current_file_info()
        self._set_metadata(file_path, given_title, self._artist, self._album, file_name)
        self._navigate_to_file(self._current_index + 1)

    def on_back(self, given_title: str):
        file_name, file_path = self._get_current_file_info()
        self._set_metadata(file_path, given_title, self._artist, self._album, file_name)

        self._navigate_to_file(self._current_index - 1)

    def on_finish(self, given_title: str, type: int):
        file_name, file_path = self._get_current_file_info()
        self._set_metadata(file_path, given_title, self._artist, self._album, file_name)

        self._enable_back(False)
        self._enable_next(False)

        for thread in self._video_threads:
            thread.join()

        if not self._rename_files(type):
            return
        self._update_status("Editing complete! Go back to home to start over.")

    # Private Methods
    def _set_callbacks(self, set_title: Callable, enable_next: Callable, 
                       enable_back: Callable, update_status: Callable):
        
        self._set_title: Callable = set_title
        self._update_status: Callable = update_status
        self._enable_next: Callable = enable_next
        self._enable_back: Callable = enable_back
        self._update_status: Callable = update_status

    def _validate_folder(self, folder, files):
        if not self.metadata_editing_folder.validate(folder):
            self.error.handle_error(update_status=self._update_status,
                                    custom_msg="Error: Folder contains Subfolders")
            return False
        if not files:
            self.error.handle_error(update_status=self._update_status,
                                    custom_msg=f"Error: No {self._mode} files found")
            return False
        return True
        
    def _get_current_file_info(self):
        file_name = self._files[self._current_index]
        file_path = os.path.join(self._folder_path, file_name)
        return file_name, file_path
    
    def _navigate_to_file(self, new_index: int):
        if not (0 <= new_index < len(self._files)):
            return # Outta bounds
        self._current_index = new_index
        self.file_name, self.file_path = self._get_current_file_info()

        title = self._get_title(self.file_path)
        self._set_title(title if title else "")
        self._update_status(f"Editing: {self.file_name}")
        self._update_navigation_button_states()


    def _get_title(self, file_path: str):
        if self._mode == "mp3":
            return self.metadata_model.get_audio_title(file_path=file_path)
        else:
            return self.metadata_model.get_video_title(file_path=file_path)

    def _update_navigation_button_states(self):
        self._enable_back(self._current_index > 0)
        self._enable_next(self._current_index < len(self._files) - 1)

    def _rename_files(self, type: int):
        for filename in self._files:
            file_path = os.path.join(self._folder_path, filename)
            title = self._get_title(file_path)

            if not title or not title.strip():
                self._update_status(f"Skipped: {filename} (no title)")
                continue

            if type == FilenameFormat.TITLE_ARTIST:
                new_name = f"{title} - {self._artist}.{self._mode}"
            elif type == FilenameFormat.TITLE_ALBUM:
                 new_name = f"{title} - {self._album}.{self._mode}"
            elif type == FilenameFormat.TITLE_ONLY:
                new_name = f"{title}.{self._mode}"
            else:
                continue
                    
            FileRenamer.rename_file(file_path, new_name, self._folder_path, self._update_status)


    def _set_metadata(self, for_file, with_title, with_artist, with_album, file_name):
        if self._mode == "mp3":
            if not self.metadata_model.set_audio_metadata(for_file, with_title, with_artist, with_album):
                self._update_status(f"Failed to save metadata for {file_name}")
                return
        else:
            self._request_video_metadata_change(for_file, with_title, with_artist, with_album)


    def _request_video_metadata_change(self, for_file, with_title, with_artist, with_album):
        thread = threading.Thread(target=self._change_video_metadata, args=(for_file, with_title, with_artist, with_album), daemon=True)
        thread.start()
        self._video_threads.append(thread)

    def _change_video_metadata(self, for_file, with_title, with_artist, with_album):
        try:
            self.metadata_model.set_video_metadata(for_file, with_title, with_artist, with_album)
        except Exception as e:
            self.error.handle_error(self._update_status, error=e)
import os

from typing import Callable
from model.validators import FolderValidator
from model.metadata_model import MetadataModel

from service.error_service import ErrorHandlingService
from service.metadata_service import MetadataService

from enum import IntEnum
class FilenameFormat(IntEnum):
    TITLE_ARTIST = 1
    TITLE_ALBUM = 2
    TITLE_ONLY = 3

class MetadataController:
    def __init__(self):
        self.metadata_editing_folder = FolderValidator()
        self.error = ErrorHandlingService()
        self._service = MetadataService(metadata_model=MetadataModel(), error_handler=self.error)

        self._files = []
        self._current_index = 0        
        self._folder_path = ""
        self._mode = ""

        self._artist: str = None
        self._album: str = None
        self._set_title: Callable = None
        self._update_status: Callable = None
        self._enable_next: Callable = None
        self._enable_back: Callable = None
        
    # Public Methods
    def editing_requested(
            self, 
            files: list, 
            data: dict, 
            set_title: Callable, 
            show_wizard: Callable, 
            update_status: Callable, 
            enable_next: Callable, 
            enable_back: Callable
        ):
        
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
        self._service.reset()

        if not self._validate_folder(self._folder_path, self._files):
            return
        show_wizard()

        file_name, file_path = self._get_current_file_info()

        title = self._service.get_title(self._mode, file_path)
        self._set_title(title if title else "")  
        self._update_status(f"Editing: {file_name}")

        self._enable_back(False)
        self._enable_next(len(self._files)>1)

    def on_next(self, given_title: str):
        file_name, file_path = self._get_current_file_info()

        self._service.set_metadata_for_file(
            mode=self._mode, 
            file_path=file_path, 
            title=given_title, 
            artist=self._artist, 
            album=self._album, 
            file_name=file_name,
            update_status=self._update_status
        )
        self._navigate_to_file(self._current_index + 1)

    def on_back(self, given_title: str):
        file_name, file_path = self._get_current_file_info()
        
        self._service.set_metadata_for_file(
            mode=self._mode, 
            file_path=file_path, 
            title=given_title, 
            artist=self._artist, 
            album=self._album, 
            file_name=file_name,
            update_status=self._update_status
        )

        self._navigate_to_file(self._current_index - 1)

    def on_finish(self, given_title: str, type: int):
        file_name, file_path = self._get_current_file_info()
        
        self._service.set_metadata_for_file(
            mode=self._mode, 
            file_path=file_path, 
            title=given_title, 
            artist=self._artist, 
            album=self._album, 
            file_name=file_name,
            update_status=self._update_status
        )

        self._enable_back(False)
        self._enable_next(False)

        self._service.wait_for_all_video_operations()

        success = self._service.rename_files(
            mode=self._mode,
            folder_path=self._folder_path,
            files=self._files,
            artist=self._artist,
            album=self._album,
            filename_format=FilenameFormat(type),
            update_status=self._update_status,
        )

        if not success:
            self._update_status("Editing Failed!.")
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
        file_name, self.file_path = self._get_current_file_info()

        title = self._service.get_title(self._mode, self.file_path)
        self._set_title(title if title else "")
        self._update_status(f"Editing: {file_name}")
        self._update_navigation_button_states()

    def _update_navigation_button_states(self):
        self._enable_back(self._current_index > 0)
        self._enable_next(self._current_index < len(self._files) - 1)
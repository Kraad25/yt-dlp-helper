import os

from model.validators import FolderValidator
from model.metadata_model import MetadataModel

from service.file_service import FileRenamer

from enum import IntEnum
class FilenameFormat(IntEnum):
    TITLE_ARTIST = 1
    TITLE_ALBUM = 2
    TITLE_ONLY = 3

class MetadataController:
    def __init__(self, view):
        self.view = view
        self.metadata_model = MetadataModel()
        self.metadata_editing_folder = FolderValidator()

        self.files = []
        self.current_index = 0        
        self.folder_path = ""

    def reset(self, folder_path: str, artist: str, album: str):
        self.view.set_presets(folder_path, artist, album)
        self.view.reset_wizard_state()

        self.folder_path = folder_path
        self.current_index=0
        
    def editing_started(self, files: list, artist: str, album: str):
        self.files = files
        self.artist = artist
        self.album = album

        if not self.metadata_editing_folder.validate(self.folder_path):
            self.view.update_status("Error: Folder contains Subfolders")
            return

        if not self.files:
            self.view.update_status("Error: No MP3 files found")
            return
        
        self.view.start_editing_success()

        file_name, file_path = self._get_current_file_info()

        title = self.metadata_model.get_title(file_path)
        self.view.set_title(title if title else "")  
        self.view.update_status(f"Editing: {file_name}")

        self.view.set_back_enabled(False)
        self.view.set_next_enabled(len(self.files)>1)

    def on_next(self, given_title: str):
        file_name, file_path = self._get_current_file_info()
        success = self.metadata_model.set_metadata(file_path, given_title, self.artist, self.album)
        
        if success:
            self.view.update_status(f"Saved: {file_name}")
        else:
            self.view.update_status(f"Failed to save metadata for {file_name}")
        
        self._navigate_to_file(self.current_index + 1)

    def on_back(self, given_title: str):
        file_name, file_path = self._get_current_file_info()
        success = self.metadata_model.set_metadata(file_path, given_title, self.artist, self.album)

        if success:
            self.view.update_status(f"Saved: {file_name}")
        else:
            self.view.update_status(f"Failed to save metadata for {file_name}")

        self._navigate_to_file(self.current_index - 1)

    def on_finish(self, given_title: str, type: int):
        file_name, file_path = self._get_current_file_info()
        success = self.metadata_model.set_metadata(file_path, given_title, self.artist, self.album)

        if success:
            self.view.update_status(f"Saved: {file_name}")
        else:
            self.view.update_status(f"Failed to save metadata for {file_name}")
            return

        self.view.set_back_enabled(False)
        self.view.set_next_enabled(False)

        self._rename_files(type)
        self.view.update_status("Editing complete! Go back to home to start over.")
    
    def _get_current_file_info(self):
        file_name = self.files[self.current_index]
        file_path = os.path.join(self.folder_path, file_name)
        return file_name, file_path
    
    def _navigate_to_file(self, new_index: int):
        if not (0 <= new_index < len(self.files)):
            return # Outta bounds
        self.current_index= new_index
        self.file_name, self.file_path = self._get_current_file_info()

        title = self.metadata_model.get_title(self.file_path)
        self.view.set_title(title if title else "")
        self.view.update_status(f"Editing: {self.file_name}")
        self._update_navigation_button_states()

    def _update_navigation_button_states(self):
        self.view.set_back_enabled(self.current_index > 0)
        self.view.set_next_enabled(self.current_index < len(self.files) - 1)

    def _rename_files(self, type: int):
        for filename in self.files:
            file_path = os.path.join(self.folder_path, filename)
            title = self.metadata_model.get_title(file_path)

            if not title or not title.strip():
                self.view.update_status(f"Skipped: {filename} (no title)")
                continue

            if type == FilenameFormat.TITLE_ARTIST:
                new_name = f"{title} - {self.artist}.mp3"
            elif type == FilenameFormat.TITLE_ALBUM:
                 new_name = f"{title} - {self.album}.mp3"
            elif type == FilenameFormat.TITLE_ONLY:
                new_name = f"{title}.mp3"
            else:
                continue

            FileRenamer.rename_file(file_path, new_name, self.folder_path, self.view)


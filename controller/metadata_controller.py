import os
import re
from model.metadata_model import MetadataModel

class MetadataController:
    def __init__(self, view):
        self.view = view
        self.metadataModel = MetadataModel()

        self.files = []
        self.current_index = 0
        self.artist = ""
        self.album = ""
        self.folder_path = ""

    def editing_started(self, folder_path, artist, album):
        self.folder_path = folder_path
        self.artist = artist
        self.album = album

        if self._contains_subfolders(self.folder_path):
            self.view.update_status("Error: Folder contains Subfolders")
            return
        
        self.files = self._list_mp3_files(self.folder_path)
        if not self.files:
            self.view.update_status("Error: No MP3 files found")
            return
        
        self.view.start_editing_success()

        self.current_index=0
        file_name, file_path = self._get_current_file_info()

        title = self.metadataModel.get_title(file_path)
        self.view.set_title(title if title else "")  
        self.view.update_status(f"Editing: {file_name}")

        self.view.set_back_enabled(False)
        self.view.set_next_enabled(len(self.files)>1)

    def on_next(self, given_title):
        file_name, file_path = self._get_current_file_info()
        success = self.metadataModel.set_metadata(file_path, given_title, self.artist, self.album)
        
        if success:
            self.view.update_status(f"Saved: {file_name}")
        else:
            self.view.update_status(f"Failed to save metadata for {file_name}")
        
        self._navigate_to_file(self.current_index + 1)

    def on_back(self, given_title):
        file_name, file_path = self._get_current_file_info()
        success = self.metadataModel.set_metadata(file_path, given_title, self.artist, self.album)

        if success:
            self.view.update_status(f"Saved: {file_name}")
        else:
            self.view.update_status(f"Failed to save metadata for {file_name}")

        self._navigate_to_file(self.current_index - 1)

    def on_finish(self, given_title, type):
        file_name, file_path = self._get_current_file_info()
        success = self.metadataModel.set_metadata(file_path, given_title, self.artist, self.album)

        if success:
            self.view.update_status(f"Saved: {file_name}")
        else:
            self.view.update_status(f"Failed to save metadata for {file_name}")
            return

        self._rename_files(type)
        
        self.view.set_back_enabled(False)
        self.view.set_next_enabled(False)
        self.view.update_status("Editing complete! Go back to home to start over.")

    def _contains_subfolders(self, folder_path):
        for f in os.listdir(folder_path):
            full = os.path.join(folder_path, f)
            if os.path.isdir(full):
                return True
        return False

    def _list_mp3_files(self, folder_path):
        return [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith('.mp3')
        ]
    
    def _get_current_file_info(self):
        file_name = self.files[self.current_index]
        file_path = os.path.join(self.folder_path, file_name)
        return file_name, file_path
    
    def _navigate_to_file(self, new_index):
        if not (0 <= new_index < len(self.files)):
            return # Outta bounds
        self.current_index= new_index
        self.file_name, self.file_path = self._get_current_file_info()

        title = self.metadataModel.get_title(self.file_path)
        self.view.set_title(title if title else "")
        self.view.update_status(f"Editing: {self.file_name}")
        self._update_navigation_button_states()

    def _update_navigation_button_states(self):
        self.view.set_back_enabled(self.current_index > 0)
        self.view.set_next_enabled(self.current_index < len(self.files) - 1)

    def _rename_files(self, type):
        for filename in self.files:
            file_path = os.path.join(self.folder_path, filename)
            title = self.metadataModel.get_title(file_path)

            if not title or not title.strip():
                self.view.update_status(f"Skipped: {filename} (no title)")
                continue

            if type == 1:
                new_name = f"{title} - {self.artist}.mp3"
            elif type == 2:
                 new_name = f"{title} - {self.album}.mp3"
            else:
                new_name = f"{title}.mp3"

        
            new_name = self._sanitize_filename(new_name)
            new_path = os.path.join(self.folder_path, new_name)

            if file_path != new_path:
                try:
                    os.rename(file_path, new_path)
                    self.view.update_status(f"Renamed: {filename} -> {new_name}")
                except Exception as e:
                    self.view.update_status(f"Rename failed: {filename} - {e}")

    def _sanitize_filename(self, name):
        return re.sub(r'[\\/:*?"<>|]', '_', name)


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
        self.filename_type = None
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
        self.file_name = self.files[self.current_index]
        self.file_path = os.path.join(self.folder_path, self.file_name)

        title = self.metadataModel.get_title(self.file_path)
        self.view.set_title(title if title else "")  
        self.view.update_status(f"Editing: {self.file_name}")

        self.view.set_back_enabled(False)
        self.view.set_next_enabled(len(self.files)>1)

    def on_next(self, title):
        self.metadataModel.set_metadata(self.file_path, title, self.artist, self.album)
        self.view.update_status(f"Saved: {self.file_name}")

        if self.current_index<len(self.files) - 1:
            self.current_index += 1
            self.file_name = self.files[self.current_index]
            self.file_path = os.path.join(self.folder_path, self.file_name)

            title = self.metadataModel.get_title(self.file_path)
            self.view.set_title(title if title else "")
            self.view.update_status(f"Editing: {self.file_name}")

        self.view.set_back_enabled(self.current_index>0)
        self.view.set_next_enabled(self.current_index < len(self.files) - 1)

    def on_back(self, title):
        self.metadataModel.set_metadata(self.file_path, title, self.artist, self.album)
        self.view.update_status(f"Saved: {self.file_name}")

        if self.current_index > 0:
            self.current_index -= 1
            self.file_name = self.files[self.current_index]
            self.file_path = os.path.join(self.folder_path, self.file_name)

            title = self.metadataModel.get_title(self.file_path)
            self.view.set_title(title if title else "")
            self.view.update_status(f"Editing: {self.file_name}")

        self.view.set_back_enabled(self.current_index > 0)
        self.view.set_next_enabled(self.current_index < len(self.files) - 1)


    def on_finish(self, title, type):
        self.metadataModel.set_metadata(self.file_path, title, self.artist, self.album)
        self.view.update_status(f"Saved: {self.file_name}")

        self._rename_files(type)
        self.view.update_status("Renaming Completed")

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

    def _show_current_file_title(self, file_path):
        title = self.metadataModel.get_title()
        self.view.update_status("Editing")

    def _rename_files(self, type):
        for filename in self.files:
            file_path = os.path.join(self.folder_path, filename)
            title = self.metadataModel.get_title(file_path)

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


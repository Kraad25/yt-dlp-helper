import os
import threading

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
        self.mode = ""
        self.video_threads = []
           
    def reset(self, data: dict, folder_path: str):
        artist = data.get("artist", "")
        album = data.get("album", "")
        mode = data.get("mode", "")
        
        self.view.set_presets(folder_path, artist, album, mode)
        self.view.reset_wizard_state()

        self.folder_path = folder_path
        self.current_index=0
        self.mode = mode
        
    def editing_started(self, files: list, artist: str, album: str):
        self.files = files
        self.artist = artist
        self.album = album

        self._validate_folder(self.folder_path, self.files)
        self.view.start_editing_success()

        file_name, file_path = self._get_current_file_info()

        title = self._get_title(file_path)
        self.view.set_title(title if title else "")  
        self.view.update_status(f"Editing: {file_name}")

        self.view.set_back_enabled(False)
        self.view.set_next_enabled(len(self.files)>1)


    def on_next(self, given_title: str):
        file_name, file_path = self._get_current_file_info()
        self._set_metadata(file_path, given_title, self.artist, self.album, file_name)
        self._navigate_to_file(self.current_index + 1)

    def on_back(self, given_title: str):
        file_name, file_path = self._get_current_file_info()
        self._set_metadata(file_path, given_title, self.artist, self.album, file_name)

        self._navigate_to_file(self.current_index - 1)

    def on_finish(self, given_title: str, type: int):
        file_name, file_path = self._get_current_file_info()
        self._set_metadata(file_path, given_title, self.artist, self.album, file_name)

        self.view.set_back_enabled(False)
        self.view.set_next_enabled(False)

        if not self._rename_files(type, self.mode):
            return
        self.view.update_status("Editing complete! Go back to home to start over.")

    def _validate_folder(self, fodler, files):
        if not self.metadata_editing_folder.validate(fodler):
            self.view.update_status("Error: Folder contains Subfolders")
            return
        if not files:
            self.view.update_status("Error: No MP3 files found")
            return
        
    def _get_current_file_info(self):
        file_name = self.files[self.current_index]
        file_path = os.path.join(self.folder_path, file_name)
        return file_name, file_path
    
    def _navigate_to_file(self, new_index: int):
        if not (0 <= new_index < len(self.files)):
            return # Outta bounds
        self.current_index= new_index
        self.file_name, self.file_path = self._get_current_file_info()

        title = self._get_title(self.file_path)
        self.view.set_title(title if title else "")
        self.view.update_status(f"Editing: {self.file_name}")
        self._update_navigation_button_states()


    def _get_title(self, file_path: str):
        if self.mode == "mp3":
            return self.metadata_model.get_audio_title(file_path=file_path)
        else:
            return self.metadata_model.get_video_title(file_path=file_path)

    def _update_navigation_button_states(self):
        self.view.set_back_enabled(self.current_index > 0)
        self.view.set_next_enabled(self.current_index < len(self.files) - 1)

    def _rename_files(self, type: int, mode: str):
        for filename in self.files:
            file_path = os.path.join(self.folder_path, filename)
            title = self._get_title(file_path)

            if not title or not title.strip():
                self.view.update_status(f"Skipped: {filename} (no title)")
                continue

            if type == FilenameFormat.TITLE_ARTIST:
                new_name = f"{title} - {self.artist}.{mode}"
            elif type == FilenameFormat.TITLE_ALBUM:
                 new_name = f"{title} - {self.album}.{mode}"
            elif type == FilenameFormat.TITLE_ONLY:
                new_name = f"{title}.{mode}"
            else:
                continue
            print(new_name)

            if mode == "mp4":
                for thread in self.video_threads:
                    thread.join()
                    
            success = FileRenamer.rename_file(file_path, new_name, self.folder_path, self.view)
            return success


    def _set_metadata(self, for_file, with_title, with_artist, with_album, file_name):
        if self.mode == "mp3":
            if not self.metadata_model.set_audio_metadata(for_file, with_title, with_artist, with_album):
                self.view.update_status(f"Failed to save metadata for {file_name}")
                return
        else:
            self._request_video_metadata_change(for_file, with_title, with_artist, with_album)


    def _request_video_metadata_change(self, for_file, with_title, with_artist, with_album):
        thread = threading.Thread(target=self._change_video_metadata, args=(for_file, with_title, with_artist, with_album), daemon=True)
        thread.start()
        self.video_threads.append(thread)

    def _change_video_metadata(self, for_file, with_title, with_artist, with_album):
        try:
            self.metadata_model.set_video_metadata(for_file, with_title, with_artist, with_album)
        except Exception as e:
            self._show_error(e)
            
    
    def _show_error(self, error):
        error_msg = str(error).lower()
        error_msg = str(error) if str(error) else "Unknown error occurred"
        self.view.update_status(f"Error: {error_msg}")
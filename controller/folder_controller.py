import os
from typing import Callable
from model.folder_model import FolderModel

class FolderController:
    def __init__(self):
        self.folder_model = FolderModel()
        self.AUDIO_EXT = (".mp3", ".aac", ".m4a", ".flac", ".ogg", ".opus", ".wav", ".wma")
        self.VIDEO_EXT = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv")

    def browse_folder(self, set_folder_path: Callable):
        folder = self.folder_model.browse_folder()
        if not folder:
            folder = self.folder_model.get_full_path()
        set_folder_path(folder)

    def enter_folder_name(self, name):
        self.folder_model.set_folder_name(folder_name=name)

    def provide_full_path(self):
        return self.folder_model.get_full_path()
    
    def get_files(self, folder_path, mode):
        if mode == "mp3":
            extensions = self.AUDIO_EXT
        elif mode == "mp4":
            extensions = self.VIDEO_EXT
        else:
            extensions = self.AUDIO_EXT + self.VIDEO_EXT
        
        return [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(extensions)
        ]
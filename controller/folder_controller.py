import os
from typing import Callable
from model.folder_model import FolderModel

class FolderController:
    def __init__(self, set_base_folder: Callable = None):
        self._folder_model = FolderModel()
        self._AUDIO_EXT = (".mp3", ".aac", ".m4a", ".flac", ".ogg", ".opus", ".wav", ".wma")
        self._VIDEO_EXT = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv")
        
        self._set_base_folder = set_base_folder
        self._new_path = self._folder_model.get_base_directory()
        
        if self._set_base_folder:
            self._initialize_folder()
        
    # Public Methods
    def browse_folder(self):
        folder = self._folder_model.browse_folder()
        if folder and os.path.exists(folder):
            self._new_path = folder
            self._set_base_folder(self._new_path)
    
    def build_target_path(self, base_dir: str, subfolder: str) -> str:
        base_dir = (base_dir or "").strip()
        subfolder = (subfolder or "").strip()

        if base_dir and not subfolder:
            self._new_path = base_dir
            return self._new_path

        if base_dir and subfolder:
            self._new_path = os.path.join(base_dir, subfolder)
            self._new_path = self._new_path.replace("\\", "/")
            return self._new_path
    
    def get_files(self, folder_path, mode):
        if mode == "mp3":
            extensions = self._AUDIO_EXT
        elif mode == "mp4":
            extensions = self._VIDEO_EXT
        
        return [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(extensions)
        ]
    
    # Private Methods
    def _initialize_folder(self):
        if self._set_base_folder:
            folder_path = self._folder_model.get_base_directory()
            
            if folder_path and os.path.exists(folder_path):
                self._set_base_folder(folder_path)
            else:
                default_path = os.path.expanduser("~/Documents")
                default_path = default_path.replace("\\", "/")
                self._set_base_folder(default_path)
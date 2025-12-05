import os
from typing import Callable
from model.folder_model import FolderModel

class FolderController:
    def __init__(self, set_base_folder: Callable = None):
        self.__folder_model = FolderModel()
        self.__AUDIO_EXT = (".mp3", ".aac", ".m4a", ".flac", ".ogg", ".opus", ".wav", ".wma")
        self.__VIDEO_EXT = (".mp4", ".mkv", ".mov", ".avi", ".webm", ".flv")
        
        self.__set_base_folder = set_base_folder
        self.__new_path = self.__folder_model.get_base_directory()
        
        if self.__set_base_folder:
            self.__initialize_folder()
        
    # Public Methods
    def browse_folder(self):
        folder = self.__folder_model.browse_folder()
        if folder and os.path.exists(folder):
            self.__new_path = folder
            self.__set_base_folder(self.__new_path)
    
    def build_target_path(self, base_dir: str, subfolder: str) -> str:
        base_dir = (base_dir or "").strip()
        subfolder = (subfolder or "").strip()

        if base_dir and not subfolder:
            self.__new_path = base_dir
            return self.__new_path

        if base_dir and subfolder:
            self.__new_path = os.path.join(base_dir, subfolder)
            self.__new_path = self.__new_path.replace("\\", "/")
            return self.__new_path
    
    def get_files(self, folder_path, mode):
        if mode == "mp3":
            extensions = self.__AUDIO_EXT
        elif mode == "mp4":
            extensions = self.__VIDEO_EXT
        else:
            extensions = self.__AUDIO_EXT + self.__VIDEO_EXT
        
        return [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(extensions)
        ]
    
    # Private Methods
    def __initialize_folder(self):
        if self.__set_base_folder:
            folder_path = self.__folder_model.get_base_directory()
            
            if folder_path and os.path.exists(folder_path):
                self.__set_base_folder(folder_path)
            else:
                default_path = os.path.expanduser("~/Documents")
                self.__set_base_folder(default_path)
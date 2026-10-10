import os
from typing import Callable
from tkinter import filedialog
from model.folder_model import FolderModel

class FolderController:
    def __init__(self, key: str, set_base_folder: Callable = None):
        self._model = FolderModel(key)
        self._listeners: list[Callable] = []

        if set_base_folder:
            self.add_base_folder_listener(set_base_folder)

    # Public Methods
    def add_base_folder_listener(self, callback: Callable):
        self._listeners.append(callback)
        callback(self.get_base_directory())

    def get_base_directory(self) -> str:
        saved = self._model.get_base_directory()
        if saved and os.path.isdir(saved):
            return saved
        return self._default_directory()

    def browse_folder(self):
        selected = filedialog.askdirectory(initialdir=self.get_base_directory())
        if not selected:
            return
        self._model.set_base_directory(selected)
        self._notify_listeners(selected)
    
    def normalize_path(self, path: str) -> str:
        return (path or "").strip().replace("\\", "/")

    # Private Methods
    def _default_directory(self) -> str:
        return os.path.expanduser("~/Documents").replace("\\", "/")

    def _notify_listeners(self, path: str):
        for callback in self._listeners:
            callback(path)
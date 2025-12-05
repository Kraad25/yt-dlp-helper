import os
import json
from tkinter import filedialog

class FolderModel:
    def __init__(self, config_path='model/folder_config.json'):
        self._config_path = config_path
        self._config = self._load_config()

    # Public Methods
    def browse_folder(self) -> str | None:
        initial_dir = self.get_base_directory()
        selected_folder = filedialog.askdirectory(initialdir=initial_dir)
        if selected_folder:
            self._set_base_directory(selected_folder)
            return selected_folder
        return self.get_base_directory()

    def get_base_directory(self):
        return self._config.get("base_dir")
    
    # Private Methods    
    def _set_base_directory (self, path: str):
        self._config["base_dir"] = path
        self._save_config()

    def _load_config(self):
        if os.path.exists(self._config_path):
            with open(self._config_path, 'r') as f:
                return json.load(f)
        return {"base_dir": "/"}

    def _save_config(self):
        with open(self._config_path, 'w') as f:
            json.dump(self._config, f, indent=4)
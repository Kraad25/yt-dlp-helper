import os
import sys
import json
from pathlib import Path
from tkinter import filedialog

def _get_app_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent  # model/ -> root

class FolderModel:
    def __init__(self):
        app_root = _get_app_root()
        config_dir = app_root / "config"
        config_dir.mkdir(exist_ok=True)
        self._config_path = (config_dir / "folder_config.json")
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
        
        default_path = os.path.expanduser("~/Documents")
        default_path = default_path.replace("\\", "/")
        return {"base_dir": default_path}

    def _save_config(self):
        with open(self._config_path, 'w') as f:
            json.dump(self._config, f, indent=4)
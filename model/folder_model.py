import os
import sys
import json
from pathlib import Path

def _get_app_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent  # model/ -> root

class FolderModel:
    def __init__(self, key: str):
        app_root = _get_app_root()
        config_dir = app_root / "config"
        config_dir.mkdir(exist_ok=True)
        self._config_path = (config_dir / "folder_config.json")

        self._key = key

    # Public Methods
    def get_base_directory(self) -> str | None:
        return self._read_config().get(self._key) or None
    
    def set_base_directory (self, path: str):
        config = self._read_config()
        config[self._key] = path
        self._write_config(config)

    # Private Methods    
    def _read_config(self) -> dict:
        try:
            with open(self._config_path, "r") as f:
                return json.load(f)
            
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def _write_config(self, config: dict):
        temp_path = self._config_path.with_suffix(".temp")
        with open(temp_path, "w") as f:
            json.dump(config, f, indent=4)
        os.replace(temp_path, self._config_path)
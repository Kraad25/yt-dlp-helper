import os, json
from tkinter import filedialog

class FolderManager:
    def __init__(self, config_path='folder_config.json'):
        self.config_path = config_path
        self.config = self._load_config()
        self.folder_name = ""

    def browse_folder(self):
        selected_folder = filedialog.askdirectory(initialdir=self._get_base_dir())
        if selected_folder:
            self.set_base_dir(selected_folder)
            return self.get_full_path()
        return None
    
    def set_folder_name(self, folder_name):
        self.folder_name = folder_name.strip()
        if os.path.isabs(self.folder_name):
            self.folder_name = os.path.basename(self.folder_name)
        else:
            self.folder_name = folder_name
    
    def get_full_path(self):
        base_dir = self._get_base_dir()
        full_path = os.path.join(base_dir, self.folder_name)
        return os.path.normpath(full_path)

    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {"base_dir": "/"}

    def _get_base_dir(self):
        return self.config.get("base_dir", "/")

    def set_base_dir(self, path):
        self.config["base_dir"] = path
        self._save_config()

    def _save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
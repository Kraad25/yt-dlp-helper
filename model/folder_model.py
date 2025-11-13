import os, json
from tkinter import filedialog

class FolderModel:
    def __init__(self, config_path='model/folder_config.json'):
        self.config_path = config_path
        self.config = self._load_config()
        self._folder_name = ""

    def browse_folder(self):
        initial_dir = self.get_base_directory()
        selected_folder = filedialog.askdirectory(initialdir=initial_dir)
        if selected_folder:
            self.set_base_directory(selected_folder)
            return self.get_full_path()  
        return None
    
    def set_folder_name(self, folder_name: str):
        folder_name = folder_name.strip()
        if os.path.isabs(folder_name):
            self._folder_name = os.path.basename(folder_name)
        else:
            self._folder_name = folder_name

    def get_full_path(self):
        base_dir = self.get_base_directory()
        full_path = os.path.join(base_dir, self._folder_name)
        return os.path.normpath(full_path)
    
    def get_base_directory(self):
        return self.config.get("base_dir", "/")
    
    def set_base_directory (self, path: str):
        self.config["base_dir"] = path
        self._save_config()

    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {"base_dir": "/"}

    def _save_config(self):
        with open(self.config_path, 'w') as f:
            json.dump(self.config, f, indent=4)
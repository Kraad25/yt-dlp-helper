import os
import json
from tkinter import filedialog

class FolderModel:
    def __init__(self, config_path='model/folder_config.json'):
        self.__config_path = config_path
        self.__config = self.__load_config()

    # Public Methods
    def browse_folder(self) -> str | None:
        initial_dir = self.get_base_directory()
        selected_folder = filedialog.askdirectory(initialdir=initial_dir)
        if selected_folder:
            self.__set_base_directory(selected_folder)
            return selected_folder
        return self.get_base_directory()

    def get_base_directory(self):
        return self.__config.get("base_dir")
    
    # Private Methods    
    def __set_base_directory (self, path: str):
        self.__config["base_dir"] = path
        self.__save_config()

    def __load_config(self):
        if os.path.exists(self.__config_path):
            with open(self.__config_path, 'r') as f:
                return json.load(f)
        return {"base_dir": "/"}

    def __save_config(self):
        with open(self.__config_path, 'w') as f:
            json.dump(self.__config, f, indent=4)
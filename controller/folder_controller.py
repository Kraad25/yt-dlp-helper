import os
from model.folder_model import FolderModel

class FolderController:
    def __init__(self, view):
        self.folder_model = FolderModel()
        self.view = view

    def browse_folder(self):
        folder = self.folder_model.browse_folder()
        if not folder:
            folder = self.folder_model.get_full_path()
        self.view.set_folder_path(folder)

    def enter_folder_name(self, name):
        self.folder_model.set_folder_name(folder_name=name)

    def provide_full_path(self):
        return self.folder_model.get_full_path()
    
    def get_files(self, folder_path):
        return [
            f for f in os.listdir(folder_path)
            if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith('.mp3')
        ]
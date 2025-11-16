from view.home_view import HomeView
from view.metadata_view import MetadataView

from controller.folder_controller import FolderController
from controller.download_controller import DownloadController
from controller.metadata_controller import MetadataController

class Application:
    def __init__(self, root):
        self.root = root

        self.current_view = None
        self.home_view = None
        self.metadata_view = None
    
    def initialize_views(self):
        self.home_view = HomeView(self.root, self)
        self.metadata_view = MetadataView(self.root, self)

        for view in (self.home_view, self.metadata_view):
            view.place(x=0, y=0, width=560, height=600)
            view.pack_propagate(False)

    def initialize_controllers(self):
        self.download_controller = DownloadController(self.home_view)
        self.metadata_controller = MetadataController(self.metadata_view)
        self.folder_controller = FolderController(self.home_view)

    def show_home(self):
        self.home_view.tkraise()

    def show_metadata(self):
        self.metadata_view.tkraise()

    def _show_about(self):
        pass

    # Event Handlers
    def on_browse_folder_requested(self):
        self.folder_controller.browse_folder()

    def on_folder_name_provided(self, name):
        self.folder_controller.enter_folder_name(name)

    def on_download_requested(self, data):
        folder_name = data.get("folder", "")
        self.folder_controller.enter_folder_name(name=folder_name)
        
        url = data.get("url", "")
        folder = data.get("folder", "")
        mode = data.get("mode", "")
        quality = data.get("quality", "")
        path = self.folder_controller.provide_full_path()
        
        self.download_controller.download_requested(url, folder, mode, quality, path)

    def on_metadata_edit_requested(self, data):
        folder_path = self.folder_controller.provide_full_path()
        artist = data.get("artist", "")
        album = data.get("album", "")

        self.metadata_controller.reset(folder_path, artist, album)
        self.show_metadata()

    def on_start_editing(self, data):
        folder_path = data.get("folder_path", "")
        artist = data.get("artist", "")
        album = data.get("album", "")
        files = self.folder_controller.get_files(folder_path)

        self.metadata_controller.editing_started(files, artist, album)

    def on_next(self, data):
        title = data.get("title", "")
        self.metadata_controller.on_next(title)

    def on_back(self, data):
        title = data.get("title", "")
        self.metadata_controller.on_back(title)

    def on_finish(self, data):
        title = data.get("title", "")
        type = data.get("filename_type", "")
        self.metadata_controller.on_finish(title, type)

    def on_home_requested(self):
        self.show_home()

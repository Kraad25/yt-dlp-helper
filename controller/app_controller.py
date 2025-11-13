import tkinter as tk
from tkinter import ttk

from view.theme import AppTheme
from view.home_view import HomeView
from view.metadata_view import MetadataView

from model.folder_model import FolderModel

from controller.download_controller import DownloadController

class Application:
    def __init__(self):
        self.root = tk.Tk()
        self.theme = AppTheme()

        self.folder_model = FolderModel()

        self.current_view = None
        self.home_view = None
        self.metadata_view = None

        self._setup_window()
        self._create_views()
        self._initialize_controllers()
        self.show_home()

    def _setup_window(self):
        self.root.title("Youtube Converter")
        self.root.resizable(False, False)

        window_width = 560
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x_position = int(screen_width * 0.3)
        y_position = int(screen_height * 0.1)
        
        self.root.geometry(f'{window_width}x{window_height}+{x_position}+{y_position}')
        self.root.configure(background=self.theme.get_background_color())

        self._create_menu_bar()

    def _create_menu_bar(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="About", command=self._show_about)
        
        self.root.configure(menu=menubar)

    def _create_views(self):
        self.home_view = HomeView(self.root, self)
        self.metadata_view = MetadataView(self.root, self)

        for view in (self.home_view, self.metadata_view):
            view.place(x=0, y=0, width=560, height=600)
            view.pack_propagate(False)

    def _initialize_controllers(self):
        self.downloadController = DownloadController(self.home_view)

    def show_view(self, view: ttk.Frame):
        self.current_view = view
        view.tkraise()

    def _show_home_view(self):
        if self.home_view:
            self.show_view(self.home_view)

    def _show_metadata_view(self):
        if self.metadata_view:
            self.show_view(self.metadata_view)

    def show_home(self):
        self._show_home_view()

    def show_metadata(self):
        self._show_metadata_view()

    def _show_about(self):
        pass

    # Event Handlers
    def on_download_requested(self, data):
        folder = data.get("folder", "")
        self.folder_model.set_folder_name(folder_name=folder)
        path = self.folder_model.get_full_path()
        self.downloadController.download_requested(data, path)

    def on_metadata_edit_requested(self, data):
        folder_path = self.folder_model.get_full_path()
        artist = data.get("artist", "")
        album = data.get("album", "")

        self.metadata_view.set_folder_path(folder_path)
        self.metadata_view.set_artist(artist)
        self.metadata_view.set_album(album)

        self.show_view(self.metadata_view)


    def on_browse_folder_requested(self):
        folder = self.folder_model.browse_folder()
        if not folder:
            folder = self.folder_model.get_full_path()
        self.home_view.set_folder_path(folder)

    def on_folder_name_provided(self, name):
        self.folder_model.set_folder_name(name)

    def on_home_requested(self):
        self.show_home()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    gui = Application()
    gui.run()
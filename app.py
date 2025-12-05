import tkinter as tk
from tkinter import messagebox
import tkinter.ttk as ttk
from view.theme import AppTheme
from view.home_view import HomeView
from view.metadata_view import MetadataView

from controller.folder_controller import FolderController
from controller.download_controller import DownloadController
from controller.metadata_controller import MetadataController

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.theme = AppTheme()

        self._home_view: HomeView = None
        self._metadata_view: MetadataView = None
        self._download_controller: DownloadController = None
        self._metadata_controller: MetadataController = None
        self._folder_controller: FolderController = None

        self._setup()

    def run(self):
        self.root.mainloop()

    def _setup(self):
        self._setup_window()
        self._create_menu_bar()
        self._initialize_views()
        self._initialize_controllers()
        self._wire_controllers_to_views()
        self._show_home()
        
        try:
            self.root.iconbitmap('skull.ico')
        except Exception:
            pass

    def _setup_window(self):
        self.root.title("YouTube Converter v1.0")
        self.root.resizable(False, False)

        window_width = 560
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x_position = int(screen_width * 0.3)
        y_position = int(screen_height * 0.1)

        self.root.geometry(f'{window_width}x{window_height}+{x_position}+{y_position}')
        self.root.configure(background=self.theme.get_background_color())

    def _create_menu_bar(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)

        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="About", command=self._show_about)

        self.root.configure(menu=menubar)

    def _initialize_views(self):
        self._home_view = HomeView(self.root)
        self._metadata_view = MetadataView(self.root)

        for view in (self._home_view, self._metadata_view):
            view.place(x=0, y=0, width=560, height=600)
            view.pack_propagate(False)

    def _initialize_controllers(self):
        self._download_controller = DownloadController()
        self._folder_controller = FolderController(self._home_view.set_base_folder_path)
        self._metadata_controller = MetadataController()

    def _wire_controllers_to_views(self):
        self._home_view.set_controllers(
            download_controller=self._download_controller,
            folder_controller=self._folder_controller,
            metadata_callback=self._show_metadata
        )

        self._metadata_view.set_controllers(
            metadata_controller=self._metadata_controller,
            folder_controller=self._folder_controller,
            home_callback=self._show_home
        )

        self._home_view.set_cancel_callback(self._download_controller.cancel_download)

    def _show_home(self):
        self._home_view.tkraise()

    def _show_metadata(self, data: dict):
        folder_path = data.get("path", "")
        self._metadata_view.reset(data, folder_path)
        self._metadata_view.tkraise()

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "YouTube Converter v1.0\n\n"
            "This program uses yt-dlp "
            "(https://github.com/yt-dlp/yt-dlp)"
            "which is licensed under the Unlicense."
        )


if __name__ == "__main__":
    app = App()
    app.run()
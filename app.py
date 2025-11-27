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

        self.__home_view: HomeView = None
        self.__metadata_view: MetadataView = None
        self.__download_controller: DownloadController = None
        self.__metadata_controller: MetadataController = None
        self.__folder_controller: FolderController = None

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
        self.__home_view = HomeView(self.root)
        self.__metadata_view = MetadataView(self.root)

        for view in (self.__home_view, self.__metadata_view):
            view.place(x=0, y=0, width=560, height=600)
            view.pack_propagate(False)

    def _initialize_controllers(self):
        self.__download_controller = DownloadController()
        self.__folder_controller = FolderController()
        self.__metadata_controller = MetadataController()

    def _wire_controllers_to_views(self):
        self.__home_view.set_controllers(
            download_controller=self.__download_controller,
            folder_controller=self.__folder_controller,
            metadata_callback=self._show_metadata
                )

    def _show_home(self):
        self.__home_view.tkraise()

    def _show_metadata(self, data: dict):
        folder_path = self.__folder_controller.provide_full_path()
        self.__metadata_view.reset(data, folder_path)
        self.__metadata_view.tkraise()

    def _show_about(self):
        messagebox.showinfo(
            "About",
            "YouTube Converter v1.0\n\n"
            "Download and manage YouTube media\n"
            "with metadata editing capabilities."
            "Created by Krishna and Mihir"
        )


if __name__ == "__main__":
    app = App()
    app.run()
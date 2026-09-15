import sys
from pathlib import Path

def _bootstrap_libs_path():
    if getattr(sys, "frozen", False):
        app_root = Path(sys.executable).resolve().parent
    else:
        app_root = Path(__file__).resolve().parent
    libs_dir = app_root / "libs"
    sys.path.insert(0, str(libs_dir))

_bootstrap_libs_path()

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from view.theme import AppTheme
from view.home_view import HomeView
from view.explorer_view import ExplorerView

from controller.folder_controller import FolderController
from controller.download_controller import DownloadController
from controller.explore_controller import ExploreController
from service.update_service import UpdateService

from service.encoder_test_service import EncoderTestService

VERSION = "1.3.0"

# Locked for now
MIN_WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 900
MAX_WINDOW_HEIGHT = 600
MAX_WINDOW_WIDTH = 900
class App:
    def __init__(self):
        AppTheme.apply_global_theme()

        self.root = ctk.CTk()

        self._home_view: HomeView = None
        self._explorer_view: ExplorerView = None
        self._download_controller: DownloadController = None
        self._explore_controller: ExploreController = None
        self._folder_controller: FolderController = None
        self._explore_folder_controller: FolderController = None

        self._update_service: UpdateService = None

        self._encoder_var = tk.StringVar(value="CPU")
        self._available_encoders: list[dict] = []

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

        tester = EncoderTestService()
        tester.list_available_encoder(self._on_encoders_detected)
        
        try:
            self.root.iconbitmap('flag.ico')
        except Exception:
            pass

    def _setup_window(self):
        self.root.title(f"Media Downloader {VERSION}")
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x_position = int(screen_width * 0.25)
        y_position = int(screen_height * 0.15)
        self.root.geometry(f'{MAX_WINDOW_WIDTH}x{MAX_WINDOW_HEIGHT}+{x_position}+{y_position}')
        self.root.minsize(width=MIN_WINDOW_WIDTH, height=MIN_WINDOW_HEIGHT)
        self.root.maxsize(width=MAX_WINDOW_WIDTH, height=MAX_WINDOW_HEIGHT)

    def _create_menu_bar(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Home", command=self._show_home)
        file_menu.add_command(label="Explore Youtube", command=self._show_explore)
        file_menu.add_separator()
        file_menu.add_command(label="Update", command=self._check_for_updates)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="About", command=self._show_about)

        self._settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=self._settings_menu)

        # Encoder submenu
        self._encoder_menu = tk.Menu(self._settings_menu, tearoff=0)
        self._settings_menu.add_cascade(label="Video encoder", menu=self._encoder_menu)

        self._encoder_menu.add_radiobutton(
            label="CPU (default)",
            variable=self._encoder_var,
            value="CPU",
            command=self._on_encoder_selected,
        )
        self.root.configure(menu=menubar)

    def _on_encoders_detected(self, encoders: list):
        self._available_encoders = encoders

        self._encoder_menu.delete(0, 'end')

        if not encoders:
            self._encoder_var.set("CPU")
            self._encoder_menu.add_radiobutton(
                label="CPU (default)",
                variable=self._encoder_var,
                value="CPU",
                command=self._on_encoder_selected,
            )
            return

        for info in encoders:
            encoder_type = info["type"]  # "QSV" / "NVENC" / "AMF" / "CPU"
            label = f"{info.get('name', '')}"
            self._encoder_menu.add_radiobutton(
                label=label,
                variable=self._encoder_var,
                value=encoder_type,
                command=lambda: self._on_encoder_selected(info["type"]),
            )

        first_type = encoders[0]["type"]
        self._encoder_var.set(first_type)
        self._on_encoder_selected(first_type)

    def _initialize_views(self):
        self._home_view = HomeView(self.root)
        self._home_view.grid(row=0, column=0, sticky="nsew")

        self._explorer_view = ExplorerView(self.root)
        self._explorer_view.grid(row=0, column=0, sticky="nsew")

    def _initialize_controllers(self):
        self._download_controller = DownloadController()
        self._folder_controller = FolderController(self._home_view.set_base_folder_path)
        self._explore_folder_controller = FolderController(self._explorer_view.set_base_folder_path)
        self._explore_controller = ExploreController(self._download_controller)
        self._update_service = UpdateService()

    def _wire_controllers_to_views(self):
        self._home_view.set_controllers(
            download_controller=self._download_controller,
            folder_controller=self._folder_controller,
        )
        self._explorer_view.set_controllers(
            explore_controller=self._explore_controller,
            folder_controller=self._explore_folder_controller,
        )
                
        self._home_view.set_cancel_callback(self._download_controller.cancel_download)

    def _show_home(self):
        self._home_view.tkraise()

    def _show_explore(self):
        self._explorer_view.tkraise()

    def _show_about(self):
        messagebox.showinfo(
            "About",
            f"YouTube Converter {VERSION}\n\n"
            "This program uses yt-dlp for downloading and processing media.\n"
            "Project page and supported sites:\n"
            "https://github.com/yt-dlp/yt-dlp\n\n"
            "See the yt-dlp repository for full licensing information."
        )

    def _check_for_updates(self):        
        self._home_view.update_status("Checking and Updating")

        self._update_service.update_program(update_status = self._change_status_for_updates)

    def _change_status_for_updates(self, message):
        self._home_view.update_status(message)

    def _on_encoder_selected(self, encoder_type: str = "CPU"):
        self._home_view.set_video_encoder(encoder_type)



if __name__ == "__main__":
    app = App()
    app.run()
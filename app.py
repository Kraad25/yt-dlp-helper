import sys
import logging
from pathlib import Path

from core.app_logger import AppLogger

app_logger = AppLogger()
app_logger.setup_logging()
app_logger.install_crash_handlers()

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

from core.ui_thread_dispatcher import UiThreadDispatcher
from core.paths import resource_dir

from view.theme import AppTheme
from view.home_view import HomeView
from view.explorer_view import ExplorerView
from view.settings_view import SettingsView

from controller.folder_controller import FolderController
from controller.download_controller import DownloadController
from controller.explore_controller import ExploreController
from controller.settings_controller import SettingsController

from model.watcher_db_model import initialize_database

VERSION = "1.3.0"

# Locked for now
MIN_WINDOW_HEIGHT = 600
MIN_WINDOW_WIDTH = 900
MAX_WINDOW_HEIGHT = 600
MAX_WINDOW_WIDTH = 900

MANUAL_DOWNLOAD_DIR_KEY = "manual_download_base_dir"
EXPLORE_DOWNLOAD_DIR_KEY = "explore_download_base_dir"

class App:
    def __init__(self):
        AppTheme.apply_global_theme()

        self.root = ctk.CTk()

        app_logger.install_tk_crash_handler(self.root)
        logging.getLogger("app").info("app start version=%s frozen=%s", VERSION, getattr(sys, "frozen", False))

        self._thread_dispatcher: UiThreadDispatcher = UiThreadDispatcher(self.root)

        self._home_view: HomeView = None
        self._explorer_view: ExplorerView = None
        self._current_view: HomeView | ExplorerView | SettingsView = None


        self._download_controller: DownloadController = None
        self._explore_controller: ExploreController = None
        self._folder_controller: FolderController = None
        self._explore_folder_controller: FolderController = None
        self._settings_controller: SettingsController = None

        initialize_database()
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
            self.root.iconbitmap(resource_dir()/"flag.ico")
        except Exception as e:
            logging.getLogger("app").warning('Icon Not Loaded Error:"%s"', e)

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

        self._file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=self._file_menu)
        self._file_menu.add_command(label="Home", command=self._show_home)
        self._file_menu.add_command(label="Explore Youtube", command=self._show_explore)
        self._file_menu.add_separator()        
        self._file_menu.add_command(label="Exit", command=self.root.destroy)

        menubar.add_command(label="About", command=self._show_about)

        # Settings submenu
        menubar.add_command(label="Settings", command=self._show_settings)

        self.root.configure(menu=menubar)

    def _initialize_views(self):
        self._home_view = HomeView(self.root)
        self._home_view.grid(row=0, column=0, sticky="nsew")

        self._explorer_view = ExplorerView(self.root)
        self._explorer_view.grid(row=0, column=0, sticky="nsew")

        self._settings_view = SettingsView(self.root)
        self._settings_view.grid(row=0, column=0, sticky="nsew")

        self._home_view.set_thread_dispatcher(self._thread_dispatcher)
        self._explorer_view.set_thread_dispatcher(self._thread_dispatcher)
        self._settings_view.set_thread_dispatcher(self._thread_dispatcher)

    def _initialize_controllers(self):
        self._settings_controller = SettingsController()
        
        self._download_controller = DownloadController(self._settings_controller)
        self._explore_controller = ExploreController(self._download_controller)
        
        self._folder_controller = FolderController(MANUAL_DOWNLOAD_DIR_KEY, self._home_view.set_base_folder_path)
        self._explore_folder_controller = FolderController(EXPLORE_DOWNLOAD_DIR_KEY, self._explorer_view.set_base_folder_path)

    def _wire_controllers_to_views(self):
        self._home_view.set_controllers(
            download_controller=self._download_controller,
            folder_controller=self._folder_controller,
        )
        self._explorer_view.set_controllers(
            explore_controller=self._explore_controller,
            folder_controller=self._explore_folder_controller,
        )

        self._settings_view.set_controllers(self._settings_controller)        

    # Views
    def _show_home(self):
        self._current_view = self._home_view
        self._home_view.tkraise()

    def _show_explore(self):
        self._current_view = self._explorer_view
        self._explorer_view.tkraise()

    def _show_settings(self):
        self._current_view = self._settings_view
        self._settings_view.tkraise()

    # About Section
    def _show_about(self):
        yt_dlp_version = self._settings_controller.get_ytdlp_version()
        ffmpeg_version = self._settings_controller.get_ffmpeg_version()

        messagebox.showinfo(
            "About",
            f"Media Downloader {VERSION}\n\n"
            "Download audio (MP3) or video (MP4) from supported sites,\n"
            "and browse YouTube without leaving the app.\n\n"
            "Powered by\n"
            f"   yt-dlp  {yt_dlp_version}\n"
            f"   ffmpeg  {ffmpeg_version}\n\n"
            "yt-dlp project and supported sites:\n"
            "https://github.com/yt-dlp/yt-dlp\n"
            "See that repository for full licensing information."
        )


if __name__ == "__main__":
    app = App()
    app.run()
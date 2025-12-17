import tkinter as tk
from tkinter import messagebox

from view.theme import AppTheme
from view.home_view import HomeView
from view.metadata_view import MetadataView

from controller.folder_controller import FolderController
from controller.download_controller import DownloadController
from controller.metadata_controller import MetadataController

from service.encoder_test_service import EncoderTestService

VERSION = "1.2.1"

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.theme = AppTheme()

        self._home_view: HomeView = None
        self._metadata_view: MetadataView = None
        self._download_controller: DownloadController = None
        self._metadata_controller: MetadataController = None
        self._folder_controller: FolderController = None

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
        self._metadata_view = MetadataView(self.root)

        for view in (self._home_view, self._metadata_view,):
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
            f"YouTube Converter {VERSION}\n\n"
            "This program uses yt-dlp for downloading and processing media.\n"
            "Project page and supported sites:\n"
            "https://github.com/yt-dlp/yt-dlp\n\n"
            "See the yt-dlp repository for full licensing information."
        )

    def _on_encoder_selected(self, encoder_type: str = "CPU"):
        self._home_view.set_video_encoder(encoder_type)


if __name__ == "__main__":
    app = App()
    app.run()
import customtkinter
from typing import Callable

from view.BaseView import BaseView
from view.custom_combobox import CustomComboBox

from controller.folder_controller import FolderController
from controller.download_controller import DownloadController

class Mode:
    MP3 = 1
    MP4 = 2

class HomeView(BaseView):

    ROW_HEADER = 0
    ROW_URL_LABEL = 1
    ROW_URL_ENTRY = 2
    ROW_DEST_LABEL = 3
    ROW_DEST_ENTRY = 4
    ROW_MODE_QUALITY = 5
    ROW_SPACER = 6
    ROW_PROGRESS = 7
    ROW_STATUS = 8
    ROW_ACTIONS = 9

    def __init__(self, parent):
        self._mode_var = customtkinter.IntVar(value=Mode.MP3)  # Default to Mp3
        self._seg_button_var = customtkinter.StringVar(value="🎵 Mp3")

        self._url_entry = None
        self._destination_entry = None
        self._progress_bar = None
        self._status_label = None
        self._quality_selector = None
        self._download_button = None

        self._download_controller: DownloadController = None
        self._folder_controller: FolderController = None

        self._on_cancel: Callable = None
        self._video_encoder: str = "CPU"

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, download_controller, folder_controller):
        self._download_controller = download_controller
        self._folder_controller = folder_controller

    def set_cancel_callback(self, callback: Callable):
        self._on_cancel = callback

    def set_base_folder_path(self, path: str):
        if self._destination_entry:
            self._destination_entry.delete(0, "end")
            self._destination_entry.insert(0, path)

    def set_download_enabled(self, enabled: bool):
        state = "normal" if enabled else "disabled"
        self._download_button.configure(state=state)

    def set_cancel_enabled(self, enabled: bool):
        if not self._cancel_button:
            return
        if enabled:
            self._enter_download_state()
        else:
            self._exit_download_state()

    def set_video_encoder(self, encoder: str):
        self._video_encoder = encoder

    def update_progress(self, value: int):
        if self._progress_bar:
            self._progress_bar.set(value / 100)

    def update_status(self, status: str):
        if self._status_label:
            self._status_label.configure(text=status)

    # Event Handlers
    def _on_download_clicked(self):
        data = self._get_form_data()
        path = data.get("path", "")

        self._download_controller.download_requested(
            data,
            path,
            self._video_encoder,
            self.set_download_enabled,
            self.set_cancel_enabled,
            self.update_progress,
            self.update_status
        )

    def _on_browse_clicked(self):
        self._folder_controller.browse_folder()

    def _on_segmented_change(self, value):
        if "Mp3" in value:
            self._mode_var.set(Mode.MP3)
        else:
            self._mode_var.set(Mode.MP4)
        self._on_mode_change()

    def _on_mode_change(self):
        mode = "mp3" if self._mode_var.get() == Mode.MP3 else "mp4"
        self._quality_selector.switch_mode(mode)

    def _on_cancel_clicked(self):
        if self._on_cancel:
            self._on_cancel()

    def _enter_download_state(self):
        self._download_button.grid_configure(column=0, columnspan=1)
        self._cancel_button.configure(state="normal")
        self._cancel_button.grid()  # re-show
        self._progress_bar.set(0)
        self._progress_bar.grid()  # re-show

    def _exit_download_state(self):
        self._download_button.grid_configure(column=0, columnspan=2)
        self._cancel_button.grid_remove()
        self._progress_bar.grid_remove()

    # Private Methods
    def _setup_style(self):
        pass  # CTk widgets are themed via themes/warm_refined.json

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(self.ROW_SPACER, weight=1)
        self.grid_rowconfigure(self.ROW_PROGRESS, minsize=18)
        
        self._title = self._create_header()
        self._url_entry = self._create_url_input()
        self._destination_entry, self._browse_button = self._create_destination_input()
        self._mode_segmented, self._quality_selector = self._create_mode_and_quality()
        self._progress_bar, self._status_label = self._create_progress_section()
        self._download_button, self._cancel_button = self._create_action_buttons()

        self.set_cancel_enabled(False)
        self.update_status("Ready")

    def _create_header(self):
        title = customtkinter.CTkLabel(
            self,
            text="Media Downloader",
            font=customtkinter.CTkFont(size=18, weight="bold"),
        ).grid(row=self.ROW_HEADER, column=0, columnspan=2, pady=(20, 15))

        return title

    def _create_url_input(self):
        url_label = customtkinter.CTkLabel(self, text="URL", font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray50")
        url_label.grid(row=self.ROW_URL_LABEL, column=0, columnspan=2, sticky="w", padx=30)

        url_entry = customtkinter.CTkEntry(self, placeholder_text="Paste a supported URL")
        url_entry.grid(row=self.ROW_URL_ENTRY, column=0, columnspan=2, sticky="ew", padx=30, pady=(2, 15))
        return url_entry

    def _create_destination_input(self):
        destination_label = customtkinter.CTkLabel(self, text="Destination", font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray50")
        destination_label.grid(row=self.ROW_DEST_LABEL, column=0, columnspan=2, sticky="w", padx=30)
        
        destination_entry = customtkinter.CTkEntry(self, placeholder_text="Select download destination")
        destination_entry.grid(row=self.ROW_DEST_ENTRY, column=0, sticky="ew", padx=(30, 8), pady=(2, 15))

        browse_button = customtkinter.CTkButton(
            self,
            text="📁",
            width=32,
            height=28, 
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=lambda: self._on_browse_clicked()
        )

        browse_button.grid(row=self.ROW_DEST_ENTRY, column=1, sticky="e", padx=(0, 30), pady=(2, 15))

        return destination_entry, browse_button

    def _create_mode_and_quality(self):
        group = customtkinter.CTkFrame(self, fg_color="transparent")
        group.grid(row=self.ROW_MODE_QUALITY, column=0, columnspan=2, sticky="w", padx=30, pady=(0, 15))

        segmented_button = customtkinter.CTkSegmentedButton(
            group,
            values=["🎵 Mp3", "🎬 Mp4"],
            variable=self._seg_button_var,
            command=self._on_segmented_change,
            width=180,
            height=36,
            font=customtkinter.CTkFont(size=14, weight="bold")
        )
        segmented_button.grid(row=0, column=0, rowspan=2, sticky="w")

        quality_label = customtkinter.CTkLabel(group, text="Quality", font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray50")
        quality_label.grid(row=0, column=1, sticky="e", padx=(30, 0))

        quality_selector = CustomComboBox(group, self._mode_var, width=130)
        quality_selector.widget.grid(row=0, column=2, sticky="w", padx=(15, 0), pady=(2, 0))

        return segmented_button, quality_selector

    def _create_progress_section(self):
        progress_bar = customtkinter.CTkProgressBar(self, height=10)
        progress_bar.set(0)
        progress_bar.grid(row=self.ROW_PROGRESS, column=0, columnspan=2, sticky="ew", padx=30, pady=(0, 4))

        # hidden until a download starts
        progress_bar.grid_remove()

        status_label = customtkinter.CTkLabel(self, text="Ready", font=customtkinter.CTkFont(size=12, slant="italic"), text_color="gray50", anchor="w")
        status_label.grid(row=self.ROW_STATUS, column=0, columnspan=2, sticky="w", padx=30, pady=(0, 15))

        return progress_bar, status_label

    def _create_action_buttons(self):
        action_row = customtkinter.CTkFrame(self, fg_color="transparent")
        action_row.grid(row=self.ROW_ACTIONS, column=0, columnspan=2, sticky="ew", padx=30, pady=(0, 25))
        action_row.grid_columnconfigure(0, weight=1)
        action_row.grid_columnconfigure(1, weight=0, minsize=0)

        download_button = customtkinter.CTkButton(
            action_row,
            text="⭳ Download",
            height=45,
            font=customtkinter.CTkFont(size=15, weight="bold"),
            command=self._on_download_clicked,
        )
        download_button.grid(row=0, column=0, sticky="ew")

        cancel_button = customtkinter.CTkButton(
            action_row,
            text="Cancel",
            width=110,
            height=45,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._on_cancel_clicked,
        )
        cancel_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

        # hidden until a download starts
        cancel_button.grid_remove()

        return download_button, cancel_button

    def _get_form_data(self):
        destination = self._destination_entry.get().strip() if self._destination_entry else ""
        path = self._folder_controller.build_target_path(destination, "")

        return {
            "url": self._url_entry.get().strip() if self._url_entry else "",
            "path": path if path else "",
            "mode": "mp3" if self._mode_var.get() == Mode.MP3 else "mp4",
            "quality": self._quality_selector.get_value(),
        }
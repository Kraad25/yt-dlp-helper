import tkinter as tk
from tkinter import ttk
from typing import Callable

from view.BaseView import BaseView
from view.custom_combobox import CustomComboBox
from view.custom_entry import CustomEntry
from view.theme import AppTheme

class Mode:
    MP3 = 1
    MP4 = 2

class HomeView(BaseView):
    def __init__(self, parent: tk.Widget):
        self.__theme = AppTheme()
        self.__mode_var = tk.IntVar(value=Mode.MP3)  # Default to Mp3

        self.__url_entry = None
        self.__base_folder_entry = None
        self.__subfolder_entry = None
        self.__artist_entry = None
        self.__album_entry = None
        self.__progress_bar = None
        self.__status_entry = None
        self.__quality_selector = None
        self.__download_button = None

        self.__download_controller = None
        self.__folder_controller = None

        self.__show_metadata: Callable = None
        self.__on_cancel: Callable = None

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, download_controller, folder_controller, metadata_callback: Callable):
        self.__download_controller = download_controller
        self.__folder_controller = folder_controller
        self.__show_metadata = metadata_callback

    def set_cancel_callback(self, callback: Callable):
        self.__on_cancel = callback

    def set_base_folder_path(self, path: str):
        if self.__base_folder_entry:
            self.__base_folder_entry.set_entry_text(path)

    def set_download_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.__download_button.config(state=state)

    def update_progress(self, value: int):
        if self.__progress_bar:
            self.__progress_bar['value'] = value

    def update_status(self, status: str):
        if self.__status_entry:
            self.__status_entry.set_readonly_entry_text(status)

    # Event Handlers
    def __on_download_clicked(self):
        data = self.__get_form_data()
        path = data.get("path", "")

        self.__download_controller.download_requested(
            data,
            path,
            self.set_download_enabled,
            self.update_progress,
            self.update_status
        )

    def __on_metadata_clicked(self):
        data = self.__get_form_data()
        self.__show_metadata(data)

    def __on_browse_clicked(self):
        self.__folder_controller.browse_folder()

    def __on_mode_change(self):
        mode = "mp3" if self.__mode_var.get() == Mode.MP3 else "mp4"
        self.__quality_selector.switch_mode(mode)

    def __on_cancel_clicked(self):
        if self.__on_cancel:
            self.__on_cancel()

    def __on_reset_clicked(self):
        if self.__url_entry:
            self.__url_entry.set_entry_text("")
        if self.__artist_entry:
            self.__artist_entry.set_entry_text("")
        if self.__album_entry:
            self.__album_entry.set_entry_text("")

        self.__mode_var.set(Mode.MP3)
        self.update_progress(0)
        self.update_status("Ready")

    # Private Methods
    def _setup_style(self):
        style = ttk.Style()
        style.configure("Beige.TFrame", background=self.__theme.get_background_color())
        style.configure(
            "Grey.TLabelframe",
            background=self.__theme.get_secondary_color(),
            borderwidth=2,
            relief="solid",
        )
        style.configure(
            "Grey.TLabelframe.Label",
            background=self.__theme.get_secondary_color(),
            font=("Segoe UI", 10),
        )

    def _create_widgets(self):
        self.configure(style="Beige.TFrame")

        self._title = self.__create_header()
        self.__url_entry = self.__create_url_input()
        self.__base_folder_entry, self._browse_button = self.__create_base_folder_input()
        self.__subfolder_entry = self.__create_subfolder_input()
        self._mp3_radio, self._mp4_radio = self.__create_mode_section()
        self.__quality_selector = self.__create_quality_section()
        self._metadata_frame, self.__artist_entry, self.__album_entry = self.__create_metadata_section()
        self.__progress_bar, self.__status_entry = self.__create_progress_section()
        self.__download_button, self._metadata_button, self._cancel_button, self._reset_button = self.__create_action_buttons()

        self.update_status("Ready")

    def __create_header(self):
        label = ttk.Label(
            self,
            text="Youtube Converter",
            font=("Helvetica", 16),
            background=self.__theme.get_background_color()
        ).place(x=195, y=20)
        return label

    def __create_url_input(self):
        label = ttk.Label(
            self,
            text="URL:",
            font=("Helvetica", 13),
            background=self.__theme.get_background_color()
        ).place(x=30, y=80)

        entry = CustomEntry(self, width=70, posx=85, posy=80)
        entry.make_entry()

        return entry

    def __create_base_folder_input(self):
        label = ttk.Label(
            self,
            text="Base:",
            font=("Helvetica", 13),
            background=self.__theme.get_background_color()
        ).place(x=30, y=120)

        entry = CustomEntry(self, width=70, posx=85, posy=120,
                            placeholder="Select base folder for downloads"
        )
        entry.make_entry()

        browse_button = tk.Button(
            self,
            text="📁",
            font=("Arial", 12),
            padx=1,
            pady=1,
            bd=0,
            command=lambda: self.__on_browse_clicked()
        )
        browse_button.place(x=520, y=116)

        return entry, browse_button
    
    def __create_subfolder_input(self):
        label = ttk.Label(
            self,
            text="Folder:",
            font=("Helvetica", 13),
            background=self.__theme.get_background_color()
        ).place(x=30, y=160)

        entry = CustomEntry(self, width=70, posx=85, posy=160,
                            placeholder="Optional subfolder name"
        )
        entry.make_entry()
        return entry
    
    def __create_mode_section(self):
        mode_button_mp3 = tk.Radiobutton(
            self,
            text="Mp3 🎵",
            variable=self.__mode_var,
            value=1,
            bg=self.__theme.get_background_color(),
            activebackground=self.__theme.get_background_color(),
            command=lambda: self.__on_mode_change()
        )
        mode_button_mp4 = tk.Radiobutton(
            self,
            text="Mp4 🎬",
            variable=self.__mode_var,
            value=2,
            bg=self.__theme.get_background_color(),
            activebackground=self.__theme.get_background_color(),
            command=lambda: self.__on_mode_change()
        )
        mode_button_mp3.place(x=30, y=197)
        mode_button_mp4.place(x=100, y=197)

        return mode_button_mp3, mode_button_mp4

    def __create_quality_section(self):
        label = ttk.Label(
            self,
            text="Quality:",
            font=("Helvetica", 13),
            background=self.__theme.get_background_color()
        ).place(x=30, y=237)

        quality_selector = CustomComboBox(self, self.__mode_var, 100, 237)
        quality_selector.make_combobox()

        return quality_selector

    def __create_metadata_section(self):
        metadata_frame = tk.LabelFrame(
            self,
            text="Metadata (Optional)",
            width=500,
            height=150,
            bg=self.__theme.get_secondary_color(),
            fg="black",
            font=("Arial", 10, "italic bold"),
            bd=5,
            relief="ridge"
        )
        metadata_frame.place(x=30, y=277)
        metadata_frame.pack_propagate(False)

        ttk.Label(metadata_frame, text="Artist :", background=self.__theme.get_secondary_color()).place(
            x=20, y=20
        )
        artist_entry = CustomEntry(metadata_frame, width=65, posx=70, posy=20,
                                   placeholder="For MP3: Artist name | For MP4: Channel / Director / Actor"
        )
        artist_entry.make_entry()

        ttk.Label(metadata_frame, text="Album :", background=self.__theme.get_secondary_color()).place(
            x=20, y=60
        )
        album_entry = CustomEntry(metadata_frame, width=65, posx=70, posy=60,
                                   placeholder="MP3 only — ignored for MP4 files"
        )
        album_entry.make_entry()

        return metadata_frame, artist_entry, album_entry

    def __create_progress_section(self):
        progress_bar = ttk.Progressbar(self, orient="horizontal", length=500, mode="determinate")
        progress_bar.place(x=30, y=437)

        ttk.Label(
            self,
            text="Status: ",
            background=self.__theme.get_background_color(),
            font=("Segoe UI", 12, "italic")
        ).place(x=163, y=477)

        status_entry = CustomEntry(self, width=20, posx=213, posy=480)
        status_entry.make_entry()

        return progress_bar, status_entry

    def __create_action_buttons(self):
        download_button = ttk.Button(self, text="Download", width=20, command=lambda: self.__on_download_clicked())
        download_button.place(x=60, y=525)

        reset_button = ttk.Button(self, text="Reset Entries", width=20, command=lambda: self.__on_reset_clicked())
        reset_button.place(x=213, y=525)
   
        cancel_button = ttk.Button(self, text="Cancel", width=20, command=lambda: self.__on_cancel_clicked())
        cancel_button.place(x=366, y=525)

        metadata_button = ttk.Button(self, text="Edit Metadata ➜", width=20, 
                                     command=lambda: self.__on_metadata_clicked()
                                    )
        metadata_button.place(x=213, y=560)

        return download_button, metadata_button, cancel_button, reset_button

    def __get_form_data(self):
        base_folder = self.__base_folder_entry.get_entry_text() if self.__base_folder_entry else ""
        subfolder = self.__subfolder_entry.get_entry_text() if self.__subfolder_entry else ""
        path = self.__folder_controller.build_target_path(base_folder, subfolder)

        return {
            "url": self.__url_entry.get_entry_text() if self.__url_entry else "",
            "path": path if path else "",
            "mode": "mp3" if self.__mode_var.get() == 1 else "mp4",
            "quality": self.__quality_selector.get_value(),
            "artist": self.__artist_entry.get_entry_text() if self.__artist_entry else "",
            "album": self.__album_entry.get_entry_text() if self.__album_entry else "",
        }
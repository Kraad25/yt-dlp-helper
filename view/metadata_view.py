import tkinter as tk
from tkinter import ttk
from typing import Callable

from view.BaseView import BaseView
from view.custom_entry import CustomEntry
from view.theme import AppTheme

from controller.metadata_controller import MetadataController
from controller.folder_controller import FolderController

class MetadataView(BaseView):
    def __init__(self, parent: tk.Widget):
        self._theme = AppTheme()
        self._filename_var = tk.IntVar(value=1)

        self._folder_path_entry = None
        self._artist_entry = None
        self._album_entry = None
        self._mode_entry = None
        self._status_entry = None
        self._title_entry = None

        self._back_button = None
        self._next_button = None
        self._button_data = {}

        self._metadata_controller: MetadataController = None
        self._folder_controller: FolderController = None

        self._show_home: Callable = None

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, metadata_controller, folder_controller, home_callback: Callable):
        self._metadata_controller = metadata_controller
        self._folder_controller = folder_controller
        self._show_home = home_callback

    def reset(self, data: dict, folder_path: str):
        artist = data.get("artist", "")
        album = data.get("album", "")
        mode = data.get("mode", "")

        self._set_presets(folder_path, artist, album, mode)
        self._reset_wizard_state()

    def set_title(self, title):
        self._title_entry.set_entry_text(title)

    # Event Handler
    def _on_home_clicked(self):
        self._show_home()

    def _on_start_editing_clicked(self):
        data = self._get_preset_data()
        folder_path = data.get("folder_path", "")
        mode = data.get("mode", "")

        files = self._folder_controller.get_files(folder_path, mode)
        self._metadata_controller.editing_requested(
            files,
            data,
            self.set_title,
            self._show_wizard,
            self._update_status,
            self._set_next_enabled,
            self._set_back_enabled,
        )

    def _on_next_clicked(self):
        data = self._get_data()
        title = data.get("title", "")
        self._metadata_controller.on_next(title)

    def _on_back_clicked(self):
        data = self._get_data()
        title = data.get("title", "")
        self._metadata_controller.on_back(title)

    def _on_finish_clicked(self):
        data = self._get_data()
        title = data.get("title", "")
        type = data.get("filename_type", "")
        self._metadata_controller.on_finish(title, type)

    # Private Methods
    def _setup_style(self):
        style = ttk.Style()
        style.configure("Beige.TFrame", background=self._theme.get_background_color())
        style.configure(
            "Grey.TLabelframe",
            background=self._theme.get_secondary_color(),
            borderwidth=2,
            relief="solid",
        )
        style.configure(
            "Grey.TLabelframe.Label",
            background=self._theme.get_secondary_color(),
            font=("Segoe UI", 10),
        )

    def _create_widgets(self):
        self.configure(style="Beige.TFrame")

        home_button = self._create_home_button()
        title = self._create_header()
        self._folder_path_entry, self._artist_entry, self._album_entry, self._mode_entry = self._show_presets()
        title_artist, title_album, title = self._show_filenaming_options()
        self._title_entry, self._back_button, self._next_button, self._button_data = self._show_editing_field()
        self._status_entry = self._show_progess_state()

    def _create_home_button(self):
        home_button = tk.Button(
            self,
            text="🏠",
            font=("Arial", 13),
            padx=1,
            pady=1,
            bd=0,
            command=lambda: self._on_home_clicked(),
        )
        home_button.place(x=10, y=10)
        return home_button

    def _create_header(self):
        title_label = ttk.Label(
            self,
            text="Metadata Editor",
            font=("Helvetica", 16),
            background=self._theme.get_background_color(),
        )
        title_label.place(x=200, y=20)
        return title_label

    def _show_presets(self):
        preset_label = ttk.Label(
            self,
            text="Presets",
            font=("Helvetica", 13, "bold"),
            background=self._theme.get_background_color(),
        )
        preset_label.place(x=30, y=80)

        folder_label = ttk.Label(
            self,
            text="Folder Path: ",
            font=("Helvetica", 10),
            background=self._theme.get_background_color(),
        )
        folder_label.place(x=30, y=120)
        folder_path_entry = CustomEntry(self, width=50, posx=130, posy=120)
        folder_path_entry.make_entry()

        artist_label = ttk.Label(
            self,
            text="Artist: ",
            font=("Helvetica", 10),
            background=self._theme.get_background_color(),
        )
        artist_label.place(x=30, y=150)
        artist_entry = CustomEntry(self, width=50, posx=130, posy=150)
        artist_entry.make_entry()

        album_label = ttk.Label(
            self,
            text="Album: ",
            font=("Helvetica", 10),
            background=self._theme.get_background_color(),
        )
        album_label.place(x=30, y=180)
        album_entry = CustomEntry(self, width=50, posx=130, posy=180)
        album_entry.make_entry()

        mode_label = ttk.Label(
            self,
            text="Mode: ",
            font=("Helvetica", 10),
            background=self._theme.get_background_color(),
        )
        mode_label.place(x=30, y=210)
        mode_entry = CustomEntry(self, width=50, posx=130, posy=210)
        mode_entry.make_entry()

        return folder_path_entry, artist_entry, album_entry, mode_entry

    def _show_filenaming_options(self):
        ttk.Label(
            self,
            text="File Name",
            font=("Helvetica", 12, "bold"),
            background=self._theme.get_background_color(),
        ).place(x=30, y=250)

        title_artist = tk.Radiobutton(
            self,
            text="Title - Artist",
            variable=self._filename_var,
            value=1,
            bg=self._theme.get_background_color(),
            activebackground=self._theme.get_background_color(),
        )
        title_album = tk.Radiobutton(
            self,
            text="Title - Album",
            variable=self._filename_var,
            value=2,
            bg=self._theme.get_background_color(),
            activebackground=self._theme.get_background_color(),
        )
        title = tk.Radiobutton(
            self,
            text="Title",
            variable=self._filename_var,
            value=3,
            bg=self._theme.get_background_color(),
            activebackground=self._theme.get_background_color(),
        )

        title_artist.place(x=30, y=270)
        title_album.place(x=30, y=300)
        title.place(x=120, y=271)

        return title_artist, title_album, title

    def _show_editing_field(self):
        editing_frame = tk.LabelFrame(
            self,
            text="Edit Metadata",
            width=500,
            height=150,
            bg=self._theme.get_secondary_color(),
            fg="black",
            font=("Arial", 10, "italic bold"),
            bd=5,
            relief="ridge",
        )
        editing_frame.place(x=30, y=350)
        editing_frame.pack_propagate(False)

        file_label = ttk.Label(
            editing_frame,
            text="Title :",
            font=("Helvetica", 11),
            background=self._theme.get_secondary_color(),
        )
        title_entry = CustomEntry(editing_frame, 50, 90, 20)
        title_entry.make_entry()

        back_button = ttk.Button(editing_frame, text="Back", command=lambda: self._on_back_clicked())
        next_button = ttk.Button(editing_frame, text="Next", command=lambda: self._on_next_clicked())
        finish_button = ttk.Button(editing_frame, text="Finish Editing", command=lambda: self._on_finish_clicked())

        start_button = ttk.Button(
            editing_frame,
            text="Start Editing",
            command=lambda: self._on_start_editing_clicked(),
        )

        button_data = {
            "back": back_button,
            "next": next_button,
            "finish": finish_button,
            "label": file_label,
            "title_entry": title_entry,
            "start": start_button,
        }

        return title_entry, back_button, next_button, button_data

    def _show_progess_state(self):
        ttk.Label(
            self,
            text="Status: ",
            background=self._theme.get_background_color(),
            font=("Segoe UI", 12, "italic"),
        ).place(x=180, y=530)

        status_entry = CustomEntry(self, width=20, posx=230, posy=533)
        status_entry.make_entry()

        return status_entry

    def _get_data(self):
        return {
            "title": self._title_entry.get_entry_text(),
            "filename_type": self._filename_var.get(),
        }

    def _get_preset_data(self):
        return {
            "folder_path": self._folder_path_entry.get_entry_text(),
            "artist": self._artist_entry.get_entry_text(),
            "album": self._album_entry.get_entry_text(),
            "mode": self._mode_entry.get_entry_text(),
        }

    def _set_presets(self, folder_path, artist, album, mode):
        self._folder_path_entry.set_readonly_entry_text(folder_path)
        self._artist_entry.set_readonly_entry_text(artist)
        self._album_entry.set_readonly_entry_text(album)
        self._mode_entry.set_readonly_entry_text(mode)

    def _reset_wizard_state(self):
        self._button_data["start"].place(x=200, y=90)

        self._button_data["label"].place_forget()
        self._button_data["back"].place_forget()
        self._button_data["next"].place_forget()
        self._button_data["finish"].place_forget()

        self._button_data["title_entry"].hide_entry()

        self._update_status("Ready")

    def _set_next_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self._next_button.config(state=state)

    def _set_back_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self._back_button.config(state=state)

    def _show_wizard(self):
        self._button_data["start"].place_forget()

        self._button_data["title_entry"].show_entry()
        self._button_data["label"].place(x=50, y=20)
        self._button_data["back"].place(x=110, y=90)
        self._button_data["next"].place(x=210, y=90)
        self._button_data["finish"].place(x=310, y=90)

    def _update_status(self, status):
        self._status_entry.set_readonly_entry_text(status)
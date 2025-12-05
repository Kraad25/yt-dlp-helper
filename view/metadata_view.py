import tkinter as tk
from tkinter import ttk
from typing import Callable

from view.BaseView import BaseView
from view.custom_entry import CustomEntry
from view.theme import AppTheme


class MetadataView(BaseView):
    def __init__(self, parent: tk.Widget):
        self.__theme = AppTheme()
        self.__filename_var = tk.IntVar(value=1)

        self.__folder_path_entry = None
        self.__artist_entry = None
        self.__album_entry = None
        self.__mode_entry = None
        self.__status_entry = None
        self.__title_entry = None

        self.__back_button = None
        self.__next_button = None
        self.__button_data = {}

        self.__metadata_controller = None
        self.__folder_controller = None

        self.__show_home: Callable = None

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, metadata_controller, folder_controller, home_callback: Callable):
        self.__metadata_controller = metadata_controller
        self.__folder_controller = folder_controller
        self.__show_home = home_callback

    def reset(self, data: dict, folder_path: str):
        artist = data.get("artist", "")
        album = data.get("album", "")
        mode = data.get("mode", "")

        self.__set_presets(folder_path, artist, album, mode)
        self.__reset_wizard_state()

    def set_title(self, title):
        self.__title_entry.set_entry_text(title)

    # Event Handler
    def __on_home_clicked(self):
        self.__show_home()

    def __on_start_editing_clicked(self):
        data = self.__get_preset_data()
        folder_path = data.get("folder_path", "")
        mode = data.get("mode", "")

        files = self.__folder_controller.get_files(folder_path, mode)
        self.__metadata_controller.editing_requested(
            files,
            data,
            self.set_title,
            self.__show_wizard,
            self.__update_status,
            self.__set_next_enabled,
            self.__set_back_enabled,
        )

    def __on_next_clicked(self):
        data = self.__get_data()
        title = data.get("title", "")
        self.__metadata_controller.on_next(title)

    def __on_back_clicked(self):
        data = self.__get_data()
        title = data.get("title", "")
        self.__metadata_controller.on_back(title)

    def __on_finish_clicked(self):
        data = self.__get_data()
        title = data.get("title", "")
        type = data.get("filename_type", "")
        self.__metadata_controller.on_finish(title, type)

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

        home_button = self.__create_home_button()
        title = self.__create_header()
        self.__folder_path_entry, self.__artist_entry, self.__album_entry, self.__mode_entry = self.__show_presets()
        title_artist, title_album, title = self.__show_filenaming_options()
        self.__title_entry, self.__back_button, self.__next_button, self.__button_data = self.__show_editing_field()
        self.__status_entry = self.__show_progess_state()

    def __create_home_button(self):
        home_button = tk.Button(
            self,
            text="🏠",
            font=("Arial", 13),
            padx=1,
            pady=1,
            bd=0,
            command=lambda: self.__on_home_clicked(),
        )
        home_button.place(x=10, y=10)
        return home_button

    def __create_header(self):
        title_label = ttk.Label(
            self,
            text="Metadata Editor",
            font=("Helvetica", 16),
            background=self.__theme.get_background_color(),
        )
        title_label.place(x=200, y=20)
        return title_label

    def __show_presets(self):
        preset_label = ttk.Label(
            self,
            text="Presets",
            font=("Helvetica", 13, "bold"),
            background=self.__theme.get_background_color(),
        )
        preset_label.place(x=30, y=80)

        folder_label = ttk.Label(
            self,
            text="Folder Path: ",
            font=("Helvetica", 10),
            background=self.__theme.get_background_color(),
        )
        folder_label.place(x=30, y=120)
        folder_path_entry = CustomEntry(self, width=50, posx=130, posy=120)
        folder_path_entry.make_entry()

        artist_label = ttk.Label(
            self,
            text="Artist: ",
            font=("Helvetica", 10),
            background=self.__theme.get_background_color(),
        )
        artist_label.place(x=30, y=150)
        artist_entry = CustomEntry(self, width=50, posx=130, posy=150)
        artist_entry.make_entry()

        album_label = ttk.Label(
            self,
            text="Album: ",
            font=("Helvetica", 10),
            background=self.__theme.get_background_color(),
        )
        album_label.place(x=30, y=180)
        album_entry = CustomEntry(self, width=50, posx=130, posy=180)
        album_entry.make_entry()

        mode_label = ttk.Label(
            self,
            text="Mode: ",
            font=("Helvetica", 10),
            background=self.__theme.get_background_color(),
        )
        mode_label.place(x=30, y=210)
        mode_entry = CustomEntry(self, width=50, posx=130, posy=210)
        mode_entry.make_entry()

        return folder_path_entry, artist_entry, album_entry, mode_entry

    def __show_filenaming_options(self):
        ttk.Label(
            self,
            text="File Name",
            font=("Helvetica", 12, "bold"),
            background=self.__theme.get_background_color(),
        ).place(x=30, y=250)

        title_artist = tk.Radiobutton(
            self,
            text="Title - Artist",
            variable=self.__filename_var,
            value=1,
            bg=self.__theme.get_background_color(),
            activebackground=self.__theme.get_background_color(),
        )
        title_album = tk.Radiobutton(
            self,
            text="Title - Album",
            variable=self.__filename_var,
            value=2,
            bg=self.__theme.get_background_color(),
            activebackground=self.__theme.get_background_color(),
        )
        title = tk.Radiobutton(
            self,
            text="Title",
            variable=self.__filename_var,
            value=3,
            bg=self.__theme.get_background_color(),
            activebackground=self.__theme.get_background_color(),
        )

        title_artist.place(x=30, y=270)
        title_album.place(x=30, y=300)
        title.place(x=120, y=271)

        return title_artist, title_album, title

    def __show_editing_field(self):
        editing_frame = tk.LabelFrame(
            self,
            text="Edit Metadata",
            width=500,
            height=150,
            bg=self.__theme.get_secondary_color(),
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
            background=self.__theme.get_secondary_color(),
        )
        title_entry = CustomEntry(editing_frame, 50, 90, 20)
        title_entry.make_entry()

        back_button = ttk.Button(editing_frame, text="Back", command=lambda: self.__on_back_clicked())
        next_button = ttk.Button(editing_frame, text="Next", command=lambda: self.__on_next_clicked())
        finish_button = ttk.Button(editing_frame, text="Finish Editing", command=lambda: self.__on_finish_clicked())

        start_button = ttk.Button(
            editing_frame,
            text="Start Editing",
            command=lambda: self.__on_start_editing_clicked(),
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

    def __show_progess_state(self):
        ttk.Label(
            self,
            text="Status: ",
            background=self.__theme.get_background_color(),
            font=("Segoe UI", 12, "italic"),
        ).place(x=180, y=530)

        status_entry = CustomEntry(self, width=20, posx=230, posy=533)
        status_entry.make_entry()

        return status_entry

    def __get_data(self):
        return {
            "title": self.__title_entry.get_entry_text(),
            "filename_type": self.__filename_var.get(),
        }

    def __get_preset_data(self):
        return {
            "folder_path": self.__folder_path_entry.get_entry_text(),
            "artist": self.__artist_entry.get_entry_text(),
            "album": self.__album_entry.get_entry_text(),
            "mode": self.__mode_entry.get_entry_text(),
        }

    def __set_presets(self, folder_path, artist, album, mode):
        self.__folder_path_entry.set_readonly_entry_text(folder_path)
        self.__artist_entry.set_readonly_entry_text(artist)
        self.__album_entry.set_readonly_entry_text(album)
        self.__mode_entry.set_readonly_entry_text(mode)

    def __reset_wizard_state(self):
        self.__button_data["start"].place(x=200, y=90)

        self.__button_data["label"].place_forget()
        self.__button_data["back"].place_forget()
        self.__button_data["next"].place_forget()
        self.__button_data["finish"].place_forget()

        self.__button_data["title_entry"].hide_entry()

        self.__update_status("Ready")

    def __set_next_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.__next_button.config(state=state)

    def __set_back_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.__back_button.config(state=state)

    def __show_wizard(self):
        self.__button_data["start"].place_forget()

        self.__button_data["title_entry"].show_entry()
        self.__button_data["label"].place(x=50, y=20)
        self.__button_data["back"].place(x=110, y=90)
        self.__button_data["next"].place(x=210, y=90)
        self.__button_data["finish"].place(x=310, y=90)

    def __update_status(self, status):
        self.__status_entry.set_readonly_entry_text(status)
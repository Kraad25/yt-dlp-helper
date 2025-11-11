import tkinter as tk
from tkinter import ttk

from typing import Optional
from view.BaseView import BaseView
from view.theme import AppTheme
from view.custom_entry import CustomEntry

class MetadataView(BaseView):
    def __init__(self, parent: tk.Widget, controller: Optional[None]):
        self.theme = AppTheme()

        self.folder_path_entry = None
        self.artist_entry = None
        self.album_entry = None
        self.progress_bar = None
        self.status_entry = None

        super().__init__(parent, controller)


    def _setup_style(self):
        style = ttk.Style()
        style.configure("Beige.TFrame", background=self.theme.get_background_color())
        style.configure("Grey.TLabelframe", background=self.theme.get_secondary_color(), borderwidth=2, relief="solid")
        style.configure("Grey.TLabelframe.Label", background=self.theme.get_secondary_color(), font=("Segoe UI", 10))

    def _create_widgets(self):
        self.configure(style="Beige.TFrame")

        self._create_home_button()
        self._create_header()
        self._show_presets()

    def _bind_events(self):
        pass

    def _create_home_button(self):
        home_button = tk.Button(self, text="🏠", font=("Arial", 13), padx=1, pady=1, bd=0, command=lambda: self._on_home_clicked())
        home_button.place(x=10, y=10)

    def _create_header(self):
        title_label = ttk.Label(self, text="Metadata Editor", font=("Helvetica", 16), background=self.theme.get_background_color())
        title_label.place(x=200, y=20)

    def _show_presets(self):
        preset_label = ttk.Label(self, text="Presets",font=("Helvetica", 13, "bold") ,background=self.theme.get_background_color())
        preset_label.place(x=30, y=80)

        folder_label = ttk.Label(self, text="Folder Path: ",font=("Helvetica", 10) ,background=self.theme.get_background_color())
        folder_label.place(x=30, y=120)
        self.folder_path_entry = CustomEntry(self, width= 50, posx=130, posy=120)
        self.folder_path_entry.make_entry()
        #self.folder_path_entry.set_entry_text(self.app.folderManager.get_full_path())

        artist_label = ttk.Label(self, text="Artist: ",font=("Helvetica", 10) ,background=self.theme.get_background_color())
        artist_label.place(x=30, y=150)
        self.artist_entry = CustomEntry(self, width= 50, posx=130, posy=150)
        self.artist_entry.make_entry()
        # self.artist_entry.set_entry_text(self.app.get_artist_preset())

        album_label = ttk.Label(self, text="Album: ",font=("Helvetica", 10) ,background=self.theme.get_background_color())
        album_label.place(x=30, y=180)
        self.album_entry = CustomEntry(self, width= 50, posx=130, posy=180)
        self.album_entry.make_entry()

    
    # Event Handler
    def _on_home_clicked(self):
        self.notify_controller("on_home_requested")
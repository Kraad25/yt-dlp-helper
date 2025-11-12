import tkinter as tk
from tkinter import ttk

from typing import Optional
from view.BaseView import BaseView
from view.theme import AppTheme
from view.custom_entry import CustomEntry

class MetadataView(BaseView):
    def __init__(self, parent: tk.Widget, controller: Optional[None]):
        self.theme = AppTheme()
        self._filename_var = tk.IntVar(value=1)

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
        self._show_filenaming_options()
        self._show_editing_field()
        self._create_action_buttons()

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

        artist_label = ttk.Label(self, text="Artist: ",font=("Helvetica", 10) ,background=self.theme.get_background_color())
        artist_label.place(x=30, y=150)
        self.artist_entry = CustomEntry(self, width= 50, posx=130, posy=150)
        self.artist_entry.make_entry()

        album_label = ttk.Label(self, text="Album: ",font=("Helvetica", 10) ,background=self.theme.get_background_color())
        album_label.place(x=30, y=180)
        self.album_entry = CustomEntry(self, width= 50, posx=130, posy=180)
        self.album_entry.make_entry()

    def _show_filenaming_options(self):
        ttk.Label(self, text="File Name",
                  font=("Helvetica", 12, "bold"),
                  background=self.theme.get_background_color()
                ).place(x=30, y=220)

        title_artist = tk.Radiobutton(self,
                                      text="Title - Artist", 
                                      variable=self._filename_var, 
                                      value=1, 
                                      bg=self.theme.get_background_color(), 
                                      activebackground=self.theme.get_background_color()
                                    )
        title_album = tk.Radiobutton(self,
                                     text="Title - Album", 
                                     variable=self._filename_var, 
                                     value=2, 
                                     bg=self.theme.get_background_color(), 
                                     activebackground=self.theme.get_background_color()
                                )
        title = tk.Radiobutton(self,
                               text="Title", 
                               variable=self._filename_var,
                               value=3, 
                               bg=self.theme.get_background_color(), 
                               activebackground=self.theme.get_background_color()
                            )
        title_artist.place(x=30, y=250)
        title_album.place(x=30, y=270)
        title.place(x=120, y=251)

    def _show_editing_field(self):
        editing_frame = tk.LabelFrame(self,
                                      text="Edit Metadata",
                                      width=500,
                                      height=150,
                                      bg=self.theme.get_secondary_color(),
                                      fg="black",
                                      font=("Arial", 10, "italic bold"),
                                      bd=5,
                                      relief="ridge"
                                    )
        editing_frame.place(x=30, y=320)
        editing_frame.pack_propagate(False)

        file_label = ttk.Label(editing_frame, text="Title :", font=("Helvetica", 11), background=self.theme.get_secondary_color())
        file_label.place(x=50, y=20)
        self.title_entry = CustomEntry(editing_frame, 50, 90, 20)
        self.title_entry.make_entry()

        back_button = ttk.Button(editing_frame, text="Back", command=lambda:None)
        back_button.place(x=210, y=90)
        next_button = ttk.Button(editing_frame, text="Next", command=lambda:None)
        next_button.place(x=310, y=90)

    def _create_action_buttons(self):
        start_editing_button = ttk.Button(self, text="Start Editing", width=20, command=lambda: self._on_metadata_clicked())
        start_editing_button.place(x=200, y=525)

    # Public Methods
    def set_folder_path(self, folder_path):
        self.folder_path_entry.set_entry_text(folder_path)

    def set_artist(self, artist):
        self.artist_entry.set_entry_text(artist)
        
    def set_album(self, album):
        self.album_entry.set_entry_text(album)

    # Event Handler
    def _on_home_clicked(self):
        self.notify_controller("on_home_requested")
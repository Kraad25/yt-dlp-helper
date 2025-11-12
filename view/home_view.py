import tkinter as tk
from tkinter import ttk

from typing import Optional
from view.BaseView import BaseView
from view.theme import AppTheme
from view.custom_entry import CustomEntry

class HomeView(BaseView):
    def __init__(self, parent: tk.Widget, controller: Optional[None]):
        self.theme = AppTheme()
        self._mode_var = tk.IntVar(value=1)  # Default to Mp3

        self.url_entry = None
        self.folder_entry = None
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

        self._create_header()
        self._create_input_section()
        self._create_mode_section()
        self._create_metadata_section()
        self._create_progress_section()
        self._create_action_buttons()

    def _bind_events(self):
        if self.folder_entry:
             self.folder_entry.entry.bind("<Return>", self._on_folder_entry_return)

    def _create_header(self):
        title = ttk.Label(self, 
                          text="Youtube Converter", 
                          font=("Helvetica", 16), 
                          background=self.theme.get_background_color()
                        ).place(x=195, y=20)

    def _create_input_section(self):
        ttk.Label(self,
                  text="URL:", 
                  font=("Helvetica", 13), 
                  background=self.theme.get_background_color()
                ).place(x=30, y=80)
        self.url_entry = CustomEntry(self, width=70, posx=85, posy=80)
        self.url_entry.make_entry()

        ttk.Label(self,
                  text="Folder:", 
                  font=("Helvetica", 13), 
                  background=self.theme.get_background_color()
                ).place(x=30, y=120)
        self.folder_entry = CustomEntry(self, width=70, posx=85, posy=120)
        self.folder_entry.make_entry()

        browse_button = tk.Button(self,
                                  text="📁", 
                                  font=("Arial", 12), 
                                  padx=1, 
                                  pady=1, 
                                  bd=0, 
                                  command=lambda: self._on_browse_clicked()
                                )
        browse_button.place(x=520, y=116)

    def _create_mode_section(self):
        mode_button_mp3 = tk.Radiobutton(self, 
                                         text="Mp3 🎵", 
                                         variable=self._mode_var, 
                                         value=1, 
                                         bg=self.theme.get_background_color(), 
                                         activebackground=self.theme.get_background_color()
                                        )
        mode_button_mp4 = tk.Radiobutton(self, 
                                         text="Mp4 🎬", 
                                         variable=self._mode_var, 
                                         value=2, 
                                         bg=self.theme.get_background_color(),
                                         activebackground=self.theme.get_background_color()
                                        )
        mode_button_mp3.place(x=30, y=160)
        mode_button_mp4.place(x=100, y=160)

    def _create_metadata_section(self):
        metadata_frame = tk.LabelFrame(self,
                                       text="Metadata (Optional)",
                                       width=500,
                                       height=150,
                                       bg=self.theme.get_secondary_color(),
                                       fg="black",
                                       font=("Arial", 10, "italic bold"),
                                       bd=5,
                                       relief="ridge"
                                      )
        metadata_frame.place(x=30, y=200)
        metadata_frame.pack_propagate(False)

        ttk.Label(metadata_frame,
                  text="Artist :", 
                  background=self.theme.get_secondary_color()
                ).place(x=20, y=20)
        self.artist_entry = CustomEntry(metadata_frame, width=65, posx=70, posy=20)
        self.artist_entry.make_entry()

        ttk.Label(metadata_frame,
                  text="Album :", 
                  background=self.theme.get_secondary_color()
                ).place(x=20, y=60)
        self.album_entry = CustomEntry(metadata_frame, width=65, posx=70, posy=60)
        self.album_entry.make_entry()

    def _create_progress_section(self):
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.place(x=30, y=400)

        ttk.Label(self, 
                  text="Status: ", 
                  background=self.theme.get_background_color(), 
                  font=("Segoe UI", 12, "italic")
                ).place(x=180, y=450)
        self.status_entry = CustomEntry(self, width=20, posx=230, posy=453)
        self.status_entry.make_entry()

    def _create_action_buttons(self):
        download_button = ttk.Button(self, text="Download", width=20, command=lambda: self._on_download_clicked())
        download_button.place(x=125, y=525)

        metadata_button = ttk.Button(self, text="Edit Metadata", width=20, command=lambda: self._on_metadata_clicked())
        metadata_button.place(x=300, y=525)


    # Event Handlers

    def _on_download_clicked(self):
        print("You have Clicked Downlaod")
        # data = self.get_form_data()
        # self.notify_controller("on_download_requested", data=data)
    

    def _on_metadata_clicked(self):
        data = self.get_form_data()
        self.notify_controller("on_metadata_edit_requested", data=data)

    def _on_browse_clicked(self):
        self.notify_controller("on_browse_folder_requested")

    def _on_folder_entry_return(self, event):
        folder_name = self.folder_entry.get_entry_text()
        self.notify_controller("on_folder_name_provided", name=folder_name)

    # Public Methods

    def get_form_data(self):
        return {
            "url": self.url_entry.get_entry_text() if self.url_entry else "",
            "folder": self.folder_entry.get_entry_text() if self.folder_entry else "",
            "mode": "mp3" if self._mode_var.get() == 1 else "mp4",
            "artist": self.artist_entry.get_entry_text() if self.artist_entry else "",
            "album": self.album_entry.get_entry_text() if self.album_entry else ""
        }

    def set_folder_path(self, path: str):
        if self.folder_entry:
            self.folder_entry.set_entry_text(path)

    def update_progress(self, value: int):
        if self.progress_bar:
            self.progress_bar['value'] = value

    def update_status(self, status: str):
        if self.status_entry:
            self.status_entry.set_entry_text(status)

    def reset_form(self):
        if self.url_entry:
            self.url_entry.set_entry_text("")
        if self.artist_entry:
            self.artist_entry.set_entry_text("")
        if self.album_entry:
            self.album_entry.set_entry_text("")
            
        self._mode_var.set(1)
        self.update_progress(0)
        self.update_status("Ready")


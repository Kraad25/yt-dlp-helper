import tkinter as tk
from tkinter import ttk

from typing import Optional
from view.BaseView import BaseView
from view.theme import AppTheme
from view.custom_entry import CustomEntry

class MetadataView(BaseView):
    def __init__(self, parent: tk.Widget, controller: Optional[None]):
        self.theme = AppTheme()
        self.filename_var = tk.IntVar(value=1)

        self.folder_path_entry = None
        self.artist_entry = None
        self.album_entry = None
        self.progress_bar = None
        self.status_entry = None
        self.button_data = {}

        self.root = parent
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
        self._show_progess_state()

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
                                      variable=self.filename_var, 
                                      value=1, 
                                      bg=self.theme.get_background_color(), 
                                      activebackground=self.theme.get_background_color()
                                    )
        title_album = tk.Radiobutton(self,
                                     text="Title - Album", 
                                     variable=self.filename_var, 
                                     value=2, 
                                     bg=self.theme.get_background_color(), 
                                     activebackground=self.theme.get_background_color()
                                )
        title = tk.Radiobutton(self,
                               text="Title", 
                               variable=self.filename_var,
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
        self.title_entry = CustomEntry(editing_frame, 50, 90, 20)
        self.title_entry.make_entry()
        
        self.back_button = ttk.Button(editing_frame, text="Back", command=lambda:self._on_back_clicked())
        self.next_button = ttk.Button(editing_frame, text="Next", command=lambda:self._on_next_clicked())
        finish_button = ttk.Button(editing_frame, text="Finish Editing", command=lambda:self._on_finish_clicked())

        
        start_button = ttk.Button(editing_frame, 
                                  text="Start Editing", 
                                  command=lambda: self._on_start_editing_clicked()
                                )
        
        self.button_data = {"back": self.back_button,
                            "next": self.next_button,
                            "finish": finish_button,
                            "label": file_label,
                            "title_entry": self.title_entry,
                            "start": start_button
                            }

    def _show_progess_state(self):
        ttk.Label(self, 
                  text="Status: ", 
                  background=self.theme.get_background_color(), 
                  font=("Segoe UI", 12, "italic")
                ).place(x=180, y=500)
        self.status_entry = CustomEntry(self, width=20, posx=230, posy=503)
        self.status_entry.make_entry()

    def _get_data(self):
        return {"title": self.title_entry.get_entry_text(),
                "filename_type": self.filename_var.get()
            }
    
    def _get_preset_data(self):
        return {"folder_path": self.folder_path_entry.get_entry_text(),
                "artist" : self.artist_entry.get_entry_text(),
                "album": self.album_entry.get_entry_text()
                }
    
    # Public Methods
    def set_folder_path(self, folder_path):
        self.folder_path_entry.set_entry_text(folder_path)

    def set_artist(self, artist):
        self.artist_entry.set_entry_text(artist)
        
    def set_album(self, album):
        self.album_entry.set_entry_text(album)

    def set_title(self, title):
        self.title_entry.set_entry_text(title)

    def set_next_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.next_button.config(state=state)

    def set_back_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.back_button.config(state=state)

    def update_status(self, status):
        self.status_entry.set_entry_text(status)

    def start_editing_success(self):
        self.button_data["start"].place_forget()

        self.button_data["title_entry"].show_entry()
        self.button_data["label"].place(x=50, y=20)
        self.button_data["back"].place(x=110, y=90)
        self.button_data["next"].place(x=210, y=90)
        self.button_data["finish"].place(x=310, y=90)

    def reset_wizard_state(self):
        self.button_data["start"].place(x=200, y=90)

        self.button_data["label"].place_forget()
        self.button_data["back"].place_forget()
        self.button_data["next"].place_forget()
        self.button_data["finish"].place_forget()
        
        self.button_data["title_entry"].hide_entry()

        self.update_status("Ready")


    # Event Handler
    def _on_home_clicked(self):
        self.notify_controller("on_home_requested")

    def _on_start_editing_clicked(self):      
        preset_data = self._get_preset_data()
        self.notify_controller("on_start_editing", data=preset_data)

    def _on_next_clicked(self):
        data = self._get_data()
        self.notify_controller("on_next", data=data)

    def _on_back_clicked(self):
        data = self._get_data()
        self.notify_controller("on_back", data=data)

    def _on_finish_clicked(self):
        data = self._get_data()
        self.notify_controller("on_finish", data=data)
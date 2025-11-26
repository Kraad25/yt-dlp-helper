import tkinter as tk
from tkinter import ttk

from typing import Callable


from view.BaseView import BaseView
from view.theme import AppTheme
from view.custom_entry import CustomEntry
from view.custom_combobox import CustomComboBox

class Mode:
    MP3 = 1
    MP4 = 2

class HomeView(BaseView):
    def __init__(self, parent: tk.Widget):
        self.theme = AppTheme()
        self.__mode_var = tk.IntVar(value=Mode.MP3)  # Default to Mp3

        self.__url_entry = None
        self.__folder_entry = None
        self.__artist_entry = None
        self.__album_entry = None
        self.__progress_bar = None
        self.__status_entry = None

        self.__download_controller = None
        self.__folder_controller = None        

        self.__show_metadata: Callable = None
        self.root = parent
        super().__init__(parent)


    # Public Methods
    def set_controllers(self, download_controller, folder_controller, metadata_callback: Callable):
        self.__download_controller = download_controller
        self.__folder_controller = folder_controller
        self.__show_metadata = metadata_callback

    def set_folder_path(self, path: str):
        if self.__folder_entry:
            self.__folder_entry.set_entry_text(path)

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
    def _on_download_clicked(self):
        data = self._get_form_data()
        folder = data.get("folder", "")
        
        self.__folder_controller.enter_folder_name(folder)
        path = self.__folder_controller.provide_full_path()

        self.__download_controller.download_requested(data, path,
                                                      self.set_download_enabled, 
                                                      self.update_progress,
                                                      self.update_status
                                                    )
    
    def _on_metadata_clicked(self):
        data = self._get_form_data()
        self.__show_metadata(data)

    def _on_browse_clicked(self):
        self.__folder_controller.browse_folder()

    def _on_folder_entry_return(self, event):
        folder_name = self.__folder_entry.get_entry_text()
        self.__folder_controller.enter_folder_name(folder_name)

    # Private Methods
    def _setup_style(self):
        style = ttk.Style()
        style.configure("Beige.TFrame", background=self.theme.get_background_color())
        style.configure("Grey.TLabelframe", background=self.theme.get_secondary_color(), borderwidth=2, relief="solid")
        style.configure("Grey.TLabelframe.Label", background=self.theme.get_secondary_color(), font=("Segoe UI", 10))

    def _create_widgets(self):
        self.configure(style="Beige.TFrame")

        self.__title = self._create_header()
        self.__url_entry = self._creat_url_input()
        self.__folder_entry, self.__browse_button = self._create_folder_input()
        self.__mp3_radio, self.__mp4_radio = self._create_mode_section()
        self.__quality_selector = self._create_quality_section()
        self.__metadata_frame, self.__artist_entry, self.__album_entry = self._create_metadata_section()
        self.__progress_bar, self.__status_entry = self._create_progress_section()
        self.__download_button, self.__metadata_button, self.__reset_button = self._create_action_buttons()
        
        self.update_status("Ready")

    def _bind_events(self):
        if self.__folder_entry:
             self.__folder_entry.entry.bind("<Return>", self._on_folder_entry_return)

    def _create_header(self):
        label = ttk.Label(self, 
                          text="Youtube Converter", 
                          font=("Helvetica", 16), 
                          background=self.theme.get_background_color()
                        ).place(x=195, y=20)
        return label

    def _creat_url_input(self):
        label = ttk.Label(self,
                  text="URL:", 
                  font=("Helvetica", 13), 
                  background=self.theme.get_background_color()
                ).place(x=30, y=80)
        entry = CustomEntry(self, width=70, posx=85, posy=80)
        entry.make_entry()

        return entry
    
    def _create_folder_input(self):
        label = ttk.Label(self,
                  text="Folder:", 
                  font=("Helvetica", 13), 
                  background=self.theme.get_background_color()
                ).place(x=30, y=120)
        entry = CustomEntry(self, width=70, posx=85, posy=120)
        entry.make_entry()

        browse_button = tk.Button(self,
                                  text="📁", 
                                  font=("Arial", 12), 
                                  padx=1, 
                                  pady=1, 
                                  bd=0, 
                                  command=lambda: self._on_browse_clicked()
                                )
        browse_button.place(x=520, y=116)

        return entry, browse_button

    def _create_mode_section(self):
        mode_button_mp3 = tk.Radiobutton(self, 
                                         text="Mp3 🎵", 
                                         variable=self.__mode_var, 
                                         value=1, 
                                         bg=self.theme.get_background_color(), 
                                         activebackground=self.theme.get_background_color(),
                                         command=lambda: self._mode_changed()
                                        )
        mode_button_mp4 = tk.Radiobutton(self, 
                                         text="Mp4 🎬", 
                                         variable=self.__mode_var, 
                                         value=2, 
                                         bg=self.theme.get_background_color(),
                                         activebackground=self.theme.get_background_color(),
                                         command=lambda: self._mode_changed()
                                        )
        mode_button_mp3.place(x=30, y=160)
        mode_button_mp4.place(x=100, y=160)

        return mode_button_mp3, mode_button_mp4

    def _create_quality_section(self):
        label = ttk.Label(self,
                  text="Quality:", 
                  font=("Helvetica", 13), 
                  background=self.theme.get_background_color()
                ).place(x=30, y=200)
        
        quality_selector = CustomComboBox(self, self.__mode_var, 100, 200)
        quality_selector.make_combobox()

        return quality_selector

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
        metadata_frame.place(x=30, y=240)
        metadata_frame.pack_propagate(False)

        ttk.Label(metadata_frame,
                  text="Artist :", 
                  background=self.theme.get_secondary_color()
                ).place(x=20, y=20)
        artist_entry = CustomEntry(metadata_frame, width=65, posx=70, posy=20)
        artist_entry.make_entry()

        ttk.Label(metadata_frame,
                  text="Album :", 
                  background=self.theme.get_secondary_color()
                ).place(x=20, y=60)
        album_entry = CustomEntry(metadata_frame, width=65, posx=70, posy=60)
        album_entry.make_entry()

        return metadata_frame, artist_entry, album_entry

    def _create_progress_section(self):
        progress_bar = ttk.Progressbar(self, orient="horizontal", length=500, mode="determinate")
        progress_bar.place(x=30, y=400)

        ttk.Label(self, 
                  text="Status: ", 
                  background=self.theme.get_background_color(), 
                  font=("Segoe UI", 12, "italic")
                ).place(x=180, y=450)
        status_entry = CustomEntry(self, width=20, posx=230, posy=453)
        status_entry.make_entry()

        return progress_bar, status_entry

    def _create_action_buttons(self):
        download_button = ttk.Button(self, text="Download", width=20, command=lambda: self._on_download_clicked())
        download_button.place(x=125, y=525)

        metadata_button = ttk.Button(self, text="Edit Metadata", width=20, command=lambda: self._on_metadata_clicked())
        metadata_button.place(x=300, y=525)

        reset_button = ttk.Button(self, text="Reset Entries", width=20, command=lambda: self._reset_form())
        reset_button.place(x=213, y=560)

        return download_button, metadata_button, reset_button

    def _reset_form(self):
        if self.__url_entry:
            self.__url_entry.set_entry_text("")
        if self.__artist_entry:
            self.__artist_entry.set_entry_text("")
        if self.__album_entry:
            self.__album_entry.set_entry_text("")
            
        self.__mode_var.set(Mode.MP3)
        self.update_progress(0)
        self.update_status("Ready")

    def _mode_changed(self):
        mode = "mp3" if self.__mode_var.get()==Mode.MP3 else "mp4"
        self.__quality_selector.switch_mode(mode)

    def _get_form_data(self):
        return {
            "url": self.__url_entry.get_entry_text() if self.__url_entry else "",
            "folder": self.__folder_entry.get_entry_text() if self.__folder_entry else "",
            "mode": "mp3" if self.__mode_var.get() == 1 else "mp4",
            "quality": self.__quality_selector.get_value(),
            "artist": self.__artist_entry.get_entry_text() if self.__artist_entry else "",
            "album": self.__album_entry.get_entry_text() if self.__album_entry else ""
        }
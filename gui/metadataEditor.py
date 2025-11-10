import tkinter as tk
from tkinter import ttk

from data import Data
from folderManger import FolderManager

class MetadataEditor(ttk.Frame):
    def __init__(self, parent, app):
        self.data = Data()
        self.folderManager = FolderManager()
        self.app = app

        style = ttk.Style()
        style.configure("Beige.TFrame", background=self.data.get_background_color())
        style.configure("Grey.TLabelframe", background=self.data.get_secondary_color(), borderwidth=2, relief="solid")
        style.configure("Grey.TLabelframe.Label", background=self.data.get_secondary_color(), font=("Segoe UI", 10))

        super().__init__(parent, style="Beige.TFrame")

        self._setup_ui()

    def _setup_ui(self):
        self._setup_header_section()
        self._setup_home_button()
        self._show_presets()
        #self._setup_metadata_fields()
        # self._setup_action_buttons()

    def _setup_header_section(self):
        title_label = ttk.Label(self, text="Metadata Editor", font=("Helvetica", 16), background=self.data.get_background_color())
        title_label.place(x=200, y=20)

    def _setup_home_button(self):
        home_button = tk.Button(self, text="🏠", font=("Arial", 13), padx=1, pady=1, bd=0, command=lambda:self.app.switch_frame(self.app.home))
        home_button.place(x=10, y=10)

    def _show_presets(self):
        preset_label = ttk.Label(self, text="Presets",font=("Helvetica", 13, "bold") ,background=self.data.get_background_color())
        preset_label.place(x=30, y=80)

        folder_label = ttk.Label(self, text="Folder Path: ",font=("Helvetica", 12) ,background=self.data.get_background_color())
        folder_label.place(x=30, y=120)
        self.folder_path_entry = ttk.Entry(self, width=50)
        self.folder_path_entry.place(x=130, y=120)
        self.folder_path_entry.insert(0, self.folderManager.get_full_path())

    def _setup_metadata_fields(self):
        editor_frame = tk.LabelFrame(self,                                                
                                    text="Metadata (Optional)",
                                    width=500,
                                    height=200,
                                    bg=self.data.get_secondary_color(),
                                    fg="black",
                                    font=("Ariel", 10, "italic bold"),
                                    bd=5,               # borderwidth
                                    relief="ridge"      # ridge, groove, sunken, raised, flat, solid
                        )
        editor_frame.place(x=30, y=100)
        editor_frame.pack_propagate(False)

        #self._populate_mode_frame(editor_frame)    
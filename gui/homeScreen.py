import tkinter as tk
from tkinter import ttk, filedialog

from data import Data

class HomeScreen(ttk.Frame):
    def __init__(self, parent, app):
        self.data = Data()

        style = ttk.Style()
        style.configure("Beige.TFrame", background=self.data.get_background_color())
        style.configure("Grey.TLabelframe", background=self.data.get_secondary_color(), borderwidth=2, relief="solid")
        style.configure("Grey.TLabelframe.Label", background=self.data.get_secondary_color(), font=("Segoe UI", 10))

        
        super().__init__(parent, style="Beige.TFrame")
        self.mode_var = tk.IntVar(value=1)  # Default to Mp3
        self.base_dir = "/"

        self._setup_ui()

    def _setup_ui(self):
        self._setup_header_section()
        self._setup_input_section()
        self._setup_mode_section()
        self._setup_action_buttons()
        self._setup_status_progress_bar()
        self._setup_mode_frame()

    def _setup_header_section(self):
        title_label = ttk.Label(self, text="Youtube Converter", font=("Helvetica", 16), background=self.data.get_background_color())
        title_label.place(x=195, y=20)

    def _setup_input_section(self):
        url_label = ttk.Label(self, text="URL:",font=("Helvetica", 13) ,background=self.data.get_background_color())
        url_label.place(x=30, y=80)
        self.url_entry = ttk.Entry(self, width=70)
        self.url_entry.place(x=85, y=80)

        folder_label = ttk.Label(self, text="Folder:",font=("Helvetica", 13) ,background=self.data.get_background_color())
        folder_label.place(x=30, y=120)
        self.folder_entry = ttk.Entry(self, width=70)
        self.folder_entry.place(x=85, y=120)

        browse_button = tk.Button(self, text="📁", font=("Arial", 12), padx=1, pady=1, bd=0, command=lambda:self._browse_folder(self.folder_entry))
        browse_button.place(x=520, y=116)

    def _setup_mode_section(self):
        mode_button_mp3 = tk.Radiobutton(self, text="Mp3 🎵", variable=self.mode_var, value=1, bg=self.data.get_background_color(), 
                                     activebackground=self.data.get_background_color())
        mode_button_mp4 = tk.Radiobutton(self, text="Mp4 🎬", variable=self.mode_var, value=2, bg=self.data.get_background_color(),
                                         activebackground=self.data.get_background_color())
        mode_button_mp3.place(x=30, y=160)
        mode_button_mp4.place(x=100, y=160)

    def _setup_action_buttons(self):
        download_button = ttk.Button(self, text="Download", width=20)
        download_button.place(x=125, y=525)

        metadata_button = ttk.Button(self, text="Edit Metadata", width=20)
        metadata_button.place(x=300, y=525)

    def _setup_status_progress_bar(self):
        self.progress_bar = ttk.Progressbar(self, orient="horizontal", length=500, mode="determinate")
        self.progress_bar.place(x=30, y=400)

        self.status_label = ttk.Label(self, text="Status: Idle", background=self.data.get_background_color(), font=("Segoe UI", 12, "italic"))
        self.status_label.place(x=230, y=450)


    def _setup_mode_frame(self):
        mode_frame = tk.LabelFrame(self,                                                
                                    text="Metadata (Optional)",
                                    width=500,
                                    height=150,
                                    bg=self.data.get_secondary_color(),
                                    fg="black",
                                    font=("Ariel", 10, "italic bold"),
                                    bd=5,               # borderwidth
                                    relief="ridge"      # ridge, groove, sunken, raised, flat, solid
)
        mode_frame.place(x=30, y=200)
        mode_frame.pack_propagate(False)

        self._populate_mode_frame(mode_frame)

    def _populate_mode_frame(self, frame):
        ttk.Label(frame, text="Artist :", background=self.data.get_secondary_color()).place(x=20, y=20)
        ttk.Entry(frame, width=65).place(x=70, y=20)

        ttk.Label(frame, text="Album :", background=self.data.get_secondary_color()).place(x=20, y=60)
        ttk.Entry(frame, width=65).place(x=70, y=60)

    
    def _browse_folder(self, folder_entry):
        folder = filedialog.askdirectory(initialdir="/", title="Choose Folder")
        if folder:
            self.base_dir = folder
            folder_entry.delete(0, tk.END)
            folder_entry.insert(0, f"{self.base_dir}")
import tkinter as tk
from tkinter import ttk
from typing import Callable

from view.BaseView import BaseView
from view.custom_combobox import CustomComboBox
from view.custom_entry import CustomEntry
from view.theme import AppTheme

from controller.folder_controller import FolderController
from controller.explore_controller import ExploreController

from PIL import ImageTk

class Mode:
    MP3 = 1
    MP4 = 2

class ExplorerView(BaseView):
    def __init__(self, parent: tk.Widget):
        self._theme = AppTheme()
        self._mode_var = tk.IntVar(value=Mode.MP3)  # Default to Mp3
        self._quality_selector = None

        self._folder_entry = None
        self._url_entry = None
        self._results_frame = None
        self._status_label = None

        self._thumb_refs = []

        self._explore_controller: ExploreController = None
        self._folder_controller: FolderController = None

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, explore_controller: ExploreController, folder_controller: FolderController):
        self._explore_controller = explore_controller
        self._folder_controller = folder_controller

    def set_base_folder_path(self, path: str):
        if self._folder_entry:
            self._folder_entry.set_entry_text(path)

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

        self._title = self._create_header()
        self._folder_entry, self._browse_button = self._create_base_folder_input()
        self._mp3_radio, self._mp4_radio = self._create_mode_section()
        self._quality_selector = self._create_quality_section()
        self._youtube_section, self._url_entry = self._create_youtube_section()
        self._status_label = self._create_status_label()

    def _create_header(self):
        label = ttk.Label(
            self,
            text="Explore Youtube and Download",
            font=("Helvetica", 16),
            background=self._theme.get_background_color()
        ).place(x=135, y=20)
        return label

    def _create_base_folder_input(self):
        label = ttk.Label(
            self,
            text="Dest:",
            font=("Helvetica", 13),
            background=self._theme.get_background_color()
        ).place(x=30, y=80)

        entry = CustomEntry(self, width=70, posx=85, posy=80,
                            placeholder="Select Destination folder for downloads"
        )
        entry.make_entry()

        browse_button = tk.Button(
            self,
            text="📁",
            font=("Arial", 12),
            padx=1,
            pady=1,
            bd=0,
            command=lambda: self._on_browse_clicked()
        )
        browse_button.place(x=520, y=76)

        return entry, browse_button

    def _create_mode_section(self):
        mode_button_mp3 = tk.Radiobutton(
            self,
            text="Mp3 🎵",
            variable=self._mode_var,
            value=1,
            bg=self._theme.get_background_color(),
            activebackground=self._theme.get_background_color(),
            command=lambda: self._on_mode_change()
        )
        mode_button_mp4 = tk.Radiobutton(
            self,
            text="Mp4 🎬",
            variable=self._mode_var,
            value=2,
            bg=self._theme.get_background_color(),
            activebackground=self._theme.get_background_color(),
            command=lambda: self._on_mode_change()
        )
        mode_button_mp3.place(x=70, y=127)
        mode_button_mp4.place(x=140, y=127)

        return mode_button_mp3, mode_button_mp4

    def _create_quality_section(self):
        label = ttk.Label(
            self,
            text="Quality:",
            font=("Helvetica", 13),
            background=self._theme.get_background_color()
        ).place(x=250, y=127)

        quality_selector = CustomComboBox(self, self._mode_var, 315, 127)
        quality_selector.make_combobox()

        return quality_selector

    def _create_youtube_section(self):
        results_container = tk.LabelFrame(
            self,
            width=500,
            height=400,
            bg=self._theme.get_secondary_color(),
            fg="black",
            font=("Arial", 10, "italic bold"),
            bd=5,
            relief="ridge"
        )
        results_container.place(x=30, y=170)
        results_container.pack_propagate(False)

        url_entry = CustomEntry(results_container, width=65, posx=50, posy=10, placeholder="Search in Youtube")
        search_entry_widget = url_entry.make_entry()
        search_entry_widget.bind("<Return>", lambda e: self._on_search_clicked())

        search_button = tk.Button(
            self,
            text="🔍",
            font=("Arial", 11),
            padx=0,
            pady=0,
            bd=0,
            command=lambda: self._on_search_clicked()
        )
        search_button.place(x=490, y=183)

        self._create_results_area(results_container)

        return results_container, url_entry

    def _create_results_area(self, parent_frame):
        canvas = tk.Canvas(parent_frame, background=self._theme.get_secondary_color(),
                            highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent_frame, orient="vertical", command=canvas.yview)
        results_frame = tk.Frame(canvas, background=self._theme.get_secondary_color())

        results_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.place(x=10, y=50, width=460, height=335)
        scrollbar.place(x=470, y=50, height=335)

        self._results_frame = results_frame

    def _create_status_label(self):
        label = ttk.Label(
            self,
            text="Type something and hit search",
            background=self._theme.get_background_color(),
            font=("Segoe UI", 9, "italic"),
        )
        label.place(x=30, y=577)
        return label

    # Event Handlers
    def _on_browse_clicked(self):
        self._folder_controller.browse_folder()

    def _on_mode_change(self):
        mode = "mp3" if self._mode_var.get() == Mode.MP3 else "mp4"
        self._quality_selector.switch_mode(mode)

    def _on_search_clicked(self):
        query = self._url_entry.get_entry_text()
        if not query:
            return

        self._clear_results()
        self._status_label.config(text=f"Searching for '{query}'...")
        self._explore_controller.search(query, self._on_results_ready, self._on_search_error)

    def _on_results_ready(self, results: list):
        if not results:
            self._status_label.config(text="No results found.")
            return
        self._status_label.config(text=f"{len(results)} results")
        for entry in results:
            self._render_result_row(entry)

    def _on_search_error(self, error_message: str):
        self._status_label.config(text=f"Search failed: {error_message}")

    def _clear_results(self):
        self._thumb_refs.clear()
        for widget in self._results_frame.winfo_children():
            widget.destroy()

    def _render_result_row(self, entry: dict):
        row = tk.Frame(self._results_frame, background=self._theme.get_secondary_color(), padx=4, pady=4)
        row.pack(fill="x", pady=2)

        thumb_label = tk.Label(row, text="...", width=14, height=4,
                                bg=self._theme.get_background_color())
        thumb_label.pack(side="left", padx=(0, 8))

        thumbnail_url = entry.get("thumbnail_url")
        self._explore_controller.get_thumbnail(
            thumbnail_url, self, lambda image, lbl=thumb_label: self._apply_thumbnail(lbl, image)
        )

        text_frame = tk.Frame(row, background=self._theme.get_secondary_color())
        text_frame.pack(side="left", fill="both", expand=True)

        title = entry.get("title", "Untitled")
        channel = entry.get("channel", "Unknown channel")
        duration = entry.get("duration")
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else ""

        tk.Label(text_frame, text=title, font=("Segoe UI", 9, "bold"), wraplength=280,
                 background=self._theme.get_secondary_color(), justify="left").pack(anchor="w")
        
        tk.Label(text_frame, text=f"{channel}  •  {duration_str}", font=("Segoe UI", 8),
                 background=self._theme.get_secondary_color()).pack(anchor="w")

        for widget in (row, thumb_label, text_frame):
            widget.bind("<Button-1>", lambda e, data=entry: self._on_result_clicked(data))

    def _apply_thumbnail(self, label: tk.Label, image):
        if image is None:
            label.config(text="No\nImage")
            return
        photo = ImageTk.PhotoImage(image)
        self._thumb_refs.append(photo)
        label.config(image=photo, text="", width=0, height=0)

    def _on_result_clicked(self, entry: dict):
        base_path = self._folder_entry.get_entry_text()
        if not base_path:
            self._status_label.config(text="Set a destination folder first.")
            return

        mode = "mp3" if self._mode_var.get() == Mode.MP3 else "mp4"
        quality = self._quality_selector.get_value()
        url = entry.get("url")
        title = entry.get("title", "this video")

        self._status_label.config(text=f"Downloading: {title}")
        self._explore_controller.download(
            url, mode, quality, base_path,
            update_status=self._on_download_status,
        )

    def _on_download_status(self, status: str):
        self._status_label.config(text=status)
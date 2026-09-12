import customtkinter
from typing import Callable

from view.BaseView import BaseView
from view.custom_combobox import CustomComboBox

from controller.folder_controller import FolderController
from controller.explore_controller import ExploreController

class Mode:
    MP3 = 1
    MP4 = 2

class ExplorerView(BaseView):

    ROW_HEADER = 0
    ROW_DEST_LABEL = 1
    ROW_DEST_ROW = 2
    ROW_MODE_QUALITY = 3
    ROW_RESULTS = 4
    ROW_STATUS = 5

    def __init__(self, parent):
        self._mode_var = customtkinter.IntVar(value=Mode.MP3)
        self._seg_button_var = customtkinter.StringVar(value="🎵 Mp3")

        self._destination_entry = None
        self._browse_button = None
        self._quality_selector = None
        self._search_entry = None
        self._results_frame = None
        self._status_label = None
        self._context_menu = None

        self._thumb_refs = []

        self._explore_controller: ExploreController = None
        self._folder_controller: FolderController = None

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, explore_controller: ExploreController, folder_controller: FolderController):
        self._explore_controller = explore_controller
        self._folder_controller = folder_controller

    def set_base_folder_path(self, path: str):
        if self._destination_entry:
            self._destination_entry.delete(0, "end")
            self._destination_entry.insert(0, path)

    # Private Methods
    def _setup_style(self):
        pass # CTk widgets are themed via themes/warm_refined.json

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(self.ROW_RESULTS, weight=1)

        self._title = self._create_header()
        self._destination_entry, self._browse_button = self._create_destination_input()
        self._mode_segmented, self._quality_selector = self._create_mode_and_quality()        
        self._results_frame, self._search_entry = self._create_results_area()
        self._status_label = self._create_status_label()
        self._context_menu = self._create_context_menu()

    def _create_header(self):
        title_label = customtkinter.CTkLabel(
            self,
            text="Explore YouTube",
            font=customtkinter.CTkFont(size=18, weight="bold"),
        )
        title_label.grid(row=self.ROW_HEADER, column=0, pady=(20, 15))

        return title_label

    def _create_destination_input(self):
        destination_label = customtkinter.CTkLabel(self, text="Destination", font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray50")
        destination_label.grid(row=self.ROW_DEST_LABEL, column=0, sticky="w", padx=30)

        dest_row = customtkinter.CTkFrame(self, fg_color="transparent")
        dest_row.grid(row=self.ROW_DEST_ROW, column=0, sticky="ew", padx=30, pady=(2, 15))
        dest_row.grid_columnconfigure(0, weight=1)
        dest_row.grid_columnconfigure(1, weight=0)

        destination_entry = customtkinter.CTkEntry(dest_row, placeholder_text="Select download destination")
        destination_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        browse_button = customtkinter.CTkButton(
            dest_row,
            text="📁",
            width=32,
            height=28,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._on_browse_clicked,
        )
        browse_button.grid(row=0, column=1, sticky="e")

        return destination_entry, browse_button

    def _create_mode_and_quality(self):
        group = customtkinter.CTkFrame(self, fg_color="transparent")
        group.grid(row=self.ROW_MODE_QUALITY, column=0, sticky="w", padx=30, pady=(0, 15))

        segmented_button = customtkinter.CTkSegmentedButton(
            group,
            values=["🎵 Mp3", "🎬 Mp4"],
            variable=self._seg_button_var,
            command=self._on_segmented_change,
            width=180,
            height=36,
            font=customtkinter.CTkFont(size=14, weight="bold"),
        )
        segmented_button.grid(row=0, column=0, sticky="w")

        quality_label = customtkinter.CTkLabel(group, text="Quality", font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray50")
        quality_label.grid(row=0, column=1, sticky="e", padx=(30, 0))

        quality_selector = CustomComboBox(group, self._mode_var, width=130)
        quality_selector.widget.grid(row=0, column=2, sticky="w", padx=(15, 0))

        return segmented_button, quality_selector

    def _create_results_area(self):
        panel = customtkinter.CTkFrame(self, fg_color=("gray88", "gray19"), corner_radius=10)
        panel.grid(row=self.ROW_RESULTS, column=0, sticky="nsew", padx=30, pady=(0, 10))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(1, weight=1)

        search_row = customtkinter.CTkFrame(panel, fg_color="transparent")
        search_row.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        search_row.grid_columnconfigure(0, weight=1)
        search_row.grid_columnconfigure(1, weight=0)

        search_entry = customtkinter.CTkEntry(search_row, placeholder_text="Search YouTube", height=32)
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        search_entry.bind("<Return>", lambda e: self._on_search_clicked())

        search_button = customtkinter.CTkButton(
            search_row, text="🔍", width=36, height=32, command=self._on_search_clicked
        )
        search_button.grid(row=0, column=1, sticky="e")

        results_frame = customtkinter.CTkScrollableFrame(panel, fg_color="transparent")
        results_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 6))
        results_frame.grid_columnconfigure(0, weight=1)

        return results_frame, search_entry

    def _create_status_label(self):
        label = customtkinter.CTkLabel(
            self,
            text="Type something and hit search",
            font=customtkinter.CTkFont(size=12, slant="italic"),
            text_color="gray50",
            anchor="w",
        )
        label.grid(row=self.ROW_STATUS, column=0, sticky="w", padx=30, pady=(0, 15))
        return label

    def _create_context_menu(self):
        import tkinter as tk
        menu = tk.Menu(self, tearoff=0)
        return menu

    # Event Handlers
    def _on_browse_clicked(self):
        self._folder_controller.browse_folder()

    def _on_segmented_change(self, value):
        self._mode_var.set(Mode.MP3 if "Mp3" in value else Mode.MP4)
        self._on_mode_change()

    def _on_mode_change(self):
        mode = "mp3" if self._mode_var.get() == Mode.MP3 else "mp4"
        self._quality_selector.switch_mode(mode)

    def _on_search_clicked(self):
        query = self._search_entry.get().strip()
        if not query:
            return

        self._clear_results()
        self._status_label.configure(text=f"Searching for '{query}'...")
        self._explore_controller.search(query, self._on_results_ready, self._on_search_error)

    def _on_results_ready(self, results: list):
        if not results:
            self._status_label.configure(text="No results found.")
            return

        self._status_label.configure(text=f"{len(results)} results")

        for index, entry in enumerate(results):
            self._render_result_row(entry, index)

    def _on_search_error(self, error_message: str):
        self._status_label.configure(text=f"Search failed: {error_message}")

    def _clear_results(self):
        self._thumb_refs.clear()
        for widget in self._results_frame.winfo_children():
            widget.destroy()

    def _render_result_row(self, entry: dict, index: int):
        row = customtkinter.CTkFrame(self._results_frame, fg_color=("gray85", "gray20"))
        row.grid(row=index, column=0, sticky="ew", pady=4, padx=2)
        row.grid_columnconfigure(1, weight=1)

        thumb_label = customtkinter.CTkLabel(row, text="...", width=112, height=63, fg_color=("gray75", "gray25"))
        thumb_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")

        thumbnail_url = entry.get("thumbnail_url")
        self._explore_controller.get_thumbnail(
            thumbnail_url, self, lambda image, lbl=thumb_label: self._apply_thumbnail(lbl, image)
        )

        text_frame = customtkinter.CTkFrame(row, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
        text_frame.grid_columnconfigure(0, weight=1)

        title = entry.get("title", "Untitled")
        channel = entry.get("channel", "Unknown channel")
        duration = entry.get("duration")
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else ""

        customtkinter.CTkLabel(
            text_frame, text=title, font=customtkinter.CTkFont(size=12, weight="bold"),
            anchor="w", justify="left", wraplength=280,
        ).grid(row=0, column=0, sticky="w")
        
        channel_label = customtkinter.CTkLabel(
            text_frame, text=f"{channel}  •  {duration_str}",
            font=customtkinter.CTkFont(size=11), text_color=("gray40", "gray60"), anchor="w", cursor="hand2",
        )
        channel_label.grid(row=1, column=0, sticky="w")
        channel_label.bind("<Button-1>", lambda e, ch=channel: self._on_channel_clicked(ch))

        for widget in (row, thumb_label, text_frame):
            widget.bind("<Button-3>", lambda e, data=entry: self._on_result_right_clicked(e, data))

    def _apply_thumbnail(self, label, image):
        if image is None:
            label.configure(text="No\nImage")
            return
        
        ctk_image = customtkinter.CTkImage(light_image=image, dark_image=image, size=(112, 63))
        self._thumb_refs.append(ctk_image)
        label.configure(image=ctk_image, text="")

    def _on_result_right_clicked(self, event, entry: dict):
        self._context_menu.delete(0, "end")
        self._context_menu.add_command(
            label=f"Download: {entry.get('title', 'this video')}",
            command=lambda: self._on_result_clicked(entry),
        )

        self._context_menu.tk_popup(event.x_root, event.y_root)

    def _on_channel_clicked(self, channel_name: str):        
        self._status_label.configure(text=f"Channel browsing for '{channel_name}' is coming soon.")

    def _on_result_clicked(self, entry: dict):
        base_path = self._destination_entry.get().strip()

        if not base_path:
            self._status_label.configure(text="Set a destination folder first.")
            return

        mode = "mp3" if self._mode_var.get() == Mode.MP3 else "mp4"
        quality = self._quality_selector.get_value()
        url = entry.get("url")
        title = entry.get("title", "this video")

        self._status_label.configure(text=f"Downloading: {title}")
        self._explore_controller.download(
            url, mode, quality, base_path,
            update_status=self._on_download_status,
        )

    def _on_download_status(self, status: str):
        self._status_label.configure(text=status)
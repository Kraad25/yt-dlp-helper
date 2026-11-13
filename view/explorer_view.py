import os

import customtkinter
from tkinter import filedialog

from view.BaseView import BaseView
from view.custom_combobox import CustomComboBox
from view.custom_dialogbox import AddWatchChannelDialog, BackFillDialog

from controller.folder_controller import FolderController
from controller.explore_controller import ExploreController

class Mode:
    MP3 = 1
    MP4 = 2

class ViewMode:
    SEARCH = "search"
    CHANNEL = "channel" 
    SECTION = "section" 

class ExplorerView(BaseView):

    # Grid layout rows
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
        self._back_button = None
        self._show_more_button = None
        self._rows_shown = 0
        self._search_entries: list[dict] = []
        self._search_has_more = False
        self._video_encoder: str = "CPU"

        self._thumb_refs = []
        self._render_generation = 0

        self._view_mode = ViewMode.SEARCH
        self._current_sections: list[dict] = []
        self._current_section_title: str = ""
        self._current_section_url: str = ""
        self._current_channel_name: str = ""

        self._explore_controller: ExploreController = None
        self._folder_controller: FolderController = None
        self._thread_dispatcher = None

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, explore_controller: ExploreController, folder_controller: FolderController):
        self._explore_controller = explore_controller
        self._folder_controller = folder_controller

        self._refresh_watchlist()        

    def set_base_folder_path(self, path: str):
        if self._destination_entry:
            self._destination_entry.delete(0, "end")
            self._destination_entry.insert(0, path)

    def set_thread_dispatcher(self, dispatcher):
        self._thread_dispatcher = dispatcher

    def set_video_encoder(self, encoder: str):
        self._video_encoder = encoder

    def update_status(self, status: str):
        if self._status_label:
            self._status_label.configure(text=status)

    # Event Handlers
    def _on_browse_clicked(self):
        selected = filedialog.askdirectory(initialdir=self._folder_controller.get_base_directory())
        self._folder_controller.store_destination_path(selected)

    def _on_segmented_change(self, value):
        self._mode_var.set(Mode.MP3 if "Mp3" in value else Mode.MP4)
        self._on_mode_change()

    def _on_show_more_clicked(self):
        self._show_more_button.configure(state="disabled")
        self.update_status("Loading more...")
        if self._view_mode == ViewMode.SECTION:
            self._explore_controller.show_more_section(
                self._thread_dispatcher.wrap(self._on_section_items_ready),
                self._thread_dispatcher.wrap(self._on_browse_error),
            )
        else:
            self._explore_controller.show_more_search(
                self._thread_dispatcher.wrap(self._on_results_ready),
                self._thread_dispatcher.wrap(self._on_search_error),
            )

    def _on_search_clicked(self):
        query = self._search_entry.get().strip()
        if not query:
            return
        
        self._set_view_mode(ViewMode.SEARCH)
        self._explore_controller.stop_section_loading()
        self._search_entries.clear()
        self._clear_results()
        self.update_status(f"Searching for '{query}'...")
        self._explore_controller.search(
            query,
            self._thread_dispatcher.wrap(self._on_results_ready),
            self._thread_dispatcher.wrap(self._on_search_error),
        )

    def _on_channel_clicked(self, channel_url: str, channel_name: str = ""):
        if not channel_url:
            self.update_status("This result has no channel link.")
            return
        
        self._explore_controller.stop_section_loading()
        self._current_channel_name = channel_name
        self._clear_results()
        self._set_view_mode(ViewMode.CHANNEL)
        self._explore_controller.browse_channel(
            channel_url,
            self._thread_dispatcher.wrap(self._on_sections_ready),
            self._thread_dispatcher.wrap(self._on_browse_error),
        )

    def _on_section_tab_clicked(self, section: dict):
        self._current_section_title = section["title"]
        self._current_section_url = section["url"]

        self._clear_results()
        self._set_view_mode(ViewMode.SECTION)
        self._render_tab_bar(active_title=section["title"])
        self.update_status(f"Loading {section['title']}...")
        self._explore_controller.browse_section(
            section["url"],
            self._thread_dispatcher.wrap(self._on_section_items_ready),
            self._thread_dispatcher.wrap(self._on_browse_error),
        )
 
    def _on_item_right_clicked(self, event, item_data: dict):
        self._context_menu.delete(0, "end")
 
        type = item_data.get("type", "video")
        if type == "playlist":
            label = f"Download release: {item_data.get('title', 'this release')}"
        else:
            label = f"Download: {item_data.get('title', 'this video')}"
 
        self._context_menu.add_command(label=label, command=lambda: self._on_download_clicked(item_data))
 
        if self._view_mode == ViewMode.SECTION:
            self._context_menu.add_separator()
            self._context_menu.add_command(
                label=f"Add '{self._current_section_title}' to watch list",
                command=self._on_add_section_to_watchlist,
            )
 
        self._context_menu.tk_popup(event.x_root, event.y_root)

    def _on_download_clicked(self, item_data: dict):
        base_path = self._destination_entry.get().strip()

        if not base_path:
            self.update_status("Set a destination folder first.")
            return

        mode = "mp3" if self._mode_var.get() == Mode.MP3 else "mp4"
        quality = self._quality_selector.get_value()
        url = item_data.get("url")
        title = item_data.get("title", "this video")
        encoder = self._video_encoder

        self.update_status(f"Downloading: {title}")
        self._explore_controller.download(
            url, mode, quality, base_path, encoder,
            update_status=self._thread_dispatcher.wrap(self.update_status),
        )

    def _on_add_section_to_watchlist(self):
        base_folder = self._destination_entry.get().strip()
        default_destination = self._folder_controller.normalize_path(os.path.join(base_folder, self._current_channel_name))
        AddWatchChannelDialog(
            self,
            channel_name=self._current_channel_name,
            section_title=self._current_section_title,
            default_destination=default_destination,
            on_confirm=self._on_watch_channel_confirmed,
        )

    # Navigation
    def _set_view_mode(self, mode: str):
        self._view_mode = mode
        if mode == ViewMode.SEARCH:
            self._back_button.grid_remove()
            self._tab_bar.grid_remove()
        else:
            self._back_button.grid()
            self._tab_bar.grid()
 
    def _on_back_clicked(self):
        self._explore_controller.stop_section_loading()
        self._clear_results()
        self._set_view_mode(ViewMode.SEARCH)
        self._restore_search_results()

    # Private Methods
    def _setup_style(self):
        pass # CTk widgets are themed via themes/warm_refined.json

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar_frame = customtkinter.CTkFrame(self, width=200)
        sidebar_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        self._setup_sidebar_grid(sidebar_frame)

        main_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew")
        self._setup_main_ui_grid(main_frame)

    def _setup_sidebar_grid(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)
        parent.grid_rowconfigure(4, weight=1)

        header = customtkinter.CTkLabel(
            parent, 
            text="Watch List", 
            font=customtkinter.CTkFont(size=16, weight="bold")
        )
        header.grid(row=0, column=0, padx=12, pady=(15, 10), sticky="n")

        active_label = customtkinter.CTkLabel(
            parent, 
            text="Active", 
            font=customtkinter.CTkFont(size=13, weight="bold"),
            text_color="gray50"
        )
        active_label.grid(row=1, column=0, padx=12, pady=(5, 2), sticky="w")

        self._active_watchlist_frame = customtkinter.CTkScrollableFrame(
            parent, 
            fg_color="transparent",
            height=180
        )
        self._active_watchlist_frame.grid(row=2, column=0, sticky="nsew", padx=5, pady=(0, 10))

        paused_label = customtkinter.CTkLabel(
            parent, 
            text="Paused", 
            font=customtkinter.CTkFont(size=13, weight="bold"),
            text_color="gray50"
        )
        paused_label.grid(row=3, column=0, padx=12, pady=(5, 2), sticky="w")

        self._paused_watchlist_frame = customtkinter.CTkScrollableFrame(
            parent, 
            fg_color="transparent",
            height=180
        )
        self._paused_watchlist_frame.grid(row=4, column=0, sticky="nsew", padx=5, pady=(0, 10))

    def _setup_main_ui_grid(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(self.ROW_RESULTS, weight=1)

        self._title = self._create_header(parent)
        self._destination_entry, self._browse_button = self._create_destination_input(parent)
        self._mode_segmented, self._quality_selector = self._create_mode_and_quality(parent)        
        self._results_frame, self._search_entry, self._back_button = self._create_results_area(parent)
        self._status_label = self._create_status_label(parent)
        self._context_menu = self._create_context_menu(parent)

    def _create_header(self, parent):
        title_label = customtkinter.CTkLabel(
            parent,
            text="Explore YouTube",
            font=customtkinter.CTkFont(size=18, weight="bold"),
        )
        title_label.grid(row=self.ROW_HEADER, column=0, pady=(20, 15))

        return title_label

    def _create_destination_input(self, parent):
        destination_label = customtkinter.CTkLabel(parent, text="Destination", font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray50")
        destination_label.grid(row=self.ROW_DEST_LABEL, column=0, sticky="w", padx=30)

        dest_row = customtkinter.CTkFrame(parent, fg_color="transparent")
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

    def _create_mode_and_quality(self, parent):
        group = customtkinter.CTkFrame(parent, fg_color="transparent")
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

    def _create_results_area(self, parent):
        panel = customtkinter.CTkFrame(parent, fg_color=("gray88", "gray19"), corner_radius=10)
        panel.grid(row=self.ROW_RESULTS, column=0, sticky="nsew", padx=30, pady=(0, 10))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)
 
        # Row 0: search bar (+ back button, hidden until browsing a channel)
        search_row = customtkinter.CTkFrame(panel, fg_color="transparent")
        search_row.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))
        search_row.grid_columnconfigure(1, weight=1)
 
        back_button = customtkinter.CTkButton(
            search_row, text="← Back", width=70, height=32,
            fg_color="transparent", border_width=1, text_color=("gray10", "gray90"),
            command=self._on_back_clicked,
        )
        back_button.grid(row=0, column=0, sticky="w", padx=(0, 8))
        back_button.grid_remove()
 
        search_entry = customtkinter.CTkEntry(search_row, placeholder_text="Search YouTube", height=32)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        search_entry.bind("<Return>", lambda e: self._on_search_clicked())
 
        search_button = customtkinter.CTkButton(
            search_row, text="🔍", width=36, height=32, command=self._on_search_clicked
        )
        search_button.grid(row=0, column=2, sticky="e")
 
        # Row 1: tab bar (Videos | Releases | Playlists | ...), hidden until a channel is browsed
        self._tab_bar = customtkinter.CTkFrame(panel, fg_color="transparent")
        self._tab_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(8, 0))
        self._tab_bar.grid_remove()

        # Row 2: "Show more" text link (hidden until there is something to load)
        self._show_more_button = customtkinter.CTkButton(
            panel,
            text="Show more",
            width=80,
            height=20,
            fg_color="transparent",
            hover=False,
            text_color=("gray40", "gray60"),
            font=customtkinter.CTkFont(size=12, underline=True),
            command=self._on_show_more_clicked,
        )
        self._show_more_button.grid(row=2, column=0, sticky="e", padx=14, pady=(4, 0))
        self._show_more_button.grid_remove()
 
        # Row 3: results / section items
        results_frame = customtkinter.CTkScrollableFrame(panel, fg_color="transparent")
        results_frame.grid(row=3, column=0, sticky="nsew", padx=6, pady=(8, 6))
        results_frame.grid_columnconfigure(0, weight=1)
 
        return results_frame, search_entry, back_button

    def _create_status_label(self, parent):
        label = customtkinter.CTkLabel(
            parent,
            text="Type something and hit search",
            font=customtkinter.CTkFont(size=12, slant="italic"),
            text_color="gray50",
            anchor="w",
        )
        label.grid(row=self.ROW_STATUS, column=0, sticky="w", padx=30, pady=(0, 15))
        return label

    def _create_context_menu(self, parent):
        import tkinter as tk
        menu = tk.Menu(parent, tearoff=0)
        return menu


    ## Helper Functions
    def _on_mode_change(self):
        mode = "mp3" if self._mode_var.get() == Mode.MP3 else "mp4"
        self._quality_selector.switch_mode(mode)

    def _on_search_error(self, error_message: str):
        self._show_more_button.configure(state="normal")
        self.update_status(f"Search failed: {error_message}")

    def _on_browse_error(self, error_message: str):
        self._show_more_button.configure(state="normal")
        self.update_status(f"Couldn't load that: {error_message}")

    ### Thumbnail rendering functions
    def _apply_thumbnail(self, label, image, generation: int):
        if generation != self._render_generation:
            return
        try:
            if not label.winfo_exists():
                return
        except Exception:
            return
 
        if image is None:
            label.configure(text="No\nImage")
            return
        ctk_image = customtkinter.CTkImage(light_image=image, dark_image=image, size=(112, 63))
        self._thumb_refs.append(ctk_image)
        label.configure(image=ctk_image, text="")

    def _load_thumbnail(self, label, thumbnail_url, generation: int):
        self._explore_controller.get_thumbnail(
            thumbnail_url, self,
            lambda image, lbl=label, gen=generation:
                self._thread_dispatcher.post(self._apply_thumbnail, lbl, image, gen),
        )

    ### Results Rendering Functions
    def _render_tab_bar(self, active_title: str = None):
        for widget in self._tab_bar.winfo_children():
            widget.destroy()
 
        for section in self._current_sections:
            is_active = section["title"] == active_title
            btn = customtkinter.CTkButton(
                self._tab_bar,
                text=section["title"],
                height=28,
                width=90,
                fg_color=("gray70", "gray30") if is_active else "transparent",
                text_color=("gray10", "gray90"),
                border_width=0 if is_active else 1,
                command=lambda s=section: self._on_section_tab_clicked(s),
            )
            btn.pack(side="left", padx=(0, 6))
 
    def _render_item_row(self, entry: dict, index: int, clickable_channel: bool):
        type = entry.get("type", "video")
 
        row = customtkinter.CTkFrame(self._results_frame, fg_color=("gray85", "gray20"))
        row.grid(row=index, column=0, sticky="ew", pady=4, padx=2)
        row.grid_columnconfigure(1, weight=1)
 
        thumb_label = customtkinter.CTkLabel(row, text="...", width=112, height=63, fg_color=("gray75", "gray25"))
        thumbnail_url = entry.get("thumbnail_url")
        generation = self._render_generation
        if thumbnail_url or type != "playlist":
            self._load_thumbnail(thumb_label, thumbnail_url, generation)
        else:
            self._explore_controller.get_playlist_cover(
                entry["url"],
                lambda cover_url, lbl=thumb_label, gen=generation:  self._thread_dispatcher.post(self._load_thumbnail, lbl, cover_url, gen),
                )
        thumb_label.grid(row=0, column=0, padx=8, pady=8, sticky="w")
 
        text_frame = customtkinter.CTkFrame(row, fg_color="transparent")
        text_frame.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=8)
        text_frame.grid_columnconfigure(0, weight=1)
 
        title = entry.get("title", "Untitled")
        customtkinter.CTkLabel(
            text_frame, text=title, font=customtkinter.CTkFont(size=12, weight="bold"),
            anchor="w", justify="left", wraplength=280,
        ).grid(row=0, column=0, sticky="w")
 
        if type == "playlist":
            subtitle = "Album / Release"
        else:
            channel = entry.get("channel", "")
            duration = entry.get("duration")
            duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else ""
            subtitle = f"{channel}  •  {duration_str}" if channel else duration_str
 
        subtitle_label = customtkinter.CTkLabel(
            text_frame, text=subtitle, font=customtkinter.CTkFont(size=11),
            text_color=("gray40", "gray60"), anchor="w",
        )
        subtitle_label.grid(row=1, column=0, sticky="w")
 
        if clickable_channel and type != "playlist":
            channel_url = entry.get("channel_url")
            channel_name = entry.get("channel", "")
            subtitle_label.configure(cursor="hand2")
            subtitle_label.bind("<Button-1>", lambda e, url=channel_url, name=channel_name: self._on_channel_clicked(url, name))
 
        for widget in (row, thumb_label, text_frame):
            widget.bind("<Button-3>", lambda e, data=entry: self._on_item_right_clicked(e, data))

    def _clear_results(self):
        self._render_generation += 1
        self._show_more_button.grid_remove()
        self._show_more_button.configure(state="normal")
        self._rows_shown = 0
        self._thumb_refs.clear()
        for widget in self._results_frame.winfo_children():
            widget.destroy()
        self._results_frame._parent_canvas.yview_moveto(0)

    def _restore_search_results(self):
        if not self._search_entries:
            self.update_status("Type something and hit search")
            return

        for entry in self._search_entries:
            self._render_item_row(entry, self._rows_shown, clickable_channel=True)
            self._rows_shown += 1

        self.update_status(f"{self._rows_shown} results")
        self._set_show_more_visible(self._search_has_more)

    def _set_show_more_visible(self, visible: bool):
        self._show_more_button.configure(state="normal")
        if visible:
            self._show_more_button.grid()
        else:
            self._show_more_button.grid_remove()
            
    ### Watch list rendering functions
    def _refresh_watchlist(self):
        self._fill_watchlist(self._active_watchlist_frame, self._explore_controller.get_watches(True))
        self._fill_watchlist(self._paused_watchlist_frame, self._explore_controller.get_watches(False))

    def _fill_watchlist(self, frame, watches: list[dict]):
        for widget in frame.winfo_children():
            widget.destroy()
        for index, watch in enumerate(watches):
            customtkinter.CTkLabel(
                frame, text=watch["section_name"], anchor="w", justify="left", wraplength=160,
            ).grid(row=index, column=0, sticky="w", padx=6, pady=2)

    ### Search event completion handlers
    def _on_results_ready(self, batch: list, has_more: bool):
        if not batch and self._rows_shown == 0:
            self.update_status("No results found")
            return

        self._search_entries.extend(batch)
        self._search_has_more = has_more

        for entry in batch:
            self._render_item_row(entry, self._rows_shown, clickable_channel=True)
            self._rows_shown += 1

        self.update_status(f"{self._rows_shown} results")
        self._set_show_more_visible(has_more)    

    def _on_sections_ready(self, sections: list):
        self._current_sections = sections
        self._render_tab_bar()
        self.update_status("Pick a tab to browse" if sections else "No sections found for this channel.")

    def _on_section_items_ready(self, items: list, has_more: bool):
        if not items and self._rows_shown == 0:
            self.update_status(f"{self._current_section_title}: nothing here yet.")
            return

        for entry in items:
            self._render_item_row(entry, self._rows_shown, clickable_channel=False)
            self._rows_shown += 1

        self.update_status(f"{self._current_section_title}: {self._rows_shown} items")
        self._set_show_more_visible(has_more)

    def _on_section_index_ready(self, items: list, truncated: bool):
        self._open_backfill_dialog(items, truncated)

    ### Section and Backfill event handlers
    def _open_backfill_dialog(self, items: list, truncated: bool):
        if not items:
            self.update_status("Nothing to back-fill here.")
            return
        
        self.update_status(f"Showing first {len(items)}" if truncated else f"{len(items)} videos found")
        BackFillDialog(
            self,
            items=items,
            on_confirm=self._on_backfill_confirmed,
        )

    def _on_watch_channel_confirmed(self, section_name, destination, auto_download, poll_interval):
        self.update_status("Loading all videos...")
        self._explore_controller.start_watch(
            section_name, destination, auto_download, poll_interval,
            self._thread_dispatcher.wrap(self._on_section_index_ready),
            self._thread_dispatcher.wrap(self._on_browse_error),
        )

    def _on_backfill_confirmed(self, selected: list):
        ticked_ids = {item["id"] for item in selected}
        error = self._explore_controller.finish_watch(ticked_ids)
        self.update_status(error if error else "Added to your watch list")
        if not error:
            self._refresh_watchlist()
            
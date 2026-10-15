import customtkinter
from tkinter import ttk
from tkinter import filedialog

CHECKED = "☑"
UNCHECKED = "☐"

class AddWatchChannelDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, channel_name, section_title, default_destination, on_confirm):
        super().__init__(parent)

        self._dialog_box_height: int = 100
        self._dialog_box_width: int = 420

        self._on_confirm = on_confirm

        self._display_name_entry = None
        self._destination_entry = None
        self._custom_interval_entry = None
        self._cancel_button = None
        self._next_button = None

        self._auto_download_var = customtkinter.StringVar(value="off")
        self._interval_mode_var = customtkinter.StringVar(value="default")


        self._setup_dialog_box(parent, channel_name, section_title, default_destination, on_confirm)

    # Event Handlers
    def _on_interval_mode_change(self):
        self._custom_interval_entry.configure(state="normal" if self._interval_mode_var.get() == "custom" else "disabled")

    def _on_browse(self):
        folder = filedialog.askdirectory(initialdir=self._destination_entry.get())
        if folder:
            self._destination_entry.delete(0, "end")
            self._destination_entry.insert(0, folder)

    def _on_submit(self):
        display_name = self._display_name_entry.get().strip()
        destination = self._destination_entry.get().strip()
        if not display_name or not destination:
            return

        auto_download = self._auto_download_var.get() == "on"
        poll_interval = None
        if self._interval_mode_var.get() == "custom":
            raw = self._custom_interval_entry.get().strip()
            poll_interval = int(raw) if raw.isdigit() else None

        self.withdraw()
        self.after(200, self.destroy)
        self._on_confirm(display_name, destination, auto_download, poll_interval)

    
    # Private Methods
    def _setup_dialog_box(self, parent, channel_name, section_title, default_destination, on_confirm):

        self._setup_window(parent)
        self._add_widgets(channel_name, section_title, default_destination, on_confirm)

        self.update_idletasks()
        self.geometry(f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}+{self.winfo_x()}+{self.winfo_y()}")

    def _setup_window(self, parent):
        self.title("Add to Watch List")

        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x_position = int(screen_width * 0.4)
        y_position = int(screen_height * 0.25)

        self.geometry(f'{self._dialog_box_width}x{self._dialog_box_height}+{x_position}+{y_position}')        
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

    def _add_widgets(self, channel_name, section_title, default_destination, on_confirm):
        self.grid_columnconfigure(0, weight=1)

        self._add_header(channel_name, section_title)

        self._display_name_entry = self._request_display_name(channel_name, section_title)
        self._destination_entry, self.browse_button = self._request_destination_folder(default_destination)

        self._request_download_choice()

        self._custom_interval_entry = self._request_poll_interval()
        self._cancel_button, self._next_button = self._add_navigation_buttons()        

    def _add_header(self, channel_name, section_title):
        header = customtkinter.CTkLabel(self, text=f"Watching: {channel_name} — {section_title}", font=customtkinter.CTkFont(size=13, weight="bold"),wraplength=380, justify="left",)
        header.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

    def _request_display_name(self, channel_name, section_title):
        display_name = customtkinter.CTkLabel(self, text="Name", text_color="gray50").grid(row=1, column=0, sticky="w", padx=20)
        name_entry = customtkinter.CTkEntry(self)
        name_entry.insert(0, f"{channel_name} - {section_title}")
        name_entry.grid(row=2, column=0, sticky="ew", padx=20, pady=(2, 15))

        return name_entry

    def _request_destination_folder(self, default_destination):
        destination_folder = customtkinter.CTkLabel(self, text="Destination", text_color="gray50").grid(row=3, column=0, sticky="w", padx=20)
        dest_row = customtkinter.CTkFrame(self, fg_color="transparent")
        dest_row.grid(row=4, column=0, sticky="ew", padx=20, pady=(2, 15))
        dest_row.grid_columnconfigure(0, weight=1)

        destination_entry = customtkinter.CTkEntry(dest_row)
        destination_entry.insert(0, default_destination)
        destination_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        browse_button = customtkinter.CTkButton(dest_row, text="📁", width=32, command=self._on_browse).grid(row=0, column=1)

        return destination_entry, browse_button

    def _request_download_choice(self):
        auto_download = customtkinter.CTkLabel(self, text="Auto-download", text_color="gray50").grid(row=5, column=0, sticky="w", padx=20)
        auto_row = customtkinter.CTkFrame(self, fg_color="transparent")
        auto_row.grid(row=6, column=0, sticky="w", padx=20, pady=(2, 15))

        off_button = customtkinter.CTkRadioButton(auto_row, text="Off", variable=self._auto_download_var, value="off").pack(side="left", padx=(0, 15))
        on_button = customtkinter.CTkRadioButton(auto_row, text="On", variable=self._auto_download_var, value="on").pack(side="left")

    def _request_poll_interval(self):
        poll_interval = customtkinter.CTkLabel(self, text="Poll interval", text_color="gray50").grid(row=7, column=0, sticky="w", padx=20)
        interval_row = customtkinter.CTkFrame(self, fg_color="transparent")
        interval_row.grid(row=8, column=0, sticky="w", padx=20, pady=(2, 15))

        default_option_button = customtkinter.CTkRadioButton(interval_row, text="Default", variable=self._interval_mode_var, value="default", command=self._on_interval_mode_change,)
        default_option_button.pack(side="left", padx=(0, 15))

        custom_option_button = customtkinter.CTkRadioButton(interval_row, text="Custom (min):", variable=self._interval_mode_var, value="custom", command=self._on_interval_mode_change,)
        custom_option_button.pack(side="left", padx=(0, 6))

        custom_interval_entry = customtkinter.CTkEntry(interval_row, width=60, state="disabled")
        custom_interval_entry.pack(side="left")

        return custom_interval_entry

    def _add_navigation_buttons(self):
        btn_row = customtkinter.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=9, column=0, sticky="ew", padx=20, pady=(10, 20))
        btn_row.grid_columnconfigure((0, 1), weight=1)
        cancel_button = customtkinter.CTkButton(btn_row, text="Cancel", fg_color="transparent", border_width=1, command=self.destroy).grid(row=0, column=0, sticky="ew", padx=(0, 8))
        next_button = customtkinter.CTkButton(btn_row, text="Next →", command=self._on_submit).grid(row=0, column=1, sticky="ew")

        return cancel_button, next_button


class BackFillDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, items: list, on_confirm):
        super().__init__(parent)

        self._dialog_box_height: int = 420
        self._dialog_box_width: int = 420

        self._on_confirm = on_confirm
        self._items: dict = {}
        self._checked: dict = {}
        self._tree = None
        self._select_all_var = None

        self._setup_dialog_box(parent, items)

    def _setup_dialog_box(self, parent, items: list):
        self._setup_window(parent)
        self._add_widgets(items)

    def _setup_window(self, parent):
        self.title("Existing Videos")

        screen_width = parent.winfo_screenwidth()
        screen_height = parent.winfo_screenheight()
        x_position = int(screen_width * 0.4)
        y_position = int(screen_height * 0.25)

        self.geometry(f'{self._dialog_box_width}x{self._dialog_box_height}+{x_position}+{y_position}')
        self.resizable(False, False)

        self.transient(parent)
        self.grab_set()

    def _add_widgets(self, items: list):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._add_header(items)
        self._add_select_all_checkbox()
        self._add_videos_found(items)
        self._add_action_buttons()

    def _add_header(self, items: list):
        header = customtkinter.CTkLabel(
            self, text=f"{len(items)} existing videos found. Download now, or leave for later?",
            font=customtkinter.CTkFont(size=13, weight="bold"), wraplength=380, justify="left",
        )
        header.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))

    def _add_select_all_checkbox(self):
        self._select_all_var = customtkinter.BooleanVar(value=False)
        checkbox = customtkinter.CTkCheckBox(
            self, text="Select All", variable=self._select_all_var, command=self._on_select_all_toggled
        )
        checkbox.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 8))

    def _add_videos_found(self, items: list):
        self._items = {item["id"]: item for item in items}
        self._checked = {item_id: False for item_id in self._items}

        container = customtkinter.CTkFrame(self, fg_color="transparent")
        container.grid(row=2, column=0, sticky="nsew", padx=20)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        self._tree = ttk.Treeview(container, columns=("check", "title"), show="headings", selectmode="none")
        self._tree.heading("check", text="")
        self._tree.heading("title", text="Title", anchor="w")
        self._tree.column("check", width=30, anchor="center", stretch=False)
        self._tree.column("title", anchor="w")
        self._tree.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self._tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self._tree.configure(yscrollcommand=scrollbar.set)

        for item_id, item in self._items.items():
            self._tree.insert("", "end", iid=item_id, values=(UNCHECKED, item.get("title", "Untitled")))

        self._tree.bind("<Button-1>", self._on_tree_clicked)

    def _add_action_buttons(self):
        btn_row = customtkinter.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=3, column=0, sticky="ew", padx=20, pady=20)
        btn_row.grid_columnconfigure((0, 1), weight=1)

        skip_button = customtkinter.CTkButton(
            btn_row, text="Skip (watch only)", fg_color="transparent", border_width=1,
            command=lambda: self._finish([]),
        )
        skip_button.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        confirm_button = customtkinter.CTkButton(btn_row, text="Confirm", command=lambda: self._finish(self._selected_items()),)
        confirm_button.grid(row=0, column=1, sticky="ew")

    def _on_tree_clicked(self, event):
        item_id = self._tree.identify_row(event.y)
        if item_id:
            self._set_checked(item_id, not self._checked[item_id])

    def _on_select_all_toggled(self):
        checked = self._select_all_var.get()
        for item_id in self._checked:
            self._set_checked(item_id, checked)

    def _set_checked(self, item_id: str, checked: bool):
        self._checked[item_id] = checked
        self._tree.set(item_id, "check", CHECKED if checked else UNCHECKED)

    def _selected_items(self) -> list:
        return [self._items[item_id] for item_id, checked in self._checked.items() if checked]

    def _finish(self, selected_ids):
        self._on_confirm(selected_ids)
        self.destroy()
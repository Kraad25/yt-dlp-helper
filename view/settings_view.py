import customtkinter

from view.base_view import BaseView

from controller.settings_controller import SettingsController

class SettingsPage:
    GENERAL = "general"
    HOME = "home"
    EXPLORE = "explore"

class SettingsView(BaseView):

    PAGE_LABELS = {
        SettingsPage.GENERAL: "General",
        SettingsPage.HOME: "Home View",
        SettingsPage.EXPLORE: "Explore View",
    }

    PARALLEL_DOWNLOAD_CHOICES = [1, 2, 3, 4]
    PARALLEL_TRANSCODING_CHOICES = [1, 2]
    DOWNLOAD_QUEUE_LIMIT_CHOICES = [50, 100, 200]

    # Grid layout rows (General page)
    ROW_TITLE = 0
    ROW_SUBTITLE = 1
    ROW_PANEL = 2

    def __init__(self, parent):
        self._accent_color = customtkinter.ThemeManager.theme["CTkButton"]["fg_color"]

        self._nav_buttons: dict = {}
        self._nav_font_active = None
        self._nav_font_idle = None
        self._pages: dict = {}
        
        self._thread_dispatcher = None

        self._settings_controller: SettingsController = None

        self._general_encoder_var = customtkinter.StringVar(value="CPU (default)")
        self._general_encoder_menu = None
        self._encoder_type_by_name: dict = {}
        self._redetect_button = None

        self._parallel_downloads_var = customtkinter.StringVar(value="2")
        self._parallel_transcodes_var = customtkinter.StringVar(value="1")
        self._queue_limit_var = customtkinter.StringVar(value="200")

        self._update_button = None
        self._update_status_label = None

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, settings_controller: SettingsController):
        self._settings_controller = settings_controller
        self._refresh_encoders()
        self._refresh_queue_settings()
        
        self._settings_controller.detect_encoders(
            on_done=self._thread_dispatcher.wrap(self._on_encoders_detected),
        )

    def set_thread_dispatcher(self, dispatcher):
        self._thread_dispatcher = dispatcher        

    # Event Handlers
    def _on_general_encoder_changed(self, name: str):
        encoder_type = self._encoder_type_by_name.get(name)
        if not encoder_type:
            return
        self._settings_controller.set_general_encoder(encoder_type)

    def _on_redetect_clicked(self):
        self._set_redetecting_button_text(True)
        self._settings_controller.detect_encoders(
            on_done=self._thread_dispatcher.wrap(self._on_encoders_detected),
            force_refresh=True,
        )

    def _on_encoders_detected(self):
        self._refresh_encoders()
        self._set_redetecting_button_text(False)

    def _on_parallel_downloads_changed(self, value: str):
        self._settings_controller.set_parallel_downloads(value)

    def _on_parallel_transcodes_changed(self, value: str):
        self._settings_controller.set_parallel_transcodes(value)

    def _on_queue_limit_changed(self, value: str):
        self._settings_controller.set_queue_limit(value)

    def _on_update_clicked(self):
        started = self._settings_controller.check_for_updates(
            on_status=self._thread_dispatcher.wrap(self._set_update_status),
            on_done=self._thread_dispatcher.wrap(self._on_update_finished),
        )
        if not started:
            return

        self._set_update_button_busy(True)
        self._set_update_status("Checking and Updating")

    def _on_update_finished(self):
        self._set_update_button_busy(False)

    # Navigation
    def _show_page(self, page_name: str):
        for name, page in self._pages.items():
            if name == page_name:
                page.grid()
            else:
                page.grid_remove()

        for name, button in self._nav_buttons.items():
            is_active = name == page_name
            button.configure(
                fg_color=self._accent_color if is_active else "transparent",
                text_color="white" if is_active else ("gray10", "gray90"),
                font=self._nav_font_active if is_active else self._nav_font_idle,
            )

    # Private Methods
    def _setup_style(self):
        pass  # CTk widgets are themed via custom_themes/warm_refined.json

    def _create_widgets(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._nav_font_active = customtkinter.CTkFont(size=14, weight="bold")
        self._nav_font_idle = customtkinter.CTkFont(size=14)

        self._create_sidebar()

        content = customtkinter.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        (
            self._pages[SettingsPage.GENERAL],
            self._general_encoder_menu,
            self._redetect_button,
            self._update_button,
            self._update_status_label,
        ) = self._create_general_page(content)

        self._pages[SettingsPage.HOME] = self._create_placeholder_page(content, "Home View")
        self._pages[SettingsPage.EXPLORE] = self._create_placeholder_page(content, "Explore View")

        self._show_page(SettingsPage.GENERAL)

    def _create_sidebar(self):
        sidebar = customtkinter.CTkFrame(self, width=200)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=(10, 0), pady=10)
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)

        header = customtkinter.CTkLabel(
            sidebar,
            text="Settings",
            font=customtkinter.CTkFont(size=16, weight="bold"),
        )
        header.grid(row=0, column=0, padx=65, pady=(15, 10), sticky="w")

        for index, (page_name, label) in enumerate(self.PAGE_LABELS.items(), start=1):
            button = customtkinter.CTkButton(
                sidebar,
                text=label,
                anchor="w",
                height=36,
                fg_color="transparent",
                hover_color=("gray85", "gray25"),
                text_color=("gray10", "gray90"),
                command=lambda name=page_name: self._show_page(name),
            )
            button.grid(row=index, column=0, sticky="ew", padx=10, pady=2)
            self._nav_buttons[page_name] = button

    def _create_general_page(self, parent):
        page = customtkinter.CTkFrame(parent, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(self.ROW_PANEL, weight=1)

        title = customtkinter.CTkLabel(
            page,
            text="General",
            font=customtkinter.CTkFont(size=18, weight="bold"),
        )
        title.grid(row=self.ROW_TITLE, column=0, sticky="w", padx=30, pady=(20, 2))

        subtitle = customtkinter.CTkLabel(
            page,
            text="Defaults for the whole app. Home and Explore use these until you change them there.",
            font=customtkinter.CTkFont(size=12),
            text_color="gray50",
            anchor="w",
            justify="left",
            wraplength=560,
        )
        subtitle.grid(row=self.ROW_SUBTITLE, column=0, sticky="w", padx=30, pady=(0, 12))

        panel = customtkinter.CTkFrame(page, fg_color=("gray88", "gray19"), corner_radius=10)
        panel.grid(row=self.ROW_PANEL, column=0, sticky="nsew", padx=30, pady=(0, 15))
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(0, weight=1)

        scroll = customtkinter.CTkScrollableFrame(panel, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        scroll.grid_columnconfigure(0, weight=1)

        encoder_menu, redetect_button = self._create_encoder_section(scroll)
        self._create_download_queue_section(scroll)
        update_button, update_status_label = self._create_updates_section(scroll)

        return page, encoder_menu, redetect_button, update_button, update_status_label

    def _create_encoder_section(self, parent):
        self._add_heading(parent, row=0, title="Encoder")
        self._add_setting_label(parent, row=1, label_text="Video encoder")

        controls = customtkinter.CTkFrame(parent, fg_color="transparent")
        controls.grid(row=1, column=1, sticky="e", padx=(0, 10))

        encoder_menu = customtkinter.CTkOptionMenu(
            controls,
            variable=self._general_encoder_var,
            values=["CPU (default)"],
            command=self._on_general_encoder_changed,
            width=200,
            height=28,
            dynamic_resizing=False,
        )
        encoder_menu.grid(row=0, column=0, sticky="e")

        redetect_button = customtkinter.CTkButton(
            controls,
            text="Re-detect",
            width=80,
            height=28,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._on_redetect_clicked,
        )
        redetect_button.grid(row=0, column=1, sticky="e", padx=(8, 0))

        return encoder_menu, redetect_button

    def _create_download_queue_section(self, parent):
        self._add_heading(parent, row=3, title="Download Queue")

        self._create_limit_row(
            parent, 
            row=4, 
            label_text="Parallel downloads", 
            variable=self._parallel_downloads_var, 
            values=self.PARALLEL_DOWNLOAD_CHOICES, 
            command=self._on_parallel_downloads_changed,
        )

        self._create_limit_row(
            parent, 
            row=5, 
            label_text="Parallel transcodes", 
            variable=self._parallel_transcodes_var, 
            values=self.PARALLEL_TRANSCODING_CHOICES, 
            command=self._on_parallel_transcodes_changed,
        )

        self._create_limit_row(
            parent, 
            row=6, 
            label_text="Queue limit", 
            variable=self._queue_limit_var, 
            values=self.DOWNLOAD_QUEUE_LIMIT_CHOICES, 
            command=self._on_queue_limit_changed,
        )

    def _create_updates_section(self, parent):
        self._add_heading(parent, row=9, title="Updates")
        self._add_setting_label(parent, row=10, label_text="yt-dlp & ffmpeg")

        update_button = customtkinter.CTkButton(
            parent,
            text="Update",
            width=80,
            height=28,
            command=self._on_update_clicked,
        )
        update_button.grid(row=10, column=1, sticky="e", padx=(0, 10))

        status_label = customtkinter.CTkLabel(
            parent,
            text="",
            font=customtkinter.CTkFont(size=11, slant="italic"),
            text_color="gray50",
            anchor="w",
            justify="left",
            wraplength=480,
        )
        status_label.grid(row=11, column=0, columnspan=2, sticky="w", padx=10, pady=(2, 0))

        return update_button, status_label

    def _add_heading(self, parent, row: int, title: str):
        heading = customtkinter.CTkLabel(parent, text=title, font=customtkinter.CTkFont(size=14, weight="bold"), text_color="gray50")
        heading.grid(row=row, column=0, columnspan=2, sticky="w", padx=10, pady=(3, 0))

    def _add_divider(self, parent, row: int):
        divider = customtkinter.CTkFrame(parent, height=1, fg_color=("gray78", "gray28"))
        divider.grid(row=row, column=0, columnspan=2, sticky="ew", padx=10, pady=0)

    def _add_setting_label(self, parent, row: int, label_text: str):
        text_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        text_frame.grid(row=row, column=0, sticky="w", padx=10, pady=1)

        label = customtkinter.CTkLabel(text_frame, text=label_text, font=customtkinter.CTkFont(size=12, weight="bold"), anchor="w")
        label.grid(row=0, column=0, sticky="w")
    
    def _create_limit_row(self, parent, row, label_text, variable, values, command):
        self._add_setting_label(parent, row, label_text)

        menu = customtkinter.CTkOptionMenu(
            parent,
            variable=variable,
            values=[str(value) for value in values],
            command=command,
            width=80,
            height=28,
            dynamic_resizing=False,
        )
        menu.grid(row=row, column=1, sticky="e", padx=(0, 10))

        return menu

    def _create_placeholder_page(self, parent, name: str):
        page = customtkinter.CTkFrame(parent, fg_color="transparent")
        page.grid(row=0, column=0, sticky="nsew")
        page.grid_columnconfigure(0, weight=1)

        label = customtkinter.CTkLabel(
            page,
            text=f"{name} settings are coming in a later step.",
            font=customtkinter.CTkFont(size=13, slant="italic"),
            text_color="gray50",
        )
        label.grid(row=0, column=0, sticky="w", padx=30, pady=30)

        return page
    
    # Helpers
    ## Setters
    def _set_redetecting_button_text(self, busy: bool):
        if busy:
            self._redetect_button.configure(state="disabled", text="Detecting...")
        else:
            self._redetect_button.configure(state="normal", text="Re-detect encoders")    

    def _set_update_button_busy(self, busy: bool):
        if busy:
            self._update_button.configure(state="disabled", text="Updating...")
        else:
            self._update_button.configure(state="normal", text="Update yt-dlp & ffmpeg")

    def _set_update_status(self, message: str):
        self._update_status_label.configure(text=message)

    ## Encoder Settings
    def _refresh_encoders(self):
        if not self._settings_controller:
            return

        available = self._settings_controller.get_available_encoders()
        self._encoder_type_by_name = {info["name"]: info["type"] for info in available}
        self._general_encoder_menu.configure(values=list(self._encoder_type_by_name))

        name_by_type = {encoder_type: name for name, encoder_type in self._encoder_type_by_name.items()}
        current_type = self._settings_controller.get_general_encoder()
        self._general_encoder_var.set(name_by_type.get(current_type, "CPU (default)"))

    ## Queue Settings
    def _refresh_queue_settings(self):
        if not self._settings_controller:
            return

        self._parallel_downloads_var.set(str(self._settings_controller.get_parallel_downloads()))
        self._parallel_transcodes_var.set(str(self._settings_controller.get_parallel_transcodes()))
        self._queue_limit_var.set(str(self._settings_controller.get_queue_limit()))
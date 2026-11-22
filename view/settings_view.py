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

    # Grid layout rows (General page)
    ROW_TITLE = 0
    ROW_SUBTITLE = 1
    ROW_ENCODER = 2
    ROW_SPACER = 3
    ROW_UPDATES = 4

    def __init__(self, parent):
        self._nav_buttons: dict = {}
        self._pages: dict = {}
        self._accent_color = customtkinter.ThemeManager.theme["CTkButton"]["fg_color"]

        self._settings_controller: SettingsController = None

        self._general_encoder_var = customtkinter.StringVar(value="CPU (default)")
        self._general_encoder_menu = None
        self._encoder_type_by_name: dict = {}

        self._redetect_button = None

        self._update_button = None
        self._update_status_label = None

        self._thread_dispatcher = None

        self._nav_font_active = None
        self._nav_font_idle = None

        super().__init__(parent)

    # Public Methods
    def set_controllers(self, settings_controller: SettingsController):
        self._settings_controller = settings_controller
        self._refresh_encoders()
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
        page.grid_rowconfigure(self.ROW_SPACER, weight=1)

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
        subtitle.grid(row=self.ROW_SUBTITLE, column=0, sticky="w", padx=30, pady=(0, 25))

        encoder_menu, redetect_button = self._create_encoder_row(page)
        update_button, update_status_label = self._create_updates_section(page)

        return page, encoder_menu, redetect_button, update_button, update_status_label

    def _create_encoder_row(self, parent):
        row = customtkinter.CTkFrame(parent, fg_color="transparent")
        row.grid(row=self.ROW_ENCODER, column=0, sticky="w", padx=30)

        label = customtkinter.CTkLabel(row, text="Default video encoder", font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray50")
        label.grid(row=0, column=0, sticky="w", padx=(0, 12))

        encoder_menu = customtkinter.CTkOptionMenu(
            row,
            variable=self._general_encoder_var,
            values=["CPU (default)"],
            command=self._on_general_encoder_changed,
            width=230,
            height=36,
            dynamic_resizing=False,
        )
        encoder_menu.grid(row=0, column=1, sticky="w")

        redetect_button = customtkinter.CTkButton(
            row,
            text="Re-detect encoders",
            width=140,
            height=36,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            command=self._on_redetect_clicked,
        )
        redetect_button.grid(row=0, column=2, sticky="w", padx=(10, 0))

        return encoder_menu, redetect_button

    def _create_updates_section(self, parent):
        section = customtkinter.CTkFrame(parent, fg_color="transparent")
        section.grid(row=self.ROW_UPDATES, column=0, sticky="ew", padx=30, pady=(0, 25))
        section.grid_columnconfigure(1, weight=1)

        label = customtkinter.CTkLabel(section, text="Updates", font=customtkinter.CTkFont(size=13, weight="bold"), text_color="gray50")
        label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        update_button = customtkinter.CTkButton(
            section,
            text="Update yt-dlp & ffmpeg",
            width=180,
            height=36,
            command=self._on_update_clicked,
        )
        update_button.grid(row=1, column=0, sticky="w")

        status_label = customtkinter.CTkLabel(
            section,
            text="",
            font=customtkinter.CTkFont(size=12, slant="italic"),
            text_color="gray50",
            anchor="w",
        )
        status_label.grid(row=1, column=1, sticky="w", padx=(12, 0))

        return update_button, status_label

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

    ## Encoder
    def _refresh_encoders(self):
        if not self._settings_controller:
            return

        available = self._settings_controller.get_available_encoders()
        self._encoder_type_by_name = {info["name"]: info["type"] for info in available}
        self._general_encoder_menu.configure(values=list(self._encoder_type_by_name))

        name_by_type = {encoder_type: name for name, encoder_type in self._encoder_type_by_name.items()}
        current_type = self._settings_controller.get_general_encoder()
        self._general_encoder_var.set(name_by_type.get(current_type, "CPU (default)"))
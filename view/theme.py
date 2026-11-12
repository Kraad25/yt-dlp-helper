import json
import customtkinter

from core.paths import resource_dir

class AppTheme:
    _THEME_PATH = resource_dir() / "custom_themes" / "warm_refined.json"
    _APPEARANCE_MODE = "light" 

    def __init__(self):
        self._raw_theme = self._load_theme_json()

    # Public Methods
    @classmethod
    def apply_global_theme(cls):
        customtkinter.set_appearance_mode(cls._APPEARANCE_MODE)
        customtkinter.set_default_color_theme(str(cls._THEME_PATH))

    def get_background_color(self) -> str:
        return self._resolve("CTk", "fg_color")

    def get_secondary_color(self) -> str:
        return self._resolve("CTkFrame", "fg_color")

    def get_accent_color(self) -> str:
        return self._resolve("CTkButton", "fg_color")

    def get_text_color(self) -> str:
        return self._resolve("CTkLabel", "text_color")

    # Private Methods
    def _load_theme_json(self) -> dict:
        with open(self._THEME_PATH, 'r') as f:
            return json.load(f)

    def _resolve(self, widget_key: str, property_key: str) -> str:
        value = self._raw_theme[widget_key][property_key]
        if isinstance(value, list):
            index = 0 if self._APPEARANCE_MODE == "light" else 1
            return value[index]
        return value
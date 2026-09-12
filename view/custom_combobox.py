import customtkinter

class CustomComboBox:    

    AUDIO_QUALITIES = ["128 kbps", "192 kbps", "256 kbps", "320 kbps"]
    VIDEO_QUALITIES = ["360p", "480p", "720p", "1080p", "2K", "4K"]

    def __init__(self, parent, mode_var, width: int = 140):
        self._parent = parent
        self._mode_var = mode_var
        self._var = customtkinter.StringVar(value=self.AUDIO_QUALITIES[1])

        self.widget = customtkinter.CTkOptionMenu(
            parent,
            variable=self._var,
            values=self.AUDIO_QUALITIES,
            width=width,
        )

    def switch_mode(self, mode: str):
        values = self.AUDIO_QUALITIES if mode == "mp3" else self.VIDEO_QUALITIES
        self.widget.configure(values=values)
        self.set_value(values[0])

    def set_value(self, value: str):
        options = self.widget.cget("values")
        if value not in options:
            value = options[0]
        self._var.set(value)

    def get_value(self) -> str:
        return self._var.get()
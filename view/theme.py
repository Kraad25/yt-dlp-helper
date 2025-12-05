class AppTheme:
    def __init__(self):
        self._beige = "#F5F5DC"
        self._light_beige = "#FAF3E0"
        self._dark_beige = "#EDE0C8"
        self._grey = "#c0c0c0"

    def get_background_color(self):
        return self._dark_beige
    def get_secondary_color(self):
        return self._grey
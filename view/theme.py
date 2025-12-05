class AppTheme:
    def __init__(self):
        self.__beige = "#F5F5DC"
        self.__light_beige = "#FAF3E0"
        self.__dark_beige = "#EDE0C8"
        self.__grey = "#c0c0c0"

    def get_background_color(self):
        return self.__dark_beige
    def get_secondary_color(self):
        return self.__grey

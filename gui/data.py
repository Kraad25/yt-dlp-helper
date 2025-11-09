class Data:
    def __init__(self):
        self.beige = "#F5F5DC"
        self.light_beige = "#FAF3E0"
        self.dark_beige = "#EDE0C8"
        self.grey = "#c0c0c0"

    def get_background_color(self):
        return self.dark_beige
    def get_secondary_color(self):
        return self.grey

    def get_window_placement(self, root):
        window_placement_x = int(root.winfo_screenwidth()*0.3)
        window_placement_y = int(root.winfo_screenheight()*0.1)
        return (str(window_placement_x) + '+' + str(window_placement_y))
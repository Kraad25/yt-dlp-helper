class Data:
    def __init__(self):
        pass

    def get_background_color(self):
        return "#EDE0C8" # Beige->#F5F5DC, Light Beige->#FAF3E0, Dark Beige->#EDE0C8
    def get_secondary_color(self):
        return "#c0c0c0"

    def get_window_placement(self, root):
        window_placement_x = int(root.winfo_screenwidth()*0.3)
        window_placement_y = int(root.winfo_screenheight()*0.1)
        return (str(window_placement_x) + '+' + str(window_placement_y))
import tkinter as tk
from tkinter import ttk

from view.theme import AppTheme
from controller.app_controller import Application

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.theme = AppTheme()
        self.controller = Application(self.root)

        self._setup_window()
        self._create_menu_bar()
        
        self.controller.initialize_views()
        self.controller.initialize_controllers()
        self.controller.show_home()

    def _setup_window(self):
        self.root.title("Youtube Converter")
        self.root.resizable(False, False)

        window_width = 560
        window_height = 600
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        x_position = int(screen_width * 0.3)
        y_position = int(screen_height * 0.1)
        
        self.root.geometry(f'{window_width}x{window_height}+{x_position}+{y_position}')
        self.root.configure(background=self.theme.get_background_color())

    def _create_menu_bar(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        # TODO : Add About section and link the method to the command
        about_menu.add_command(label="About", command=lambda:None)
        
        self.root.configure(menu=menubar)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = App()
    app.run()
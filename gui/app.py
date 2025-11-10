import tkinter as tk

from data import Data
from homeScreen import HomeScreen
from metadataEditor import MetadataEditor

class Application:
    def __init__(self):
        self.root = tk.Tk()
        data = Data()
        
        self.root.title("Youtube Converter")
        self.root.resizable(False, False)

        self.root.geometry('560x600+' + data.get_window_placement(self.root))
        self.root.configure(background=data.get_background_color())
        self._create_menu_bar()

        self._load_frames()
        self.switch_frame(self.editor)
    
    def switch_frame(self, new_frame):
        new_frame.tkraise()

    def run(self):
        self.root.mainloop()

    def _create_menu_bar(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        about_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="About", command=self._about)
        
        self.root.configure(menu=menubar)

    def _load_frames(self):
        self.home = HomeScreen(self.root, self)
        self.editor = MetadataEditor(self.root, self)

        for frame in (self.home, self.editor):
            frame.place(x=0, y=0, width=560, height=600)
            frame.pack_propagate(False)


    def _about(self):
        pass


if __name__ == "__main__":
    gui = Application()
    gui.run()
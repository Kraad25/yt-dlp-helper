import tkinter as tk
from tkinter import ttk

class Entries:
    def __init__(self, parent, width, posx=0, posy=0):
        self.parent = parent
        self.width = width
        self.posx = posx
        self.posy = posy

    def make_entry(self):
        self.entry = ttk.Entry(self.parent, width=self.width)
        self.entry.place(x=self.posx, y=self.posy)
        return self.entry
    
    def set_entry_text(self, text):
        self.entry.delete(0, tk.END)
        self.entry.insert(0, text)

    def get_entry_text(self):
        return self.entry.get().strip()
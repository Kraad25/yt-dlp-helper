import tkinter as tk
from tkinter import ttk

class CustomComboBox:

    def __init__(self, parent, mode, posx=0, posy=0, width=20,):
        self.parent = parent
        self.posx = posx
        self.posy = posy
        self.width=width
        
        self._var = tk.StringVar(value="192 kbps")
    
        self.AUDIO_QUALITIES = ["128 kbps", "192 kbps", "256 kbps", "320 kbps"]
        self.VIDEO_QUALITIES = ["360p", "480p", "720p", "1080p", "2K", "4K"]
        
    def make_combobox(self):
        self.combobox = ttk.Combobox(self.parent, 
                                        textvariable = self._var, 
                                        values = self.AUDIO_QUALITIES, 
                                        state = "readonly", 
                                        width = self.width
                                    )
        self.combobox.place(x=self.posx, y=self.posy)

    def switch_mode(self, mode):
        if mode == "mp3":
            self.combobox['values'] = self.AUDIO_QUALITIES
            self.set_value(self.AUDIO_QUALITIES[0])

        if mode == "mp4":
            self.combobox['values'] = self.VIDEO_QUALITIES
            self.set_value(self.VIDEO_QUALITIES[0])

    def set_value(self, value):
        options = self.combobox['values']
        if value not in options:
            value = options[0]
        self._var.set(value)

    def get_value(self):
        return self._var.get()
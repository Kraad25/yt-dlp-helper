import tkinter as tk
from tkinter import ttk

class CustomComboBox:

    def __init__(self, parent, mode, posx=0, posy=0, width=20,):
        self._parent = parent
        self._posx = posx
        self._posy = posy
        self._width=width
        
        self._var = tk.StringVar(value="192 kbps")
    
        self._AUDIO_QUALITIES = ["128 kbps", "192 kbps", "256 kbps", "320 kbps"]
        self._VIDEO_QUALITIES = ["360p", "480p", "720p", "1080p", "2K", "4K"]
        
    def make_combobox(self):
        self.combobox = ttk.Combobox(self._parent, 
                                        textvariable = self._var, 
                                        values = self._AUDIO_QUALITIES, 
                                        state = "readonly", 
                                        width = self._width
                                    )
        self.combobox.place(x=self._posx, y=self._posy)

    def switch_mode(self, mode):
        if mode == "mp3":
            self.combobox['values'] = self._AUDIO_QUALITIES
            self.set_value(self._AUDIO_QUALITIES[0])

        if mode == "mp4":
            self.combobox['values'] = self._VIDEO_QUALITIES
            self.set_value(self._VIDEO_QUALITIES[0])

    def set_value(self, value):
        options = self.combobox['values']
        if value not in options:
            value = options[0]
        self._var.set(value)

    def get_value(self):
        return self._var.get()
import tkinter as tk
from tkinter import ttk

class CustomEntry:
    def __init__(self, parent, width, posx=0, posy=0, placeholder: str|None=None):
        self._parent = parent
        self._width = width
        self._posx = posx
        self._posy = posy
        self._entry = None

        # Placeholder functionality can be implemented if needed
        self._placeholder = placeholder
        self._has_placeholder = False

    def make_entry(self):
        self._entry = ttk.Entry(self._parent, width=self._width)
        self._entry.place(x=self._posx, y=self._posy)

        if self._placeholder:
            self._entry.bind("<FocusIn>", self._on_focus_in)
            self._entry.bind("<FocusOut>", self._on_focus_out)
            self._set_placeholder()

        return self._entry
    
    def set_entry_text(self, text):
        self._entry.config(foreground="black")
        self._entry.delete(0, tk.END)
        self._entry.insert(0, text)
        self._has_placeholder = False

    def set_readonly_entry_text(self, text):
        self._entry.config(state='normal', foreground="black")
        self._entry.delete(0, tk.END)
        self._entry.insert(0, text)
        self._entry.config(state='readonly')
        self._has_placeholder = False

    def get_entry_text(self):
        if self._has_placeholder:
            return ""
        return self._entry.get().strip()
    
    def hide_entry(self):
        self._entry.place_forget()

    def show_entry(self):
        self._entry.place(x=self._posx, y=self._posy)

    # Placeholder internals
    def _set_placeholder(self):
        self._entry.config(
            foreground="#888888",              # softer grey
            font=("Segoe UI", 9, "italic")
        )

        self._entry.delete(0, tk.END)
        self._entry.insert(0, self._placeholder)
        self._has_placeholder = True

    def _on_focus_in(self, event):
        if self._has_placeholder:
            self._entry.delete(0, tk.END)
            self._entry.config(
                foreground="black",
                font=("Segoe UI", 9)
            )
            self._has_placeholder = False

    def _on_focus_out(self, event):
        if not self._entry.get().strip():
            self._set_placeholder()
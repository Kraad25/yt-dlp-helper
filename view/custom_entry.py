import tkinter as tk
from tkinter import ttk

class CustomEntry:
    def __init__(self, parent, width, posx=0, posy=0, placeholder: str|None=None):
        self.__parent = parent
        self.__width = width
        self.__posx = posx
        self.__posy = posy
        self.__entry = None

        # Placeholder functionality can be implemented if needed
        self.__placeholder = placeholder
        self.__has_placeholder = False

    def make_entry(self):
        self.__entry = ttk.Entry(self.__parent, width=self.__width)
        self.__entry.place(x=self.__posx, y=self.__posy)

        if self.__placeholder:
            self.__entry.bind("<FocusIn>", self.__on_focus_in)
            self.__entry.bind("<FocusOut>", self.__on_focus_out)
            self.__set_placeholder()

        return self.__entry
    
    def set_entry_text(self, text):
        self.__entry.config(foreground="black")
        self.__entry.delete(0, tk.END)
        self.__entry.insert(0, text)
        self.__has_placeholder = False

    def set_readonly_entry_text(self, text):
        self.__entry.config(state='normal', foreground="black")
        self.__entry.delete(0, tk.END)
        self.__entry.insert(0, text)
        self.__entry.config(state='readonly')
        self.__has_placeholder = False

    def get_entry_text(self):
        if self.__has_placeholder:
            return ""
        return self.__entry.get().strip()
    
    def hide_entry(self):
        self.__entry.place_forget()

    def show_entry(self):
        self.__entry.place(x=self.__posx, y=self.__posy)

    # Placeholder internals
    def __set_placeholder(self):
        self.__entry.config(
            foreground="#888888",              # softer grey
            font=("Segoe UI", 9, "italic")
        )

        self.__entry.delete(0, tk.END)
        self.__entry.insert(0, self.__placeholder)
        self.__has_placeholder = True

    def __on_focus_in(self, event):
        if self.__has_placeholder:
            self.__entry.delete(0, tk.END)
            self.__entry.config(
                foreground="black",
                font=("Segoe UI", 9)
            )
            self.__has_placeholder = False

    def __on_focus_out(self, event):
        if not self.__entry.get().strip():
            self.__set_placeholder()
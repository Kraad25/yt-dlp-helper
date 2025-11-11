import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod

class BaseView(ttk.Frame, ABC):
    def __init__(self, parent: tk.Widget, controller):
        super().__init__(parent)
        self._controller = controller

        self._setup_style()
        self._create_widgets()
        self._bind_events()

    @abstractmethod
    def _setup_style(self):
        pass

    @abstractmethod
    def _create_widgets(self):
        pass

    @abstractmethod
    def _bind_events(self):
        pass

    # **kwargs catches all the extra keyword arguments in dictionary and allows flexibility for different events 
    def notify_controller(self, event_name: str, **kwargs):
        if self._controller and hasattr(self._controller, event_name):
            handler = getattr(self._controller, event_name)
            handler(**kwargs)

    def show_error(self, title: str, message: str):
        from tkinter import messagebox
        messagebox.showerror(title, message)

    def show_info(self, title: str, message: str):
        from tkinter import messagebox
        messagebox.showinfo(title, message)

    def update_view(self, data: dict):
        pass    
            

    
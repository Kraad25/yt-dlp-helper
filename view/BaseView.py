import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod

class BaseView(ttk.Frame, ABC):
    def __init__(self, parent: tk.Widget):
        super().__init__(parent)

        self._setup_style()
        self._create_widgets()

    @abstractmethod
    def _setup_style(self):
        pass

    @abstractmethod
    def _create_widgets(self):
        pass
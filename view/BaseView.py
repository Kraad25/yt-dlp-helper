import customtkinter
from abc import ABC, abstractmethod

class BaseView(customtkinter.CTkFrame, ABC):
    def __init__(self, parent, width: int = 900, height: int = 600):
        super().__init__(parent, width=width, height=height)

        self._setup_style()
        self._create_widgets()

    @abstractmethod
    def _setup_style(self):
        pass

    @abstractmethod
    def _create_widgets(self):
        pass
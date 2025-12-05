import os

from typing import Callable
from model.validators import FolderValidator
from model.metadata_model import MetadataModel

from service.error_service import ErrorHandlingService
from service.metadata_service import MetadataService

class MetadataController:
    def __init__(self):
        self.__metadata_editing_folder = FolderValidator()
        self.__error = ErrorHandlingService()
        self.__service = MetadataService(metadata_model=MetadataModel(), error_handler=self.__error)

        self.__files = []
        self.__current_index = 0        
        self.__folder_path = ""
        self.__mode = ""

        self.__artist: str = None
        self.__album: str = None
        self.__set_title: Callable = None
        self.__update_status: Callable = None
        self.__enable_next: Callable = None
        self.__enable_back: Callable = None
        
    # Public Methods
    def editing_requested(
            self, 
            files: list, 
            data: dict, 
            set_title: Callable, 
            show_wizard: Callable, 
            update_status: Callable, 
            enable_next: Callable, 
            enable_back: Callable
        ):
        
        folder_path = data.get("folder_path", "")
        artist = data.get("artist", "")
        album = data.get("album", "")
        mode = data.get("mode", "")

        self.__files = files
        self.__artist = artist
        self.__album = album
        self.__folder_path = folder_path
        self.__mode = mode
        self.__current_index = 0
        
        self.__set_callbacks(set_title, enable_next, enable_back, update_status)
        self.__service.reset()

        if not self.__validate_folder(self.__folder_path, self.__files):
            return
        show_wizard()

        file_name, file_path = self.__get_current_file_info()

        title = self.__service.get_title(self.__mode, file_path)
        self.__set_title(title if title else "")  
        self.__update_status(f"Editing: {file_name}")

        self.__enable_back(False)
        self.__enable_next(len(self.__files)>1)

    def on_next(self, given_title: str):
        file_name, file_path = self.__get_current_file_info()

        self.__service.set_metadata_for_file(
            mode=self.__mode, 
            file_path=file_path, 
            title=given_title, 
            artist=self.__artist, 
            album=self.__album, 
            file_name=file_name,
            update_status=self.__update_status
        )
        self.__navigate_to_file(self.__current_index + 1)

    def on_back(self, given_title: str):
        file_name, file_path = self.__get_current_file_info()
        
        self.__service.set_metadata_for_file(
            mode=self.__mode, 
            file_path=file_path, 
            title=given_title, 
            artist=self.__artist, 
            album=self.__album, 
            file_name=file_name,
            update_status=self.__update_status
        )

        self.__navigate_to_file(self.__current_index - 1)

    def on_finish(self, given_title: str, type: int):
        file_name, file_path = self.__get_current_file_info()
        
        self.__service.set_metadata_for_file(
            mode=self.__mode, 
            file_path=file_path, 
            title=given_title, 
            artist=self.__artist, 
            album=self.__album, 
            file_name=file_name,
            update_status=self.__update_status
        )

        self.__enable_back(False)
        self.__enable_next(False)

        self.__service.wait_for_all_video_operations()

        success = self.__service.rename_files(
            mode=self.__mode,
            folder_path=self.__folder_path,
            files=self.__files,
            artist=self.__artist,
            album=self.__album,
            filename_format=type,
            update_status=self.__update_status,
        )

        if not success:
            self.__update_status("Editing Failed!.")
            return
        
        self.__update_status("Editing complete! Go back to home to start over.")

    # Private Methods
    def __set_callbacks(self, set_title: Callable, enable_next: Callable, 
                       enable_back: Callable, update_status: Callable):
        
        self.__set_title: Callable = set_title
        self.__update_status: Callable = update_status
        self.__enable_next: Callable = enable_next
        self.__enable_back: Callable = enable_back
        self.__update_status: Callable = update_status

    def __validate_folder(self, folder, files):
        if not self.__metadata_editing_folder.validate(folder):
            self.__error.handle_error(update_status=self.__update_status,
                                    custom_msg="Error: Folder contains Subfolders")
            return False
        if not files:
            self.__error.handle_error(update_status=self.__update_status,
                                    custom_msg=f"Error: No {self.__mode} files found")
            return False
        return True
        
    def __get_current_file_info(self):
        file_name = self.__files[self.__current_index]
        file_path = os.path.join(self.__folder_path, file_name)
        return file_name, file_path
    
    def __navigate_to_file(self, new_index: int):
        if not (0 <= new_index < len(self.__files)):
            return # Outta bounds
        self.__current_index = new_index
        file_name, self.file_path = self.__get_current_file_info()

        title = self.__service.get_title(self.__mode, self.file_path)
        self.__set_title(title if title else "")
        self.__update_status(f"Editing: {file_name}")
        self.__update_navigation_button_states()

    def __update_navigation_button_states(self):
        self.__enable_back(self.__current_index > 0)
        self.__enable_next(self.__current_index < len(self.__files) - 1)
import os
import re
from typing import Callable

class FileRenamer:
    @staticmethod
    def rename_file(file_path, new_name, folder_path, update_status: Callable):
        new_name = FileRenamer._sanitize_filename(new_name)
        new_path = os.path.join(folder_path, new_name)
        if file_path != new_path:
            try:
                os.rename(file_path, new_path)
                update_status(f"Renamed: {os.path.basename(file_path)} -> {new_name}")
            except Exception as e:
                update_status(f"Rename failed: {os.path.basename(file_path)} - {e}")
    
    @staticmethod
    def _sanitize_filename(name):
        name = name.replace(': ', '：')  
        name = re.sub(r'[\\/*?"<>|]', '_', name)
        return name
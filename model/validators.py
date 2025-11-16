import os

class DownloadValidator:
    SUPPORTED_MODES = ['mp3','mp4']

    def __init__(self):
        pass
    
    def validate(self, url, folder, mode):
        if not url:
            return "Error: URL missing"
        if not folder:
            return "Error: Folder missing"
        if mode not in self.SUPPORTED_MODES:
            modes_str = ", ".join(self.SUPPORTED_MODES)
            return f"Error: Unsupported mode. Supported: {modes_str}"
        return None
    
class FolderValidator:
    def __init__(self):
        pass

    def validate(self, folder_path):
        if self._contains_subfolders(folder_path):            
            return False
        return True
    
    def _contains_subfolders(self, folder_path):
        for f in os.listdir(folder_path):
            full = os.path.join(folder_path, f)
            if os.path.isdir(full):
                return True
        return False

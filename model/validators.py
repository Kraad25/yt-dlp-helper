import os

class DownloadValidator:
    SUPPORTED_MODES = {'mp3', 'mp4'}
    ERROR_MESSAGES = {
        'url_missing': "Error: URL missing",
        'folder_missing': "Error: Folder missing",
        'unsupported_mode': "Error: Unsupported mode. Supported: {}"
    }

    def __init__(self):
        pass
    
    def validate(self, url, folder, mode):
        if not url:
            return self.ERROR_MESSAGES['url_missing']
        if not folder:
            return self.ERROR_MESSAGES['folder_missing']
        if mode not in self.SUPPORTED_MODES:
            modes_str = ", ".join(self.SUPPORTED_MODES)
            return self.ERROR_MESSAGES['unsupported_mode'].format(modes_str)
        return None
    
class FolderValidator:
    def __init__(self):
        pass

    def validate(self, folder_path):
        return not self._contains_subfolders(folder_path)
    
    def _contains_subfolders(self, folder_path):
        return any(os.path.isdir(os.path.join(folder_path, f)) for f in os.listdir(folder_path))

import os

class DownloadValidator:
    SUPPORTED_MODES = {'mp3', 'mp4'}
    ERROR_MESSAGES = {
        'url_missing': "Error: URL missing",
        'unsupported_mode': "Error: Unsupported mode. Supported: {}"
    }

    @staticmethod
    def validate(url, mode):
        if not url:
            return DownloadValidator.ERROR_MESSAGES['url_missing']

        if mode not in DownloadValidator.SUPPORTED_MODES:
            modes_str = ", ".join(DownloadValidator.SUPPORTED_MODES)
            return DownloadValidator.ERROR_MESSAGES['unsupported_mode'].format(modes_str)
        return None
    
class FolderValidator:
    @staticmethod
    def validate(folder_path):
        return not FolderValidator._contains_subfolders(folder_path)
    
    @staticmethod
    def _contains_subfolders(folder_path):
        return any(os.path.isdir(os.path.join(folder_path, f)) for f in os.listdir(folder_path))

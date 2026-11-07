import os
from urllib.parse import urlparse

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

class WatcherValidator:
    MIN_POLL_INTERVAL = 15

    ERROR_MESSAGES = {
        'url_missing': "Section URL must be an https YouTube link",
        'empty_display_name': "Provide a section/display name",
        'empty_destination_path': "Destination's parent folder must exist",
        'wrong_type': "Poll interval must be a whole number, at least 15",
    }
    
    @staticmethod
    def validate(section_info: dict):
        if not WatcherValidator._is_url(section_info["section_url"]):
            return WatcherValidator.ERROR_MESSAGES['url_missing']
        if not WatcherValidator._has_section_name(section_info["section_name"]):
            return WatcherValidator.ERROR_MESSAGES['empty_display_name']
        if not WatcherValidator._has_destination_path(section_info["destination_path"]):
            return WatcherValidator.ERROR_MESSAGES['empty_destination_path']
        if not WatcherValidator._is_poll_interval_int(section_info["poll_interval"]):
            return WatcherValidator.ERROR_MESSAGES['wrong_type']

        return None

    @staticmethod
    def _is_url(url):
        try:
            parsed = urlparse(url.strip())
        except (AttributeError, ValueError):
            return False
        
        return parsed.scheme == "https" and parsed.hostname in ("youtube.com", "www.youtube.com")

    @staticmethod
    def _has_section_name(name) -> bool:
        return WatcherValidator._is_non_blank(name)

    @staticmethod
    def _has_destination_path(path) -> bool:
        if not WatcherValidator._is_non_blank(path):
            return False
        parent = os.path.dirname(path.strip().rstrip("/\\"))
        return os.path.isdir(parent)

    @staticmethod
    def _is_poll_interval_int(poll_interval) -> bool:          
        try:
            return int(poll_interval) >= WatcherValidator.MIN_POLL_INTERVAL
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _is_non_blank(text) -> bool:
        return bool(text and text.strip())

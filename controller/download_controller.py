import threading
from model.youtube_model import YoutubeModel

class DownloadController:    
    def __init__(self, view):
        self.view = view
        self.youtubeModel = YoutubeModel()
        self.SUPPORTED_MODES = ['mp3','mp4'] 

    def download_requested(self, data: dict, folderPath: str):
        error_msg = self._validate_data(data)
        if error_msg:
            self.view.update_status(error_msg)
            return
        url = data['url']
        mode = data['mode']
        quality = data['quality']

        if mode == 'mp4':
            self._request_video_downlad(url, folderPath, quality)
        else:
            self._request_audio_download(url, folderPath, quality)

        self.view.update_progress(0)
        self.view.update_status("Downloading")

    def _validate_data(self, data: dict):
        url = data.get("url", "")
        folder = data.get("folder", "")
        mode = data.get("mode", "")

        if not url:
            return "Error: URL missing"
        if not folder:
            return "Error: Folder missing"
        if mode not in self.SUPPORTED_MODES:
            modes_str = ", ".join(self.SUPPORTED_MODES)
            return f"Error: Unsupported mode. Supported: {modes_str}"
        return None
    
    def _request_audio_download(self, url, folderPath, quality):
        thread = threading.Thread(target=self._run_audio_download, args=(url, folderPath, quality), daemon=True)
        thread.start()

    def _request_video_downlad(self, url, folderPath, quality):
        thread = threading.Thread(target=self._run_video_download, args=(url, folderPath, quality), daemon=True)
        thread.start()

    
    def _run_audio_download(self, url: str, folderPath: str, quality: str):
        try:
            self.youtubeModel.audio_download(url=url, out_dir=folderPath, quality=quality, progress_hook=self._progress_hook)
            self.view.update_status("Done")
        except Exception as e:
            error_msg = str(e).lower()
            if "not a valid url" in error_msg:
                error_msg = "Not a Valid URL"
            else:
                error_msg = str(e) if str(e) else "Unknown error occurred"
            self.view.update_status(f"Error: {error_msg}")

    def _run_video_download(self, url: str, folderPath: str, quality: str):
        try:
            self.youtubeModel.video_download(
                url=url,
                out_dir=folderPath,
                quality=quality,
                progress_hook=self._progress_hook
            )
            self.view.update_status("Done")
        except Exception as e:
            error_msg = str(e).lower()
            if "not a valid url" in error_msg:
                error_msg = "Not a Valid URL"
            else:
                error_msg = str(e) if str(e) else "Unknown error occurred"
            self.view.update_status(f"Error: {error_msg}")


    def _progress_hook(self, d: dict):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            percent = int((downloaded / total) * 100)

            if hasattr(self.view, 'root') and self.view.root:
                self.view.root.after(0, self.view.update_progress, percent)
                self.view.root.after(0, self.view.update_status, f"Downloading: {percent}%")
        
        elif d['status'] == 'finished':
            if hasattr(self.view, 'root') and self.view.root:
                self.view.root.after(0, self.view.update_status, "Processing file...")
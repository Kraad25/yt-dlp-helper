import threading
from model.youtube_model import YoutubeModel

class DownloadController:
    def __init__(self, view):
        self.view = view
        self.youtubeModel = YoutubeModel()

    def download_requested(self, data: dict, folderPath: str):
        error_msg = self._validate_data(data)
        if error_msg:
            self.view.update_status(error_msg)
            return
        url = data['url']
        self.view.update_progress(0)
        self.view.update_status("Downloading")

        thread = threading.Thread(target=self._run_download, args=(url, folderPath), daemon=True)
        thread.start()

    def _validate_data(self, data: dict):
        url = data.get("url", "")
        folder = data.get("folder", "")
        mode = data.get("mode", "")

        if not url:
            return "Error: URL missing"
        if not folder:
            return "Error: Folder missing"
        if mode != 'mp3':
            return "Error: Mode must be mp3"
        return None
    
    def _run_download(self, url: str, folderPath: str):
        try:
            self.youtubeModel.download(url=url, out_dir=folderPath, progress_hook=self._progress_hook)
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

            self.view.root.after(0, self.view.update_progress, percent)
            self.view.root.after(0, self.view.update_status, f"Downloading: {percent}%")
        
        elif d['status'] == 'finished':
            self.view.root.after(0, self.view.update_status, "Processing file...")
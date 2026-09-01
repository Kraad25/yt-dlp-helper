import sys
import subprocess
import zipfile
import shutil
import threading
import urllib.request

from typing import Callable
from pathlib import Path

class UpdateService:
    def __init__(self):
        self._app_root = self._get_app_root()
        self._libs_dir = self._app_root / "libs"
        self._python_exe = self._app_root / "python-embed" / "python.exe"
        self._ffmpeg_dir = self._get_ffmpeg_dir()


    # Public
    def update_program(self, update_status: Callable):
        thread = threading.Thread(target=self._run_update_sequence, args=(update_status,), daemon=True)
        thread.start()

    # Private
    def _get_app_root(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent.parent
    
    def _get_ffmpeg_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return self._app_root / "_internal" / "ffmpeg"
        return self._app_root / "ffmpeg"
    
    def _update_yt_dlp(self, update_status: Callable) -> bool:
        update_status("Checking for yt-dlp updates")
        python = str(self._python_exe) if self._python_exe.exists() else sys.executable

        try:
            result = subprocess.run(
                [python, "-m", "pip", "install", "--upgrade",
                 "--target", str(self._libs_dir), "yt-dlp"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )

            update_status("Updated yt-dlp Successfully")
            return True
        
        except Exception as e:
            update_status(f"yt-dlp Update Failed: {str(e)}")
            return False
        
    def _update_ffmpeg(self, update_status: Callable) -> bool:
        update_status("Checking for ffmpeg updates")
        download_url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
        tmp_zip = self._app_root / "ffmpeg_update.zip"

        try:
            urllib.request.urlretrieve(download_url, tmp_zip)

            with zipfile.ZipFile(tmp_zip, "r") as zf:
                names = zf.namelist()

                ffmpeg_entry = next((n for n in names if n.endswith("bin/ffmpeg.exe")), None)
                ffprobe_entry = next((n for n in names if n.endswith("bin/ffprobe.exe")), None)

                if not ffmpeg_entry or not ffprobe_entry:
                    update_status("Could not locate ffmpeg/ffprobe inside the archive")
                    return False

                self._ffmpeg_dir.mkdir(parents=True, exist_ok=True)
                for entry, target_name in [(ffmpeg_entry, "ffmpeg.exe"), (ffprobe_entry, "ffprobe.exe")]:
                    with zf.open(entry) as src, open(self._ffmpeg_dir / target_name, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            tmp_zip.unlink()
            update_status("Updated ffmpeg Successfully")
            return True
        
        except Exception as e:
            if tmp_zip.exists():
                tmp_zip.unlink()
            update_status(f"ffmpeg Update Failed: {str(e)}")
            return False
        
    def _run_update_sequence(self, update_status: Callable) -> None:
        ytdlp_success = self._update_yt_dlp(update_status)
        if not ytdlp_success:
            return

        ffmpeg_success = self._update_ffmpeg(update_status)
        if not ffmpeg_success:
            return

        update_status("yt-dlp And ffmpeg Updated Successfully")
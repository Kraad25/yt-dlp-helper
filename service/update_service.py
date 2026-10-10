import re
import sys
import subprocess
import zipfile
import shutil
import threading
import urllib.request
import json

from typing import Callable
from pathlib import Path

class UpdateService:
    def __init__(self):
        self._app_root = self._get_app_root()
        self._libs_dir = self._app_root / "libs"
        self._python_exe = self._app_root / "python-embed" / "python.exe"
        self._ffmpeg_dir = self._get_ffmpeg_dir()

        self._PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"


    # Public
    def update_program(self, update_status: Callable):
        thread = threading.Thread(target=self._run_update_sequence, args=(update_status,), daemon=True)
        thread.start()

    def get_ytdlp_version(self) -> str:
        import yt_dlp.version
        return yt_dlp.version.__version__

    def get_ffmpeg_version(self) -> str:
        exe = self._ffmpeg_dir / "ffmpeg.exe"
        try:
            result = subprocess.run(
                [str(exe), "-version"], capture_output=True, text=True, timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            first_line = result.stdout.splitlines()[0]
            return first_line.removeprefix("ffmpeg version ").split(" Copyright")[0]
        except Exception:
            return "unknown"

    # Private
    def _get_app_root(self) -> Path:
        if getattr(sys, "frozen", False):
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parent.parent
    
    def _get_ffmpeg_dir(self) -> Path:
        if getattr(sys, "frozen", False):
            return self._app_root / "_internal" / "ffmpeg"
        return self._app_root / "ffmpeg"

    def _parse_version(self, version: str) -> tuple:
        return tuple(int(part) for part in version.split("."))

    def _get_latest_ytdlp_version(self) -> str:
        with urllib.request.urlopen(self._PYPI_URL, timeout=10) as response:
            return json.load(response)["info"]["version"]

    def _get_installed_ytdlp_version(self) -> str | None:
        try:
            text = (self._libs_dir / "yt_dlp" / "version.py").read_text()
            match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
            return match.group(1) if match else None
        except OSError:
            return None
    
    def _update_yt_dlp(self, update_status: Callable) -> str | None:
        update_status("Checking for yt-dlp updates")
        loaded = self.get_ytdlp_version()
        installed = self._get_installed_ytdlp_version() or loaded

        try:
            latest = self._get_latest_ytdlp_version()
            if self._parse_version(latest) <= self._parse_version(installed):
                if self._parse_version(installed) > self._parse_version(loaded):
                    return f"yt-dlp {installed} installed, restart to use it"
                return f"yt-dlp is up to date ({installed})"
        except Exception as e:
            update_status(f"Couldn't check for yt-dlp updates: {e}")
            return None

        update_status(f"yt-dlp {latest} available (you have {installed}), updating...")
        python = str(self._python_exe) if self._python_exe.exists() else sys.executable

        try:
            result = subprocess.run(
                [python, "-m", "pip", "install", "--upgrade",
                "--target", str(self._libs_dir), "yt-dlp"],
                capture_output=True, text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode != 0:
                last_line = (result.stderr.strip().splitlines() or ["unknown error"])[-1]
                update_status(f"yt-dlp update failed: {last_line}")
                return None
            return f"yt-dlp updated to {latest}, restart to use it"
        except Exception as e:
            update_status(f"yt-dlp update failed: {e}")
            return None
        
    def _update_ffmpeg(self, update_status: Callable) -> str | None:
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
                    return None

                self._ffmpeg_dir.mkdir(parents=True, exist_ok=True)
                for entry, target_name in [(ffmpeg_entry, "ffmpeg.exe"), (ffprobe_entry, "ffprobe.exe")]:
                    with zf.open(entry) as src, open(self._ffmpeg_dir / target_name, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            tmp_zip.unlink()
            return "ffmpeg re-downloaded"
        
        except Exception as e:
            if tmp_zip.exists():
                tmp_zip.unlink()
            update_status(f"ffmpeg Update Failed: {str(e)}")
            return None
        
    def _run_update_sequence(self, update_status: Callable) -> None:
        ytdlp_result = self._update_yt_dlp(update_status)
        if ytdlp_result is None:
            return

        ffmpeg_result = self._update_ffmpeg(update_status)
        if ffmpeg_result is None:
            return

        update_status(f"{ytdlp_result}. {ffmpeg_result}")
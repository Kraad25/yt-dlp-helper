import sys
import re
import subprocess
import zipfile
import shutil
import threading
import urllib.request
import json

from typing import Callable

from core.paths import install_dir, ffmpeg_directory
from core.job_logger import JobLogger, job_ids

version_log = JobLogger("version")

class UpdateService:
    def __init__(self):
        self._app_root = install_dir()
        self._libs_dir = self._app_root / "libs"
        self._python_exe = self._app_root / "python-embed" / "python.exe"
        self._ffmpeg_dir = ffmpeg_directory()

        self._PYPI_URL = "https://pypi.org/pypi/yt-dlp/json"
        self._FFMPEG_API_URL = "https://api.github.com/repos/yt-dlp/FFmpeg-Builds/releases/latest"
        self._FFMPEG_ASSET = "ffmpeg-master-latest-win64-gpl.zip"


    # Public
    def update_program(self, update_status: Callable, on_done: Callable = lambda: None):
        thread = threading.Thread(target=self._run_update_sequence, args=(update_status, on_done), daemon=True)
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
        except Exception as e:
            version_log.warning('ffmpeg Version Unknown Path:"%s" Error:"%s"', exe, e)
            return "unknown"

    # Private
    def _parse_version(self, version: str) -> tuple:
        return tuple(int(part) for part in version.split("."))

    def _get_latest_ytdlp_version(self) -> str:
        with urllib.request.urlopen(self._PYPI_URL, timeout=10) as response:
            return json.load(response)["info"]["version"]

    def _get_installed_ytdlp_version(self) -> str | None:
        path = self._libs_dir / "yt_dlp" / "version.py"
        try:
            text = path.read_text()
        except OSError as e:
            version_log.warning('Installed yt-dlp Version Unreadable Path:"%s" Error:"%s"', path, e)
            return None
        
        match = re.search(r"__version__\s*=\s*['\"]([^'\"]+)['\"]", text)
        if not match:
            version_log.warning('Installed yt-dlp Version Not Found In File Path:"%s"', path)
            return None
        
        return match.group(1)
    
    def _get_latest_ffmpeg_stamp(self) -> str:
        request = urllib.request.Request(
            self._FFMPEG_API_URL, headers={"User-Agent": "MediaDownloader"}
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            assets = json.load(response)["assets"]
        asset = next(a for a in assets if a["name"] == self._FFMPEG_ASSET)
        return asset["updated_at"]

    def _get_installed_ffmpeg_stamp(self) -> str | None:
        path = self._ffmpeg_dir / "ffmpeg_build.txt"
        try:
            return path.read_text().strip()
        
        except FileNotFoundError:
            version_log.info("ffmpeg Build Stamp Missing, will download")
            return None
        
        except OSError as e:
            version_log.warning('ffmpeg Build Stamp Unreadable Path:"%s" Error:"%s"', path, e)
            return None
    
    def _update_yt_dlp(self, update_status: Callable, log: JobLogger) -> str | None:
        update_status("Checking for yt-dlp updates")
        loaded = self.get_ytdlp_version()
        installed = self._get_installed_ytdlp_version() or loaded

        log.info("Checking For yt-dlp Updates Loaded:%s Installed:%s", loaded, installed)

        try:
            latest = self._get_latest_ytdlp_version()
            if self._parse_version(latest) <= self._parse_version(installed):
                if self._parse_version(installed) > self._parse_version(loaded):
                    log.info("yt-dlp Already Installed, restart needed Installed:%s Loaded:%s", installed, loaded)
                    return f"yt-dlp {installed} installed, restart to use it"

                log.info("yt-dlp Up To Date Version:%s", installed)
                return f"yt-dlp is up to date ({installed})"
            
        except Exception as e:
            log.error('yt-dlp Current Version Check Failed Error:"%s"', e)
            update_status(f"Couldn't check for yt-dlp updates: {e}")
            return None

        update_status(f"yt-dlp {latest} available (you have {installed}), updating...")
        log.info("yt-dlp Update Available From:%s To:%s", installed, latest)

        if self._python_exe.exists():
            python = str(self._python_exe)
        elif getattr(sys, "frozen", False):
            log.error('yt-dlp Install Skipped, python-embed not found Path:"%s"', self._python_exe)
            update_status("Updater unavailable: python-embed not found")
            return None
        else:
            python = sys.executable

        try:
            result = subprocess.run(
                [
                    python, "-m", "pip", "install", "--upgrade",
                    "--target", str(self._libs_dir), "yt-dlp"
                ], 
                capture_output=True, text=True, timeout=300,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,
            )
            if result.returncode != 0:
                last_line = (result.stderr.strip().splitlines() or ["unknown error"])[-1]
                log.error('yt-dlp Install Failed, pip returned an error Code:%s Pip:"%s"', result.returncode, last_line)
                update_status(f"yt-dlp update failed: {last_line}")
                return None
            
            log.info("yt-dlp Installed Version:%s", latest)
            return f"yt-dlp updated to {latest}, restart to use it"

        except subprocess.TimeoutExpired:
            log.error("yt-dlp Install Failed, pip timed out after 300 seconds")
            update_status("yt-dlp update timed out")
            return None
        
        except Exception as e:
            log.error('yt-dlp Install Failed Error:"%s"', e)
            update_status(f"yt-dlp update failed: {e}")
            return None
        
    def _update_ffmpeg(self, update_status: Callable, log: JobLogger) -> str | None:
        update_status("Checking for ffmpeg updates")

        try:
            latest_stamp = self._get_latest_ffmpeg_stamp()
        except Exception as e:
            log.error('ffmpeg Update Check Failed Error:"%s"', e)
            update_status(f"Couldn't check for ffmpeg updates: {e}")
            return None
        
        installed_stamp = self._get_installed_ffmpeg_stamp()        
        log.info('Checking ffmpeg Installed Build:"%s" Latest Build:"%s"', installed_stamp, latest_stamp)

        if latest_stamp == installed_stamp:
            log.info("ffmpeg Up To Date")
            return "ffmpeg is up to date"

        update_status("Downloading new ffmpeg build...")
        log.info("Downloading New ffmpeg Build")
        download_url = f"https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/{self._FFMPEG_ASSET}"
        tmp_zip = self._app_root / "ffmpeg_update.zip"

        try:
            with urllib.request.urlopen(download_url, timeout=30) as response, open(tmp_zip, "wb") as out:
                shutil.copyfileobj(response, out)

            with zipfile.ZipFile(tmp_zip, "r") as zf:
                names = zf.namelist()

                ffmpeg_entry = next((n for n in names if n.endswith("bin/ffmpeg.exe")), None)
                ffprobe_entry = next((n for n in names if n.endswith("bin/ffprobe.exe")), None)

                if not ffmpeg_entry or not ffprobe_entry:
                    raise RuntimeError("ffmpeg.exe or ffprobe.exe missing inside the archive")

                self._ffmpeg_dir.mkdir(parents=True, exist_ok=True)
                for entry, target_name in [(ffmpeg_entry, "ffmpeg.exe"), (ffprobe_entry, "ffprobe.exe")]:
                    with zf.open(entry) as src, open(self._ffmpeg_dir / target_name, "wb") as dst:
                        shutil.copyfileobj(src, dst)

            tmp_zip.unlink()
            (self._ffmpeg_dir / "ffmpeg_build.txt").write_text(latest_stamp)
            log.info('ffmpeg Installed Build:"%s"', latest_stamp)
            return "ffmpeg re-downloaded"
        
        except Exception as e:
            log.error('ffmpeg Install Failed Error:"%s"', e)
            if tmp_zip.exists():
                tmp_zip.unlink()
            update_status(f"ffmpeg Update Failed: {str(e)}")
            return None
        
    def _run_update_sequence(self, update_status: Callable, on_done: Callable) -> None:
        log = JobLogger(job_ids.next_id("up"))
        log.info("Update Start")
        ytdlp_result = None
        ffmpeg_result = None

        try:
            ytdlp_result = self._update_yt_dlp(update_status, log)
            ffmpeg_result = self._update_ffmpeg(update_status, log)

            if ytdlp_result and ffmpeg_result:
                update_status(f"{ytdlp_result}. {ffmpeg_result}")
            else:
                failed = [name for name, result in (("yt-dlp", ytdlp_result), ("ffmpeg", ffmpeg_result)) if result is None]
                update_status(f"Update incomplete, {' and '.join(failed)} failed. See the log for details")
                
        finally:
            log.info('Update End yt-dlp:"%s" ffmpeg:"%s"', ytdlp_result, ffmpeg_result)
            on_done()
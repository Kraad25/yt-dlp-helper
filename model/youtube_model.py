import yt_dlp
import os
import sys
from pathlib import Path

def _get_app_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

class YoutubeModel:
    def __init__(self):
        app_root = _get_app_root()
        self._ffmpeg_dir = app_root / "ffmpeg"

    def audio_download(self, url, out_dir, quality='192 kbps', progress_hook=None):
        quality_value = quality.split()[0]  # "192 kbps" -> "192"

        ydl_opts = {
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
            'ffmpeg_location': str(self._ffmpeg_dir),
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': quality_value,
                },
                {
                    'key': 'FFmpegMetadata',
                }
            ]
        }
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    def video_download(self, url, out_dir, quality='720p', progress_hook=None):
        quality_map = {
            "360p": 360,
            "480p": 480,
            "720p": 720,
            "1080p": 1080,
            "2K": 1440,
            "4K": 2160,
        }
        height = quality_map.get(quality, 720)
        
        ydl_opts = {
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': str(self._ffmpeg_dir),
            'format': f'bestvideo[ext=mp4][height<={height}]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'merge_output_format': 'mp4',
            'postprocessors': [
                {'key': 'FFmpegMetadata'},
            ]
        }
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
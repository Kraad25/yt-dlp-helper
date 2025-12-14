import yt_dlp
import os
import sys
from pathlib import Path


class YoutubeModel:
    def __init__(self, ffmpeg_dir: Path= None):
        self._ffmpeg_dir = ffmpeg_dir

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
        downloaded_file = None

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
            downloaded_file = ydl.prepare_filename(ydl.extract_info(url, download=False))
        return downloaded_file
import yt_dlp
import os

class YoutubeModel:
    def audio_download(self, url, out_dir, quality='192 kbps', progress_hook=None):
        quality_value = quality.split()[0]  # "192 kbps" -> "192"

        ydl_opts = {
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'format': 'bestaudio/best',
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
            'format': f'bestvideo[height<={height}]+bestaudio/best/best',
            'postprocessors': [
                {'key': 'FFmpegMetadata'},
                {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}
            ]
        }
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
import yt_dlp
import os

class YoutubeModel:
    def __init__(self):
        pass

    def download(self, url, out_dir, format_type='mp3', progress_hook = None):
        ydl_opts = {
            'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True
        }

        if format_type == 'mp3':
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            },
            {
            'key': 'FFmpegMetadata',
             }
            ]
        if progress_hook:
            ydl_opts['progress_hooks'] = [progress_hook]
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
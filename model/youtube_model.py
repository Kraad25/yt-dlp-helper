import yt_dlp
import os
import sys
from pathlib import Path


class YoutubeModel:
    def __init__(self, ffmpeg_dir: Path= None):
        self._ffmpeg_dir = ffmpeg_dir

        self._POSSIBLE_CHANNEL_SECTIONS = [
        ("Videos", "videos"),
        ("Shorts", "shorts"),
        ("Live", "streams"),
        ("Releases", "releases"),
        ("Playlists", "playlists"),
    ]

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

    def search_videos(self, query: str, limit: int = 8) -> list[dict]:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
        }
 
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
 
        results = []
        for entry in (info.get('entries') or []):
            video_id = entry.get('id')
            if not video_id:
                continue
 
            thumbnails = entry.get('thumbnails') or []
            thumb_url = thumbnails[-1]['url'] if thumbnails else None
 
            results.append({
                'id': video_id,
                'title': entry.get('title', 'Untitled'),
                'channel': entry.get('channel') or entry.get('uploader') or 'Unknown channel',
                'channel_url': entry.get('channel_url') or entry.get('uploader_url'),
                'duration': entry.get('duration'),
                'thumbnail_url': thumb_url,
                'url': f"https://www.youtube.com/watch?v={video_id}",
            })
        return results

    def get_channel_sections(self, channel_url: str) -> list[dict]:        
        base_url = channel_url.rstrip('/')
        return [
            {"title": title, "url": f"{base_url}/{slug}"}
            for title, slug in self._POSSIBLE_CHANNEL_SECTIONS
        ]

    def get_section_contents(self, section_url: str, limit: int = 8) -> list[dict]:        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
            'playlistend': limit,
        }
 
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(section_url, download=False)
 
        results = []
        for entry in (info.get('entries') or []):
            entry_id = entry.get('id')
            entry_url = entry.get('url')
            if not entry_id or not entry_url:
                continue
 
            if 'playlist?list=' in entry_url:
                results.append({
                    'type': 'playlist',
                    'id': entry_id,
                    'title': entry.get('title', 'Untitled'),
                    'thumbnail_url': self._get_playlist_cover(entry_url),
                    'url': entry_url,
                })
            else:
                thumbnails = entry.get('thumbnails') or []
                thumb_url = thumbnails[-1]['url'] if thumbnails else None
                results.append({
                    'type': 'video',
                    'id': entry_id,
                    'title': entry.get('title', 'Untitled'),
                    'duration': entry.get('duration'),
                    'thumbnail_url': thumb_url,
                    'url': f"https://www.youtube.com/watch?v={entry_id}",
                })
 
        return results

    ## Private Methods

    def _get_playlist_cover(self, playlist_url: str) -> str | None:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
            'playlistend': 1,   # <- only want the first track
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

        entries = info.get('entries') or []
        if not entries:
            return None

        first_track = entries[0]
        thumbnails = first_track.get('thumbnails') or []
        thumb_url = thumbnails[-1]['url'] if thumbnails else None

        return thumb_url
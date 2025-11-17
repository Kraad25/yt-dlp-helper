from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB
import subprocess
import os

class MetadataModel:
    def __init__(self):
        pass

    def get_audio_title(self, file_path):
        try:
            audio = MP3(file_path, ID3=ID3)
            return str(audio.tags.get('TIT2', "")) if audio.tags else ""
        except Exception:
            return ""
        
    def get_video_title(self, file_path):
        cmd = [
            "ffprobe", "-v", "error",
            "-show_entries", "format_tags=title",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except Exception:
            return ""

    def set_audio_metadata(self, file_path: str, title: str, artist: str, album: str) -> None:
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags["TIT2"] = TIT2(encoding=3, text=title)
            audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
            audio.tags["TALB"] = TALB(encoding=3, text=album)
            
            if "TRCK" in audio.tags:
                del audio.tags["TRCK"]
            
            audio.save()
            return True
        except Exception as e:
            return False
    
    def set_video_metadata(self, file_path: str, title: str = "", artist: str = "", album: str = "", comment: str = "") -> bool:
        temp_path = file_path + ".temp.mp4"
        cmd = [
            "ffmpeg", "-y", "-i", file_path,
            "-metadata", f"title={title}",
            "-metadata", f"artist={artist}",
            "-metadata", f"album={album}",
            "-metadata", f"comment={comment}",
            "-codec", "copy", temp_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.replace(temp_path, file_path)
            return True
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return False
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB

class MetadataModel:
    def __init__(self):
        pass

    def get_title(self, file_path):
        try:
            audio = MP3(file_path, ID3=ID3)
            return str(audio.tags.get('TIT2', "")) if audio.tags else ""
        except Exception:
            return ""

    def set_metadata(self, file_path: str, title: str, artist: str, album: str) -> None:
        try:
            audio = MP3(file_path, ID3=ID3)
            if audio.tags is None:
                audio.add_tags()
            audio.tags["TIT2"] = TIT2(encoding=3, text=title)
            audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
            audio.tags["TALB"] = TALB(encoding=3, text=album)
            audio.save()
        except Exception as e:
            print(f"Could not set metadata for {file_path}: {e}")
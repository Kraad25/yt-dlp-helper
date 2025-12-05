from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.id3 import ID3, TIT2, TPE1, TALB

MP4_TITLE_TAG   = "\xa9nam"
MP4_ARTIST_TAG  = "\xa9ART"
MP4_COMMENT_TAG = "\xa9cmt"

class MetadataModel:
    def get_audio_title(self, file_path):
        try:
            audio = MP3(file_path, ID3=ID3)
            return str(audio.tags.get('TIT2', "")) if audio.tags else ""
        except Exception:
            return ""
        
    def get_video_title(self, file_path):
        try:
            from mutagen.mp4 import MP4
            video = MP4(file_path)
            return video.get(MP4_TITLE_TAG, [""])[0]
        except Exception:
            return ""

    def set_audio_metadata(self, file_path: str, title: str, artist: str, album: str) -> bool:
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
    
    def set_video_metadata(self, file_path: str, title: str = "", artist: str = "", comment: str = "") -> bool:
        try:
            video = MP4(file_path)
            if title:
                video[MP4_TITLE_TAG] = title      
            if artist:
                video[MP4_ARTIST_TAG] = artist     
            if comment:
                video[MP4_COMMENT_TAG] = comment    
            
            video.save()
            return True
        except Exception as e:
            return False
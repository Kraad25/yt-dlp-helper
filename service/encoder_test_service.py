import sys
import subprocess
import threading
from pathlib import Path
from typing import Callable

def _get_app_root() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

class EncoderTestService:
    def __init__(self):
        app_root = _get_app_root()
        self._ffmpeg_dir = app_root / "ffmpeg"
        self._ffmpeg_path = self._ffmpeg_dir / 'ffmpeg.exe'

    def list_available_encoder(self, callback: Callable) -> list:
        threading.Thread(target=self._check_all_encoders, args=(callback,), daemon=True).start()

    def _check_all_encoders(self, callback: Callable):
        encoders = []
        
        encoder_tests = [
            ('h264_qsv', 'Intel Quick Sync (QSV)', 'QSV'),
            ('h264_nvenc', 'NVIDIA NVENC (H.264)', 'NVENC'),
            ('hevc_nvenc', 'NVIDIA NVENC (HEVC)', 'NVENC'),
            ('h264_amf', 'AMD AMF (H.264)', 'AMF'),
            ('hevc_amf', 'AMD AMF (HEVC)', 'AMF'),
            ('libx264', 'CPU', 'CPU'),
        ]
        
        for encoder, name, type_ in encoder_tests:
            if self.test_encoder_live(encoder):
                encoders.append({'encoder': encoder, 'name': name, 'type': type_})

        callback(encoders)    
    
    def test_encoder_live(self, encoder: str) -> bool:
        cmd = [
            str(self._ffmpeg_path), '-f', 'lavfi', '-i', 'nullsrc',
            '-c:v', encoder, '-frames:v', '1', '-f', 'null', '-'
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=5, startupinfo=si)
        return result.returncode == 0
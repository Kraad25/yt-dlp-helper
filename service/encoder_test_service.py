import sys
import time
import json
import subprocess
import threading
from pathlib import Path
from typing import Callable

CACHE_MAX_AGE_SECONDS = 10*(24 * 60 * 60)  # 10 day

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

        config_dir = app_root / "config"
        config_dir.mkdir(exist_ok=True)
        self._cache_path = config_dir / "encoder_cache.json"

    def list_available_encoder(self, callback: Callable, force_refresh: bool = False) -> None:
        if not force_refresh:
            cached = self._read_cache()
            if cached is not None:
                threading.Thread(target=callback, args=(cached,), daemon=True).start()
                return
        
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
            if self._test_encoder_live(encoder):
                encoders.append({'encoder': encoder, 'name': name, 'type': type_})

        self._write_cache(encoders)
        callback(encoders)    
    
    def _test_encoder_live(self, encoder: str) -> bool:
        cmd = [
            str(self._ffmpeg_path), '-f', 'lavfi', '-i', 'nullsrc',
            '-c:v', encoder, '-frames:v', '1', '-f', 'null', '-'
        ]
        result = subprocess.run(cmd, capture_output=True, timeout=5, startupinfo=si)
        return result.returncode == 0

    def _read_cache(self):
        if not self._cache_path.exists():
            return None
        try:
            with open(self._cache_path, 'r') as f:
                data = json.load(f)
            timestamp = data.get("timestamp", 0)
            if (time.time() - timestamp) > CACHE_MAX_AGE_SECONDS:
                return None
            return data.get("encoders", [])
        except Exception:
            return None

    def _write_cache(self, encoders: list):
        data = {"timestamp": time.time(), "encoders": encoders}
        try:
            with open(self._cache_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass
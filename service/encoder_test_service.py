import time
import json
import subprocess
import threading
from typing import Callable

from core.paths import user_data_dir, ffmpeg_directory
from core.job_logger import JobLogger

CACHE_MAX_AGE_SECONDS = 10*(24 * 60 * 60)  # 10 day
ENCODER_TEST_TIMEOUT_SECONDS = 15

log = JobLogger("encoder")

si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

class EncoderTestService:
    def __init__(self):
        self._ffmpeg_dir = ffmpeg_directory()
        self._ffmpeg_path = self._ffmpeg_dir / 'ffmpeg.exe'

        config_dir = user_data_dir() / "config"
        config_dir.mkdir(exist_ok=True)
        self._cache_path = config_dir / "encoder_cache.json"

    def list_available_encoder(self, callback: Callable, force_refresh: bool = False) -> None:
        if not force_refresh:
            cached = self._read_cache()
            if cached is not None:
                log.info("Encoder Cache Used Found:%s", [e.get("encoder") for e in cached])
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
        
        try:
            for encoder, name, type_ in encoder_tests:
                if self._test_encoder_live(encoder):
                    encoders.append({'encoder': encoder, 'name': name, 'type': type_})

            if encoders:
                self._write_cache(encoders)
        except Exception:
            log.exception("Encoder Detection Crashed, falling back to CPU")
            encoders = []

        log.info("Encoder Detection Done Found=%s", [e['encoder'] for e in encoders])
        callback(encoders)    
    
    def _test_encoder_live(self, encoder: str) -> bool:
        cmd = [
            str(self._ffmpeg_path), '-f', 'lavfi', '-i', 'nullsrc',
            '-c:v', encoder, '-frames:v', '1', '-f', 'null', '-'
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True,
                timeout=ENCODER_TEST_TIMEOUT_SECONDS, startupinfo=si,
            )

        except  subprocess.TimeoutExpired:
            log.warning("Encoder Test Timed Out Encoder=%s Timeout=%ss", encoder, ENCODER_TEST_TIMEOUT_SECONDS)
            return False
        except OSError as e:
            log.warning('Encoder Test Could Not Run Encoder=%s Error="%s"', encoder, e)
            return False
        
        log.info("Encoder Test Encoder=%s Available=%s", encoder, result.returncode == 0)
        return result.returncode == 0

    def _ffmpeg_mtime(self) -> float | None:
        try:
            return self._ffmpeg_path.stat().st_mtime
        except OSError:
            return None

    def _read_cache(self):
        if not self._cache_path.exists():
            return None
        try:
            with open(self._cache_path, 'r') as f:
                data = json.load(f)

        except Exception as e:
            log.warning('Encoder Cache Unreadable, re-testing error="%s"', e)
            return None

        timestamp = data.get("timestamp", 0)
        if (time.time() - timestamp) > CACHE_MAX_AGE_SECONDS:
            log.info("Encoder Cache Too Old, re-testing")
            return None
        
        if data.get("ffmpeg_mtime") != self._ffmpeg_mtime():
            log.info("Encoder Cache Stale (ffmpeg changed), re-testing")
            return None
        
        return data.get("encoders", [])

    def _write_cache(self, encoders: list):
        data = {"timestamp": time.time(), "ffmpeg_mtime": self._ffmpeg_mtime(), "encoders": encoders}
        try:
            with open(self._cache_path, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            log.warning('Encoder Cache Not Saved error="%s"', e)
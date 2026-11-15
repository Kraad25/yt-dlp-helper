import os
import json
import tempfile
import threading
import subprocess
from pathlib import Path

si = subprocess.STARTUPINFO()
si.dwFlags |= subprocess.STARTF_USESHOWWINDOW

class VideoProcessingService:
    def __init__(self, ffmpeg_dir: Path):   
        self._ffmpeg_dir = ffmpeg_dir
        self._ffprobe_path = self._ffmpeg_dir / 'ffprobe.exe'

    def transcode(self, input_file: str, encoder: str, cancel: threading.Event) -> None:
        try:
            if cancel.is_set():
                return
            
            if self._is_h264_video(input_file):
                return
            
            encoder_args = self._build_video_encoder_args(encoder)
            self._transcode_with_encoder(input_file, encoder_args, cancel)

        except Exception as e:
            raise Exception(f"Transcoding Failed: {e}")

    def _is_h264_video(self, input_file: str) -> bool:
        try:
            probe_data = self._probe_video_stream(input_file)
            codec = probe_data['streams'][0].get('codec_name', '')
            return codec == 'h264'
        except Exception:
            return False # Assumes needs transcoding on error
        
    def _transcode_with_encoder(self, input_file: str, encoder_args: list, cancel: threading.Event) -> None:
        input_path = Path(input_file)
        temp_output = input_path.with_stem(f"{input_path.stem}_temp")

        cmd = [
            str(self._ffmpeg_dir / "ffmpeg.exe"),
            "-y",
            "-loglevel", "error",
            "-i", str(input_path),
            "-map", "0:v:0",
            "-map", "0:a:0?",
            *encoder_args,           
            '-c:a', 'copy',
            "-movflags", "+faststart",
            str(temp_output),
        ]

        with tempfile.TemporaryFile() as error_log:
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=error_log,
                startupinfo=si,
            )

            while True:
                try:
                    process.wait(timeout=0.2)
                    break
                except subprocess.TimeoutExpired:
                    if cancel.is_set():
                        process.kill()
                        process.wait()
                        temp_output.unlink(missing_ok=True)
                        return

            if process.returncode != 0:
                error_log.seek(0)
                message = error_log.read().decode(errors="replace").strip()
                temp_output.unlink(missing_ok=True)
                raise Exception(f"FFmpeg error: {message}")

        os.replace(temp_output, input_path)
        
    def _probe_video_stream(self, input_file: str) -> dict:
        cmd = self._build_probe_cmd(input_file)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, startupinfo=si)
       
        if result.returncode != 0:
            raise RuntimeError("Probe failed")
       
        return json.loads(result.stdout)
   
    def _build_probe_cmd(self, input_file: str) -> list:
        return [
            str(self._ffprobe_path),
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=codec_name,width,height,bit_rate,avg_frame_rate',
            '-of', 'json',
            input_file
        ]

    def _build_video_encoder_args(self, encoder) -> list:
        if encoder == 'QSV': # Intel QSV
            return ['-c:v', 'h264_qsv', '-preset', 'fast', '-global_quality', '18']
        elif encoder == 'NVENC': # NVIDIA GPU
            return ['-c:v', 'h264_nvenc', '-preset', 'fast', '-cq', '18']
        elif encoder == 'AMF': # AMD AMF
            return [
                '-c:v', 'h264_amf',
                '-quality', 'balanced',
                '-rc', 'cqp',
                '-qp_i', '18',
                '-qp_p', '18',
                '-qp_b', '18'
            ]
        
        else:  # CPU
            return ['-c:v', 'libx264', '-preset', 'fast', '-crf', '23']
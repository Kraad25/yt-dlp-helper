import json
import shutil
import subprocess
from pathlib import Path

class VideoProcessingService:
    def __init__(self, ffmpeg_dir: Path):   
        self._ffmpeg_dir = ffmpeg_dir
        self._ffprobe_path = self._ffmpeg_dir / 'ffprobe.exe'

    def transcode(self, input_file: str) -> None:
        print("Hello")
        try:
            if self._is_h264_video(input_file):
                return
            self._transcode_to_h264_qsv(input_file)
        except Exception as e:
            raise Exception(f"Transcoding Failed: {e}")

    def _is_h264_video(self, input_file: str) -> bool:
        try:
            probe_data = self._probe_video_stream(input_file)
            codec = probe_data['streams'][0].get('codec_name', '')
            return codec == 'h264'
        except:
            return False # Assumes needs transcoding on error
        
    def _transcode_to_h264_qsv(self, input_file: str) -> None:
        input_path = Path(input_file)
        temp_output = input_path.with_stem(f"{input_path.stem}_temp")

        cmd = [
            str(self._ffmpeg_dir / 'ffmpeg.exe'),
            '-y',
            '-i', str(input_path),

            # Include first video + first audio stream
            '-map', '0:v:0',
            '-map', '0:a:0?',

            # Video → H.264 (QSV)
            '-c:v', 'h264_qsv',
            '-preset', 'veryfast',
            '-global_quality', '23',

            # Audio → copy unchanged
            '-c:a', 'copy',

            '-movflags', '+faststart',
            str(temp_output),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            temp_output.unlink(missing_ok=True)
            raise Exception(f"FFmpeg error: {result.stderr}")

        input_path.unlink()
        shutil.move(str(temp_output), str(input_path))
        
    def _probe_video_stream(self, input_file: str) -> dict:
        cmd = self._build_probe_cmd(input_file)
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
       
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

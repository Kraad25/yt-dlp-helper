import errno
import re

class ErrorHandlingService:
    RULES = [
        (r"confirm your age|age[- ]restricted", "Video is age-restricted"),
        (r"private video", "Video is private"),
        (r"not available in your (country|region)", "Video is not available in your region"),
        (r"video unavailable", "Video is unavailable"),
        (r"is not a valid url|unsupported url", "Invalid URL format"),
        (r"HTTP Error 403\b", "Access denied (403)"),
        (r"HTTP Error 404\b", "Video not found (404)"),
        (r"requested format is not available|no video formats", "No video formats available"),
        (r"no space left|disk full", "Not enough disk space"),
        (r"read-only", "Folder is read-only"),
        (r"probe failed", "Cannot read video file"),
        (r"ffmpeg error", "FFmpeg failed while processing the video"),
        (r"transcoding failed", "Failed to process video"),
    ]

    def classify_error(self, error: Exception = None) -> str:
        if error is None:
            return "Error: Unknown"

        if isinstance(error, PermissionError):
            return "Error: Permission denied - check folder access"
        if isinstance(error, FileNotFoundError):
            return "Error: File not found - may have been moved"
        if isinstance(error, OSError) and error.errno == errno.ENOSPC:
            return "Error: Not enough disk space"

        text = str(error)
        if "cancelled by user" in text.lower():
            return "Download cancelled"

        for pattern, message in self.RULES:
            if re.search(pattern, text, re.I):
                return f"Error: {message}"

        return f"Error: {text}"
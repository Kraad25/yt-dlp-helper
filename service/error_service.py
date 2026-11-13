class ErrorHandlingService:
    def __init__(self):
        self._patterns = {
            # Download errors
            "is not a valid url": "Invalid URL format",
            "video unavailable": "Video is unavailable",
            "private": "Video is private",
            "geo": "Video is not available in your region",
            "403": "Access denied (403)",
            "404": "Video not found (404)",
            "no formats": "No video formats available",
            "age-restricted": "Video is age-restricted",
            
            # File/System errors
            "permission denied": "Permission denied - check folder access",
            "no space": "Not enough disk space",
            "disk full": "Not enough disk space",
            "file not found": "File not found - may have been moved",
            "read-only": "Folder is read-only",

            # FFmpeg/Transcoding errors
            "probe failed": "Cannot read video file",
            "transcoding failed": "Failed to process video",
            "codec": "Unsupported video codec",
            "ffmpeg": "FFmpeg error - check installation",
        }

    def classify_error(self, error: Exception=None):
        if error is None:
            return "Error: Unknown"

        error_str = str(error).lower()

        # Special-Case: Exceptions raised on purpose
        if "cancelled by user" in error_str:
            return "Download cancelled"
        
        # Generic Errors
        for pattern, value in self._patterns.items():
            if pattern in error_str:
                return f"Error: {value}"
            
        # Fallback
        return f"RawError: {str(error)}"
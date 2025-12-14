class ErrorHandlingService:
    def __init__(self):
        self._patterns = {
            # Download errors
            "is not a valid url": "Invalid URL format",
            "video unavailable": "Video is unavailable",
            "private": "Video is private",
            "age": "Video is age-restricted",
            "geo": "Video is not available in your region",
            "403": "Access denied (403)",
            "404": "Video not found (404)",
            "no formats": "No video formats available",
            
            # FFmpeg/Transcoding errors
            "ffmpeg": "FFmpeg error - check installation",
            "probe failed": "Cannot read video file",
            "transcoding failed": "Failed to process video",
            "codec": "Unsupported video codec",
            
            # File/System errors
            "permission denied": "Permission denied - check folder access",
            "no space": "Not enough disk space",
            "disk full": "Not enough disk space",
            "file not found": "File not found - may have been moved",
            "read-only": "Folder is read-only",
        }

    def handle_error(self, update_status, error: Exception=None, custom_msg: str=None):
        if custom_msg is not None:
            update_status(custom_msg)
            return
        
        if error is None:
            update_status("Error: Unknown")
            return

        error_str = str(error).lower()

        # Special-Case: Exceptions raised on purpose
        if "cancelled by user" in error_str:
            update_status("Download cancelled")
            return
        
        # Generic Errors
        for pattern, value in self._patterns.items():
            if pattern in error_str:
                update_status(f"Error: {value}")
                return
            
        # Fallback
        update_status(f"RawError: {str(error)}")
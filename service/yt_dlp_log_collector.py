class YtdlpLogCollector:
    def __init__(self, log):
        self._log = log
        self.errors: list[str] = []

    def debug(self, msg):
        pass

    def info(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        try:
            self.errors.append(str(msg))
            self._log.error('yt-dlp: "%s"', msg)
        except Exception:
            pass
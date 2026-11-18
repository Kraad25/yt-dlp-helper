import sys
import logging
import threading
from logging.handlers import RotatingFileHandler

from core.paths import user_data_dir

class AppLogger:
        
    LOG_FORMAT = "%(asctime)s %(levelname)s [%(threadName)s] %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    MAX_BYTES = 2_000_000
    BACKUP_COUNT = 1

    def __init__(self):
        self._crash_log = logging.getLogger("crash")

    # Public Methods
    def setup_logging(self):
        root = logging.getLogger()
        root.setLevel(logging.INFO)
        try:
            log_dir = user_data_dir() / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            handler = RotatingFileHandler(
                log_dir / "app.log",
                maxBytes=self.MAX_BYTES,
                backupCount=self.BACKUP_COUNT,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter(self.LOG_FORMAT, self.DATE_FORMAT))
            root.addHandler(handler)
        except OSError:
            # Safe: the app must still start without a log file
            root.addHandler(logging.NullHandler())

    def install_crash_handlers(self):
        sys.excepthook = self._on_main_thread_error
        threading.excepthook = self._on_worker_thread_error

    def install_tk_crash_handler(self, tk_root):
        tk_root.report_callback_exception = self._on_tk_callback_error

    # Private Methods
    def _on_main_thread_error(self, exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        self._crash_log.critical("Uncaught error in main thread", exc_info=(exc_type, exc, tb))

    def _on_worker_thread_error(self, args):
        if args.exc_type is SystemExit:
            return
        name = args.thread.name if args.thread else "unknown"
        self._crash_log.critical(
            "Uncaught error in thread %s", name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    def _on_tk_callback_error(self, exc_type, exc, tb):
        self._crash_log.error("Error in Tk callback", exc_info=(exc_type, exc, tb))
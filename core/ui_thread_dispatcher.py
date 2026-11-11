import queue
import logging

class UiThreadDispatcher:
    def __init__(self, root, interval_ms: int = 10):
        self._root = root
        self._interval = interval_ms
        self._queue = queue.SimpleQueue()
        self._root.after(self._interval, self._drain)

    def post(self, fn, *args, **kwargs):
        self._queue.put((fn, args, kwargs))

    def wrap(self, fn):
        return lambda *a, **k: self.post(fn, *a, **k)

    def _drain(self):
        try:
            while True:
                fn, args, kwargs = self._queue.get_nowait()
                try:
                    fn(*args, **kwargs)
                except Exception:
                    logging.getLogger(__name__).exception("UI callback failed")
        except queue.Empty:
            pass
        self._root.after(self._interval, self._drain)
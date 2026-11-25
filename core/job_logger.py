import itertools
import logging
import threading

class JobIds:
    def __init__(self):
        self._counters = {}
        self._lock = threading.Lock()

    def next_id(self, kind: str) -> str:
        with self._lock:
            counter = self._counters.setdefault(kind, itertools.count(1))
            return f"{kind}-{next(counter):04d}"

class JobLogger(logging.LoggerAdapter):
    def __init__(self, job_id: str):
        super().__init__(logging.getLogger("job"), {})
        self.job_id = job_id

    def process(self, msg, kwargs):
        return f"[{self.job_id}] {msg}", kwargs


job_ids = JobIds()
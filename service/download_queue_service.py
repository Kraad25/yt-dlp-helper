import threading
from collections import deque
from typing import Callable

from core.job_logger import JobLogger

log = JobLogger("queue")

class WorkLine:
    def __init__(self, name: str, worker_count: int, handler: Callable, on_skipped: Callable, limit: int | None = None, on_queue_update: Callable | None = None):

        self._name = name
        self._worker_count = worker_count
        self._handler = handler
        self._on_skipped = on_skipped
        self._limit = limit
        self._on_queue_update = on_queue_update

        self._waiting = deque()
        self._running = 0

        self._queue_lock = threading.Condition()

    def start_worker_loop(self):
        for worker_id in range(1, self._worker_count + 1):
            threading.Thread(target=self._worker_loop, args=(worker_id,), daemon=True).start()

    def append_job(self, job) -> bool:
        with self._queue_lock:

            # Reject a job if queue is full
            if self._limit is not None and len(self._waiting) >= self._limit:
                log.warning("Job Refused, line is full Id:%s Line:%s Limit:%s", job.log.job_id, self._name, self._limit)
                return False

            self._waiting.append(job)
            log.info("Job Queued Id:%s Line:%s Waiting:%s", job.log.job_id, self._name, len(self._waiting))
            self._queue_lock.notify() # Notify a worker

        self._send_queue_update()
        return True

    def get_position_of(self, job) -> int:
        with self._queue_lock:
            try:
                return list(self._waiting).index(job) + 1 # 1 means next in line
            except ValueError:
                return 0 # 0 means not waiting (running or finished)

    def get_waiting_count(self) -> int:
        with self._queue_lock:
            return len(self._waiting)

    def get_running_count(self) -> int:
        with self._queue_lock:
            return self._running

    def _send_queue_update(self):
        if not self._on_queue_update:
            return
        try:
            self._on_queue_update()
        except Exception as e:
            log.error('Queue Update Callback Crashed Line:%s Error:"%s"', self._name, e)

    # Private Methods
    def _take(self):
        with self._queue_lock:
            while not self._waiting:
                self._queue_lock.wait()

            job = self._waiting.popleft() # FIFO
            self._running += 1

        self._send_queue_update()    
        return job

    def _worker_loop(self, worker_id: int):
        log.info("Worker Started Line:%s Id:%s", self._name, worker_id)
        while True:
            job = self._take()
            try:
                if job.cancel.is_set():
                    log.info("Job Skipped, cancelled while waiting Id:%s Line:%s", job.log.job_id, self._name)
                    self._on_skipped(job)

                else:
                    log.info("Job Started Id:%s Line:%s Worker:%s", job.log.job_id, self._name, worker_id)
                    self._handler(job)

            except Exception as e:
                log.error('Job Handler Crashed Id:%s Line:%s Error:"%s"', job.log.job_id, self._name, e)

            finally:
                with self._queue_lock:
                    self._running -= 1

                self._send_queue_update()

class DownloadQueue:
    def __init__(self, download_workers:int, transcode_workers:int, queue_limit:int, run_download:Callable, run_transcode:Callable, on_skipped:Callable, on_queue_update:Callable):
        self._download_line = WorkLine(
            name="download", 
            worker_count=download_workers, 
            handler=run_download, 
            on_skipped=on_skipped, 
            limit=queue_limit, 
            on_queue_update=on_queue_update
        )

        self._transcode_line = WorkLine(
            name="transcode", 
            worker_count=transcode_workers, 
            handler=run_transcode,
            limit=None,
            on_skipped=on_skipped,
            on_queue_update=on_queue_update
        )

    def start_workers(self):
        self._download_line.start_worker_loop()
        self._transcode_line.start_worker_loop()

    def add_job(self, job) -> bool:
        return self._download_line.append_job(job)

    def handover_to_transcode(self, job) -> bool:
        return self._transcode_line.append_job(job)

    def get_position_of(self, job) -> int:
        return self._download_line.get_position_of(job)

    def counts(self) -> dict:
        return {
            "downloading": self._download_line.get_running_count(),
            "transcoding": self._transcode_line.get_running_count(),
            "waiting": self._download_line.get_waiting_count(),
            "waiting_transcode": self._transcode_line.get_waiting_count(),
        }
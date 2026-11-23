from typing import Callable

from model.settings_model import SettingsModel

from service.encoder_test_service import EncoderTestService
from service.update_service import UpdateService

from core.job_logger import JobLogger

log = JobLogger("settings")

class EncoderScope:
    HOME = "home"
    EXPLORE = "explore"

class SettingsController:
    _ENCODER_KEYS = {
            EncoderScope.HOME: SettingsModel.HOME_ENCODER,
            EncoderScope.EXPLORE: SettingsModel.EXPLORE_ENCODER,
        }

    PARALLEL_DOWNLOAD_CHOICES = [1, 2, 3, 4]
    PARALLEL_TRANSCODING_CHOICES = [1, 2]
    DOWNLOAD_QUEUE_LIMIT_CHOICES = [50, 100, 200]
    
    def __init__(self):
        self._model = SettingsModel()
        self._encoder_tester = EncoderTestService()
        self._update_service = UpdateService()

        self._available: dict[str, str] | None = None

        self._on_encoders_done = None
        self._updating = False

    # Public Methods: versions
    def get_ytdlp_version(self) -> str:
        return self._update_service.get_ytdlp_version() or "unknown"

    def get_ffmpeg_version(self) -> str:
        return self._update_service.get_ffmpeg_version() or "unknown"

    # Public Methods: encoders
    def detect_encoders(self, on_done: Callable, force_refresh: bool = False):
        self._on_encoders_done = on_done
        self._encoder_tester.list_available_encoder(self._store_encoders, force_refresh=force_refresh)

    def set_general_encoder(self, encoder: str):
        if not encoder:
            return
        self._model.set(SettingsModel.GENERAL_ENCODER, encoder)

    def get_available_encoders(self) -> list[dict]:
        if self._available is None:
            return [{"type": "CPU", "name": "CPU (default)"}]
        return [{"type": t, "name": n} for t, n in self._available.items()]

    def get_general_encoder(self) -> str:
        saved = self._model.get(SettingsModel.GENERAL_ENCODER)
        return saved if self._is_usable(saved) else "CPU"

    def get_encoder(self, scope: str) -> str:
        own = self._model.get(self._ENCODER_KEYS[scope])
        if own and self._is_usable(own):
            log.info("Encoder Selected Scope:%s Type:%s Source:own", scope, own)
            return own

        if own:
            log.warning("Saved Encoder Not Available Scope:%s Type:%s, following General", scope, own)

        general = self.get_general_encoder()
        log.info("Encoder Selected Scope=%s Type:%s Source:general", scope, general)
        return general

    # Public Methods: Download & Transcode Queue
    ## Getters
    def get_parallel_downloads(self) -> int:
        return self._get_choice(SettingsModel.GENERAL_PARALLEL_DOWNLOADS, self.PARALLEL_DOWNLOAD_CHOICES)
    
    def get_parallel_transcodes(self) -> int:
        return self._get_choice(SettingsModel.GENERAL_PARALLEL_TRANSCODES, self.PARALLEL_TRANSCODING_CHOICES)

    def get_queue_limit(self) -> int:
        return self._get_choice(SettingsModel.GENERAL_QUEUE_LIMIT, self.DOWNLOAD_QUEUE_LIMIT_CHOICES)

    ## Setters
    def set_parallel_downloads(self, value):
        self._set_choice("Parallel Downloads", SettingsModel.GENERAL_PARALLEL_DOWNLOADS, value, self.PARALLEL_DOWNLOAD_CHOICES)

    def set_parallel_transcodes(self, value):
        self._set_choice("Parallel Transcodes", SettingsModel.GENERAL_PARALLEL_TRANSCODES, value, self.PARALLEL_TRANSCODING_CHOICES)

    def set_queue_limit(self, value):
        self._set_choice("Queue Limit", SettingsModel.GENERAL_QUEUE_LIMIT, value, self.DOWNLOAD_QUEUE_LIMIT_CHOICES)

    # Public Methods: updates
    def check_for_updates(self, on_status: Callable, on_done: Callable) -> bool:
        if self._updating:
            return False

        self._updating = True
        self._update_service.update_program(
            update_status=on_status,
            on_done=lambda: self._finish_update(on_done),
        )
        return True

    # Private Methods
    def _is_usable(self, encoder: str) -> bool:
        return self._available is None or encoder in self._available

    def _finish_update(self, on_done: Callable):
        self._updating = False
        on_done()

    def _store_encoders(self, encoders: list):
        available = {}
        for info in encoders:
            available.setdefault(info["type"], info["name"])
        available["CPU"] = "CPU (default)"

        self._available = available
        self._on_encoders_done()

    def _get_choice(self, key: str, choices: list) -> int:
        default = SettingsModel.DEFAULTS[key]
        try:
            value = int(self._model.get(key))
        except (TypeError, ValueError):
            return default
        return value if value in choices else default

    def _set_choice(self, label: str, key: str, value, choices: list):
        try:
            wanted = int(value)
        except (TypeError, ValueError):
            log.warning('%s Not Changed, not a number Value:"%s"', label, value)
            return

        if wanted not in choices:
            log.warning("%s Not Changed, %s is not an allowed choice", label, wanted)
            return

        old = self._get_choice(key, choices)
        if wanted == old:
            return

        self._model.set(key, wanted)
        log.info("%s Changed From:%s To:%s", label, old, wanted)
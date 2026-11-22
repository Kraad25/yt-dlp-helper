from typing import Callable

from model.settings_model import SettingsModel

from service.encoder_test_service import EncoderTestService
from service.update_service import UpdateService

from core.job_logger import JobLogger

log = JobLogger("encoder")

class EncoderScope:
    HOME = "home"
    EXPLORE = "explore"

class SettingsController:
    _ENCODER_KEYS = {
            EncoderScope.HOME: SettingsModel.HOME_ENCODER,
            EncoderScope.EXPLORE: SettingsModel.EXPLORE_ENCODER,
        }
    
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
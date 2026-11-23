import os
import json

from core.paths import user_data_dir
from core.job_logger import JobLogger

from model.validators import WatcherValidator

log = JobLogger("settings")

class SettingsModel:
    GENERAL_ENCODER = "general.encoder"
    GENERAL_PARALLEL_DOWNLOADS = "general.parallel_downloads"
    GENERAL_PARALLEL_TRANSCODES = "general.parallel_transcodes"
    GENERAL_QUEUE_LIMIT = "general.queue_limit"

    HOME_ENCODER = "home.encoder"

    EXPLORE_ENCODER = "explore.encoder"
    EXPLORE_AUTO_DOWNLOAD = "explore.auto_download"
    EXPLORE_POLL_INTERVAL = "explore.poll_interval"
    EXPLORE_FORMAT = "explore.format"

    # None means "not chosen here, follow General"
    DEFAULTS = {
        GENERAL_ENCODER: "CPU",
        GENERAL_PARALLEL_DOWNLOADS: 2,
        GENERAL_PARALLEL_TRANSCODES: 1,
        GENERAL_QUEUE_LIMIT: 200,

        HOME_ENCODER: None,
        
        EXPLORE_ENCODER: None,
        EXPLORE_AUTO_DOWNLOAD: False,
        EXPLORE_POLL_INTERVAL: WatcherValidator.MIN_POLL_INTERVAL,
        EXPLORE_FORMAT: "mp3",
    }

    def __init__(self):
        config_dir = user_data_dir() / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        self._config_path = config_dir / "settings.json"

        self._config = self._read_config()

    # Public Methods
    def get(self, key: str):
        self._check_key(key)
        return self._config.get(key, self.DEFAULTS[key])

    def set(self, key: str, value):
        self._check_key(key)
        self._config[key] = value
        self._write_config()

    # Private Methods
    def _check_key(self, key: str):
        if key not in self.DEFAULTS:
            raise KeyError(f"Unknown setting: {key}")

    def _read_config(self) -> dict:
        try:
            with open(self._config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            return config if isinstance(config, dict) else {}

        except FileNotFoundError:
            return {}

        except (json.JSONDecodeError, OSError) as e:
            log.warning('Settings Unreadable, using defaults Error:"%s"', e)
            return {}

    def _write_config(self):
        temp_path = self._config_path.with_suffix(".temp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=4)
            os.replace(temp_path, self._config_path)
        except OSError as e:
            log.error('Settings Not Saved Error:"%s"', e)
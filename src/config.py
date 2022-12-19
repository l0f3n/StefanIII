import json
import os
from pathlib import Path

from log import get_logger

logger = get_logger(__name__)

class Config:

    DEFAULT = {
        "token": "YOUR-DISCORD-BOT-TOKEN",
        "spotify_id": "YOUR-SPOTIFY-ID",
        "spotify_secret": "YOUR-SPOTIFY-SECRET",
        "prefix": "-",
        "title_max_length": 30,
        "is_looping_queue": True,
        "is_looping_song": False,
        "before_current": 10,
        "after_current": 20,
        "message_delete_delay": 2, # Can be set to False to disable message deletion
        "nightcore": False,
        "nightcore_tempo": 1.2,
        "nightcore_pitch": 1.15,
        "queue_message_threshold": 5,
        "update_interval": 5,
    }

    def __init__(self, path: str):
        self.path = Path(path)
        self.config = {}
        self.subscribers = []

        self.load(self.path)

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def publish(self):
        for callback in self.subscribers:
            callback()

    def get(self, key: str, allow_default=True):
        if key in self.config:

            if not allow_default and self.config[key] == Config.DEFAULT[key]:
                return None

            return self.config[key]
        else:
            logger.warning(f"No config called '{key}' exists.")
            return None

    def set(self, key: str, value):
        if key in self.config:
            logger.debug(f"Setting config variable '{key}' to '{value}'.")
            self.config[key] = value
            self.save()
            self.publish()
        else:
            logger.warning(f"Can't set config varible '{key}', it doesn't exist.")

    def set_from_env_var(self, key: str, env_var: str):
        """
        Tries to set a config value based on an environment variable. Do
        nothing if that config doesn't already exist or an environment 
        variable is not found.
        """
        if not self.get(key, allow_default=False) and (value := os.getenv(env_var)):       
            logger.debug(f"Trying to set config variable '{key}' using environment variable '{env_var}'")
            self.set(key, value)
    
    def toggle(self, key: str):
        self.set(key, not self.get(key))

    def load(self, path: Path):
        self.path = path

        if self.path.exists():
            logger.debug(f"Found config file '{path}', using those values")
            with open(self.path, encoding="utf8") as f:
                self.config = json.loads(f.read())
                self._update_if_needed_()

        else:
            logger.debug(f"Config file '{path}' not found, using default configuration")
            self.config = Config.DEFAULT
            self.save()

        self.publish()

    def _update_if_needed_(self):
        default_keys = set(Config.DEFAULT.keys())
        my_keys = set(self.config.keys())

        new_keys = default_keys.difference(my_keys)

        for key in new_keys:
            logger.debug(f"Adding default value for new config variable '{key}'")
            self.config[key] = Config.DEFAULT[key]
        
        old_keys = my_keys.difference(default_keys)

        for key in old_keys:
            logger.debug(f"Removing config value for old config variable '{key}'")
            del self.config[key]

        if new_keys or old_keys:
            self.save()

    def save(self):
        with open(self.path, "w", encoding="utf8") as f:
            f.write(json.dumps(self.config, indent=4))


config = Config('config.json')

import json
from pathlib import Path
import sys

class Config:

    DEFAULT = {
        "token": "YOUR-DISCORD-BOT-TOKEN", 
        "prefix": "-",
        "title_max_length": 30,
        "is_looping": True,
        "before_current": 10,
        "after_current": 20,
    }

    def __init__(self, path: str):
        self.load(path)
        self._on_update_callbacks = []

    def _notify(self):
        for callback in self._on_update_callbacks:
            callback()

    def add_on_update_callback(self, callback):
        self._on_update_callbacks.append(callback)
    
    def get(self, key: str):
        if key in self.config:
            return self.config[key]
        else:
            print(f"Error: No config with key '{key}' exists.")
            return None

    def set(self, key: str, value):
        if key in self.config:
            self.config[key] = value
            self.save()
            self._notify()
        else:
            print(f"Error: Can't set config with key '{key}': No such config exists.")
    
    def load(self, path: str):
        self.path = Path(path)
        
        if not self.path.exists():
            print(f"Creating config file ('{self.path}'). Please fill in missing values.")
            self.config = Config.DEFAULT
            self.save()
            sys.exit()

        with open(self.path, encoding="utf8") as f:
            self.config = json.loads(f.read())
            self._update_if_needed_()

    def _update_if_needed_(self):
        default_keys = set(Config.DEFAULT.keys())
        my_keys = set(self.config.keys())

        new_keys = default_keys.difference(my_keys)
        old_keys = my_keys.difference(default_keys)

        if new_keys or old_keys:

            for key in new_keys:
                self.config[key] = Config.DEFAULT[key]
            
            for key in old_keys:
                del self.config[key]

            self.save()

    def save(self):
        with open(self.path, "w", encoding="utf8") as f:
            f.write(json.dumps(self.config, indent=4))

config = Config("config.json")
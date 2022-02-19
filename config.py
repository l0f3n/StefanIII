import json
from pathlib import Path
import sys

class Config:

    def __init__(self, path: str):
        self.load(path)
    
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
        else:
            print(f"Error: Can't set config with key '{key}': No such config exists.")
    
    def load(self, path: str):
        self.path = Path(path)
        
        if not self.path.exists():
            print(f"Creating config file ('{self.path}'). Please fill in missing values.")
            self.config = {"token": "YOUR-DISCORD-BOT-TOKEN", "prefix": "-"}
            self.save()
            sys.exit()

        with open(self.path, encoding="utf8") as f:
            self.config = json.loads(f.read())

    def save(self):
        with open(self.path, "w", encoding="utf8") as f:
            f.write(json.dumps(self.config, indent=4))
from datetime import datetime
import json
from pathlib import Path

import yt_dlp

class Queue:

    PLAYLISTS_PATH = "playlists.json"

    def __init__(self) -> None:
        self.playlist = []
        self.current = 0

    def add_song(self, url: str):
        YDL_OPTIONS = {
            'format': 'bestaudio',
            'extract-audio': True,
            'audio-format ': "opus",
            '--id': True,
            'outtmpl': "./downloads/%(title)s.%(ext)s"
        }

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url)
            self.playlist.append({"title": info.get("title").replace("\"", "\'").replace(":", "-"), 
                                  "url": url, 
                                  "duration": info.get("duration")
                                  })

    def next(self):
        self.current = (self.current + 1) % len(self.playlist)

    def get_current_song(self):
        if not (0 <= self.current < len(self.playlist)):
            print("Error: Invalid song index")
            return None
        else:
            return f"./downloads/{self.playlist[self.current]['title']}.webm"

    def get_playlists(self):
        if not Path(Queue.PLAYLISTS_PATH).exists():
            print("Error: Can't load playlists, no such file exists")
            return {}

        with open(Queue.PLAYLISTS_PATH, encoding="utf8") as f:
            return [(key, value["description"], value["songs"]) for key, value in json.loads(f.read()).items()]

    def get_queue(self):
        return self.playlist


    def save(self, name: str, desc: str = None) -> bool:
        playlists = {}
        if Path(Queue.PLAYLISTS_PATH).exists():
            with open(Queue.PLAYLISTS_PATH, encoding="utf8") as f:
                playlists = json.loads(f.read())
        
        if name not in playlists:
            playlists[name] = {
                                "created": datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "description": desc if desc else "Ingen beskrivning",
                                "songs": [], 
                            }

        playlists[name]["updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        playlists[name]["songs"] = self.playlist

        if desc:
            playlists[name]["description"] = desc
        
        with open(Queue.PLAYLISTS_PATH, "w", encoding="utf8") as f:
            f.write(json.dumps(playlists, indent=4))
        
        return True

    def load(self, name: str) -> bool:
        if not Path(Queue.PLAYLISTS_PATH).exists():
            print("Error: Can't load playlists, no such file exists")
            return False
        
        with open(Queue.PLAYLISTS_PATH, encoding="utf8") as f:
            playlists = json.loads(f.read())

        if name not in playlists:
           print("Error: No playlist with that name exists")
           return False
           
        self.playlist = playlists[name]["songs"]
        return True

import datetime as dt
import json
from pathlib import Path
import random

import yt_dlp

class Queue:

    PLAYLISTS_PATH = "playlists.json"

    YDL_OPTIONS = {
            'format': 'bestaudio',
            'extract-audio': True,
            'audio-format ': "opus",
            '--id': True,
            'outtmpl': "./downloads/%(title)s.%(ext)s"
        }

    def __init__(self) -> None:
        self.playlist = []
        self.current = 0
        self._on_update_callbacks = []

    def _prepare_index_(self, index):
        return index+1
    
    def _unprepare_index_(self, index):
        return index-1

    def _notify(self):
        for callback in self._on_update_callbacks:
            callback()

    def add_on_update_callback(self, callback):
        self._on_update_callbacks.append(callback)

    def add_song_from_url(self, url: str):

        with yt_dlp.YoutubeDL(Queue.YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                for entry_info in info['entries']:
                    self._add_song_from_info(entry_info)
            else:
                self._add_song_from_info(info)
        
        self._notify()

    def _add_song_from_info(self, info):

        self.playlist.append({  
            "title": info.get("title").replace("\"", "\'").replace(":", "-"), 
            "url": info.get('original_url'), 
            "source": info.get('url'), 
            "duration": info.get("duration")
        })

    def next(self):
        if self.playlist:
            self.current = (self.current + 1) % len(self.playlist)
        self._notify()
    
    def prev(self):
        if self.playlist:
            self.current = (self.current - 1) % len(self.playlist)
        self._notify()

    def move(self, index):
        index = self._unprepare_index_(index)
        if index < len(self.playlist):
            self.current = index
        self._notify()

    def shuffle(self):
        random.shuffle(self.playlist)
        self._notify()

    def clear(self):
        self.playlist = []
        self.current = 0
        self._notify()

    def remove(self, index: int):
        index = self._unprepare_index_(index)
        if (index) < len(self.playlist):
            del self.playlist[(index)]
        
        if index < self.current:
            self.current -= 1

        self._notify()

    def num_songs(self):
        return len(self.playlist)

    def get_current_index(self):
        return self._prepare_index_(self.current)

    def current_song_source(self):
        assert 0 <= self.current < len(self.playlist), "Invalid song index"

        return self.playlist[self.current]['source']

    def get_playlists(self):
        if not Path(Queue.PLAYLISTS_PATH).exists():
            print("Error: Can't load playlists, no such file exists")
            return {}

        with open(Queue.PLAYLISTS_PATH, encoding="utf8") as f:
            return [(key, value["description"], value["songs"]) for key, value in json.loads(f.read()).items()]

    def get_queue(self):
        return self.playlist

    def duration(self):
        return dt.timedelta(seconds=sum(song["duration"] for song in self.playlist))

    def save(self, name: str, desc: str = None) -> bool:
        playlists = {}
        if Path(Queue.PLAYLISTS_PATH).exists():
            with open(Queue.PLAYLISTS_PATH, encoding="utf8") as f:
                playlists = json.loads(f.read())
        
        if name not in playlists:
            playlists[name] = {
                                "created": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                "updated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "description": desc if desc else "Ingen beskrivning",
                                "songs": [], 
                            }

        playlists[name]["updated"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
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
        
        self.playlist = playlists[name]

        # for song in playlists[name]["songs"]:
        #     self.add_song_from_url(song["url"])
        
        return True

    def playlist_string(self, title_max_len):
        if not self.playlist:
            return ""
        
        index_len = len(str(self.num_songs())) + 1
        title_len = min(title_max_len, max(len(song['title']) for song in self.playlist))

        entries = []

        for i, song in enumerate(self.playlist, start=1):
            duration = song['duration']

            # Format song index
            index = str(i) + ':'

            # Format song title
            title = song['title']
            title = title if len(title) < title_max_len else title[:title_max_len-3] + '...'

            # Format song time
            time = str(dt.timedelta(seconds=duration))
            time = time if len(time) == 8 else '0' + time

            entry = f"{index:<{index_len}} {title:<{title_len}} [{time}]"

            if i == self._prepare_index_(self.current):
                entry = f"--> {entry} <--"
            else:
                entry = f"    {entry}    "

            entries.append(entry)
        
        return "```" + '\n'.join(entries) + "```"


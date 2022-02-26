import datetime as dt
import json
from pathlib import Path
import random
import re

import yt_dlp

class Queue:

    PLAYLISTS_PATH = "playlists.json"

    # A regular expression that includes all characters EXCEPT the alphanumerics.
    TITLE_SANITIZE_RE = re.compile('[^a-zA-Z0-9]')

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

    def add_song_from_url(self, url: str, notify=True):

        YDL_OPTIONS = {
            'format': 'bestaudio',
            'extract-audio': True,
            'ignoreerrors': True,
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)

            if 'entries' in info:
                for entry_info in info['entries']:
                    self._add_song_from_info(entry_info)
            else:
                self._add_song_from_info(info)

        if notify:
            self._notify()

    def add_song_from_query(self, query: str):
        
        YDL_OPTIONS = {
            'format': 'bestaudio',
            'extract-audio': True,
            'default_search': 'ytsearch',
            'ignoreerrors': True,
            'quiet': True,
            'noplaylist': True,
        }

        with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info:
                self._add_song_from_info(info['entries'][0])
        
        self._notify()

    def _add_song_from_info(self, info):

        # If a video is unavailable in a playlist we get None as info argument.
        # So we check that and just ignore it if that is the case.
        if not info:
            print("Warning: Ignoring unavailable video")
            return

        self.playlist.append({  
            "title": self._sanitize_title(info.get('title')), 
            "url": info.get('original_url'), 
            "source": info.get('url'), 
            "duration": info.get("duration")
        })

    def _sanitize_title(self, title):
        """
        Only keep letters, digits and spaces from title. Strip whitespace from
        either side and turn all sequences of mulitple spaces into a single 
        space.

        >>> queue._sanitize_title(" * Song Title   #3 !!")
        "Song Title 3"
        """
        
        return ' '.join(Queue.TITLE_SANITIZE_RE.sub(' ', title).split()) 

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
        
        # The source link gotten from youtube-dl apparently expire after some
        # (unknown to us) time. So if we load a playlist that hasn't been
        # updated for some time need to gather info for the songs again. We
        # probably need to save updated time for each entry instead to make
        # this always work. TODO: Look into to this to see if there is a
        # better solution, like saving another link or simply keep track 
        # of when each song was updated. Maybe add command to update playlist
        # like this in worst case.

        updated_time = dt.datetime.strptime(playlists[name]['updated'], "%Y-%m-%d %H:%M")
        time_since_updated = dt.datetime.now() - updated_time

        if time_since_updated > dt.timedelta(hours=4):
            for song in playlists[name]['songs']:
                self.add_song_from_url(song['url'], notify=False)
        else:
            self.playlist.extend(playlists[name]['songs'])
        
        self._notify()
        
        return True

    def playlist_string(self, title_max_len, before_current, after_current):
        if not self.playlist:
            return ""

        assert before_current + after_current <= 60, "Can't display more than about 60 songs at once"

        # Calculate start and end index to only show before_current # of songs
        # before current and after_current # of songs after current. Always 
        # show (before_current + after_current) number of songs if more than 
        # that are in the playlist.

        extra_start = max(0, (self.current+after_current)-len(self.playlist))
        start = max(0, (self.current-before_current)-extra_start)

        extra_end = max(0, -(self.current-before_current))
        end = min(len(self.playlist), (self.current+after_current)+extra_end)

        index_len = len(str(end)) + 1
        title_len = min(title_max_len, max(len(song['title']) for song in self.playlist))

        entries = []

        for i, song in enumerate(self.playlist[start:end], start=self._prepare_index_(start)):
            duration = song['duration']

            # Format song index
            index = str(i) + ':'

            # Format song title
            title = song['title']
            title = title if len(title) < title_max_len else title[:title_max_len-3] + '...'

            # Format song time
            time = str(dt.timedelta(seconds=duration))
            time = '0' + time if len(time) == 7 else time

            entry = f"{index:<{index_len}} {title:<{title_len}} [{time}]"

            if i == self._prepare_index_(self.current):
                entry = f"--> {entry} <--"
            else:
                entry = f"    {entry}    "

            entries.append(entry)
        
        return "```" + '\n'.join(entries) + "```"


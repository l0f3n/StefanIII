import datetime as dt
import json
from pathlib import Path
import random
import re
from typing import Iterable, List

from utils import format_time

from .song import Song
from log import get_logger


logger = get_logger(__name__)


class SongQueue:

    PLAYLISTS_PATH = "playlists.json"

    queue: List[Song]
    current: int

    def __init__(self, config) -> None:
        self.config = config

        self.queue = []
        self._current = 0

        self.subscribers = []

    def subscribe(self, callback):
        self.subscribers.append(callback)

    def publish(self):
        for callback in self.subscribers:
            callback()
    
    @property
    def current(self):
        return self._current

    @current.setter
    def current(self, value):
        self._current = value
        self.publish()

    def _prepare_index_(self, index):
        return index+1
    
    def _unprepare_index_(self, index):
        return index-1

    def add_songs(self, songs: List[Song]):
        self.queue.extend(songs)
        self.publish()

    def add_song(self, song: Song):
        self.queue.append(song)
        self.publish()

    def next(self):
        if self.queue:
            self.current = (self.current + 1) % len(self.queue)

    def prev(self):
        if self.queue:
            self.current = (self.current - 1) % len(self.queue)

    def move(self, index):
        index = self._unprepare_index_(index)
        if 0 <= index < len(self.queue):
            self.current = index

    def shuffle(self):
        random.shuffle(self.queue)

    def clear(self):
        self.queue = []
        self.current = 0

    def remove(self, arg):

        if isinstance(arg, int):
            index = self._unprepare_index_(arg)

            if 0 <= index < len(self.queue):
                del self.queue[index]
            
            # Decrease index if we removed song before current one in queue or
            # we remove the song at the end of the queue that was not the last song
            if index < self.current or (index != 0 and self.current == len(self.queue)):
                self.current -= 1

        elif isinstance(arg, Iterable):
            # Remove the songs back to front so that we remove the correct song, 
            # otherwise we would remove a song before another one and its index 
            # would change causing us to remove the wrong one.
            for index in sorted(arg, reverse=True):
                self.remove(index)

    def num_songs(self):
        return len(self.queue)

    def get_current_index(self):
        return self._prepare_index_(self.current)

    def current_song_source(self):
        assert 0 <= self.current < len(self.queue), "Invalid song index"

        return self.queue[self.current].source
    
    def current_song(self):
        assert 0 <= self.current < len(self.queue), "Invalid song index"

        return self.queue[self.current]

    def get_playlists(self):
        if not Path(SongQueue.PLAYLISTS_PATH).exists():
            logger.warning(f"Can't load playlists, file '{SongQueue.PLAYLISTS_PATH}' not found")
            return {}

        with open(SongQueue.PLAYLISTS_PATH, encoding="utf8") as f:
            return [(key, value["description"], value["songs"]) for key, value in json.loads(f.read()).items()]

    def get_queue(self):
        return self.queue

    def duration(self, time_scaling: int = 1) -> str:
        total_seconds = int(sum(song.duration/time_scaling for song in self.queue))
        return format_time(total_seconds, show_hours=(total_seconds > 3600))

    def _longest_song_between(self, start: int, end: int) -> int:
        return max(song.duration for song in self.queue[start:end])

    def save(self, name: str, desc: str = None) -> bool:
        if len(self.queue) == 0:
            return False
        
        playlists = {}
        if Path(SongQueue.PLAYLISTS_PATH).exists():
            with open(SongQueue.PLAYLISTS_PATH, encoding="utf8") as f:
                playlists = json.loads(f.read())
        
        if name not in playlists:
            playlists[name] = {
                                "created": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), 
                                "updated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "description": desc if desc else "Ingen beskrivning",
                                "songs": [], 
                            }

        playlists[name]["updated"] = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        playlists[name]["songs"] = [song.to_json() for song in self.queue]

        if desc:
            playlists[name]["description"] = desc
        
        with open(SongQueue.PLAYLISTS_PATH, "w", encoding="utf8") as f:
            f.write(json.dumps(playlists, indent=4))
        
        return True

    def load(self, name: str) -> bool:
        if not Path(SongQueue.PLAYLISTS_PATH).exists():
            logger.warning(f"Can't load playlists, file '{SongQueue.PLAYLISTS_PATH}' not found")
            return False
        
        with open(SongQueue.PLAYLISTS_PATH, encoding="utf8") as f:
            playlists = json.loads(f.read())

        if name not in playlists:
            logger.warning(f"Can't load playlist '{name}', playlist not found")
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
                if (url := song.get('url')):
                    # If it has a url, the source was from Youtube, in which
                    # case we need to update it.
                    self.queue.extend(Song.from_youtube_url(url))
                else:
                    # Otherwise we can just add it normally
                    self.queue.append(song)
            self.save(name)
        else:
            self.queue.extend([Song.from_json(song) for song in playlists[name]['songs']])

        self.publish()

        return True

    def playlist_string(self, title_max_len, before_current, after_current, current_music_time, time_scaling=1):
        if not self.queue:
            return ""

        assert before_current + after_current <= 60, "Can't display more than about 60 songs at once"

        # Calculate start and end index to only show before_current # of songs
        # before current and after_current # of songs after current. Always 
        # show (before_current + after_current) number of songs if more than 
        # that are in the playlist.

        extra_start = max(0, (self.current+after_current)-len(self.queue))
        start = max(0, (self.current-before_current)-extra_start)

        extra_end = max(0, -(self.current-before_current))
        end = min(len(self.queue), (self.current+after_current)+extra_end)

        index_len = len(str(end)) + 1
        title_len = min(title_max_len, max(len(song.title) for song in self.queue))

        entries = []

        show_hours = self._longest_song_between(start, end)/time_scaling > 3600

        for i, song in enumerate(self.queue[start:end], start=self._prepare_index_(start)):

            # Format song index
            index = str(i) + ':'

            # Format song title
            title = song.title
            title = title if len(title) < title_max_len else title[:title_max_len-3] + '...'

            # Format song time
            time = format_time(int(song.duration/time_scaling), show_hours=show_hours)

            entry = f"{index:<{index_len}} {title:<{title_len}}"

            if i == self._prepare_index_(self.current):
                # Format current song time
                current_time = format_time(int(current_music_time), show_hours=show_hours)

                entry = f"{entry} [{current_time} / {time}]"
            else:
                entry = f"{entry} [-----{(show_hours*3)*'-'} / {time}]"

            entries.append(entry)
        
        return "```" + '\n'.join(entries) + "```"


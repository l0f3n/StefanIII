import datetime as dt
import json
from pathlib import Path
import random
import re
from typing import Iterable

import youtube_dl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from utils import format_time

class Queue:

    PLAYLISTS_PATH = "playlists.json"

    # A regular expression that includes all characters EXCEPT the alphanumerics.
    TITLE_SANITIZE_RE = re.compile('[^a-zA-Z0-9åäöÅÄÖ]')

    COMMON_YDL_OPTIONS = {
        'format': 'bestaudio',
        'extract-audio': True,
        'ignoreerrors': True,
        'quiet': True,
        'noplaylist': True,
    }

    def __init__(self, config) -> None:
        self.config = config

        self.playlist = []
        self.current = 0
        self._on_update_callbacks = []

    def _prepare_index_(self, index):
        return index+1
    
    def _unprepare_index_(self, index):
        return index-1

    async def _notify(self):
        for callback in self._on_update_callbacks:
            await callback()

    def _is_spotify_url(self, url: str):
        return url.startswith("https://open.spotify.com/")

    def add_on_update_callback(self, callback):
        self._on_update_callbacks.append(callback)

    async def add_song_from_url(self, url: str):
        if self._is_spotify_url(url):
            await self.add_song_from_spotify_url(url)
        else:
            await self.add_song_from_youtube_url(url)
    
    async def add_song_from_youtube_url(self, url):
        YDL_OPTIONS = {
            **Queue.COMMON_YDL_OPTIONS,
        }

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)

            # We don't get any info when we (probably among other things) don't
            # have access to the specified playlist. Just ignore it then.
            if not info:
                print("Warning: No info found for the specified url")
                return

            if 'entries' in info:
                for entry_info in info['entries']:
                    await self._add_song_from_info(entry_info)
            else:
                await self._add_song_from_info(info)

    def _spotify_query_string(self, track):
        return track['name'] + ' - ' + track['artists'][0]['name']

    async def add_song_from_spotify_url(self, url: str):
        spotify_id = self.config.get("spotify_id", allow_default=False)
        spotify_secret = self.config.get("spotify_secret", allow_default=False)
        
        if not spotify_id or not spotify_secret:
            print("Error: Can't add song from Spotify, please add your credentials to 'config.json'")
            return

        spotify = spotipy.Spotify(
                    auth_manager=SpotifyClientCredentials(
                        client_id=spotify_id, 
                        client_secret=spotify_secret))
        
        parsed_url = url.replace("https://open.spotify.com/", "")
        item_type, item_id = parsed_url.split("/")
        
        try:
            if item_type == "track":
                await self.add_song_from_query(self._spotify_query_string(spotify.track(item_id)))

            elif item_type == "playlist":
                for track in spotify.playlist(item_id)['tracks']['items']:
                    await self.add_song_from_query(self._spotify_query_string(track['track']))
            
            elif item_type == "album":
                for track in spotify.album_tracks(item_id)['tracks']['items']:
                    await self.add_song_from_query(self._spotify_query_string(track))

        except spotipy.oauth2.SpotifyOauthError:
            print("Error: Something went wrong when using Spotify credentials")
            return

    async def add_song_from_query(self, query: str):
        
        YDL_OPTIONS = {
            **Queue.COMMON_YDL_OPTIONS,
            'default_search': 'ytsearch',
        }

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(query, download=False)
            
            # We don't get any info when we (probably among other things) don't
            # get any search result for the query. Just ignore it then.
            if not info:
                print(f"Warn: No search results found for query '{query}'")
                return
            
            if 'entries' in info:
                await self._add_song_from_info(info['entries'][0])

    async def _add_song_from_info(self, info):

        # If a video is unavailable in a playlist we get None as info argument.
        # So we check that and just ignore it if that is the case.
        if not info:
            print("Warning: Ignoring unavailable video")
            return

        self.playlist.append({  
            "title": self._sanitize_title(info.get('title')), 
            "url": info.get('original_url'), 
            "source": info.get('url'), 
            "duration": info.get("duration"),
            "asr": info.get('asr'),
        })

        await self._notify()

    def _sanitize_title(self, title):
        """
        Only keep letters, digits and spaces from title. Strip whitespace from
        either side and turn all sequences of mulitple spaces into a single 
        space.

        >>> queue._sanitize_title(" * Song Title   #3 !!")
        "Song Title 3"
        """
        
        return ' '.join(Queue.TITLE_SANITIZE_RE.sub(' ', title.replace("'", '')).split()) 

    async def next(self):
        if self.playlist:
            self.current = (self.current + 1) % len(self.playlist)
        await self._notify()
    
    async def prev(self):
        if self.playlist:
            self.current = (self.current - 1) % len(self.playlist)
        await self._notify()

    async def move(self, index):
        index = self._unprepare_index_(index)
        if index < len(self.playlist):
            self.current = index
        await self._notify()

    async def shuffle(self):
        random.shuffle(self.playlist)
        await self._notify()

    async def clear(self):
        self.playlist = []
        self.current = 0
        await self._notify()

    async def remove(self, arg, notify=True):

        if isinstance(arg, int):
            index = self._unprepare_index_(arg)

            if 0 <= index < len(self.playlist):
                del self.playlist[index]
            
            # Decrease index if we removed song before current one in queue or
            # we remove the song at the end of the queue that was not the last song
            if index < self.current or (index != 0 and self.current == len(self.playlist)):
                self.current -= 1

        elif isinstance(arg, Iterable):
            # Remove the songs back to front so that we remove the correct song, 
            # otherwise we would remove a song before another one and its index 
            # would change causing us to remove the wrong one.
            for index in sorted(arg, reverse=True):
                await self.remove(index, notify=False)

        if notify:
            await self._notify()

    def num_songs(self):
        return len(self.playlist)

    def get_current_index(self):
        return self._prepare_index_(self.current)

    def current_song_source(self):
        assert 0 <= self.current < len(self.playlist), "Invalid song index"

        return self.playlist[self.current]['source']
    
    def current_song(self):
        assert 0 <= self.current < len(self.playlist), "Invalid song index"

        return self.playlist[self.current]

    def get_playlists(self):
        if not Path(Queue.PLAYLISTS_PATH).exists():
            print("Error: Can't load playlists, no such file exists")
            return {}

        with open(Queue.PLAYLISTS_PATH, encoding="utf8") as f:
            return [(key, value["description"], value["songs"]) for key, value in json.loads(f.read()).items()]

    def get_queue(self):
        return self.playlist

    def duration(self, time_scaling=1):
        total_seconds = int(sum(song["duration"]/time_scaling for song in self.playlist))
        return format_time(total_seconds, show_hours=(total_seconds > 3600))

    def _longest_song_between(self, start, end):
        return max(song['duration'] for song in self.playlist[start:end])

    def save(self, name: str, desc: str = None) -> bool:
        if len(self.playlist) == 0:
            return False
        
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

    async def load(self, name: str) -> bool:
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
                await self.add_song_from_youtube_url(song['url'])
            self.save(name)
        else:
            self.playlist.extend(playlists[name]['songs'])
            await self._notify()
        
        return True

    def playlist_string(self, title_max_len, before_current, after_current, current_music_time, time_scaling=1):
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

        show_hours = self._longest_song_between(start, end)/time_scaling > 3600

        for i, song in enumerate(self.playlist[start:end], start=self._prepare_index_(start)):

            # Format song index
            index = str(i) + ':'

            # Format song title
            title = song['title']
            title = title if len(title) < title_max_len else title[:title_max_len-3] + '...'

            # Format song time
            time = format_time(int(song['duration']/time_scaling), show_hours=show_hours)

            entry = f"{index:<{index_len}} {title:<{title_len}}"

            if i == self._prepare_index_(self.current):
                # Format current song time
                current_time = format_time(int(current_music_time), show_hours=show_hours)

                entry = f"{entry} [{current_time} / {time}]"
            else:
                entry = f"{entry} [-----{(show_hours*3)*'-'} / {time}]"

            entries.append(entry)
        
        return "```" + '\n'.join(entries) + "```"

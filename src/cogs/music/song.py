from __future__ import annotations
from pathlib import Path
import re
from typing import List, Dict, Optional

import ffmpeg 
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import youtube_dl

from log import get_logger
from config import config

logger = get_logger(__name__)

class Song:

    title: str
    source: str
    duration: float
    sample_rate: int

    _COMMON_YDL_OPTIONS = {
        'format': 'bestaudio',
        'extract-audio': True,
        'ignoreerrors': True,
        'quiet': True,
        'noplaylist': True,
    }

    # A regular expression that includes all characters EXCEPT the alphanumerics.
    TITLE_SANITIZE_RE = re.compile('[^a-zA-Z0-9åäöÅÄÖ]')

    def __init__(self, title: str, source: str, duration: float, sample_rate: int):
        self.title = title
        self.source = source
        self.duration = duration
        self.sample_rate = sample_rate

    def to_json(self) -> Dict:
        return {
            'title': self.title,
            'source': self.source,
            'duration': self.duration,
            'sample_rate': self.sample_rate,
        }

    @staticmethod
    def from_json(json) -> Song:
        title = json['title']
        source = json['source']
        duration = json['duration']
        sample_rate = json['sample_rate']

        return Song(title, source, duration, sample_rate)

    @staticmethod
    def from_query(query: str) -> Song:
    
        ydl_options = {
            **Song._COMMON_YDL_OPTIONS,
            'default_search': 'ytsearch',
        }

        with youtube_dl.YoutubeDL(ydl_options) as ydl:
            info = ydl.extract_info(query, download=False)
            
            # We don't get any info when we (probably among other things) don't
            # get any search result for the query. Just ignore it then.
            if not info:
                logger.warning(f"No search results found for query '{query}'")
                return None
            
            # Take the first search result from YouTube and create a song from it
            if 'entries' in info:
                entry_info = info['entries'][0]
                return Song.from_source_url(entry_info['url'], title=entry_info['title'])

    @staticmethod
    def from_url(url: str) -> List[Song]:
        if Song._is_spotify_url(url):
            return Song.from_spotify_url(url)
        else:
            return Song.from_youtube_url(url)

    @staticmethod
    def from_spotify_url(url: str) -> List[Song]:
        
        spotify_id = config.get("spotify_id", allow_default=False)
        spotify_secret = config.get("spotify_secret", allow_default=False)

        if not spotify_id or not spotify_secret:
            logger.warning("Can't add song from Spotify, spotify_id or spotify_secret not set")
            return []

        spotify = spotipy.Spotify(
                    auth_manager=SpotifyClientCredentials(
                        client_id=spotify_id, 
                        client_secret=spotify_secret))
        
        parsed_url = url.replace("https://open.spotify.com/", "")
        item_type, item_id = parsed_url.split("/")
        
        songs = []

        try:

            if item_type == "track":
                songs.append(Song.from_query(Song._spotify_query_string(spotify.track(item_id))))

            elif item_type == "playlist":
                for track in spotify.playlist(item_id)['tracks']['items']:
                    songs.append(Song.from_query(Song._spotify_query_string(track['track'])))

            elif item_type == "album":
                for track in spotify.album_tracks(item_id)['tracks']['items']:
                    songs.append(Song.from_query(Song._spotify_query_string(track)))

        except spotipy.oauth2.SpotifyOauthError as e:
            logger.warning("Something went wrong when using Spotify credentials", exc_info=e)
            return []

        return songs

    @staticmethod
    def from_youtube_url(url: str) -> List[Song]:
        YDL_OPTIONS = {
            **Song._COMMON_YDL_OPTIONS,
        }

        songs = []

        with youtube_dl.YoutubeDL(YDL_OPTIONS) as ydl:
            info = ydl.extract_info(url, download=False)

            # We don't get any info when we (probably among other things) don't
            # have access to the specified playlist. Just ignore it then.
            if not info:
                logger.warning(f"No info found for url '{url}'")
                return

            if 'entries' in info:
                for entry_info in info['entries']:
                    songs.append(Song.from_source_url(entry_info['url'], title=entry_info['title']))
            else:
                songs.append(Song.from_source_url(info['url']))
        
        return songs

    @staticmethod
    def from_source_url(url: str, title: Optional[str] = None) -> Song:
        """
        When we finally have the url to the audio source, we can use 
        ffmpeg.probe to get all the needed information from it.
        """

        info = ffmpeg.probe(url)

        format = info['format']
        stream = info['streams'][0]

        title = Song._sanitize_title(title if title else Path(format['filename']).name)
        source = format['filename']
        duration = float(format["duration"])
        sample_rate = stream['sample_rate']

        return Song(title, source, duration, sample_rate)

    @staticmethod
    def _sanitize_title(title: str) -> str:
        """
        Only keep letters, digits and spaces from title. Strip whitespace from
        either side and turn all sequences of mulitple spaces into a single 
        space.

        >>> Song._sanitize_title(" * Song Title   #3 !!")
        "Song Title 3"
        """
        
        return ' '.join(Song.TITLE_SANITIZE_RE.sub(' ', title.replace("'", '')).split())

    @staticmethod
    def _spotify_query_string(track) -> str:
        return track['name'] + ' - ' + track['artists'][0]['name']

    @staticmethod
    def _is_spotify_url(url: str):
        return url.startswith("https://open.spotify.com/")
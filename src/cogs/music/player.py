import datetime as dt
from typing import Dict, Callable

import discord
from discord import FFmpegPCMAudio

from .song import Song


class MusicPlayer:

    def __init__(self, voice_client: discord.VoiceClient, song: Song, ffmpeg_options: Dict, after: Callable):
        self._vc = voice_client
        self._song = song
        self._after = after

        self._start_time = dt.datetime.now()
        self._pause_time = dt.datetime.now()

        self._is_stopped = True

        self.ffmpeg_options = ffmpeg_options

    def play(self, song: Song = None, force_start: bool = True, ignore_pause: bool = True):

        if song:
            self._song = song

        if self.is_playing():
            # We can simply just switch the source if we are already playing something
            self._vc.source = FFmpegPCMAudio(self._song.source, **self.ffmpeg_options)
            self._start_time = dt.datetime.now()
            self._is_stopped = False

        elif self.is_paused() and not ignore_pause:
            self._vc.resume()
            self._start_time = dt.datetime.now() - (self._pause_time - self._start_time)
            self._is_stopped = False

        elif not self.is_stopped() or (self.is_stopped() and force_start):
            # But if we are not playing we need to send a new source to the voice client
            self._vc.play(FFmpegPCMAudio(self._song.source, **self.ffmpeg_options), after=self._after)
            self._start_time = dt.datetime.now()
            self._is_stopped = False

    def pause(self):

        if self.is_playing():
            self._vc.pause()

        self._pause_time = dt.datetime.now()

    def seek(self, seek_time: int):

        if not self.is_stopped():
            # When we are playing or paused we just fastforward the current song from the beginning to the desired time
            
            ffmpeg_options = self.ffmpeg_options.copy()
            options = ffmpeg_options['options']
            ffmpeg_options['options'] = f"{options} -ss {seek_time}"

            source = FFmpegPCMAudio(self._song.source, **ffmpeg_options)

            was_paused = self.is_paused()

            self._vc.source = source
            self._start_time = dt.datetime.now() - dt.timedelta(seconds=seek_time)

            if was_paused:
                # When we are paused we additionally need to change the time we paused the music, which is right now
                self._pause_time = dt.datetime.now()
                self._vc.pause()

    def stop(self):

        if self._vc.is_playing():
            self._vc.stop()

        self._is_stopped = True
        self._start_time = dt.datetime.now()
        self._pause_time = dt.datetime.now()

    def is_playing(self):
        return self._vc.is_playing()

    def is_paused(self):
        return not self._is_stopped and self._vc.is_paused()

    def is_stopped(self):
        return self._is_stopped

    def elapsed_time(self):
        if self.is_playing():
            return (dt.datetime.now() - self._start_time).total_seconds()
        else:
            return (self._pause_time - self._start_time).total_seconds()

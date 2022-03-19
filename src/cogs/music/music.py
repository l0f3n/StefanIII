import asyncio
from typing import Optional

from discord import Color, Embed
from discord.ext import commands

from log import get_logger
from .playlist import Queue
from .player import MusicPlayer

logger = get_logger(__name__)


class Music(commands.Cog):

    _FFMPEG_COMMON_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    }

    _FFMPEG_STANDARD_OPTIONS = {
        **_FFMPEG_COMMON_OPTIONS,
        'options': '-vn'
    }

    def __init__(self, bot, config):
        super().__init__()

        self.bot = bot

        self.queue = Queue(config)

        self.config = config
        self.config.add_on_update_callback(self._handle_playlist_change)

        self.queue_message = None
        self.queue_message_lock = asyncio.Lock()

        self.messages_since_last_update = self.config.get('queue_message_threshold')

        self._music_player: Optional[MusicPlayer] = None

        self._is_handling_change = False

        asyncio.run_coroutine_threadsafe(Music._call_periodically(1, self._handle_playlist_change), self.bot.loop)

    async def cog_after_invoke(self, ctx):
        self.messages_since_last_update += 1

        return await super().cog_after_invoke(ctx)

    async def _handle_playlist_change(self):
        if self.queue_message:
            await self.queue_message.edit(content=None, embed=self.make_queue_embed())

    @staticmethod
    async def _call_periodically(interval, func):
        """
        Periodically call func every interval seconds.
        """

        while True:
            await asyncio.sleep(interval)
            await func()

    async def close(self):
        if self.queue_message:
            await self.queue_message.delete()

    def ffmpeg_options(self):
        if not self.config.get('nightcore'):
            return Music._FFMPEG_STANDARD_OPTIONS
        else:
            tempo = self.config.get("nightcore_tempo")
            pitch = self.config.get("nightcore_pitch")
            freq = self.queue.current_song()['asr']

            return {
                **Music._FFMPEG_COMMON_OPTIONS,
                'options': f'-af atempo={tempo},asetrate={freq}*{pitch} -vn'
            }

    def time_scale(self):
        return self.nightcore_time_scale() if self.config.get("nightcore") else 1

    def make_queue_embed(self):
        description = self.queue.playlist_string(self.config.get("title_max_length"), self.config.get("before_current"),
                                                 self.config.get("after_current"), self.elapsed_time(),
                                                 self.time_scale())

        playing = "✓" if self.is_playing() else "✗"

        nightcore = "✓" if self.config.get("nightcore") else "✗"

        looped = "kö"
        if self.config.get("is_looping_song"):
            looping = "✓"
            looped = "låt"
        else:
            looping = "✓" if self.config.get("is_looping_queue") else "✗"

        time = self.queue.duration(self.time_scale())

        info = f"Spelar: {playing}⠀Loopar {looped}: {looping}⠀Nightcore: {nightcore}⠀Antal låtar: {self.queue.num_songs()}⠀Längd: {time}\n"

        description = info + description

        return Embed(color=Color.orange(), title=f"Nuvarande kö 😙", description=description)

    def nightcore_time_scale(self):
        # Using asetrate in ffmpeg apparently changes the duration of song as
        # well, so we need to multiply these.
        return self.config.get("nightcore_tempo") * self.config.get("nightcore_pitch")

    def play_next(self, ctx, e, loop):
        if e:
            logger.error(f"Something went wrong in play_next()", exc_info=e)
            return

        asyncio.run_coroutine_threadsafe(self.play_next_async(ctx), loop)

    async def play_next_async(self, ctx):
        if self.queue.get_current_index() == self.queue.num_songs() and not (
                self.config.get("is_looping_queue") or self.config.get("is_looping_song")):
            self.stop()

        elif not self.is_stopped():
            if not self.config.get("is_looping_song"):
                await self.queue.next()

            if self._music_player:
                self._music_player.song = self.queue.current_song()
                self._music_player.play(force_start=False)

    # =================================================
    # ========== Wrappers around MusicPlayer ==========
    # =================================================

    def is_playing(self):
        if self._music_player:
            return self._music_player.is_playing()
        return False

    def is_paused(self):
        if self._music_player:
            return self._music_player.is_paused()
        return False

    def is_stopped(self):
        if self._music_player:
            return self._music_player.is_stopped()
        return True

    def stop(self):
        if self._music_player:
            self._music_player.stop()

    def elapsed_time(self):
        if self._music_player:
            return self._music_player.elapsed_time()
        return 0

    # ==============================
    # ========== Commands ==========
    # ==============================

    @commands.command(name="clear", aliases=["töm", "rensa"])
    async def _clear(self, ctx):
        """
        Remove all songs in the queue.
        """

        self.stop()
        await self.queue.clear()

    @commands.command(name="load", aliases=["ladda"])
    async def _load(self, ctx, name):
        """
        Load a previously saved playlist given its name.
        """

        success = await self.queue.load(name)

        if success and not self.is_stopped():
            await self.bot.join_channel()

            # Will only run the first time
            if not self._music_player and (vc := self.bot.get_voice_client(ctx)):
                self._music_player = MusicPlayer(vc, self.queue.current_song(), self.ffmpeg_options(), lambda x: self.play_next(ctx, x, self.bot.loop))

            if self._music_player.is_stopped():
                self._music_player.play()

    @commands.command(name="loop", aliases=["loopa", "snurra"])
    async def _loop(self, ctx, arg1=""):
        """
        Toggles looping of queue or song.
        """

        if arg1 in ["sång", "låt", "stycke"]:
            await self.config.toggle('is_looping_song')
        elif arg1 in ["kö", "lista"] or True:
            await self.config.toggle('is_looping_queue')

    @commands.command(name="move")
    async def _move(self, ctx, index):
        """
        Move to a song given its index.
        """

        await self.queue.move(int(index))

        if self.queue.num_songs() > 0:

            if self._music_player:
                self._music_player.song = self.queue.current_song()
                self._music_player.play()

    @commands.command(name="next")
    async def _next(self, ctx):
        """
        Move to the next song.
        """

        if not (self.queue.get_current_index() == self.queue.num_songs() and not self.config.get("is_looping_queue")):
            await self.queue.next()

            if self._music_player:
                self._music_player.song = self.queue.current_song()
                self._music_player.play()

        else:
            self.stop()

    @commands.command(name="nightcore")
    async def _nightcore(self, ctx):
        """
        Toggle nightcore mode, increasing pitch and speed of music.
        """

        await self.config.toggle('nightcore')

        if self.config.get('nightcore'):
            # If we previously played normally, we need go backward
            seek_time = self.elapsed_time() / self.nightcore_time_scale()
        else:
            # And if we previously played nightcore, we need to go forward
            seek_time = self.elapsed_time() * self.nightcore_time_scale()

        if self._music_player:
            self._music_player.ffmpeg_options = self.ffmpeg_options()
            self._music_player.seek(seek_time)

    @commands.command(name="pause", aliases=["pausa"])
    async def _pause(self, ctx):
        """
        Pause the currently playing song at the current time.
        """

        if self._music_player:
            self._music_player.pause()

    @commands.command(name="play", aliases=["p"])
    async def _play(self, ctx, *args):
        """
        Start playing music.

        If there is one argument that is a url it either imports a playlist 
        or video from youtube, or playlist, album or track from spotify.

        If there are multiple arguments or a single one that is not a url, it
        searches it on youtube and adds the first result to the queue.
        """

        if len(args) == 1 and args[0].startswith(('http', 'www')):
            # Assume user provided url
            message = await ctx.send("Schysst förslag! Det fixar jag! 🤩")
            await self.queue.add_song_from_url(args[0])
            await message.delete(delay=self.config.get("message_delete_delay"))

        elif len(args) >= 1:
            # Assume user provided a string to search for on youtube
            message = await ctx.send("Jag ska se vad jag kan skaka fram. 🤔")
            await self.queue.add_song_from_query(' '.join(args))
            await message.delete(delay=self.config.get("message_delete_delay"))

        if self.queue.num_songs() == 0:
            logger.warning("Can't play music, no songs in queue")
            return

        if not self.bot.get_voice_client(ctx):
            await self.bot.join_channel()

        if not self._music_player and (vc := self.bot.get_voice_client(ctx)):
            self._music_player = MusicPlayer(vc, self.queue.current_song(), self.ffmpeg_options(), lambda x: self.play_next(ctx, x, self.bot.loop))

        if self._music_player.is_stopped() or len(args) == 0:
            self._music_player.play()

    @commands.command(name="playlists", aliases=["spellistor", 'pl'])
    async def _playlists(self, ctx):
        """
        Lists all the saved playlists.
        """

        embed = Embed(title="Spellistor:", color=Color.orange())
        for name, desc, songs in self.queue.get_playlists():
            noun = "låt" if len(songs) == 1 else "låtar"
            embed.add_field(name=f"**{name} ({len(songs)} {noun})**", value=f"{desc}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="previous", aliases=["prev"])
    async def _previous(self, ctx):
        """
        Move to the previous song.
        """

        if not (self.queue.get_current_index() == 1 and not self.config.get("is_looping_queue")):
            await self.queue.prev()

            if self._music_player:
                self._music_player.song = self.queue.current_song()
                self._music_player.play()

        else:
            self.stop()

    @commands.command(name="queue", aliases=["q", "kö"])
    async def _queue(self, ctx):
        """
        Shows the current queue, which will continuously update.
        """

        async with self.queue_message_lock:
            self.messages_since_last_update = 0
            if self.queue_message:
                await self.queue_message.delete()

            self.queue_message = await ctx.send(embed=self.make_queue_embed())

    @commands.command(name="remove")
    async def _remove(self, ctx, *args):
        """
        Remove songs given one or multiple indexes.

        Will inclusively remove every song between ranges given as x:y.
        """

        # Expand every 'x:y' entry to x, x+1, ..., y-1, y. Ignore incorrect ranges
        indexes = []
        for arg in args:
            if ':' in arg:
                start, end = [int(x) for x in arg.split(':')]
                if start > end:
                    continue
                for i in range(start, end + 1):
                    indexes.append(i)
            else:
                indexes.append(int(arg))

        removed_current_song = self.queue.get_current_index() in indexes

        await self.queue.remove(index for index in indexes if 1 <= index <= self.queue.num_songs())

        if self.queue.num_songs() > 0:

            if removed_current_song:

                if self._music_player:
                    self._music_player.song = self.queue.current_song()
                    self._music_player.play()

        else:
            self.stop()

    @commands.command(name="save", aliases=["spara"])
    async def _save(self, ctx, name, desc=None):
        """ 
        Save the current queue as a playlist with the given name.
        
        Can optionally also take a description of the queue.
        """

        self.queue.save(name, desc)

    @commands.command(name="seek", aliases=["sök", "spoola"])
    async def _seek(self, ctx, time):
        """
        Skip to the given time in the current song.
        """

        if self._music_player:
            self._music_player.seek(int(time))

    @commands.command(name="shuffle", aliases=["slumpa", "skaka", "blanda", "stavmixa"])
    async def _shuffle(self, ctx):
        """
        Shuffle the current queue.
        """

        await self.queue.shuffle()

        if self._music_player:
            self._music_player.song = self.queue.current_song()
            self._music_player.play()

    @commands.command(name="stop", aliases=["stoppa"])
    async def _stop(self, ctx):
        """
        Stop the current song.
        """

        self.stop()

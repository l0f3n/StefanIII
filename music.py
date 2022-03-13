import asyncio
import datetime as dt

from discord import Color, Embed, FFmpegPCMAudio
from discord.ext import commands

from config import config
from playlist import Queue

class Music(commands.Cog):

    _FFMPEG_COMMON_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    }
    
    _FFMPEG_STANDARD_OPTIONS = {
        **_FFMPEG_COMMON_OPTIONS,
        'options': '-vn'
    }

    def __init__(self, bot):
        self.bot = bot

        self.queue = Queue()
        self.queue.add_on_update_callback(self._handle_playlist_change)
        
        self.config = config
        self.config.add_on_update_callback(self._handle_playlist_change)

        self.queue_message = None
        self.queue_message_lock = asyncio.Lock()

        self.message_count = 0
        self.message_count_lock = asyncio.Lock()

        self.is_playing = False
        self.current_music_start_time = dt.datetime.now()

        self._is_handling_change = False


    # Override

    async def cog_after_invoke(self, ctx):
        self.message_count += 1

        return await super().cog_after_invoke(ctx)


    # Private methods

    async def _handle_playlist_change(self):
        self._is_handling_change = True
        
        if not self.is_playing:
            self.current_music_start_time = dt.datetime.now()
            if self.queue.num_songs() == 1:
                await self.bot.join_channel()
                self.play()
        
        async with self.message_count_lock:
            send_new_message = (self.message_count % self.config.get('queue_message_threshold')) == 0

        async with self.queue_message_lock:
            if send_new_message:            
                if self.queue_message:
                    await self.queue_message.delete()

                self.queue_message = await self.bot.latest_context.send(embed=self.make_queue_embed())

            elif self.queue_message:
                await self.queue_message.edit(content=None, embed=self.make_queue_embed())
            
        self._is_handling_change = False

    async def _update_music_time(self):
        while True:        
            await asyncio.sleep(self.config.get('music_time_update_interval'))
            
            if not self.is_playing:
                break
            
            await self._handle_playlist_change()


    # Public methods

    async def close(self):
        if self.queue_message:
            await self.queue_message.delete()

    def current_elapsed_time(self):
        return (dt.datetime.now() - self.current_music_start_time).total_seconds()

    def current_ffmpeg_options(self):
        if not self.config.get('nightcore'):
            return Music._FFMPEG_STANDARD_OPTIONS
        else:
            freq = self.queue.current_song()['asr']

            return {
                **Music._FFMPEG_COMMON_OPTIONS,
                'options': f'-af atempo={self.config.get("nightcore_tempo")},asetrate={freq}*{self.config.get("nightcore_pitch")} -vn'
            }

    def current_time_scale(self):
        return self.nightcore_time_scale() if self.config.get("nightcore") else 1

    def make_queue_embed(self):
        description = self.queue.playlist_string(self.config.get("title_max_length"), self.config.get("before_current"), self.config.get("after_current"), self.current_elapsed_time(), self.current_time_scale())

        playing = "✓" if self.is_playing else "✗"

        nightcore = "✓" if self.config.get("nightcore") else "✗"

        looped = "kö"
        if self.config.get("is_looping_song"):
            looping = "✓"
            looped = "låt"
        else:
            looping = "✓" if self.config.get("is_looping_queue") else "✗"
            
        time = str(self.queue.duration(self.current_time_scale()))

        info = f"Spelar: {playing}⠀Loopar {looped}: {looping}⠀Nightcore: {nightcore}⠀Antal låtar: {self.queue.num_songs()}⠀Längd: {time}\n"

        description = info + description

        return Embed(color=Color.orange(), title=f"Nuvarande kö 😙", description=description)

    def nightcore_time_scale(self):
        # Using asetrate in ffmpeg apparently changes the duration of song as
        # well, so we need to multiply these.
        return self.config.get("nightcore_tempo")*self.config.get("nightcore_pitch")

    def play(self, ctx=None):
        ctx = ctx or self.bot.current_context

        if not ctx or not ctx.voice_client:
            print("Error: Cant't play music, bot is not connected to voice")
            return

        if ctx.voice_client.is_playing():
            # Just change audio source if we are currently playing something else
            ctx.voice_client.source = FFmpegPCMAudio(self.queue.current_song_source(), **self.current_ffmpeg_options())
        else:
            # Otherwise start playing as normal
            source = FFmpegPCMAudio(self.queue.current_song_source(), **self.current_ffmpeg_options())
            ctx.voice_client.play(source, after=lambda e: self.play_next(ctx, e, self.bot.loop))

        self.current_music_start_time = dt.datetime.now()

        if not self.is_playing:
            self.is_playing = True
            asyncio.run_coroutine_threadsafe(self._update_music_time(), self.bot.loop)

        if not self._is_handling_change:
            asyncio.run_coroutine_threadsafe(self._handle_playlist_change(), self.bot.loop)

    def play_next(self, ctx, e, loop):
        if e:
            print(f"Error: play_next(): {e}")
            return

        asyncio.run_coroutine_threadsafe(self.play_next_async(ctx), loop)

    async def play_next_async(self, ctx):
        if self.queue.get_current_index() == self.queue.num_songs() and not (self.config.get("is_looping_queue") or self.config.get("is_looping_song")):
            self.stop(ctx)
        
        elif self.is_playing:
            if not self.config.get("is_looping_song"):
                await self.queue.next()
            self.play(ctx)

    def seek(self, time):
        if not self.is_playing:
            print("Warn: Can't seek when not playing any music")
            return
        
        source = FFmpegPCMAudio(self.queue.current_song_source(), **self.current_ffmpeg_options())
        
        read_time = 0
        while source.read() and read_time < time*1000:
            read_time += 20

        self.bot.current_context.voice_client.source = source
        self.current_music_start_time = dt.datetime.now() - dt.timedelta(seconds=time)

        if not self._is_handling_change:
            asyncio.run_coroutine_threadsafe(self._handle_playlist_change(), self.bot.loop)

    def stop(self, ctx=None):
        ctx = ctx or self.bot.current_context
        
        if not ctx or not ctx.voice_client:
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        self.is_playing = False
        self.current_music_start_time = dt.datetime.now()

        if not self._is_handling_change:
            asyncio.run_coroutine_threadsafe(self._handle_playlist_change(), self.bot.loop)


    # ==============================
    # ========== Commands ==========
    # ==============================

    @commands.command(name="clear", aliases=["töm", "rensa"])
    async def _clear(self, ctx):

        self.stop()
        await self.queue.clear()

    @commands.command(name="load", aliases=["ladda"])
    async def _load(self, ctx, name):
        
        success = await self.queue.load(name)

        if success and not self.is_playing:
            await self.bot.join_channel()
            self.play()
    
    @commands.command(name="loopa", aliases=["snurra"])
    async def _loop(self, ctx, arg1=""):
        """ TODO: Write docstring """ 

        if arg1 in ["sång", "låt", "stycke"]:
            await self.config.toggle('is_looping_song')
        elif arg1 in ["kö", "lista"] or True:
            await self.config.toggle('is_looping_queue')

    @commands.command(name="move")
    async def _move(self, ctx, index):

        await self.queue.move(int(index))

        if self.queue.num_songs() > 0:
            self.play()

    @commands.command(name="next")
    async def _next(self, ctx):

        if not (self.queue.get_current_index() == self.queue.num_songs() and not self.config.get("is_looping_queue")):
            await self.queue.next()
            self.play()
        else:
            self.stop()

    @commands.command(name="nightcore")
    async def _nightcore(self, ctx):

        await self.config.toggle('nightcore')

        if self.config.get('nightcore'):
            # If we previously played normally, we need go backward
            seek_time = self.current_elapsed_time()/self.nightcore_time_scale()
        else:
            # And if we previously played nightcore, we need to go forward
            seek_time = self.current_elapsed_time()*self.nightcore_time_scale()

        self.seek(seek_time)

    @commands.command(name="play")
    async def _play(self, ctx, *args):

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
            print("Warn: Can't play music, no songs in queue")
            return

        if not self.is_playing or len(args) == 0:
            await self.bot.join_channel()
            self.play()
    
    @commands.command(name="playlists", aliases=["spellistor", 'pl', 'sp'])
    async def _playlists(self, ctx):
        embed=Embed(title="Spellistor:", color=Color.orange())
        for name, desc, songs in self.queue.get_playlists():
            noun = "låt" if len(songs) == 1 else "låtar"
            embed.add_field(name=f"**{name} ({len(songs)} {noun})**", value=f"{desc}", inline=False)
        await ctx.send(embed=embed)
    
    @commands.command(name="previous", aliases=["prev"])
    async def _previous(self, ctx):

        if not (self.queue.get_current_index() == 1 and not self.config.get("is_looping_queue")):
            await self.queue.prev()
            self.play()
        else:
            self.stop()

    @commands.command(name="queue", aliases=["kö"])
    async def _queue(self, ctx):
        async with self.queue_message_lock:
            # self.current_message_count = 0
            if self.queue_message:
                await self.queue_message.delete()
        
            # self.latest_queue_message = 
            self.queue_message = await ctx.send(embed=self.make_queue_embed())

    @commands.command(name="remove")
    async def _remove(self, ctx, *args):

        # Expand every 'x:y' entry to x, x+1, ..., y-1, y. Ignore incorrect ranges
        indexes = []
        for arg in args:
            if ':' in arg:
                start, end = [int(x) for x in arg.split(':')]
                if start > end:
                    continue
                for i in range(start, end+1):
                    indexes.append(i)
            else:
                indexes.append(int(arg))

        # Remove the songs back to front so that we remove the correct song, 
        # otherwise we would remove a song before another one and its index 
        # would change causing us to remove the wrong one.
        removed_current_song = False
        for index in filter(lambda x: 0 <= x <= self.queue.num_songs(), sorted(indexes, reverse=True)):
            removed_current_song = removed_current_song or (self.queue.get_current_index() == int(index))
            await self.queue.remove(index)

        if self.queue.num_songs() > 0:

            if removed_current_song:
                self.play()

        else:
            self.stop()

    @commands.command(name="save", aliases=["spara"])
    async def _save(self, ctx, name, desc=None):
        """ TODO: Write docstring """
        self.queue.save(name, desc)

    @commands.command(name="seek", aliases=["sök", "spoola"])
    async def _seek(self, ctx, time):

        self.seek(int(time))

    @commands.command(name="shuffle", aliases=["slumpa", "skaka", "blanda", "stavmixa"])
    async def _shuffle(self, ctx):

        await self.queue.shuffle()
        self.play()

    @commands.command(name="stop", aliases=["stoppa"])
    async def _stop(self, ctx):
        self.stop()
    
import asyncio
import discord
from discord import Embed, Color, FFmpegPCMAudio
from discord.ext import commands

from config import config
import playlist

class Stefan(commands.Bot):
    _FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
        'options': '-vn'
    }

    _FFMPEG_NIGHTCORE_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
        'options': f'-af atempo={config.get("nightcore_tempo")},asetrate=44100*{config.get("nightcore_pitch")} -vn'
    }
    
    def __init__(self, *args, **kwargs):
        commands.Bot.__init__(self, *args, **kwargs)

        self.queue = playlist.Queue()
        self.queue.add_on_update_callback(self._handle_playlist_change)
        config.add_on_update_callback(self._handle_playlist_change)

        self._is_playing = False
        self.latest_queue_message = None
        self.message_delete_delay = config.get("message_delete_delay")

        self.before_invoke(self._handle_before_invoke)
        self.after_invoke(self._handle_after_invoke)

        self._ctx = None

    @property
    def is_playing(self):
        return self._is_playing

    @is_playing.setter
    def is_playing(self, value):
        self._is_playing = value
        self._handle_playlist_change()

    def _handle_playlist_change(self):
        if self.latest_queue_message:
            asyncio.run_coroutine_threadsafe(stefan.latest_queue_message.edit(content=None, embed=self.make_queue_embed()), self.loop)

    async def _handle_before_invoke(self, ctx):
        self._ctx = ctx
        await ctx.message.add_reaction("👌")

    async def _handle_after_invoke(self, ctx):
        self._ctx = None
        await ctx.message.remove_reaction("👌", self.user)
        await ctx.message.add_reaction("👍")
        if self.message_delete_delay != False:
            await ctx.message.delete(delay=self.message_delete_delay)

    async def close(self):
        if self.latest_queue_message:
            await self.latest_queue_message.channel.send("Jag dör! 😱")
            await self.latest_queue_message.delete()
        return await super().close()

    def music_play(self, ctx=None):       
        ctx = ctx or self._ctx
        
        if not ctx or not ctx.voice_client:
            print("Error: Cant't play music, bot is not connected to voice")
            return

        ffmpeg_options = Stefan._FFMPEG_NIGHTCORE_OPTIONS if config.get("nightcore") else Stefan._FFMPEG_OPTIONS

        if ctx.voice_client.is_playing():
            # Just change audio source if we are currently playing something else
            ctx.voice_client.source = FFmpegPCMAudio(stefan.queue.current_song_source(), **ffmpeg_options)
        else:
            # Otherwise start playing as normal
            source = FFmpegPCMAudio(stefan.queue.current_song_source(), **ffmpeg_options)
            ctx.voice_client.play(source, after=lambda e: play_next(ctx, e))

        stefan.is_playing = True

    def music_stop(self, ctx=None):        
        ctx = ctx or self._ctx
        
        if not ctx or not ctx.voice_client:
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        stefan.is_playing = False

    def make_queue_embed(self):
        time_scaling = config.get("nightcore_tempo") if config.get("nightcore") else 1

        description = self.queue.playlist_string(config.get("title_max_length"), config.get("before_current"), config.get("after_current"), time_scaling)

        playing = "✓" if stefan.is_playing else "✗"

        nightcore = "✓" if config.get("nightcore") else "✗"

        looped = "kö"
        if config.get("is_looping_song"):
            looping = "✓"
            looped = "låt"
        else:
            looping = "✓" if config.get("is_looping_queue") else "✗"
            
        time = str(self.queue.duration(time_scaling))

        info = f"Spelar: {playing}⠀Loopar {looped}: {looping}⠀Nightcore: {nightcore}⠀Antal låtar: {stefan.queue.num_songs()}⠀Längd: {time}\n"

        description = info + description

        return Embed(color=Color.orange(), title=f"Nuvarande kö 😙", description=description)
        

stefan = Stefan(command_prefix=config.get("prefix"))

@stefan.event
async def on_ready():
    print("Stefan anmäler sig för tjänstgöring.")
    await stefan.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ert skitsnack"))

@stefan.command()
async def ping(ctx):
    """ TODO: Write docstring """
    await ctx.message.channel.send("Pong!")

@stefan.command(name = "prefix")
async def prefix(ctx, new_prefix):
    """ TODO: Write docstring """

    stefan.command_prefix = new_prefix
    config.set("prefix", new_prefix)

    await ctx.message.channel.send("Tack för mitt nya prefix! 🥰")

@stefan.command(name = "kom", aliases = ["komsi", "älskling", "hit"])
async def kom(ctx, arg1="", arg2="", arg3=""):
    """ TODO: Write docstring """
    cm = " ".join(filter(None, [ctx.invoked_with, arg1, arg2, arg3]))
    # await ctx.send("cm: " + cm + "\narg1: " + arg1 + "\narg2: " + arg2 + "\narg3: " + arg3)
    if cm in ["kom", "kom hit", "komsi komsi", "älskling jag är hemma", "hit"]:
        # If user is in a channel
        if ctx.author.voice:
            # If bot is in a channel
            if ctx.guild.voice_client:
                # If they are in the same channel
                if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                    await ctx.send("Jag är redan här för dig! 🥰")
                # If they are in different channels
                else:
                    # If bot has company
                    if len(ctx.guild.voice_client.channel.members) > 1:
                        await ctx.send("Jag är upptagen! 😤")
                    # If bot is alone
                    else:
                        await ctx.send("Äntligen lite sällskap igen! 😊")
                        await ctx.guild.voice_client.disconnect()
                        await ctx.author.voice.channel.connect()
            # If user is in a channel, but bot is not
            else:
                await ctx.send("Jag kommer! 😁")
                await ctx.author.voice.channel.connect()
        # If user is not in a channel
        else:
            await ctx.send("Jag vet inte vart jag ska. 😢")
    else:
        pass

@stefan.command(name = "stick", aliases = ["schas", "försvinn", "dra", "gå"])
async def stick(ctx):
    """ TODO: Write docstring """
    # If bot is in a channel
    if ctx.guild.voice_client:
        # If user is in a channel
        if ctx.author.voice:
            # If they are in the same channel
            if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                await ctx.send('Okej då... 😥')
                await ctx.guild.voice_client.disconnect()
            # If they are in different channels
            else:
                # If bot has company
                if len(ctx.guild.voice_client.channel.members) > 1:
                    await ctx.send("Förstör inte det roliga! 😠")
                # If bot is alone
                else:
                    await ctx.send('Okej då... 😥')
                    await ctx.guild.voice_client.disconnect()
        # If bot is in a channel, but user is not
        else:
            # If bot has company
            if len(ctx.guild.voice_client.channel.members) > 1:
                await ctx.send("Förstör inte det roliga! 😠")
            # If bot is alone
            else:
                await ctx.send('Okej då... 😥')
                await ctx.guild.voice_client.disconnect()
    # If bot is not in a channel
    else:
        await ctx.send("Jag har redan stuckit ju! 💔")

@stefan.command(name = "hjälp", aliases = ["hilfe", "aidez-moi", "h"])
async def hjälp(ctx):
    """ TODO: Write docstring """
    embed=Embed(title="Mina kommandon 😎 :", color=Color.orange(), description = f"Genom att skriva \"{stefan.command_prefix}\" följt av ett av nedanstående kommandon kan du få mig att göra roliga saker! Lek med mig! 🥰")
    embed.add_field(name="**stick / gå / schas / försvinn / dra**", value="Säg åt mig att lämna röstkanalen. 😥", inline=False)
    embed.add_field(name="**kom / hit / komsi komsi / älskling jag är hemma**", value="Be mig att göra dig sällskap! 😇", inline=False)
    embed.add_field(name="**prefix**", value="Ge mig ett nytt prefix som jag kan lyssna på! ☺️")
    await ctx.send(embed=embed)


def play_next(ctx, e):
    if e:
        print(f"Error: play_next(): {e}")
        return

    if stefan.queue.get_current_index() == stefan.queue.num_songs() and not (config.get("is_looping_queue") or config.get("is_looping_song")):
        stefan.music_stop(ctx)    
    
    elif stefan.is_playing:
        if not config.get("is_looping_song"):
            stefan.queue.next()
        stefan.music_play(ctx)
    

@stefan.command()
async def next(ctx):
    """ TODO: Write docstring """
    if not (stefan.queue.get_current_index() == stefan.queue.num_songs() and not config.get("is_looping_queue")):
        stefan.queue.next()
        stefan.music_play()
    else:
        stefan.music_stop()


@stefan.command()
async def prev(ctx):
    """ TODO: Write docstring """
    if not (stefan.queue.get_current_index() == 1 and not config.get("is_looping_queue")):
        stefan.queue.prev()
        stefan.music_play()
    else:
        stefan.music_stop()


@stefan.command()
async def play(ctx, *args):
    """ TODO: Write docstring """    

    was_empty_before = stefan.queue.num_songs() == 0

    if len(args) == 1 and args[0].startswith(('http', 'www')):
        # Assume user provided url
        message = await ctx.send("Schysst förslag! Det fixar jag! 🤩")
        stefan.queue.add_song_from_url(args[0])
        await message.delete(delay=stefan.message_delete_delay)
    elif len(args) >= 1:
        # Assume user provided a string to search for on youtube
        message = await ctx.send("Jag ska se vad jag kan skaka fram. 🤔")
        stefan.queue.add_song_from_query(' '.join(args))
        await message.delete(delay=stefan.message_delete_delay)

    if stefan.queue.num_songs() == 0:
        return

    # Move bot to users channel
    if ctx.author.voice:
        if ctx.guild.voice_client:
            if ctx.author.voice.channel != ctx.guild.voice_client.channel:
                await ctx.guild.voice_client.move_to(ctx.author.voice.channel)
        else:
            await ctx.author.voice.channel.connect()

    if was_empty_before or len(args) == 0:
        stefan.music_play()


@stefan.command()
async def stop(ctx):
    """ TODO: Write docstring """
    stefan.music_stop()


@stefan.command()
async def clear(ctx):
    """ TODO: Write docstring """    

    stefan.music_stop()
    stefan.queue.clear()


@stefan.command()
async def remove(ctx, index: int):
    """ TODO: Write docstring """    

    removed_current_song = stefan.queue.get_current_index() == index

    stefan.queue.remove(index)

    if stefan.queue.num_songs() > 0:

        if removed_current_song:
            stefan.music_play()

    else:
        stefan.music_stop()
    

@stefan.command()
async def move(ctx, index):
    """ TODO: Write docstring """    

    stefan.queue.move(int(index))

    if stefan.queue.num_songs() > 0:
        stefan.music_play()


@stefan.command(name="slumpa", aliases=["skaka", "blanda", "stavmixa"])
async def shuffle(ctx):
    """ TODO: Write docstring """    

    stefan.queue.shuffle()
    stefan.music_play()


@stefan.command(name="loopa", aliases=["snurra"])
async def loopa(ctx, arg1=""):
    """ TODO: Write docstring """ 

    if arg1 in ["sång", "låt", "stycke"]:
        config.toggle('is_looping_song')
    elif arg1 in ["kö", "lista"] or True:
        config.toggle('is_looping_queue')


@stefan.command()
async def nightcore(ctx):
    """ TODO: Write docstring """    

    config.toggle('nightcore')


@stefan.command()
async def playlists(ctx):
    embed=Embed(title="Spellistor:", color=Color.orange())
    for name, desc, songs in stefan.queue.get_playlists():
        noun = "låt" if len(songs) == 1 else "låtar"
        embed.add_field(name=f"**{name} ({len(songs)} {noun})**", value=f"{desc}", inline=False)
    await ctx.send(embed=embed)


@stefan.command()
async def kö(ctx, name=None):
    
    if stefan.latest_queue_message:
        await stefan.latest_queue_message.delete()
    
    stefan.latest_queue_message = await ctx.send(embed=stefan.make_queue_embed())


@stefan.command()
async def save(ctx, name, desc=None):
    """ TODO: Write docstring """
    stefan.queue.save(name, desc)


@stefan.command()
async def load(ctx, name):
    """ TODO: Write docstring """
    
    was_empty_before = stefan.queue.num_songs() == 0

    stefan.queue.load(name)

    if was_empty_before or not stefan.is_playing:
        stefan.music_play()

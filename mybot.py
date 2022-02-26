
import asyncio
import discord
from discord import Embed, Color, FFmpegPCMAudio
from discord.ext import commands

from config import config
import playlist

class MyBot(commands.Bot):
    _FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 
        'options': '-vn'
    }
    
    def __init__(self, *args, **kwargs):
        commands.Bot.__init__(self, *args, **kwargs)

        self.queue = playlist.Queue()
        self.queue.add_on_update_callback(self._handle_playlist_change)
        config.add_on_update_callback(self._handle_playlist_change)

        self._is_playing = False
        self.latest_queue_message = None

    @property
    def is_playing(self):
        return self._is_playing

    @is_playing.setter
    def is_playing(self, value):
        self._is_playing = value
        self._handle_playlist_change()

    def _handle_playlist_change(self):
        if self.latest_queue_message:
            asyncio.run_coroutine_threadsafe(bot.latest_queue_message.edit(content=None, embed=self.make_queue_embed()), self.loop)
    
    def music_play(self, ctx):       
        if not ctx.voice_client:
            print("Error: Cant't play music, bot is not connected to voice")
            return

        if ctx.voice_client.is_playing():
            # Just change audio source if we are currently playing something else
            ctx.voice_client.source = FFmpegPCMAudio(bot.queue.current_song_source(), **MyBot._FFMPEG_OPTIONS)
        else:
            # Otherwise start playing as normal
            source = FFmpegPCMAudio(bot.queue.current_song_source(), **MyBot._FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda e: play_next(ctx, e))

        bot.is_playing = True

    def music_stop(self, ctx):        
        if not ctx.voice_client:
            return

        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

        bot.is_playing = False

    def make_queue_embed(self):
        description = self.queue.playlist_string(config.get("title_max_length"), config.get("before_current"), config.get("after_current"))

        looping = "✓" if config.get("is_looping") else "✗"

        playing = "✓" if bot.is_playing else "✗"

        time = str(self.queue.duration())
        time = time if len(time) == 8 else '0' + time

        info = f"Spelar: {playing}⠀Loopar: {looping}⠀Antal låtar: {bot.queue.num_songs()}⠀Längd: {time}\n"

        description = info + description

        return Embed(color=Color.orange(), title=f"Nuvarande kö 😙", description=description)
        

bot = MyBot(command_prefix=config.get("prefix"))

@bot.event
async def on_ready():
    print("Stefan anmäler sig för tjänstgöring.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ert skitsnack"))

@bot.command()
async def ping(ctx):
    """ TODO: Write docstring """
    await ctx.message.channel.send("Pong!")

@bot.command(name = "prefix")
async def prefix(ctx, new_prefix):
    """ TODO: Write docstring """

    bot.command_prefix = new_prefix
    config.set("prefix", new_prefix)

    await ctx.message.channel.send("Tack för mitt nya prefix! 🥰")

@bot.command(name = "kom", aliases = ["komsi", "älskling", "hit"])
async def kom(ctx, arg1="", arg2="", arg3=""):
    """ TODO: Write docstring """
    cm = ctx.invoked_with
   # await ctx.send("cm: " + cm + "\narg1: " + arg1 + "\narg2: " + arg2 + "\narg3: " + arg3)
    if (cm == "kom"
        or (cm == "hit")
        or (cm == "komsi" and arg1 == "komsi")
        or (cm == "älskling" and arg1 == "jag" and arg2 == "är" and arg3 == "hemma")):
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

@bot.command(name = "stick", aliases = ["schas", "försvinn", "dra", "gå"])
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

@bot.command(name = "hjälp", aliases = ["hilfe", "aidez-moi", "h"])
async def hjälp(ctx):
    """ TODO: Write docstring """
    embed=Embed(title="Mina kommandon 😎 :", color=Color.orange(), description = f"Genom att skriva \"{bot.command_prefix}\" följt av ett av nedanstående kommandon kan du få mig att göra roliga saker! Lek med mig! 🥰")
    embed.add_field(name="**stick / gå / schas / försvinn / dra**", value="Säg åt mig att lämna röstkanalen. 😥", inline=False)
    embed.add_field(name="**kom / hit / komsi komsi / älskling jag är hemma**", value="Be mig att göra dig sällskap! 😇", inline=False)
    embed.add_field(name="**prefix**", value="Ge mig ett nytt prefix som jag kan lyssna på! ☺️")
    await ctx.send(embed=embed)


def play_next(ctx, e):
    if e:
        print(f"Error: play_next(): {e}")
        return

    if bot.queue.get_current_index() == bot.queue.num_songs() and not config.get("is_looping"):
        bot.music_stop(ctx)    

    elif bot.is_playing:
        bot.queue.next()
        bot.music_play(ctx)
    

@bot.command()
async def next(ctx):
    """ TODO: Write docstring """
    if not (bot.queue.get_current_index() == bot.queue.num_songs() and not config.get("is_looping")):
        bot.queue.next()
        bot.music_play(ctx)
    else:
        bot.music_stop(ctx)


@bot.command()
async def prev(ctx):
    """ TODO: Write docstring """
    if not (bot.queue.get_current_index() == 1 and not config.get("is_looping")):
        bot.queue.prev()
        bot.music_play(ctx)
    else:
        bot.music_stop(ctx)


@bot.command()
async def play(ctx, url=None):
    """ TODO: Write docstring """    
    # await ctx.message.add_reaction("👌")

    was_empty_before = bot.queue.num_songs() == 0

    if url != None:
        bot.queue.add_song_from_url(url)

    if bot.queue.num_songs() == 0:
        return

    if was_empty_before or not url:
        bot.music_play(ctx)
    
    # await ctx.message.remove_reaction("👌", bot.user)
    # await ctx.message.add_reaction("👍")
    # await ctx.message.delete(delay=5)


@bot.command()
async def stop(ctx):
    """ TODO: Write docstring """
    bot.music_stop(ctx)


@bot.command()
async def clear(ctx):
    """ TODO: Write docstring """    

    bot.music_stop(ctx)
    bot.queue.clear()


@bot.command()
async def remove(ctx, index: int):
    """ TODO: Write docstring """    

    removed_current_song = bot.queue.get_current_index() == index

    bot.queue.remove(index)

    if bot.queue.num_songs() > 0:

        if removed_current_song:
            bot.music_play(ctx)

    else:
        bot.music_stop(ctx)
    

@bot.command()
async def move(ctx, index):
    """ TODO: Write docstring """    

    bot.queue.move(int(index))
    bot.music_play(ctx)


@bot.command(name="slumpa", aliases=["skaka", "blanda", "stavmixa"])
async def shuffle(ctx):
    """ TODO: Write docstring """    

    bot.queue.shuffle()
    bot.music_play(ctx)


@bot.command(name="loopa", aliases=["snurra"])
async def loopa(ctx):
    """ TODO: Write docstring """    

    config.set("is_looping", not config.get("is_looping"))


@bot.command()
async def playlists(ctx):
    embed=Embed(title="Spellistor:", color=Color.orange())
    for name, desc, songs in bot.queue.get_playlists():
        noun = "låt" if len(songs) == 1 else "låtar"
        embed.add_field(name=f"**{name} ({len(songs)} {noun})**", value=f"{desc}", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def kö(ctx, name=None):
    
    if bot.latest_queue_message:
        await bot.latest_queue_message.delete()
    
    bot.latest_queue_message = await ctx.send(embed=bot.make_queue_embed())


@bot.command()
async def save(ctx, name, desc=None):
    """ TODO: Write docstring """
    bot.queue.save(name, desc)


@bot.command()
async def load(ctx, name):
    """ TODO: Write docstring """
    
    was_empty_before = bot.queue.num_songs() == 0

    bot.queue.load(name)

    if was_empty_before or not bot.is_playing:
        bot.music_play(ctx)
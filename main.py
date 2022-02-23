""" TODO: Write docstring """

import asyncio
import discord
from discord import Embed, Color, FFmpegOpusAudio
from discord.ext import commands

import config
import playlist

config = config.Config("config.json")
bot = commands.Bot(command_prefix=config.get("prefix"))
queue = playlist.Queue()

is_playing = False
latest_queue_message = None
loop = None

@bot.event
async def on_ready():
    print("Stefan anmäler sig för tjänstgöring.")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="ert skitsnack"))
    global loop
    loop = asyncio.get_running_loop()

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


def make_queue_embed():
    description = queue.playlist_string(config.get("title_max_length"))

    playing = "spelande" if is_playing else "pausade"

    looping = "loopande" if config.get("is_looping") else "icke-loopande"

    time = str(queue.duration())
    time = time if len(time) == 8 else '0' + time

    return Embed(color=Color.orange(), title=f"Nuvarande {playing} {looping} kö 😙 {queue.num_songs()} låtar [{time}]", description=description)


def play_next(ctx, e):
    if e:
        print(f"Error: play_next(): {e}")
        return

    if queue.get_current_index() == queue.num_songs() and not config.get("is_looping"):
        return
    
    if is_playing:
        queue.next()

        # We have stopped playing, so we need to call play again after getting the
        # new source
        source = FFmpegOpusAudio(queue.get_current_song())
        ctx.voice_client.play(source, after=lambda e: play_next(ctx, e))
    
    global latest_queue_message
    if latest_queue_message:
        asyncio.run_coroutine_threadsafe(latest_queue_message.edit(embed=make_queue_embed()), loop)


@bot.command()
async def next(ctx):
    """ TODO: Write docstring """
    if queue.get_current_index() == queue.num_songs() and not config.get("is_looping"):
        return

    queue.next()

    if ctx.voice_client.is_playing():
        # Simply change audio source
        ctx.voice_client.source = FFmpegOpusAudio(queue.get_current_song())
    
    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(embed=make_queue_embed())


@bot.command()
async def prev(ctx):
    """ TODO: Write docstring """
    if not (queue.get_current_index() == 1 and not config.get("is_looping")):
        queue.prev()

    if ctx.voice_client.is_playing():
        # Simply change audio source
        ctx.voice_client.source = FFmpegOpusAudio(queue.get_current_song())

    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(embed=make_queue_embed())


@bot.command()
async def play(ctx, url=None):
    """ TODO: Write docstring """    
    if url != None:
        queue.add_song(url)

    if not ctx.voice_client.is_playing():

        source = FFmpegOpusAudio(queue.get_current_song())
        ctx.voice_client.play(source, after=lambda e: play_next(ctx, e))
    
        global is_playing
        is_playing = True

    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(embed=make_queue_embed())


@bot.command()
async def stop(ctx):
    """ TODO: Write docstring """
    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

        global is_playing
        is_playing = False
    
    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(embed=make_queue_embed())


@bot.command()
async def clear(ctx):
    """ TODO: Write docstring """    

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

        global is_playing
        is_playing = False
    
    queue.clear()

    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(content="Inga låtar i kön", embed=None)


@bot.command()
async def remove(ctx, index: int):
    """ TODO: Write docstring """    

    removed_current_song = queue.get_current_index() == index

    queue.remove(index)

    if queue.num_songs() > 0:

        if removed_current_song and ctx.voice_client.is_playing():
            # Change audio source
            ctx.voice_client.source = FFmpegOpusAudio(queue.get_current_song())
    
    elif ctx.voice_client.is_playing():
        ctx.voice_client.stop()

        global is_playing
        is_playing = False
    
    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(embed=make_queue_embed())

@bot.command()
async def move(ctx, index):
    """ TODO: Write docstring """    

    queue.move(int(index))

    if ctx.voice_client.is_playing():
        # Simply change audio source
        ctx.voice_client.source = FFmpegOpusAudio(queue.get_current_song())

    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(embed=make_queue_embed())


@bot.command(name="slumpa", aliases=["skaka", "blanda", "stavmixa"])
async def shuffle(ctx):
    """ TODO: Write docstring """    

    queue.shuffle()

    if ctx.voice_client.is_playing():
        # Simply change audio source
        ctx.voice_client.source = FFmpegOpusAudio(queue.get_current_song())
    
    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(embed=make_queue_embed())


@bot.command(name="loopa", aliases=["snurra"])
async def loopa(ctx):
    """ TODO: Write docstring """    

    config.set("is_looping", not config.get("is_looping"))

    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.edit(embed=make_queue_embed())


@bot.command()
async def playlists(ctx):
    embed=Embed(title="Spellistor:", color=Color.orange())
    for name, desc, songs in queue.get_playlists():
        noun = "låt" if len(songs) == 1 else "låtar"
        embed.add_field(name=f"**{name} ({len(songs)} {noun})**", value=f"{desc}", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def kö(ctx, name=None):
    if queue.num_songs() == 0:
        await ctx.send("Inga låtar finns i kön")
        return
    
    global latest_queue_message
    if latest_queue_message:
        await latest_queue_message.delete()
    
    latest_queue_message = await ctx.send(embed=make_queue_embed())


@bot.command()
async def save(ctx, name, desc=None):
    """ TODO: Write docstring """
    queue.save(name, desc)


@bot.command()
async def load(ctx, name):
    """ TODO: Write docstring """
    queue.load(name)


bot.run(config.get("token"))

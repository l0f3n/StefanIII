""" TODO: Write docstring """

import discord
from discord import Embed, Color, FFmpegOpusAudio
from discord.ext import commands
from functools import partial

import config
import playlist

config = config.Config("config.json")
bot = commands.Bot(command_prefix=config.get("prefix"))
queue = playlist.Queue()

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

@bot.command()
async def next(ctx):
    """ TODO: Write docstring """
    queue.next()

    if ctx.voice_client.is_playing():
        ctx.voice_client.stop()

    source = FFmpegOpusAudio(queue.get_current_song())
    # cooked_after_play = partial(after_play, ctx)
    ctx.voice_client.play(source)

# def after_play(ctx, err):
#     if err:
#         print("Error: Unexpected error in after_play:", err)
#         return
    
#     queue.next()

#     if not ctx.voice_client.is_playing():
#         source = FFmpegOpusAudio(queue.get_current_source())
#         cooked_after_play = partial(after_play, ctx)
#         ctx.voice_client.play(source, after=cooked_after_play)  


@bot.command()
async def play(ctx, url=None):
    """ TODO: Write docstring """
    if url != None:
        queue.add_song(url)

    if not ctx.voice_client.is_playing():
        source = FFmpegOpusAudio(queue.get_current_song())
        # cooked_after_play = partial(after_play, ctx)
        ctx.voice_client.play(source)


@bot.command()
async def playlists(ctx):
    embed=Embed(title="Spellistor:", color=Color.orange())
    for name, desc, songs in queue.get_playlists():
        embed.add_field(name=f"**{name} ({len(songs)} låtar)**", value=f"{desc}", inline=False)
    await ctx.send(embed=embed)


@bot.command()
async def save(ctx, name, desc=None):
    """ TODO: Write docstring """
    queue.save(name, desc)


@bot.command()
async def load(ctx, name):
    """ TODO: Write docstring """
    queue.load(name)


bot.run(config.get("token"))

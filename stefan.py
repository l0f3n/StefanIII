import discord
from discord import Embed, Color
from discord.ext import commands

from music import Music
from config import config

class Stefan(commands.Bot):
    
    def __init__(self, *args, **kwargs):
        commands.Bot.__init__(self, *args, **kwargs)

        self.current_context = None
        self.latest_context = None
        
        self.before_invoke(self._handle_before_invoke)
        self.after_invoke(self._handle_after_invoke)


    async def _handle_before_invoke(self, ctx):
        self.current_context = ctx
        self.latest_context = ctx
        await ctx.message.add_reaction("👌")

    async def _handle_after_invoke(self, ctx):
        self.current_context = None
        await ctx.message.remove_reaction("👌", self.user)
        await ctx.message.add_reaction("👍")

    async def close(self):
        for cog in self.cogs.values():
            await cog.close()

        if self.latest_context:
            await self.latest_context.send("Jag dör! 😱")

        return await super().close()

    async def join_channel(self):
        """
        Joins the users channel given the current context.
        """
        if not self.current_context:
            return
        
        if self.current_context.author and self.current_context.author.voice:
            if self.current_context.guild and self.current_context.guild.voice_client:
                if self.current_context.author.voice.channel != self.current_context.guild.voice_client.channel:
                    await self.current_context.guild.voice_client.move_to(self.current_context.author.voice.channel)
            else:
                await self.current_context.author.voice.channel.connect()


stefan = Stefan(command_prefix=config.get("prefix"))
stefan.add_cog(Music(stefan))

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
    await config.set("prefix", new_prefix)

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

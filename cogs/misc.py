from discord import Color, Embed
from discord.ext import commands

class Misc(commands.Cog):
    
    def __init__(self, bot, config) -> None:
        super().__init__()

        self.bot = bot
        self.config = config

    async def close(self):
        pass

    @commands.command()
    async def ping(self, ctx):
        """ TODO: Write docstring """
        await ctx.message.channel.send("Pong!")

    @commands.command(name = "prefix")
    async def prefix(self, ctx, new_prefix):
        """ TODO: Write docstring """

        self.command_prefix = new_prefix
        await self.config.set("prefix", new_prefix)

        await ctx.message.channel.send("Tack för mitt nya prefix! 🥰")

    @commands.command(name = "kom", aliases = ["komsi", "älskling", "hit"])
    async def kom(self, ctx, arg1="", arg2="", arg3=""):
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

    @commands.command(name = "stick", aliases = ["schas", "försvinn", "dra", "gå"])
    async def stick(self, ctx):
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

    @commands.command(name = "hjälp", aliases = ["hilfe", "aidez-moi", "h"])
    async def hjälp(self, ctx):
        """ TODO: Write docstring """
        embed=Embed(title="Mina kommandon 😎 :", color=Color.orange(), description = f"Genom att skriva \"{self.command_prefix}\" följt av ett av nedanstående kommandon kan du få mig att göra roliga saker! Lek med mig! 🥰")
        embed.add_field(name="**stick / gå / schas / försvinn / dra**", value="Säg åt mig att lämna röstkanalen. 😥", inline=False)
        embed.add_field(name="**kom / hit / komsi komsi / älskling jag är hemma**", value="Be mig att göra dig sällskap! 😇", inline=False)
        embed.add_field(name="**prefix**", value="Ge mig ett nytt prefix som jag kan lyssna på! ☺️")
        await ctx.send(embed=embed)
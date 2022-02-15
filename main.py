from discord.ext import commands

def read_token():
    with open('token.txt') as f:
        return f.read()

def read_prefix():
    with open('prefix.txt') as f:
        return f.read()

bot = commands.Bot(command_prefix=read_prefix())

@bot.command()
async def ping(ctx):
    await ctx.message.channel.send("Pong!")

@bot.command(name = "prefix", aliases = ["pix", "fax"])
async def prefix(ctx, new_prefix):
    bot.command_prefix = new_prefix
    with open('prefix.txt', "w") as f:
        f.write(new_prefix)
    await ctx.message.channel.send("Tack för mitt nya prefix! 🥰")

@bot.command(name = "kom", aliases = ["komsi komsi", "älskling jag är hemma", "hit"])
async def kom(ctx):
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

@bot.command(name = "stick", aliases = ["schas", "försvinn", "dra", "gå"])
async def stick(ctx):
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


bot.run(read_token())

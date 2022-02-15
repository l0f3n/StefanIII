from discord.ext import commands

bot = commands.Bot(command_prefix='-')

@bot.command()
async def ping(ctx):
    print("pong")


def read_token():
    with open('token.txt') as f:
        return f.read()


bot.run(read_token())
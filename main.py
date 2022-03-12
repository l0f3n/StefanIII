""" TODO: Write docstring """

from config import config
from stefan import stefan
import discord.errors


def main():
    discord_token = config.get("token", allow_default=False)

    if not discord_token:
        print("Error: Can't start bot, please add your discord bot token to 'config.json'")
        return

    try:
        stefan.run(config.get("token"))
    except discord.errors.LoginFailure:
        print("Error: Something went wrong when using discord credentials")


if __name__ == '__main__':
    main()

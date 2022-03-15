import discord.errors

from config import Config
from stefan import Stefan
from cogs import Music, Misc

def main():
    config = Config('config.json')

    config.set_from_env_var('token', 'DISCORD_TOKEN')
    config.set_from_env_var('spotify_id', 'SPOTITFY_ID')
    config.set_from_env_var('spotify_secret', 'SPOTIFY_SECRET')
    
    discord_token = config.get("token", allow_default=False)

    if not discord_token:
        print("Error: Can't start bot, please add your discord bot token to 'config.json'")
        return

    try:
        stefan = Stefan(command_prefix=config.get("prefix"))
        stefan.add_cog(Music(stefan, config))
        stefan.add_cog(Misc(stefan, config))

        stefan.run(config.get("token"))
    except discord.errors.LoginFailure:
        print("Error: Something went wrong when using discord credentials")


if __name__ == '__main__':
    main()

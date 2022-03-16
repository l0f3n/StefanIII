import discord.errors

from config import Config
from log import get_logger
from stefan import Stefan
from cogs import Music, Misc

logger = get_logger(__name__)

def main():
    config = Config('config.json')

    config.set_from_env_var('token', 'DISCORD_TOKEN')
    config.set_from_env_var('spotify_id', 'SPOTIFY_ID')
    config.set_from_env_var('spotify_secret', 'SPOTIFY_SECRET')
    
    discord_token = config.get("token", allow_default=False)

    if not discord_token:
        logger.error("Can't start bot, no token provided")
        return

    try:
        stefan = Stefan(command_prefix=config.get("prefix"))
        stefan.add_cog(Music(stefan, config))
        stefan.add_cog(Misc(stefan, config))

        stefan.run(config.get("token"))
    except discord.errors.LoginFailure as e:
        logger.error("Something went wrong when using discord credentials", exc_info=e)


if __name__ == '__main__':
    main()

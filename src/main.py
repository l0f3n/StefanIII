import discord.errors

from config import config
from log import get_logger
from stefan import Stefan

logger = get_logger(__name__)

def main():

    config.set_from_env_var('token', 'DISCORD_TOKEN')
    config.set_from_env_var('spotify_id', 'SPOTIFY_ID')
    config.set_from_env_var('spotify_secret', 'SPOTIFY_SECRET')

    prefix = config.get("prefix")

    logger.info(f"Using prefix: '{prefix}'")

    discord_token = config.get("token", allow_default=False)

    if not discord_token:
        logger.error("Can't start bot, no token provided")
        return

    try:
        intents = discord.Intents.default()
        intents.message_content = True

        stefan = Stefan(command_prefix=prefix, intents=intents)

        stefan.run(config.get("token"), log_handler=None)
    except discord.errors.LoginFailure as e:
        logger.error("Something went wrong when using discord credentials", exc_info=e)


if __name__ == '__main__':
    main()

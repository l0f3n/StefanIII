""" TODO: Write docstring """

from config import config
from mybot import bot

bot.run(config.get("token"))

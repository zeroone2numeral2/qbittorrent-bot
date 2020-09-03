# noinspection PyPackageRequirements
from telegram.utils.request import Request

from .bot import CustomBot
from .bot import CustomUpdater
from config import config

custom_bot = CustomBot(config.telegram.token, request=Request(con_pool_size=config.telegram.workers + 4))
updater = CustomUpdater(bot=custom_bot, workers=config.telegram.get('workers', 1))

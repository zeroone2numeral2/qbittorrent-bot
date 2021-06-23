# noinspection PyPackageRequirements
from telegram.ext import Defaults

from .bot import CustomBot
from .bot import CustomUpdater
from config import config

updater = CustomUpdater(
    token=config.telegram.token,
    defauls=Defaults(timeout=config.telegram.timeout),
    workers=config.telegram.get('workers', 1)
)

# noinspection PyPackageRequirements
from telegram.ext import Defaults

from .bot import CustomUpdater
from config import config

updater = CustomUpdater(
    token=config.telegram.token,
    defaults=Defaults(timeout=config.telegram.timeout, disable_web_page_preview=True),
    workers=config.telegram.get('workers', 1)
)

# noinspection PyPackageRequirements
from telegram.ext import Defaults

from .bot import CustomUpdater
from config import config

REQUEST_KWARGS = {}
if config.proxy.url:
    REQUEST_KWARGS['proxy_url'] = config.proxy.url 
    if config.proxy.username:
        REQUEST_KWARGS['urllib3_proxy_kwargs'] = {
            'username': config.proxy.username,
            'password': config.proxy.password 
        }

BOT_API_KWARGS = {}
if config.bot_api.url:
    # local Bot API server (e.g. the one in ./telegram-bot-api, connected to Telegram through an MTProto proxy)
    bot_api_url = config.bot_api.url.rstrip('/')
    BOT_API_KWARGS['base_url'] = f'{bot_api_url}/bot'
    BOT_API_KWARGS['base_file_url'] = f'{bot_api_url}/file/bot'


updater = CustomUpdater(
    token=config.telegram.token,
    defaults=Defaults(timeout=config.telegram.timeout, disable_web_page_preview=True),
    workers=config.telegram.workers,
    request_kwargs=REQUEST_KWARGS,
    **BOT_API_KWARGS,
)

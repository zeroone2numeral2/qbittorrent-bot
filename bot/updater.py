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


updater = CustomUpdater(
    token=config.telegram.token,
    defaults=Defaults(timeout=config.telegram.timeout, disable_web_page_preview=True),
    workers=config.telegram.workers,
    request_kwargs=REQUEST_KWARGS,
)

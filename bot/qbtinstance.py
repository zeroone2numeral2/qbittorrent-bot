import logging

import requests

from .updater import updater
from qbt import CustomClient
from qbt import OfflineClient
from config import config

logger = logging.getLogger(__name__)


try:
    qb = CustomClient(config.qbittorrent.url, bot_username=updater.bot.username)
    qb.login(config.qbittorrent.login, config.qbittorrent.secret)
except requests.exceptions.ConnectionError as e:
    logger.error('exception while connecting to qbittorrent: %s', str(e))
    qb = OfflineClient()

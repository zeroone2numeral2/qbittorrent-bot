import logging
import logging.config
import json

from telegram import ParseMode
from telegram.utils.request import Request
import requests

from .bot import CustomBot
from .bot import CustomUpdater
from qbt import CustomClient
from qbt import OfflineClient
from utils import u
from config import config

cutom_bot = CustomBot(config.telegram.token, request=Request(con_pool_size=config.telegram.workers + 4))
updater = CustomUpdater(bot=cutom_bot, workers=config.telegram.get('workers', 1))


def load_logging_config(file_path='logging.json', logfile='logs/qbtbot.log'):
    with open(file_path, 'r') as f:
        logging_config = json.load(f)
    logging_config['handlers']['file']['filename'] = logfile
    logging.config.dictConfig(logging_config)


logger = logging.getLogger(__name__)

try:
    qb = CustomClient(config.qbittorrent.url, bot_username=updater.bot.username)
    qb.login(config.qbittorrent.login, config.qbittorrent.secret)
except requests.exceptions.ConnectionError as e:
    logger.error('exception while connecting to qbittorrent: %s', str(e))
    qb = OfflineClient()


class Completed:
    def __init__(self):
        self._data = list()

    def init(self, hashes_list):
        self._data = hashes_list

    def is_new(self, torrent_hash):
        if torrent_hash not in self._data:
            self._data.append(torrent_hash)
            return True
        else:
            return False


completed_torrents = Completed()


@u.failwithmessage_job
def notify_completed(bot, _):
    logger.info('executing completed job')

    completed = qb.torrents(filter='completed')

    for t in completed:
        if completed_torrents.is_new(t.hash):
            torrent = qb.torrent(t.hash)
            text = '<code>{}</code> completed'.format(u.html_escape(torrent.name))
            bot.send_message(
                config.telegram.admins[0],
                text,
                reply_markup=torrent.short_markup(force_resume_button=False),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )


def main():
    load_logging_config()

    updater.import_handlers(r'bot/plugins/')

    logger.info('registering "completed torrents" job')
    try:
        completed_torrents.init([t.hash for t in qb.torrents(filter='completed')])
        updater.job_queue.run_repeating(notify_completed, interval=120, first=120)
    except ConnectionError:
        # catch the connection error raised by the OffilneClient, in case we are offline
        logger.warning('cannot register the completed torrents job: qbittorrent is not online')

    updater.run(clean=True)

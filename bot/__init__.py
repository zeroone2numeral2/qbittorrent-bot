import logging
import logging.config
import json

from telegram import ParseMode, Bot
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


class HashesStorage:
    def __init__(self, file_name):
        self._file_name = file_name

        try:
            with open(self._file_name, 'r') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._data = list()

    @staticmethod
    def to_list(string):
        if not isinstance(string, list):
            return [string]

        return string

    def save(self):
        with open(self._file_name, 'w+') as f:
            json.dump(self._data, f)

    def insert(self, hashes_list: [str, list]):
        hashes_list = self.to_list(hashes_list)

        for h in hashes_list:
            if h in self._data:
                continue

            self._data.append(h)

        self.save()


class Completed(HashesStorage):
    def is_new(self, torrent_hash):
        if torrent_hash not in self._data:
            self._data.append(torrent_hash)
            self.save()
            return True
        else:
            return False


class DontNotify(HashesStorage):
    def send_notification(self, torrent_hash):
        if torrent_hash not in self._data:
            return True

        return False


completed_torrents = Completed('completed.json')
dont_notify_torrents = DontNotify('do_not_notify.json')


@u.failwithmessage_job
def notify_completed(bot: Bot, _):
    logger.info('executing completed job')

    completed = qb.torrents(filter='completed')

    for t in completed:
        if completed_torrents.is_new(t.hash):
            torrent = qb.torrent(t.hash)

            logger.info('completed: %s (%s)', torrent.hash, torrent.name)

            if config.qbittorrent.get('pause_completed_torrents', False):
                logger.info('pausing: %s (%s)', torrent.hash, torrent.name)
                torrent.pause()

            if not dont_notify_torrents.send_notification(t.hash):
                logger.info('we will not send a notification about %s (%s)', t.hash, t.name)
                continue

            text = '<code>{}</code> completed ({})'.format(u.html_escape(torrent.name), torrent.size_pretty)

            send_message_kwargs = dict(
                text=text,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                disable_notification=True
            )

            if config.telegram.get('completed_torrents_notification', None):
                # don't send the message in private if there's a notifications channel set
                bot.send_message(config.telegram.completed_torrents_notification, **send_message_kwargs)
            else:
                bot.send_message(
                    config.telegram.admins[0],
                    reply_markup=torrent.short_markup(force_resume_button=False),
                    **send_message_kwargs
                )


def main():
    load_logging_config()

    updater.import_handlers(r'bot/plugins/')

    logger.info('registering "completed torrents" job')
    try:
        completed_torrents.insert([t.hash for t in qb.torrents(filter='completed')])
        updater.job_queue.run_repeating(notify_completed, interval=120, first=120)
    except ConnectionError:
        # catch the connection error raised by the OffilneClient, in case we are offline
        logger.warning('cannot register the completed torrents job: qbittorrent is not online')

    updater.run(clean=True)

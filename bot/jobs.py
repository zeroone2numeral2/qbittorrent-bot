import logging
import json

from telegram import ParseMode
from telegram.ext import CallbackContext

from .qbtinstance import qb
from utils import u
from config import config

logger = logging.getLogger("jobs")


class HashesStorage:
    def __init__(self, file_path):
        self._file_path = file_path

        try:
            with open(self._file_path, 'r') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._data = list()

    @staticmethod
    def to_list(string):
        if not isinstance(string, list):
            return [string]

        return string

    def save(self):
        with open(self._file_path, 'w+') as f:
            json.dump(self._data, f)

    def insert(self, hashes_list: [str, list]):
        hashes_list = self.to_list(hashes_list)

        for h in hashes_list:
            if h in self._data:
                continue

            self._data.append(h)

        self.save()


class Completed(HashesStorage):
    def is_new(self, torrent_hash, append=True):
        if torrent_hash not in self._data:
            if append:
                self._data.append(torrent_hash)
                self.save()

            return True
        else:
            return False


completed_torrents = Completed('completed.json')

try:
    completed_torrents.insert([t.hash for t in qb.torrents(filter='completed')])
except ConnectionError:
    # catch the connection error raised by the OffilneClient, in case we are offline
    logger.warning('cannot register the completed torrents job: qbittorrent is not online')


@u.failwithmessage_job
def notify_completed(context: CallbackContext):
    logger.info('executing completed job...')

    completed = qb.torrents(filter='completed', get_torrent_generic_properties=False)

    for torrent in completed:
        if not completed_torrents.is_new(torrent.hash):
            continue

        logger.info('new completed torrent: %s (%s)', torrent.hash, torrent.name)

        if not config.notifications.completed_torrents:
            logger.info("notifications chat not set in the config file")
            continue

        if config.notifications.no_notification_tag:
            tag_lower = config.notifications.no_notification_tag.lower()
            if tag_lower in torrent.tags_list(lower=True):
                logger.info('the torrent has been tagged "%s": no notification will be sent', tag_lower)
                continue

        drive_free_space = u.free_space(qb.save_path)
        text = f'<code>{torrent.name_escaped}</code> completed ({torrent.size_pretty}, free space: {drive_free_space})'

        logger.debug("sending message")
        context.bot.send_message(
            chat_id=config.notifications.completed_torrents,
            text=text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            disable_notification=True
        )

    logger.info('...completed job executed')

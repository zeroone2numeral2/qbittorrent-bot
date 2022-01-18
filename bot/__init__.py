import datetime
import logging
import logging.config
import json

from requests import HTTPError

from .updater import updater
from .jobs import notify_completed
from .qbtinstance import qb
from utils import utils
from config import config


def load_logging_config(file_path='logging.json'):
    with open(file_path, 'r') as f:
        logging_config = json.load(f)

    logging.config.dictConfig(logging_config)


logger = logging.getLogger(__name__)


def main():
    load_logging_config()

    updater.import_handlers(r'bot/plugins/')

    if qb.online:
        logger.info('registering jobs')
        updater.job_queue.run_repeating(notify_completed, interval=120, first=60)

        # create the category on startup
        if config.qbittorrent.added_torrents_category:
            logger.debug("creating category: %s", config.qbittorrent.added_torrents_category)
            try:
                qb.create_category(config.qbittorrent.added_torrents_category)
            except HTTPError as e:
                if "409" in str(e):
                    logger.debug("category already exists (%s)", str(e))
                else:
                    raise e

    updater.set_bot_commands(show_first=["overview", "active"])
    updater.run(drop_pending_updates=True)

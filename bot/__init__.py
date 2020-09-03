import logging
import logging.config
import json

from .updater import updater
from .jobs import notify_completed
from .qbtinstance import qb


def load_logging_config(file_path='logging.json', logfile='logs/qbtbot.log'):
    with open(file_path, 'r') as f:
        logging_config = json.load(f)
    logging_config['handlers']['file']['filename'] = logfile
    logging.config.dictConfig(logging_config)


logger = logging.getLogger(__name__)


def main():
    load_logging_config()

    updater.import_handlers(r'bot/plugins/')

    if qb.online:
        logger.info('registering "completed torrents" job')
        updater.job_queue.run_repeating(notify_completed, interval=120, first=120)

    updater.run(clean=True)

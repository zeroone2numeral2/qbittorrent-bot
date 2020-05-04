import logging
import os
import re

# noinspection PyPackageRequirements
from telegram.ext import Filters, MessageHandler

from bot import qb
from bot import updater
from utils import u
from utils import kb
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_magnet(_, update):
    logger.info('magnet url from %s', update.effective_user.first_name)

    magnet_link = update.message.text
    qb.download_from_link(magnet_link)
    # always returns an empty json:
    # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_link

    torrent_hash = re.search(r'magnet:\?xt=urn:btih:([a-z0-9]+)(?:&.*)?', magnet_link, re.I).group(1)
    logger.info('torrent hash from regex: %s', torrent_hash)

    update.message.reply_html(
        'Magnet added',
        reply_markup=kb.short_markup(torrent_hash, force_resume_button=False),
        quote=True
    )

    torrents = qb.torrents(filter='all')
    logger.debug('all torrents hashes:')
    for t in torrents:
        logger.debug('%s - %s', t.hash, t.name)


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_file(bot, update):
    logger.info('document from %s', update.effective_user.first_name)

    if update.message.document.mime_type != 'application/x-bittorrent':
        update.message.reply_markdown('Please send me a `.torrent` file')
        return

    file_id = update.message.document.file_id
    torrent_file = bot.get_file(file_id)

    file_path = './downloads/{}'.format(update.message.document.file_name)
    torrent_file.download(file_path)

    with open(file_path, 'rb') as f:
        # this method always returns an empty json:
        # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_file
        qb.download_from_file(f)

    os.remove(file_path)
    update.message.reply_text('Torrent added', quote=True)


updater.add_handler(MessageHandler(Filters.text & Filters.regex(r'^magnet:\?.*'), add_from_magnet))
updater.add_handler(MessageHandler(Filters.document, add_from_file))

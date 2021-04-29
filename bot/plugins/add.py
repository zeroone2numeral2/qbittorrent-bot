import logging
import os
import re

# noinspection PyPackageRequirements
from telegram import Update
from telegram.ext import Filters, MessageHandler, CallbackContext

from bot.qbtinstance import qb
from bot.updater import updater
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
        reply_markup=kb.short_markup(torrent_hash),
        quote=True
    )


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_file(update: Update, context: CallbackContext):
    logger.info('document from %s', update.effective_user.first_name)

    if update.message.document.mime_type != 'application/x-bittorrent':
        update.message.reply_markdown('Please send me a `.torrent` file')
        return

    file_id = update.message.document.file_id
    torrent_file = context.bot.get_file(file_id)

    file_path = './downloads/{}'.format(update.message.document.file_name)
    torrent_file.download(file_path)

    with open(file_path, 'rb') as f:
        # this method always returns an empty json:
        # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_file
        qb.download_from_file(f)

    os.remove(file_path)
    update.message.reply_text('Torrent added', quote=True)


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_url(update: Update, context: CallbackContext):
    logger.info('url from %s', update.effective_user.first_name)

    magnet_link = update.message.text
    qb.download_from_link(magnet_link)
    # always returns an empty json:
    # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_link

    update.message.reply_text('Torrent url added', quote=True)

updater.add_handler(MessageHandler(Filters.text & Filters.regex(r'^magnet:\?.*'), add_from_magnet))
updater.add_handler(MessageHandler(Filters.document, add_from_file))
updater.add_handler(MessageHandler(Filters.text & Filters.regex(r"^https?:\/\/.*(jackett|\.torren|\/torrent).*"), add_from_url))

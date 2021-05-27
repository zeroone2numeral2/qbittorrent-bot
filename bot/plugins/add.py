import logging
import os
import re

# noinspection PyPackageRequirements
from telegram import Update, BotCommand, ParseMode
from telegram.ext import Filters, MessageHandler, CallbackContext

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import kb
from utils import Permissions
from config import config

logger = logging.getLogger(__name__)


def notify_addition(current_chat_id: int):
    if not config.telegram.get("new_torrents_notification", 0):
        return

    target_chat_id = config.telegram.new_torrents_notification
    if target_chat_id != current_chat_id:  # do not send if the target chat is the current chat
        return target_chat_id


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_magnet(update: Update, context: CallbackContext):
    logger.info('magnet url from %s', update.effective_user.first_name)

    magnet_link = update.message.text

    kwargs = dict()
    if config.qbittorrent.get("added_torrents_tag", None):
        kwargs["tags"] = config.qbittorrent.added_torrents_tag

    qb.download_from_link(magnet_link, **kwargs)
    # always returns an empty json:
    # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_link

    torrent_hash = u.hash_from_magnet(magnet_link)
    logger.info('torrent hash from regex: %s', torrent_hash)

    torrent_keyboard_markup = kb.short_markup(torrent_hash)
    update.message.reply_html(
        'Magnet added',
        reply_markup=torrent_keyboard_markup,
        quote=True
    )

    target_chat_id = notify_addition(update.effective_chat.id)
    if not target_chat_id:
        return

    text = "User {} [{}] added a magnet link, hash: <code>{}</code>".format(
        update.effective_user.full_name, update.effective_user.id,
        torrent_hash
    )
    context.bot.send_message(
        target_chat_id,
        text,
        reply_markup=torrent_keyboard_markup,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def on_invalid_mime_type(update: Update, context: CallbackContext):
    logger.info('invalid document from %s', update.effective_user.first_name)
    logger.debug("file name: %s", update.message.document.file_name)
    logger.debug("mime type: %s", update.message.document.mime_type)

    update.message.reply_markdown('Please send me a `.torrent` file', quote=True)


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_file(update: Update, context: CallbackContext):
    logger.info('application/x-bittorrent document from %s', update.effective_user.first_name)

    file_id = update.message.document.file_id
    torrent_file = context.bot.get_file(file_id)

    file_path = './downloads/{}'.format(update.message.document.file_name)
    torrent_file.download(file_path)

    kwargs = dict()
    if config.qbittorrent.get("added_torrents_tag", None):
        kwargs["tags"] = config.qbittorrent.added_torrents_tag

    with open(file_path, 'rb') as f:
        # this method always returns an empty json:
        # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_file
        qb.download_from_file(f, **kwargs)

    update.message.reply_text('Torrent added', quote=True)

    os.remove(file_path)

    target_chat_id = notify_addition(update.effective_chat.id)
    if not target_chat_id:
        return

    text = "User {} [{}]  added torrent file {}".format(
        update.effective_user.full_name, update.effective_user.id,
        update.message.document.file_name or "[unknown file name]"
    )
    context.bot.send_message(target_chat_id, text, disable_web_page_preview=True)


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_url(update: Update, context: CallbackContext):
    logger.info('url from %s', update.effective_user.first_name)

    torrent_url = update.message.text

    kwargs = dict()
    if config.qbittorrent.get("added_torrents_tag", None):
        kwargs["tags"] = config.qbittorrent.added_torrents_tag

    qb.download_from_link(torrent_url, **kwargs)
    # always returns an empty json:
    # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_link

    update.message.reply_text('Torrent url added', quote=True)

    target_chat_id = notify_addition(update.effective_chat.id)
    if not target_chat_id:
        return

    text = "User {} [{}] added a torrent from an url: {}".format(
        update.effective_user.full_name, update.effective_user.id,
        torrent_url
    )
    context.bot.send_message(target_chat_id, text, disable_web_page_preview=True)


updater.add_handler(MessageHandler(Filters.text & Filters.regex(r'^magnet:\?.*'), add_from_magnet))
updater.add_handler(MessageHandler(Filters.document.mime_type("application/x-bittorrent"), add_from_file))
updater.add_handler(MessageHandler(Filters.document, on_invalid_mime_type))
updater.add_handler(MessageHandler(Filters.text & Filters.regex(r"^https?:\/\/.*(jackett|\.torren|\/torrent).*"), add_from_url))

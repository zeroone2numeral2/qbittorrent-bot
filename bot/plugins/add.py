import logging
import os
import re
from html import escape
import hashlib

# noinspection PyPackageRequirements
from typing import Optional

from telegram import Update, BotCommand, ParseMode, User, Bot
from telegram.ext import Filters, MessageHandler, CallbackContext
import bencoding

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import kb
from utils import Permissions
from config import config

logger = logging.getLogger(__name__)


def notify_addition(current_chat_id: int, bot: Bot, user: User, torrent_description: str):
    if not config.notifications.added_torrents:
        return

    target_chat_id = config.notifications.added_torrents
    if target_chat_id != current_chat_id:  # do not send if the target chat is the current chat
        return

    text = f"User {escape(user.full_name)} [<code>{user.id}</code>] added a torrent: " \
           f"<code>{escape(torrent_description)}</code>"
    bot.send_message(
        target_chat_id,
        text,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )


def get_qbt_request_kwargs() -> dict:
    kwargs = dict()
    if config.qbittorrent.added_torrents_tag:
        # string with tags separated by ",", but since it's only one tehre's no need to join
        kwargs["tags"] = config.qbittorrent.added_torrents_tag
    if config.qbittorrent.added_torrents_category:
        kwargs["category"] = config.qbittorrent.added_torrents_category

    return kwargs


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_magnet(update: Update, context: CallbackContext):
    logger.info('magnet url from %s', update.effective_user.first_name)

    magnet_link = update.message.text

    kwargs = get_qbt_request_kwargs()

    qb.download_from_link(magnet_link, **kwargs)
    # always returns an empty json:
    # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_link

    torrent_hash = u.hash_from_magnet(magnet_link)
    logger.info('torrent hash from regex: %s', torrent_hash)

    update.message.reply_html(
        'Magnet added',
        reply_markup=kb.short_markup(torrent_hash),
        quote=True
    )

    notify_addition(update.effective_chat.id, context.bot, update.effective_user, torrent_hash)


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_file(update: Update, context: CallbackContext):
    logger.info('application/x-bittorrent document from %s', update.effective_user.first_name)

    document = update.message.document
    if document.mime_type != "application/x-bittorrent" and not document.file_name.lower().endswith(".torrent"):
        logger.info('invalid document from %s (mime type: %s; file name: %s)', update.effective_user.full_name,
                    document.mime_type, document.file_name)

        update.message.reply_markdown(
            'Please send me a valid torrent file (`.torrent` extension or `application/x-bittorrent` mime type)',
            quote=True
        )
        return

    file_id = document.file_id
    torrent_file = context.bot.get_file(file_id)

    file_path = './downloads/{}'.format(document.file_name)
    torrent_file.download(file_path)

    kwargs = get_qbt_request_kwargs()

    with open(file_path, 'rb') as f:
        # https://stackoverflow.com/a/46270711
        decoded_dict = bencoding.bdecode(f.read())
        torrent_hash = hashlib.sha1(bencoding.bencode(decoded_dict[b"info"])).hexdigest()

        f.seek(0)

        # this method always returns an empty json:
        # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_file
        qb.download_from_file(f, **kwargs)

    update.message.reply_text(
        'Torrent added',
        quote=True,
        reply_markup=kb.short_markup(torrent_hash)
    )

    os.remove(file_path)

    notify_addition(update.effective_chat.id, context.bot, update.effective_user, document.file_name or "[unknown file name]")


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_url(update: Update, context: CallbackContext):
    logger.info('url from %s', update.effective_user.first_name)

    torrent_url = update.message.text

    kwargs = get_qbt_request_kwargs()

    qb.download_from_link(torrent_url, **kwargs)
    # always returns an empty json:
    # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_link

    update.message.reply_text('Torrent url added', quote=True)

    notify_addition(update.effective_chat.id, context.bot, update.effective_user, torrent_url)


updater.add_handler(MessageHandler(Filters.document, add_from_file))
updater.add_handler(MessageHandler(Filters.text & Filters.regex(r'^magnet:\?.*'), add_from_magnet))
updater.add_handler(MessageHandler(Filters.text & Filters.regex(r"^https?:\/\/.*(jackett|\.torren|\/torrent).*"), add_from_url))

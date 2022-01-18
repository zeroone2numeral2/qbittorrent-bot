import logging

# noinspection PyPackageRequirements
import re

from telegram import Update, BotCommand
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, Filters

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def on_add_or_remove_tags_command(update: Update, context: CallbackContext):
    logger.info('+tags from %s', update.message.from_user.first_name)

    replied_to_text = update.message.reply_to_message.text
    hash_match = re.search(r"infohash:(\w+)", replied_to_text)
    if not hash_match:
        update.message.reply_text("Reply to a torrent's info message (it must contain the torrent hash)")
        return

    torrent_hash = hash_match.group(1)
    torrent = qb.torrent(torrent_hash)

    action = context.matches[0].group(1)
    tags_list_str = context.matches[0].group(2)
    tags_list = [tag.strip() for tag in tags_list_str.split(",")]

    if action == "+":
        text = f"Tags added to <b>{torrent.name_escaped}</b>: <code>{tags_list_str}</code> " \
               f"[<a href=\"{torrent.info_deeplink}\">info</a>]"
        torrent.add_tags(tags_list)
    else:
        text = f"Tags removed from <b>{torrent.name_escaped}</b>: <code>{tags_list_str}</code> " \
               f"[<a href=\"{torrent.info_deeplink}\">info</a>]"
        torrent.remove_tags(tags_list)

    update.message.reply_html(text)


updater.add_handler(MessageHandler(Filters.regex(r"^(\+|\-)(.+)") & Filters.reply, on_add_or_remove_tags_command))

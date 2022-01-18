import logging
import re

# noinspection PyPackageRequirements
from telegram.ext import CallbackQueryHandler, CallbackContext, MessageHandler, Filters, CommandHandler
# noinspection PyPackageRequirements
from telegram import ParseMode, Update, BotCommand

from qbt.custom import TORRENTS_CATEGORIES
from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


TORRENT_STRING_COMPACT = """• <code>{short_name_escaped}</code> ({progress_pretty}% of {size_pretty}, {state_pretty}, <b>{generic_speed_pretty}/s</b>) \
[<a href="{info_deeplink}">info</a>]"""

TORRENT_STRING_COMPLETED = '• <code>{name_escaped}</code> ({size_pretty})'

TORRENT_CATEG_REGEX_PATTERN = r'^\/({})$'.format(r'|'.join(TORRENTS_CATEGORIES))
TORRENT_CATEG_REGEX = re.compile(TORRENT_CATEG_REGEX_PATTERN, re.I)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_torrents_list_selection(update: Update, context: CallbackContext):
    logger.info('torrents list menu button from %s: %s', update.message.from_user.first_name, context.match[0])

    qbfilter = context.match[0].replace("/", "")
    logger.info('torrents status: %s', qbfilter)

    update.message.reply_html(f"Listing torrents with status <code>{qbfilter}</code> (migth take some seconds):")

    torrents = qb.torrents(filter=qbfilter, sort='dlspeed', reverse=False, get_torrent_generic_properties=False) or []
    logger.info('qbittirrent request returned %d torrents', len(torrents))

    if not torrents:
        update.message.reply_html('There is no torrent to be listed for <i>{}</i>'.format(qbfilter))
        return

    if qbfilter == 'completed':
        base_string = TORRENT_STRING_COMPLETED  # use a shorter string with less info for completed torrents
    else:
        base_string = TORRENT_STRING_COMPACT

    strings_list = [base_string.format(**torrent.dict()) for torrent in torrents]

    for strings_chunk in u.split_text(strings_list):
        update.message.reply_html('\n'.join(strings_chunk))


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_available_filters_command(update: Update, context: CallbackContext):
    logger.info('/available_filters from %s')

    update.message.reply_text("\n".join([f"/{c}" for c in TORRENTS_CATEGORIES]))


updater.add_handler(
    MessageHandler(Filters.regex(TORRENT_CATEG_REGEX), on_torrents_list_selection),
    bot_command=[BotCommand(c, f"filter only {c} torrents") for c in TORRENTS_CATEGORIES],
)
updater.add_handler(
    CommandHandler(["available_filters", "af"], on_available_filters_command),
    bot_command=[BotCommand("available_filters", "show commands to filter the torrents list by status")],
)

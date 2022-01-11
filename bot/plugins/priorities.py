import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext
# noinspection PyPackageRequirements
from telegram import ParseMode, Update, BotCommand

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)

TORRENT_STRING = '{t.priority}. <code>{t.name}</code> (<b>{t.state_pretty}</b>, [<a href="{t.info_deeplink}">manage</a>])'


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_priorities_command(update: Update, context: CallbackContext):
    logger.info('/priorities from %s', update.effective_user.first_name)

    torrents = qb.torrents(sort='priority', reverse=False, get_properties=False)

    # filter out paused completed torrents
    non_completed_torrents = list()
    for torrent in torrents:
        if torrent.state in ('pausedUP',):
            continue

        non_completed_torrents.append(torrent)
        if len(non_completed_torrents) == 25:
            # list must contain 25 torrents max
            break

    lines = [TORRENT_STRING.format(t=t) for t in non_completed_torrents]

    for strings_chunk in u.split_text(lines):
        update.message.reply_html('\n'.join(strings_chunk))


updater.add_handler(CommandHandler(['priorities'], on_priorities_command), bot_command=BotCommand("priorities", "see the torrents list sorted by priority"))

import logging

# noinspection PyPackageRequirements
from telegram import Update, BotCommand
from telegram.ext import CommandHandler, CallbackContext

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def on_remove_dead_trackers_command(update: Update, context: CallbackContext):
    logger.info('remove dead trackers from %s', update.message.from_user.first_name)

    torrents = qb.torrents(filter='all', get_torrent_generic_properties=False)

    removed_trackers = 0
    affected_torrents = 0
    for torrent in torrents:
        trackers = torrent.trackers()

        urls_to_remove = []
        for tracker in trackers:
            if tracker["status"] != 4:
                # status 4: "Tracker has been contacted, but it is not working (or doesn't send proper replies)"
                continue

            urls_to_remove.append(tracker["url"])

        if urls_to_remove:
            torrent.remove_trackers(urls_to_remove)
            removed_trackers += len(urls_to_remove)
            affected_torrents += 1

    update.message.reply_text(f"Removed {removed_trackers} trackers from {affected_torrents} torrents")


# updater.add_handler(CommandHandler(['removedeadtrackers', 'rdt'], on_remove_dead_trackers_command), bot_command=BotCommand("removedeadtrackers", "remove dead trackers from all torrents"))

import logging
import json
import os
from collections import defaultdict

# noinspection PyPackageRequirements
from telegram import Update, BotCommand
from telegram.ext import CommandHandler, CallbackContext

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def on_json_command(update: Update, context: CallbackContext):
    logger.info('/json command from %s', update.message.from_user.first_name)

    torrents = qb.torrents(filter='all', get_torrent_generic_properties=True)

    logger.info('qbittirrent request returned %d torrents', len(torrents))

    if not torrents:
        update.message.reply_html('There is no torrent')
        return

    update.message.reply_text("Sending file, it might take a while...")

    result_dict = defaultdict(list)
    for torrent in torrents:
        torrent_dict = torrent.dict()
        torrent_dict["_trackers"] = torrent.trackers()
        result_dict[torrent.state].append(torrent_dict)

    file_path = os.path.join('downloads', f'{update.message.message_id}.json')

    with open(file_path, 'w+') as f:
        json.dump(result_dict, f, indent=2)

    update.message.reply_document(open(file_path, 'rb'), caption='#torrents_list', timeout=60 * 10)

    os.remove(file_path)


updater.add_handler(CommandHandler('json', on_json_command), bot_command=BotCommand("json", "backup the torrents list"))

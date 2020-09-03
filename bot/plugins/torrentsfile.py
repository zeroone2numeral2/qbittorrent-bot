import logging
import json
import os
from collections import defaultdict

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_json_command(_, update):
    logger.info('/json command from %s', update.message.from_user.first_name)

    torrents = qb.torrents(filter='all')

    logger.info('qbittirrent request returned %d torrents', len(torrents))

    if not torrents:
        update.message.reply_html('There is no torrent')
        return

    result_dict = defaultdict(list)
    for torrent in torrents:
        result_dict[torrent.state].append(torrent.dict())

    file_path = os.path.join('downloads', '{}.json'.format(update.message.message_id))

    with open(file_path, 'w+') as f:
        json.dump(result_dict, f, indent=4)

    update.message.reply_document(open(file_path, 'rb'), caption='#torrents_list', timeout=60 * 10)

    os.remove(file_path)


updater.add_handler(CommandHandler('json', on_json_command))

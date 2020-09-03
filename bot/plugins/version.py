import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_version_command(_, update):
    logger.info('/version from %s', update.message.from_user.first_name)

    text = 'qBittorrent version: <code>{}</code>\nAPI version: <code>{}</code>'.format(
        qb.qbittorrent_version,
        qb.api_version
    )

    update.message.reply_html(text)


updater.add_handler(CommandHandler('version', on_version_command))

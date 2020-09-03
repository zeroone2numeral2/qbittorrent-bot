import logging
from pprint import pformat

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler

from bot.updater import updater
from utils import u
from utils import Permissions
from config import config

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def on_config_command(_, update):
    logger.info('/config from %s', update.effective_user.first_name)

    update.message.reply_html('<code>{}</code>'.format(pformat(config.qbittorrent)))


updater.add_handler(CommandHandler('config', on_config_command))

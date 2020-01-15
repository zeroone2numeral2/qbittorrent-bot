import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler

from bot import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def send_log_file(_, update):
    logger.info('/getlog from %s', update.effective_user.first_name)

    with open('logs/qbtbot.log', 'rb') as f:
        update.message.reply_document(f, timeout=600)


updater.add_handler(CommandHandler(['getlog', 'log'], send_log_file))

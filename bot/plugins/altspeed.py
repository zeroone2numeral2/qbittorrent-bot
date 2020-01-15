import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler

from bot import qb
from bot import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def change_alternative_limits(_, update, args):
    logger.info('/altdown or /altup from %s', update.message.from_user.first_name)

    preferences_to_edit = dict()

    preference_key = 'alt_dl_limit'
    if update.message.text.lower().startswith('/altup'):
        preference_key = 'alt_up_limit'

    kbs: str = args[0]
    if not kbs.isdigit():
        update.message.reply_text('Please pass the alternative speed limit in kb/s, as an integer')
        return

    preferences_to_edit[preference_key] = int(kbs)
    qb.set_preferences(**preferences_to_edit)

    update.message.reply_markdown('`{}` set to {} kb/s'.format(preference_key, kbs))


updater.add_handler(CommandHandler(['altdown', 'altup'], change_alternative_limits, pass_args=True))

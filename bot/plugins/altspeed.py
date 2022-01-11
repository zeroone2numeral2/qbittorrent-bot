import logging
import re

# noinspection PyPackageRequirements
from telegram import Update, BotCommand
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions
from utils import kb

logger = logging.getLogger(__name__)

PRESETS = [10, 50, 100, 200]


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def change_alternative_limits(update: Update, context: CallbackContext):
    logger.info('/altdown or /altup from %s', update.message.from_user.first_name)

    if re.search(r'^[!/]altdown$', update.message.text, re.I):
        logger.info('/altdown: showing alternative download speed limits presets')

        reply_markup = kb.alternative_download_limits(PRESETS)
        update.message.reply_markdown('Select the alternative download speed', reply_markup=reply_markup)

        return

    if not context.args:
        update.message.reply_text("Speed must be provided after the command (in kb/s)")
        return

    preferences_to_edit = dict()

    preference_key = 'alt_dl_limit'
    if update.message.text.lower().startswith('/altup'):
        preference_key = 'alt_up_limit'

    kbs: str = context.args[0]
    if not kbs.isdigit():
        update.message.reply_text('Please pass the alternative speed limit in kb/s, as an integer')
        return

    preferences_to_edit[preference_key] = int(kbs) * 1014
    qb.set_preferences(**preferences_to_edit)

    update.message.reply_markdown('`{}` set to {} kb/s'.format(preference_key, kbs))


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def alt_speed_callback(update: Update, context: CallbackContext):
    logger.info('alternative speed inline button')

    speed_up_kbs = int(context.match[1]) * 1024
    speed_down_kbs = int(context.match[2]) * 1024

    preferences_to_edit = dict(
        alt_up_limit=speed_up_kbs,
        alt_dl_limit=speed_down_kbs
    )

    qb.set_preferences(**preferences_to_edit)

    update.callback_query.answer(
        f'Alternative speed set to:\n▲ {context.match[1]} kb/s\n▼ {context.match[2]} kb/s',
        show_alert=True
    )


updater.add_handler(CommandHandler(['altdown', 'altup'], change_alternative_limits), bot_command=[
    BotCommand("altdown", "set the alternative download speed"),
    BotCommand("altup", "set the alternative upload speed"),
])
updater.add_handler(CallbackQueryHandler(alt_speed_callback, pattern=r'^altspeed:(\d+):(\d+)$'))

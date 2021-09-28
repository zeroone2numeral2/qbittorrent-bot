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


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def on_settings_command(update: Update, context: CallbackContext):
    logger.info('/settings from %s', update.effective_user.first_name)

    preferences = qb.preferences()
    lines = sorted(['{}: <code>{}</code>'.format(k, v) for k, v in preferences.items()])

    for strings_chunk in u.split_text(lines):
        update.message.reply_html('\n'.join(strings_chunk))


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def change_setting(update: Update, context: CallbackContext):
    logger.info('/set from %s', update.effective_user.first_name)

    if len(context.args) < 2:
        update.message.reply_html('Usage: /set <code>[setting] [value]</code>')
        return

    key = context.args[0].lower()
    val = context.args[1]

    qb.set_preferences(**{key: val})

    update.message.reply_html('<b>Setting changed</b>:\n\n<code>{}</code>'.format(val))


updater.add_handler(CommandHandler(['settings', 's'], on_settings_command), bot_command=BotCommand("settings", "see qbittorrent's settings list"))
updater.add_handler(CommandHandler(['set'], change_setting), bot_command=BotCommand("set", "change a qbittorrent setting"))

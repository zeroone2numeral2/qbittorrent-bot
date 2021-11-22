import logging

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
def on_freespace_command(update: Update, context: CallbackContext):
    logger.info('/space from %s', update.message.from_user.first_name)

    drive_free_space = u.free_space(qb.save_path)
    text = f"<code>{drive_free_space}</code> free, save path: <code>{qb.save_path}</code>"

    update.message.reply_html(text)


updater.add_handler(CommandHandler(["space", "freespace"], on_freespace_command), bot_command=BotCommand("freespace", "free space from download path"))

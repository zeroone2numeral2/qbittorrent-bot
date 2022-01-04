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
def on_resume_all_command(update: Update, context: CallbackContext):
    logger.info('resume all command from %s', update.message.from_user.first_name)

    qb.resume_all()

    update.message.reply_text('Resumed all torrents')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def on_pause_all_command(update: Update, context: CallbackContext):
    logger.info('pause all command from %s', update.message.from_user.first_name)

    qb.pause_all()

    update.message.reply_text('Paused all torrents')


updater.add_handler(CommandHandler(['resumeall'], on_resume_all_command), bot_command=BotCommand("resumeall", "resume all torrents"))
updater.add_handler(CommandHandler(['pauseall'], on_pause_all_command), bot_command=BotCommand("pauseall", "pause all torrents"))

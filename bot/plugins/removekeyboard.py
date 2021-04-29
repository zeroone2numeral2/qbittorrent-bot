import logging

# noinspection PyPackageRequirements
from telegram import Update, BotCommand
from telegram.ext import CommandHandler, CallbackContext

from bot.updater import updater
from utils import u
from utils import kb

logger = logging.getLogger(__name__)


@u.failwithmessage
def remove_keyboard(update: Update, context: CallbackContext):
    logger.info('/rmkb from %s', update.effective_user.first_name)

    update.message.reply_text('Keyboard removed', reply_markup=kb.REMOVE)


updater.add_handler(CommandHandler(['rmkb'], remove_keyboard), bot_command=BotCommand("rmkb", "force-remove the virtual keyboard"))

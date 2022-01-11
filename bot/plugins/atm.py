import logging

# noinspection PyPackageRequirements
from telegram import Update, BotCommand
from telegram.ext import CommandHandler, CallbackContext

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_atm_command(update: Update, context: CallbackContext):
    logger.info('/atm command used by %s', update.effective_user.first_name)

    preferences = qb.preferences()
    text = "Auto Torrent Management enabled by default: {auto_tmm_enabled}\n\n" \
           "- relocate torrents if their category changes: {torrent_changed_tmm_enabled}\n" \
           "- relocate affected torrents when default save path changes: {save_path_changed_tmm_enabled}\n" \
           "- relocate affected torrents when their " \
           "category's save path changes: {category_changed_tmm_enabled}".format(**preferences)

    update.message.reply_html(text)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_atm_list_command(update: Update, context: CallbackContext):
    logger.info('/atmyes or /atmno command used by %s', update.effective_user.first_name)

    torrents = qb.torrents()

    atm_enabled = update.message.text.lower().endswith("atmyes")

    base_string = "• <code>{short_name}</code> ({size_pretty}, {state_pretty}) [<a href=\"{info_deeplink}\">info</a>]"
    strings_list = [torrent.string(base_string=base_string) for torrent in torrents if torrent['auto_tmm'] is atm_enabled]

    update.message.reply_html(
        f"There are <b>{len(strings_list)}/{len(torrents)}</b> torrents with "
        f"Automatic Torrent Management {'enabled' if atm_enabled else 'disabled'}:"
    )

    if not strings_list:
        update.message.reply_text("-")
        return

    for strings_chunk in u.split_text(strings_list):
        update.message.reply_html('\n'.join(strings_chunk))


updater.add_handler(CommandHandler(['atm'], on_atm_command), bot_command=BotCommand("atm", "info about auto torrent management"))
updater.add_handler(CommandHandler(['atmyes'], on_atm_list_command), bot_command=BotCommand("atmyes", "list torrents which have ATM enabled"))
updater.add_handler(CommandHandler(['atmno'], on_atm_list_command), bot_command=BotCommand("atmno", "list torrents which have ATM disabled"))

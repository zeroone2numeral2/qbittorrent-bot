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
def on_filter_command(update: Update, context: CallbackContext):
    logger.info('/filter command used by %s (query: %s)', update.effective_user.first_name, context.args)

    if not context.args[0:]:
        update.message.reply_text('Please provide a search term')
        return

    query = ' '.join(context.args[0:])

    torrents = qb.filter(query)

    if not torrents:
        update.message.reply_text('No results for "{}"'.format(query))
        return

    base_string = "• <code>{short_name_escaped}</code> ({progress_pretty}% of {size_pretty}, {share_ratio_rounded}, {state_pretty}) [<a href=\"{info_deeplink}\">info</a>]"
    strings_list = [torrent.string(base_string=base_string) for torrent in torrents]

    for strings_chunk in u.split_text(strings_list):
        update.message.reply_html('\n'.join(strings_chunk))


updater.add_handler(CommandHandler(['filter', 'f'], on_filter_command), bot_command=BotCommand("filter", "filter torrents by substring"))

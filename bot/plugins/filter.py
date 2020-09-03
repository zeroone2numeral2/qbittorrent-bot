import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import Permissions

logger = logging.getLogger(__name__)

@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_filter_command(_, update, args):
    logger.info('/filter command used by %s (query: %s)', update.effective_user.first_name, args)

    if not args[0:]:
        update.message.reply_text('Please provide a search term')
        return

    query = ' '.join(args[0:])

    torrents = qb.filter(query)

    if not torrents:
        update.message.reply_text('No results for "{}"'.format(query))
        return

    strings_list = [torrent.string() for torrent in torrents]

    for strings_chunk in u.split_text(strings_list):
        update.message.reply_html('\n'.join(strings_chunk), disable_web_page_preview=True)


updater.add_handler(CommandHandler(['filter', 'f'], on_filter_command, pass_args=True))

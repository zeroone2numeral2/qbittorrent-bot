import logging
import re

# noinspection PyPackageRequirements
from telegram.ext import RegexHandler, CallbackQueryHandler
# noinspection PyPackageRequirements
from telegram import ParseMode
from telegram.error import BadRequest

from bot import qb
from bot import updater
from utils import u
from utils import kb
from utils import Permissions

logger = logging.getLogger(__name__)


TORRENT_STRING_COMPACT = """• <code>{short_name}</code> ({progress_pretty}% of {size_pretty}, {state_pretty}, <b>{dl_speed_pretty}/s</b>) \
[<a href="{info_deeplink}">info</a>]"""

TORRENT_STRING_COMPLETED = '• <code>{name}</code> ({size_pretty})'

TORRENTS_CATEGORIES = [r'\/?all', r'\/?completed', r'\/?downloading', r'\/?paused', r'\/?inactive', r'\/?active', r'\/?tostart']

TORRENT_CATEG_REGEX_PATTERN = r'^({})'.format('|'.join(TORRENTS_CATEGORIES))
TORRENT_CATEG_REGEX = re.compile(TORRENT_CATEG_REGEX_PATTERN, re.I)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_torrents_list_selection(_, update, groups):
    logger.info('torrents list menu button from %s: %s', update.message.from_user.first_name, groups[0])

    qbfilter = groups[0]
    if qbfilter.startswith('/'):
        # remove the "/" if the category has been used as command
        qbfilter = qbfilter.replace('/', '')

    logger.info('torrents status: %s', qbfilter)

    torrents = qb.torrents(filter=qbfilter, sort='dlspeed', reverse=False) or []
    if qbfilter == 'tostart':
        all_torrents = qb.torrents(filter='all')
        completed_torrents = [t.hash for t in qb.torrents(filter='completed')]
        active_torrents = [t.hash for t in qb.torrents(filter='active')]

        torrents = [t for t in all_torrents if t.hash not in completed_torrents and t.hash not in active_torrents]

    logger.info('qbittirrent request returned %d torrents', len(torrents))

    if not torrents:
        update.message.reply_html('There is no torrent to be listed for <i>{}</i>'.format(qbfilter))
        return

    if qbfilter == 'completed':
        base_string = TORRENT_STRING_COMPLETED  # use a shorter string with less info for completed torrents
    else:
        base_string = TORRENT_STRING_COMPACT

    markup = None
    if qbfilter == 'active':
        markup = kb.REFRESH_ACTIVE

    strings_list = [base_string.format(**torrent.dict()) for torrent in torrents]

    for strings_chunk in u.split_text(strings_list):
        update.message.reply_html('\n'.join(strings_chunk), disable_web_page_preview=True, reply_markup=markup)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def refresh_active_torrents(_, update):
    logger.info('refresh active torrents inline button used by %s', update.effective_user.first_name)

    torrents = qb.torrents(filter='active', sort='dlspeed', reverse=False) or []

    if not torrents:
        update.callback_query.answer('Cannot refresh: no torrents')
        return

    strings_list = [TORRENT_STRING_COMPACT.format(**torrent.dict()) for torrent in torrents]

    # we assume the list doesn't require more than one message
    try:
        update.callback_query.edit_message_text(
            '\n'.join(strings_list),
            reply_markup=kb.REFRESH_ACTIVE,
            parse_mode=ParseMode.HTML
        )
    except BadRequest as br:
        logger.error('Telegram error when refreshing the active torrents list: %s', br.message)
        update.callback_query.answer('Error: {}'.format(br.message))
        return

    update.callback_query.answer('Refreshed')


updater.add_handler(RegexHandler(TORRENT_CATEG_REGEX, on_torrents_list_selection, pass_groups=True))
updater.add_handler(CallbackQueryHandler(refresh_active_torrents, pattern=r'^refreshactive$'))

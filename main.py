import logging
import logging.config
import re
import os
import json
from collections import defaultdict
from pprint import pformat
from pprint import pprint

import requests
# noinspection PyPackageRequirements
from telegram import ParseMode
# noinspection PyPackageRequirements
from telegram.constants import MAX_MESSAGE_LENGTH
# noinspection PyPackageRequirements
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
    RegexHandler,
    Updater
)
# noinspection PyPackageRequirements
from telegram.error import BadRequest

from qbt import CustomClient
from qbt import OfflineClient
from config import config
from utils import kb
from utils import u
from utils import Permissions
from utils import permissions


def load_logging_config(file_path, logfile):
    with open(file_path, 'r') as f:
        logging_config = json.load(f)
    logging_config['handlers']['file']['filename'] = logfile
    logging.config.dictConfig(logging_config)


logger = logging.getLogger(__name__)
load_logging_config(config.logging.config, config.logging.path)

updater = Updater(token=config.telegram.token, workers=config.telegram.get('workers', 1))
dispatcher = updater.dispatcher

try:
    qb = CustomClient(config.qbittorrent.url, bot_username=updater.bot.username)
    qb.login(config.qbittorrent.login, config.qbittorrent.secret)
except requests.exceptions.ConnectionError as e:
    logger.error('exception while connecting to qbittorrent: %s', str(e))
    qb = OfflineClient()

HELP_MESSAGE = """<b>Commands</b>:

<i>READ commands</i>
• /start or /help: show this message
• /completed, /active, /paused, /downloading, /inactive, /all: show the torrents list by status
• /tostart: show torrents that are not active or completed
• /filter or /f <code>[substring]</code>: filter by substring (filters from the full list)
• /settings or /s: get current settings list
• /json: get a json file containing a list of all the torrents

<i>WRITE commands</i>
• <code>.torrent</code> document: add torrent by file
• magnet url: add a torrent by magnet url

<i>EDIT commands</i>
• /alton or /slow: enable alternative speed limits
• /altoff or /fast: disable alterative speed limits
• /altdown <code>[kb/s]</code>: change the alternative max download speed
• /altup <code>[kb/s]</code>: change the alternative max upload speed
• /pauseall: pause all torrents
• /resumeall: resume all torrents
• /set <code>[setting] [new value]</code>: change a setting

<i>ADMIN commands</i>
• /getlog or /log: get the log file
• /permissions: get the current permissions configuration
• /pset <code>[key] [val]</code>: change the value of a permission key
• /config: get the qbittorrent's section of the config file

<i>FREE commands</i>
• /rmkb: remove the keyboard, if any"""

TORRENTS_CATEGORIES = [r'\/?all', r'\/?completed', r'\/?downloading', r'\/?paused', r'\/?inactive', r'\/?active', r'\/?tostart']
TORRENT_CATEG_REGEX_PATTERN = r'^({})'.format('|'.join(TORRENTS_CATEGORIES))
TORRENT_CATEG_REGEX = re.compile(TORRENT_CATEG_REGEX_PATTERN, re.I)

TORRENT_STRING_FILTERED = """• <code>{name}</code>
  {progress_bar} {progress}%
  <b>state</b>: {state}
  <b>size</b>: {size}
  <b>dl/up speed</b>: {dlspeed}/s, {upspeed}/s
  <b>leechs/seeds</b> {num_leechs}/{num_seeds}
  <b>eta</b>: {eta}
  <b>priority</b>: {priority}
  <b>force start</b>: {force_start}
  [<a href="{info_deeplink}">info</a>]"""

TORRENT_STRING_COMPACT = """• <code>{name}</code> ({progress}% of {size}, {state}, <b>{dlspeed}/s</b>) \
[<a href="{info_deeplink}">info</a>]"""

TORRENT_STRING_COMPLETED = '• <code>{name}</code> ({size})'

ALTERNATIVE_SPEED_ALREADY_ENABLED = """We are already using the alternative speed limits \
(down: {alt_dl_limit} kb/s, up: {alt_up_limit} kb/s)"""

ALTERNATIVE_SPEED_ENABLED = """Alternative speed limits enabled \
(down: {alt_dl_limit} kb/s, up: {alt_up_limit} kb/s)"""

ALTERNATIVE_SPEED_ALREADY_DISABLED = """Alternative speed limits are already disabled \
(normal limits: {dl_limit} down, {up_limit} up)"""

ALTERNATIVE_SPEED_DISABLED = """Alternative speed limits disabled \
(normal limits: {dl_limit} down, {up_limit} up)"""

PREF_FROMATTING = {
    # 'alt_dl_limit': lambda speed: u.get_human_readable(speed),
    # 'alt_up_limit': lambda speed: u.get_human_readable(speed)
    'alt_dl_limit': lambda speed: round(speed, 2),
    'alt_up_limit': lambda speed: round(speed, 2)
}


class Completed:
    def __init__(self):
        self._data = list()

    def init(self, hashes_list):
        self._data = hashes_list

    def is_new(self, torrent_hash):
        if torrent_hash not in self._data:
            self._data.append(torrent_hash)
            return True
        else:
            return False


completed_torrents = Completed()


def split_text(strings_list):
    avg_len = sum(map(len, strings_list)) / len(strings_list)
    elements_per_msg = int(MAX_MESSAGE_LENGTH / avg_len)

    for i in range(0, len(strings_list), elements_per_msg):
        yield strings_list[i:i + elements_per_msg]


def polish_preferences(preferences):
    for pref in PREF_FROMATTING:
        preferences[pref] = PREF_FROMATTING[pref](preferences[pref])


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_info_deeplink(_, update, groups=[]):
    logger.info('info deeplink from %s', update.message.from_user.first_name)

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)

    update.message.reply_html(torrent.string(), reply_markup=torrent.short_markup())


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_help(_, update):
    logger.info('/help from %s', update.message.from_user.first_name)

    update.message.reply_html(HELP_MESSAGE)
    

@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def on_slow(_, update):
    logger.info('/slow from %s', update.message.from_user.first_name)

    preferences = qb.preferences()
    polish_preferences(preferences)

    if bool(qb.get_alternative_speed_status()):
        update.message.reply_text(ALTERNATIVE_SPEED_ALREADY_ENABLED.format(**preferences))
    else:
        qb.toggle_alternative_speed()
        update.message.reply_text(ALTERNATIVE_SPEED_ENABLED.format(**preferences))
        

@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def on_fast(_, update):
    logger.info('/fast from %s', update.message.from_user.first_name)

    preferences = qb.preferences()
    format_dict = dict(
        dl_limit='{} kb/s'.format(preferences['dl_limit']) if preferences['dl_limit'] > -1 else 'none',
        up_limit='{} kb/s'.format(preferences['up_limit']) if preferences['up_limit'] > -1 else 'none'
    )

    if not bool(qb.get_alternative_speed_status()):
        update.message.reply_text(ALTERNATIVE_SPEED_ALREADY_DISABLED.format(**format_dict))
    else:
        qb.toggle_alternative_speed()
        update.message.reply_text(ALTERNATIVE_SPEED_DISABLED.format(**format_dict))


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


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def on_resume_all_command(_, update):
    logger.info('resume all command from %s', update.message.from_user.first_name)

    qb.resume_all()

    update.message.reply_text('Resumed all torrents')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def on_pause_all_command(_, update):
    logger.info('pause all command from %s', update.message.from_user.first_name)

    qb.pause_all()

    update.message.reply_text('Paused all torrents')


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_torrents_button(_, update):
    logger.info('torrents button from %s', update.message.from_user.first_name)

    update.message.reply_text('Select a category:', reply_markup=kb.LISTS_MENU)


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

    for strings_chunk in split_text(strings_list):
        update.message.reply_html('\n'.join(strings_chunk), disable_web_page_preview=True, reply_markup=markup)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_json_command(_, update):
    logger.info('/json command from %s', update.message.from_user.first_name)

    torrents = qb.torrents(filter='all')

    logger.info('qbittirrent request returned %d torrents', len(torrents))

    if not torrents:
        update.message.reply_html('There is no torrent')
        return

    result_dict = defaultdict(list)
    for torrent in torrents:
        result_dict[torrent.state].append(torrent.dict())

    file_path = os.path.join('downloads', '{}.json'.format(update.message.message_id))

    with open(file_path, 'w+') as f:
        json.dump(result_dict, f, indent=4)

    update.message.reply_document(open(file_path, 'rb'), caption='#torrents_list', timeout=60*10)

    os.remove(file_path)


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def change_setting(_, update, args):
    logger.info('/set from %s', update.effective_user.first_name)

    if len(args) < 2:
        update.message.reply_html('Usage: /set <code>[setting] [value]</code>')
        return

    key = args[0].lower()
    val = args[1]

    qb.set_preferences(**{key: val})

    update.message.reply_html('<b>Setting changed</b>:\n\n<code>{}</code>'.format(val))


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

    strings_list = [TORRENT_STRING_FILTERED.format(**torrent.dict()) for torrent in torrents]

    for strings_chunk in split_text(strings_list):
        update.message.reply_html('\n'.join(strings_chunk), disable_web_page_preview=True)


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


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def manage_torrent_cb(_, update, groups):
    logger.info('manage torrent inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)

    update.callback_query.edit_message_text(
        torrent.string(refresh_properties=True),
        reply_markup=torrent.actions_keyboard,
        parse_mode=ParseMode.HTML
    )
    update.callback_query.answer('Use the keyboard to manage the torrent')


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def see_trackers_cb(_, update, groups):
    logger.info('trackers inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    trackers = torrent.trackers()

    strings_list = ['<b>{status}:</b> {url} <b>({num_peers})</b>'.format(**{k: u.html_escape(str(v)) for k, v in tracker.items()}) for tracker in trackers]
    text = '\n'.join(strings_list)

    if len(text) > MAX_MESSAGE_LENGTH:
        trackers_info = dict()
        for tracker in trackers:
            if not trackers_info.get(tracker['status'], None):
                trackers_info[tracker['status']] = dict(count=0, num_peers=0)

            trackers_info[tracker['status']]['count'] += 1
            trackers_info[tracker['status']]['num_peers'] += tracker['num_peers']

        lines_list = list()
        for status, status_counts in trackers_info.items():
            lines_list.append('<b>{}</b>: {} trackers, {} peers'.format(status, status_counts['count'], status_counts['num_peers']))

        text = '\n'.join(lines_list)

    update.callback_query.edit_message_text(
        text or 'No trackers',
        reply_markup=torrent.actions_keyboard,
        parse_mode=ParseMode.HTML,
        disable_web_page_preview=True
    )
    update.callback_query.answer('Trackers list')


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def refresh_torrent_cb(_, update, groups):
    logger.info('refresh torrent inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    
    try:
        update.callback_query.edit_message_text(
            torrent.string(),
            reply_markup=torrent.actions_keyboard,
            parse_mode=ParseMode.HTML
        )
    except BadRequest as e:
        logger.info('bad request: %s', e.message)
    
    update.callback_query.answer('Torrent info refreshed')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def pause_torrent_cb(_, update, groups):
    logger.info('pause torrent inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.pause()

    update.callback_query.answer('Paused')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def resume_torrent_cb(_, update, groups):
    logger.info('resume torrent inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.resume()

    update.callback_query.answer('Resumed')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def force_resume_torrent_cb(_, update, groups):
    logger.info('force-resume torrent inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.toggle_force_start(True)
    torrent.resume()

    update.callback_query.answer('Force-resumed')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def force_start_torrent_cb(_, update, groups):
    logger.info('force start torrent inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.toggle_force_start(True)

    update.callback_query.answer('Force-start set to "true"')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def unforce_start_torrent_cb(_, update, groups):
    logger.info('unforce start torrent inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.toggle_force_start(False)

    update.callback_query.answer('Force-start set to "false"')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def priority_up_cb(_, update, groups):
    logger.info('priority up inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.increase_priority()

    update.callback_query.answer('Increased priority')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def max_priority_cb(_, update, groups):
    logger.info('max priority inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.max_priority()

    update.callback_query.answer('Max priority set')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def recheck_cb(_, update, groups):
    logger.info('recheck inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.recheck()

    update.callback_query.answer('Re-check started')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def ask_confirm_delete_with_files_cb(_, update, groups):
    logger.info('delete with files inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    # torrent.delete(with_files=True)

    update.callback_query.edit_message_text(
        'Are you sure you want to delete {}, <b>with all the connected files included</b>?'.format(u.html_escape(torrent.name)),
        reply_markup=kb.confirm_delete(torrent.hash),
        parse_mode=ParseMode.HTML
    )
    update.callback_query.answer('Confirmation needed')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
def confirm_delete_with_files_cb(_, update, groups):
    logger.info('confirmation delete with files inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)
    torrent.delete(with_files=True)

    update.callback_query.edit_message_text('{} deleted (with files)'.format(torrent.name))


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def reduce_buttons(_, update, groups):
    logger.info('remove buttons inline button')

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)

    update.callback_query.edit_message_text(
        torrent.string(refresh_properties=True),
        reply_markup=torrent.short_markup(),
        parse_mode=ParseMode.HTML
    )
    update.callback_query.answer('Inline keyboard reduced')


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_magnet(_, update):
    logger.info('magnet url from %s', update.effective_user.first_name)

    magnet_link = update.message.text
    qb.download_from_link(magnet_link)
    # always returns an empty json:
    # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_link

    torrent_hash = re.search(r'magnet:\?xt=urn:btih:([a-z0-9]+)(?:&.*)?', magnet_link, re.I).group(1)
    logger.info('torrent hash from regex: %s', torrent_hash)

    update.message.reply_html(
        'Magnet added',
        reply_markup=kb.short_markup(torrent_hash, force_resume_button=False),
        quote=True
    )


@u.check_permissions(required_permission=Permissions.WRITE)
@u.failwithmessage
def add_from_file(bot, update):
    logger.info('document from %s', update.effective_user.first_name)

    if update.message.document.mime_type != 'application/x-bittorrent':
        update.message.reply_markdown('Please send me a `.torrent` file')
        return

    file_id = update.message.document.file_id
    torrent_file = bot.get_file(file_id)

    file_path = './downloads/{}'.format(update.message.document.file_name)
    torrent_file.download(file_path)

    with open(file_path, 'rb') as f:
        # this method always returns an empty json:
        # https://python-qbittorrent.readthedocs.io/en/latest/modules/api.html#qbittorrent.client.Client.download_from_file
        qb.download_from_file(f)

    os.remove(file_path)
    update.message.reply_text('Torrent added', quote=True)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_settings_command(_, update):
    logger.info('/settings from %s', update.effective_user.first_name)

    preferences = qb.preferences()
    lines = sorted(['{}: <code>{}</code>'.format(k, v) for k, v in preferences.items()])

    for strings_chunk in split_text(lines):
        update.message.reply_html('\n'.join(strings_chunk), disable_web_page_preview=True)


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def send_log_file(_, update):
    logger.info('/getlog from %s', update.effective_user.first_name)

    with open(config.logging.path, 'rb') as f:
        update.message.reply_document(f, timeout=600)


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def get_permissions(_, update):
    logger.info('/permissions from %s', update.effective_user.first_name)

    update.message.reply_html('<code>{}</code>'.format(str(permissions)))


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def set_permission(_, update, args):
    logger.info('/pset from %s', update.effective_user.first_name)

    if len(args) < 2:
        update.message.reply_html('Usage: /pset <code>[permission key] [true/false/1/0]</code>')
        return

    key = args[0].lower()
    val = args[1].lower()
    if val.lower() not in ('true', 'false', '0', '1'):
        update.message.reply_html('Wrong value passed. Usage: /pset <code>[permission key] [true/false/1/0]</code>')
        return

    if permissions.get(key, None) is None:
        update.message.reply_text('Wrong key. Use /permissions to see the current permissions config')
        return

    actual_val = True if val in ('true', '1') else False
    permissions.set(key, actual_val)

    update.message.reply_html('<b>New config</b>:\n\n<code>{}</code>'.format(str(permissions)))


@u.check_permissions(required_permission=Permissions.ADMIN)
@u.failwithmessage
def on_config_command(_, update):
    logger.info('/config from %s', update.effective_user.first_name)

    update.message.reply_html('<code>{}</code>'.format(pformat(config.qbittorrent)))


@u.failwithmessage
def remove_keyboard(_, update):
    logger.info('/rmkb from %s', update.effective_user.first_name)
    
    update.message.reply_text('Keyboard removed', reply_markup=kb.REMOVE)


@u.failwithmessage
def error_callback(_, update, error):
    logger.info('update %s generated error %s', update, error, exc_info=True)


@u.failwithmessage_job
def notify_completed(bot, _):
    logger.info('executing completed job')

    completed = qb.torrents(filter='completed')

    for t in completed:
        if completed_torrents.is_new(t.hash):
            torrent = qb.torrent(t.hash)
            text = '<code>{}</code> completed'.format(u.html_escape(torrent.name))
            bot.send_message(
                config.telegram.admins[0],
                text,
                reply_markup=torrent.short_markup(force_resume_button=False),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True
            )


def main():
    logger.info('registering handlers...')
    dispatcher.add_handler(RegexHandler(r'^\/start$', on_help))
    dispatcher.add_handler(RegexHandler(r'^\/start info(.*)$', on_info_deeplink, pass_groups=True))
    dispatcher.add_handler(CommandHandler('help', on_help))
    dispatcher.add_handler(CommandHandler(['settings', 's'], on_settings_command))
    dispatcher.add_handler(CommandHandler(['set'], change_setting, pass_args=True))
    dispatcher.add_handler(CommandHandler(['permissions', 'p'], get_permissions))
    dispatcher.add_handler(CommandHandler(['pset'], set_permission, pass_args=True))
    dispatcher.add_handler(CommandHandler(['filter', 'f'], on_filter_command, pass_args=True))
    dispatcher.add_handler(CommandHandler(['getlog', 'log'], send_log_file))
    dispatcher.add_handler(CommandHandler(['altoff', 'fast'], on_fast))
    dispatcher.add_handler(CommandHandler(['alton', 'slow'], on_slow))
    dispatcher.add_handler(CommandHandler(['altdown', 'altup'], change_alternative_limits, pass_args=True))
    dispatcher.add_handler(CommandHandler('json', on_json_command))
    dispatcher.add_handler(CommandHandler('config', on_config_command))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r'^magnet:\?.*'), add_from_magnet))
    dispatcher.add_handler(MessageHandler(Filters.document, add_from_file))
    dispatcher.add_handler(RegexHandler(TORRENT_CATEG_REGEX, on_torrents_list_selection, pass_groups=True))
    dispatcher.add_handler(CommandHandler(['resumeall'], on_resume_all_command))
    dispatcher.add_handler(CommandHandler(['pauseall'], on_pause_all_command))
    dispatcher.add_handler(CommandHandler(['rmkb'], remove_keyboard))

    dispatcher.add_handler(CallbackQueryHandler(manage_torrent_cb, pattern=r'^manage:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(see_trackers_cb, pattern=r'^trackers:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(refresh_torrent_cb, pattern=r'^refresh:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(pause_torrent_cb, pattern=r'^pause:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(resume_torrent_cb, pattern=r'^resume:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(force_resume_torrent_cb, pattern=r'^forceresume:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(force_start_torrent_cb, pattern=r'^forcestart:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(unforce_start_torrent_cb, pattern=r'^unforcestart:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(priority_up_cb, pattern=r'^priorityup:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(max_priority_cb, pattern=r'^maxpriority:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(recheck_cb, pattern=r'^recheck:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(ask_confirm_delete_with_files_cb, pattern=r'^deletewithfiles:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(confirm_delete_with_files_cb, pattern=r'^confirmdeletewithfiles:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(reduce_buttons, pattern=r'^reduce:(.*)$', pass_groups=True))
    dispatcher.add_handler(CallbackQueryHandler(refresh_active_torrents, pattern=r'^refreshactive$'))

    dispatcher.add_error_handler(error_callback)
    
    logger.info('registering "completed torrents" job')
    try:
        completed_torrents.init([t.hash for t in qb.torrents(filter='completed')])
        updater.job_queue.run_repeating(notify_completed, interval=120, first=120)
    except ConnectionError:
        # catch the connection error raised by the OffilneClient, in case we are offline
        logger.warning('cannot register the completed torrents job: qbittorrent is not online')

    logger.info('starting as @%s', updater.bot.username)
    updater.start_polling(clean=True)
    updater.idle()


if __name__ == '__main__':
    main()

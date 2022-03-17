from telegram import ReplyKeyboardMarkup
from telegram import ReplyKeyboardRemove
from telegram import InlineKeyboardMarkup
from telegram import InlineKeyboardButton

from config import config

SORTING_KEYS = ('name', 'size', 'progress', 'eta')

MAIN_MENU = ReplyKeyboardMarkup([['torrents'], ['speed cap'], ['pause all', 'resume all']], resize_keyboard=True)

LISTS_MENU = ReplyKeyboardMarkup(
    [
        ['all', 'completed'],
        ['downloading', 'paused'],
        ['active', 'inactive'],
        ['back']
    ],
    resize_keyboard=True
)

QUICK_MENU_BUTTON = InlineKeyboardMarkup([
    [
        InlineKeyboardButton('🐇', callback_data='quick:altoff'),
        InlineKeyboardButton('🐌', callback_data='quick:alton'),
        InlineKeyboardButton('10 🐌', callback_data='altdown:10'),  # change alternative download speed
        InlineKeyboardButton('50 🐌', callback_data='altdown:50'),  # change alternative download speed
        InlineKeyboardButton('100 🐌', callback_data='altdown:100'),  # change alternative download speed
        InlineKeyboardButton('200 🐌', callback_data='altdown:200'),  # change alternative download speed
    ],
    [
        InlineKeyboardButton('✅ 🕑', callback_data='quick:schedon'),
        InlineKeyboardButton('❌ 🕑', callback_data='quick:schedoff'),
        InlineKeyboardButton('🔄 %', callback_data='quick:refresh:percentage'),
        InlineKeyboardButton('🔄 kb/s', callback_data='quick:refresh:dlspeed'),
    ]
])

SPEEDCAP_MENU = InlineKeyboardMarkup([[InlineKeyboardButton('toggle', callback_data='togglespeedcap')]])

REFRESH_ACTIVE = InlineKeyboardMarkup([[InlineKeyboardButton('refresh', callback_data='refreshactive')]])

REFRESH_TRANSFER_INFO = InlineKeyboardMarkup([[InlineKeyboardButton('refresh', callback_data='refreshtransferinfo')]])

REMOVE = ReplyKeyboardRemove()


def get_overview_altspeed_markup():
    if config.qbittorrent.altspeed_presets:
        altspeed = config.qbittorrent.altspeed_presets
    else:
        altspeed = []

    speeds_row = []
    for up, down in altspeed:
        inline_button = InlineKeyboardButton(f'▲{up} ▼{down}', callback_data=f'altspeed:{up}:{down}')
        speeds_row.append(inline_button)

    keyboard = [speeds_row, [
        InlineKeyboardButton('ON', callback_data='overview:alton'),
        InlineKeyboardButton('OFF', callback_data='overview:altoff'),
        InlineKeyboardButton('back', callback_data='overview:refresh:dlspeed'),
    ]]

    return InlineKeyboardMarkup(keyboard)


def get_overview_schedule_markup():
    keyboard = [[
        InlineKeyboardButton('ON', callback_data='overview:schedon'),
        InlineKeyboardButton('OFF', callback_data='overview:schedoff'),
        InlineKeyboardButton('back', callback_data='overview:refresh:dlspeed')
    ]]

    return InlineKeyboardMarkup(keyboard)


def get_overview_base_markup():
    keyboard = [[
        InlineKeyboardButton('⚙️ alt speed', callback_data='overview:altspeed'),
        InlineKeyboardButton('⚙️ schedule', callback_data='overview:schedule'),
    ], [
        InlineKeyboardButton('📶 transfer info', callback_data='overview:transferinfo'),
        InlineKeyboardButton('💾 space', callback_data='overview:freespace'),
        InlineKeyboardButton('🔄 kb/s', callback_data='overview:refresh:dlspeed'),
    ]]

    return InlineKeyboardMarkup(keyboard)


def sort_markup(qbfilter, exclude_key='', row_width=2):
    markup = []
    sorting_keys_new = [e for e in SORTING_KEYS if e != exclude_key]
    for i in range(0, len(sorting_keys_new), row_width):
        row_keys = sorting_keys_new[i:i + row_width]
        row = [InlineKeyboardButton(row_key, callback_data='sort:{}:{}'.format(qbfilter, row_key)) for row_key in row_keys]
        markup.append(row)

    return InlineKeyboardMarkup(markup)


def actions_markup(torrent_hash):
    keyboard = [
        [
            InlineKeyboardButton('resume', callback_data='resume:{}'.format(torrent_hash)),
            InlineKeyboardButton('pause', callback_data='pause:{}'.format(torrent_hash)),
            InlineKeyboardButton('refresh', callback_data='refresh:{}'.format(torrent_hash)),
        ],
        [
            InlineKeyboardButton('force start', callback_data='forcestart:{}'.format(torrent_hash)),
            InlineKeyboardButton('un-force start', callback_data='unforcestart:{}'.format(torrent_hash)),
        ],
        [
            InlineKeyboardButton('atm on/off', callback_data='toggleatm:{}'.format(torrent_hash)),
            InlineKeyboardButton('see trackers', callback_data='trackers:{}'.format(torrent_hash))
        ],
        [
            InlineKeyboardButton('delete', callback_data='deletewithfiles:{}'.format(torrent_hash)),
            InlineKeyboardButton('force recheck', callback_data='recheck:{}'.format(torrent_hash)),
            InlineKeyboardButton('reduce buttons', callback_data='reduce:{}'.format(torrent_hash)),
        ]
    ]

    if config.notifications.completed_torrents and config.notifications.no_notification_tag:
        # add an option to add the "do not notify" tag to the torrent
        button = InlineKeyboardButton('do not notify', callback_data='nonotification:{}'.format(torrent_hash))
        keyboard[1].append(button)

    return InlineKeyboardMarkup(keyboard)


def confirm_delete(torrent_hash):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('no, go back', callback_data='manage:{}'.format(torrent_hash)),
        InlineKeyboardButton('yes, delete', callback_data='confirmdeletewithfiles:{}'.format(torrent_hash))
    ]])


def short_markup(torrent_hash, do_not_notify_tag_emoji=False):
    markup = [[
        InlineKeyboardButton('pause', callback_data='pause:{}'.format(torrent_hash)),
        InlineKeyboardButton('manage', callback_data='manage:{}'.format(torrent_hash)),
    ]]

    if config.notifications.completed_torrents and config.notifications.no_notification_tag:
        label = "🏷 do not notify" if do_not_notify_tag_emoji else "do not notify"
        markup[0].insert(0, InlineKeyboardButton(label, callback_data='nonotification:{}'.format(torrent_hash)))

    return InlineKeyboardMarkup(markup)


def alternative_download_limits(values: [list, tuple]):
    markup = [[]]
    for kbs in values:
        markup[0].append(InlineKeyboardButton('{} kbs'.format(kbs), callback_data='altdown:{}'.format(kbs)))

    return InlineKeyboardMarkup(markup)

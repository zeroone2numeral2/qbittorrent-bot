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


def get_quick_menu_markup():
    altspeed = [(5, 10), (5, 50), (5, 200)]  # (up, down)

    base_keyboard = [[
        InlineKeyboardButton('alt ✅', callback_data='quick:alton'),
        InlineKeyboardButton('alt ❌', callback_data='quick:altoff'),
    ], [
        InlineKeyboardButton('🕑 ✅', callback_data='quick:schedon'),
        InlineKeyboardButton('🕑 ❌', callback_data='quick:schedoff'),
    ], [
        InlineKeyboardButton('💾 free space', callback_data='quick:freespace'),
        InlineKeyboardButton('🔄 %', callback_data='quick:refresh:percentage'),
        InlineKeyboardButton('🔄 kb/s', callback_data='quick:refresh:dlspeed'),
    ]]

    if config.qbittorrent.altspeed_presets:
        altspeed = config.qbittorrent.altspeed_presets

    for up, down in altspeed:
        inline_button = InlineKeyboardButton(f'▲{up}/▼{down}', callback_data=f'altspeed:{up}:{down}')
        base_keyboard[0].append(inline_button)

    return InlineKeyboardMarkup(base_keyboard)


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
            InlineKeyboardButton('see trackers', callback_data='trackers:{}'.format(torrent_hash))
        ],
        [
            InlineKeyboardButton('priority up', callback_data='priorityup:{}'.format(torrent_hash)),
            InlineKeyboardButton('max priority', callback_data='maxpriority:{}'.format(torrent_hash)),
            InlineKeyboardButton('atm on/off', callback_data='toggleatm:{}'.format(torrent_hash)),
        ],
        [
            InlineKeyboardButton('delete', callback_data='deletewithfiles:{}'.format(torrent_hash)),
            InlineKeyboardButton('force recheck', callback_data='recheck:{}'.format(torrent_hash)),
            InlineKeyboardButton('reduce buttons', callback_data='reduce:{}'.format(torrent_hash)),
        ]
    ]

    if config.telegram.completed_torrents_notification and config.telegram.no_notification_tag:
        # add an option to add the "do not notify" tag to the torrent
        button = InlineKeyboardButton('do not notify', callback_data='nonotification:{}'.format(torrent_hash))
        keyboard[1].append(button)

    return InlineKeyboardMarkup(keyboard)


def confirm_delete(torrent_hash):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton('no, go back', callback_data='manage:{}'.format(torrent_hash)),
        InlineKeyboardButton('yes, delete', callback_data='confirmdeletewithfiles:{}'.format(torrent_hash))
    ]])


def short_markup(torrent_hash, max_priority_button=True, do_not_notify_tag_button=True):
    markup = [[
        InlineKeyboardButton('pause', callback_data='pause:{}'.format(torrent_hash)),
        InlineKeyboardButton('manage', callback_data='manage:{}'.format(torrent_hash)),
    ]]

    if max_priority_button:
        markup[0].insert(0, InlineKeyboardButton('max priority', callback_data='maxpriority:{}'.format(torrent_hash)))

    if do_not_notify_tag_button \
            and config.telegram.completed_torrents_notification \
            and config.telegram.no_notification_tag:
        markup[0].insert(0, InlineKeyboardButton('do not notify', callback_data='nonotification:{}'.format(torrent_hash)))

    return InlineKeyboardMarkup(markup)


def alternative_download_limits(values: [list, tuple]):
    markup = [[]]
    for kbs in values:
        markup[0].append(InlineKeyboardButton('{} kbs'.format(kbs), callback_data='altdown:{}'.format(kbs)))

    return InlineKeyboardMarkup(markup)

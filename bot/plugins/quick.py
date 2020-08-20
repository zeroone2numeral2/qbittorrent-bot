import datetime
import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler, CallbackQueryHandler
# noinspection PyPackageRequirements
from telegram import ParseMode, MAX_MESSAGE_LENGTH

from bot import qb
from bot import updater
from utils import u
from utils import kb
from utils import Permissions

logger = logging.getLogger(__name__)

QUICK_INFO_TEXT = """<b>Completed:</b>
{completed}

<b>Active:</b>
{active}

{schedule}
{alt_speed}
{current_speed}
<b>Last refresh:</b> {last_refresh}"""

TORRENT_STRING_COMPACT = """• <code>{short_name}</code> ({progress_pretty}% of {size_pretty}, {state_pretty}, \
<b>{generic_speed_pretty}/s</b>) [<a href="{info_deeplink}">info</a>]"""


def get_quick_info_text():
    active_torrents = qb.torrents(filter='active', sort='dlspeed', reverse=False)
    completed_trnts = qb.torrents(filter='completed')

    if not active_torrents:
        active_torrents_strings_list = ['no active torrent']
    else:
        active_torrents_with_traffic = list()
        active_torrents_without_traffic_count = 0

        for active_torrent in active_torrents:
            if active_torrent.generic_speed > 0 or active_torrent.state not in ('forcedDL', 'forcedUP'):
                # add to this list only torrents that are generating traffic OR active torrents
                # that have not been force-started
                active_torrents_with_traffic.append(active_torrent)
            else:
                active_torrents_without_traffic_count += 1

        active_torrents_strings_list = [TORRENT_STRING_COMPACT.format(**t.dict()) for t in active_torrents_with_traffic]

        if active_torrents_without_traffic_count > 0:
            no_traffic_row = 'there are other <b>{}</b> active torrents stalled'.format(active_torrents_without_traffic_count)
            active_torrents_strings_list.append(no_traffic_row)

    if completed_trnts:
        completed_torrents_strings_list = ['• {}'.format(t.short_name) for t in completed_trnts]
    else:
        completed_torrents_strings_list = ['no completed torrent']

    # shorten the message if it's too long to send
    completed_torrents_string_len = sum(map(len, completed_torrents_strings_list))
    active_torrents_string_len = sum(map(len, active_torrents_strings_list))
    if (completed_torrents_string_len + active_torrents_string_len) > MAX_MESSAGE_LENGTH:
        # we assume the longest one between the two is the completed torrents list
        completed_torrents_strings_list = ['list too long, use /completed to see completed torrents']

    schedule_info = qb.get_schedule()
    if not schedule_info:
        schedule_string = '<b>Schedule</b>: off'
    else:
        schedule_string = '<b>Schedule</b>: on, from {from_hour} to {to_hour} ({days})'.format(**schedule_info)

    alt_speed_info = qb.get_alt_speed(human_readable=True)
    alt_speed_string = '<b>Alt speed is {status}</b> (down: {alt_dl_limit}/s, up: {alt_up_limit}/s)'.format(
        **alt_speed_info
    )

    current_speed = qb.get_speed()
    current_speed_string = '<b>Current speed</b>: down: {0}/s, up: {1}/s'.format(*current_speed)

    text = QUICK_INFO_TEXT.format(
        completed='\n'.join(completed_torrents_strings_list),
        active='\n'.join(active_torrents_strings_list),
        schedule=schedule_string,
        alt_speed=alt_speed_string,
        current_speed=current_speed_string,
        last_refresh=datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    )

    return text


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_quick_info_command(_, update):
    logger.info('/quick command from %s', update.message.from_user.first_name)

    text = get_quick_info_text()
    update.message.reply_html(text, reply_markup=kb.QUICK_MENU_BUTTON)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_refresh_button_quick(bot, update):
    logger.info('quick info: refresh button')

    text = get_quick_info_text()

    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Refreshed')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_alton_button_quick(_, update):
    logger.info('quick info: alton button')

    if not bool(qb.get_alternative_speed_status()):
        qb.toggle_alternative_speed()

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Alternative speed enabled')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_altoff_button_quick(_, update):
    logger.info('quick info: altoff button')

    if bool(qb.get_alternative_speed_status()):
        qb.toggle_alternative_speed()

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Alternative speed disabled')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_schedon_button_quick(_, update):
    logger.info('quick info: schedon button')

    qb.set_preferences(**{'scheduler_enabled': True})

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Scheduled altenrative speed on')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_schedoff_button_quick(_, update):
    logger.info('quick info: schedoff button')

    qb.set_preferences(**{'scheduler_enabled': False})

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Scheduled altenrative speed off')


updater.add_handler(CommandHandler(['quick'], on_quick_info_command))
updater.add_handler(CallbackQueryHandler(on_refresh_button_quick, pattern=r'^quick:refresh$'))
updater.add_handler(CallbackQueryHandler(on_alton_button_quick, pattern=r'^quick:alton$'))
updater.add_handler(CallbackQueryHandler(on_altoff_button_quick, pattern=r'^quick:altoff$'))
updater.add_handler(CallbackQueryHandler(on_schedon_button_quick, pattern=r'^quick:schedon'))
updater.add_handler(CallbackQueryHandler(on_schedoff_button_quick, pattern=r'^quick:schedoff'))

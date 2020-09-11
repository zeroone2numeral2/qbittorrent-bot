import datetime
import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler, CallbackQueryHandler, RegexHandler
# noinspection PyPackageRequirements
from telegram import ParseMode, MAX_MESSAGE_LENGTH, Bot

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import kb
from utils import Permissions

logger = logging.getLogger(__name__)

QUICK_INFO_TEXT = """<b>Completed ({total_completed_count}):</b>
{completed}

<b>Active ({total_active_count}):</b>
{active}

{schedule}
{alt_speed}
{current_speed}
<b>Last refresh:</b> {last_refresh}"""

TORRENT_STRING_COMPACT = """• <code>{short_name}</code> ({progress_pretty}% of {size_pretty}, {state_pretty}, \
<b>{generic_speed_pretty}/s</b>) [<a href="{info_deeplink}">info</a>]"""


def get_quick_info_text(sort_active_by_dl_speed=True):
    if sort_active_by_dl_speed:
        active_torrents_sort = 'dlspeed'
    else:
        active_torrents_sort = 'progress'

    active_torrents = qb.torrents(filter='active', sort=active_torrents_sort, reverse=False)
    completed_torrents = qb.torrents(filter='completed')

    total_active_count = 0
    total_completed_count = 0

    if not active_torrents:
        active_torrents_strings_list = ['no active torrent']
    else:
        total_active_count = len(active_torrents)  # non-filtered count

        active_torrents_filtered = list()
        active_torrents_without_traffic_count = 0
        active_torrents_fetching_metadata_count = 0

        for active_torrent in active_torrents:
            if active_torrent.state in ('metaDL',):
                active_torrents_fetching_metadata_count += 1
            elif active_torrent.state in ('stalledDL',):
                # for some reasons, sometime in the active list we find also torrents in this state
                active_torrents_without_traffic_count += 1
            elif active_torrent.state in ('forcedDL', 'forcedUP') and active_torrent.generic_speed <= 0:
                # count torrents that are not generating traffic and that have been force-started
                active_torrents_without_traffic_count += 1
            else:
                active_torrents_filtered.append(active_torrent)

        active_torrents_strings_list = [TORRENT_STRING_COMPACT.format(**t.dict()) for t in active_torrents_filtered]

        # the list contains the strings to concatenate as the last row of the active torrents list
        other_torrents_counts_string = list()
        if active_torrents_without_traffic_count > 0:
            text = '<b>{}</b> stalled'.format(active_torrents_without_traffic_count)
            other_torrents_counts_string.append(text)
        if active_torrents_fetching_metadata_count > 0:
            text = '<b>{}</b> fetching metadata'.format(active_torrents_fetching_metadata_count)
            other_torrents_counts_string.append(text)

        if other_torrents_counts_string:
            active_torrents_strings_list.append('• ' + ', '.join(other_torrents_counts_string))

    if completed_torrents:
        total_completed_count = len(completed_torrents)
        completed_torrents_strings_list = ['• {}'.format(t.short_name) for t in completed_torrents]
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
        total_completed_count=total_completed_count,
        completed='\n'.join(completed_torrents_strings_list),
        total_active_count=total_active_count,
        active='\n'.join(active_torrents_strings_list),
        schedule=schedule_string,
        alt_speed=alt_speed_string,
        current_speed=current_speed_string,
        last_refresh=datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    )

    return text


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_quick_info_command(_, update, user_data):
    logger.info('/quick command from %s', update.message.from_user.first_name)

    text = get_quick_info_text()
    sent_message = update.message.reply_html(text, reply_markup=kb.QUICK_MENU_BUTTON)

    user_data['last_quick_message_id'] = sent_message.message_id


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_quick_info_refresh(bot: Bot, update, user_data):
    logger.info('/quick refresh from %s', update.message.from_user.first_name)

    message_id = user_data.get('last_quick_message_id', None)
    if not message_id:
        return

    bot.delete_message(update.effective_chat.id, update.message.message_id)

    text = get_quick_info_text()
    bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.QUICK_MENU_BUTTON
    )


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_refresh_button_quick(bot, update, groups=None):
    logger.info('quick info: refresh button')

    sort_active_by_dl_speed = True
    if groups[0] == 'percentage':
        sort_active_by_dl_speed = False

    text = get_quick_info_text(sort_active_by_dl_speed=sort_active_by_dl_speed)

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


updater.add_handler(CommandHandler(['quick'], on_quick_info_command, pass_user_data=True))
updater.add_handler(RegexHandler(r'^[aA]$', on_quick_info_refresh, pass_user_data=True))
updater.add_handler(CallbackQueryHandler(on_refresh_button_quick, pattern=r'^quick:refresh:(\w+)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(on_alton_button_quick, pattern=r'^quick:alton$'))
updater.add_handler(CallbackQueryHandler(on_altoff_button_quick, pattern=r'^quick:altoff$'))
updater.add_handler(CallbackQueryHandler(on_schedon_button_quick, pattern=r'^quick:schedon'))
updater.add_handler(CallbackQueryHandler(on_schedoff_button_quick, pattern=r'^quick:schedoff'))

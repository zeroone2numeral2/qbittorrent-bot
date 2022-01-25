import datetime
import logging
from collections import Counter

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
# noinspection PyPackageRequirements
from telegram import ParseMode, MAX_MESSAGE_LENGTH, Bot, Update, BotCommand

from qbt.custom import STATES_DICT
from bot.qbtinstance import qb
from bot.updater import updater
from .transfer_info import get_speed_text
from utils import u
from utils import kb
from utils import Permissions

logger = logging.getLogger(__name__)

QUICK_INFO_TEXT = """• <b>completed:</b> {completed_count}
• <b>torrent states:</b> {states_count}
• <b>categories:</b> {categories_count}

➤ <b>Active, uploading ({active_up_count}):</b>
{active_up}

➤ <b>Active, downloading ({active_down_count}):</b>
{active_down}

{current_speed}

{schedule}
<b>Last refresh:</b> {last_refresh}"""

TORRENT_STRING_COMPACT = """• <code>{short_name_escaped}</code> ({progress_pretty}% of {size_pretty}, \
{share_ratio_rounded}, <b>{generic_speed_pretty}/s</b>) [<a href="{info_deeplink}">info</a>]"""


def get_quick_info_text(sort_active_by_dl_speed=True):
    all_torrents = qb.torrents(filter='all', get_torrent_generic_properties=False)
    states_counter = Counter([t.state for t in all_torrents])
    categories_counter = Counter([t.category for t in all_torrents])

    active_torrents_up = [torrent for torrent in all_torrents if torrent.state in ("uploading",)]
    active_torrents_up.sort(key=lambda t: t['upspeed'])

    active_torrents_down = [torrent for torrent in all_torrents if torrent.state in ("downloading",)]
    active_torrents_down.sort(key=lambda t: t['dlspeed'])

    active_torrents_down_strings_list = ['no active downloading torrents']
    active_torrents_up_strings_list = ['no active uploading torrents']
    states_count_string = 'none'
    categories_count_string = 'none'

    active_up_count = len(active_torrents_up)
    active_down_count = len(active_torrents_down)
    completed_count = len([t for t in all_torrents if t.progress == 1.00])

    if active_torrents_down:
        active_torrents_down_strings_list = [TORRENT_STRING_COMPACT.format(**t.dict()) for t in active_torrents_down]
    if active_torrents_up:
        active_torrents_up_strings_list = [TORRENT_STRING_COMPACT.format(**t.dict()) for t in active_torrents_up]

    states_count_list = list()
    for state, count in states_counter.most_common():
        states_count_list.append(f"{count} {STATES_DICT[state]}")
    if states_count_list:
        states_count_string = ', '.join(states_count_list)

    categories_count_list = list()
    for category, count in categories_counter.most_common():
        categories_count_list.append(f"{count} {category or 'not set'}")
    if categories_count_list:
        categories_count_string = ', '.join(categories_count_list)

    schedule_info = qb.get_schedule()
    if not schedule_info:
        schedule_string = '<b>Schedule</b>: off'
    else:
        schedule_string = '<b>Schedule</b>: on, from {from_hour} to {to_hour} ({days})'.format(**schedule_info)

    alt_speed_info = qb.get_alt_speed(human_readable=True)

    current_speed = qb.get_speed()
    speed_limit_global = qb.get_global_speed_limit()
    speed_limit_global_set = any(speed_limit_global)
    if alt_speed_info['status'] == 'on':
        current_speed_string = f'▲ <b>{current_speed[1]}/s</b> ({alt_speed_info["alt_up_limit"]}/s)\n' \
                               f'▼ <b>{current_speed[0]}/s</b> ({alt_speed_info["alt_dl_limit"]}/s)\n' \
                               f'alt speed is <b>on</b>'
    else:
        # add global limits in parenthesis only if they are set
        global_speed_limit_are_set = "\nsome global speed limits are set" if speed_limit_global_set else ""
        up_limit = f" ({speed_limit_global[1]}/s)" if speed_limit_global[1] else ""
        dl_limit = f" ({speed_limit_global[0]}/s)" if speed_limit_global[0] else ""
        current_speed_string = f'▲ <b>{current_speed[1]}/s</b>{up_limit}\n' \
                               f'▼ <b>{current_speed[0]}/s</b>{dl_limit}' \
                               f'{global_speed_limit_are_set}'

    text = QUICK_INFO_TEXT.format(
        completed_count=completed_count,
        states_count=states_count_string,
        categories_count=categories_count_string,
        active_down_count=active_down_count,
        active_up_count=active_up_count,
        active_up='\n'.join(active_torrents_up_strings_list),
        active_down='\n'.join(active_torrents_down_strings_list),
        schedule=schedule_string,
        current_speed=current_speed_string,
        last_refresh=datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    )

    return text


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_overview_command(update: Update, context: CallbackContext):
    logger.info('/overview command from %s', update.message.from_user.first_name)

    text = get_quick_info_text()
    sent_message = update.message.reply_html(text, reply_markup=kb.get_overview_base_markup())

    context.user_data['last_overview_message_id'] = sent_message.message_id


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_overview_refresh(update: Update, context: CallbackContext):
    logger.info('/overview refresh from %s', update.message.from_user.first_name)

    message_id = context.user_data.get('last_overview_message_id', None)
    if not message_id:
        logger.debug("no 'last_overview_message_id' saved")
        return

    context.bot.delete_message(update.effective_chat.id, update.message.message_id)

    text = get_quick_info_text()
    context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_overview_base_markup()
    )


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_refresh_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: refresh button')

    sort_active_by_dl_speed = True
    if context.match[0] == 'percentage':
        sort_active_by_dl_speed = False

    text = get_quick_info_text(sort_active_by_dl_speed=sort_active_by_dl_speed)

    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_overview_base_markup())
    update.callback_query.answer('Refreshed')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_alton_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: alton button')

    if not bool(qb.get_alternative_speed_status()):
        qb.toggle_alternative_speed()

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_overview_altspeed_markup())
    update.callback_query.answer('Alternative speed enabled')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_altoff_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: altoff button')

    if bool(qb.get_alternative_speed_status()):
        qb.toggle_alternative_speed()

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_overview_altspeed_markup())
    update.callback_query.answer('Alternative speed disabled')


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_free_space_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: free space')

    try:
        drive_free_space = u.free_space(qb.save_path)
        text = f"{drive_free_space} free\n\n{qb.save_path}"
    except Exception as e:
        text = f"Exception while fetching the drive's free space: {e}"

    update.callback_query.answer(text, show_alert=True, cache_time=15)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_transfer_info_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: show transfer info')

    text = get_speed_text()

    update.callback_query.answer("showing transfer info data...")
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_overview_base_markup())


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_manage_alt_speed_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: manage alt speed')

    update.callback_query.edit_message_reply_markup(reply_markup=kb.get_overview_altspeed_markup())
    update.callback_query.answer("use these buttons to configure your alt speed settings")


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_manage_schedule_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: manage schedule')

    update.callback_query.edit_message_reply_markup(reply_markup=kb.get_overview_schedule_markup())
    update.callback_query.answer("use these buttons to configure your schedule settings")


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_schedon_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: schedon button')

    qb.set_preferences(**{'scheduler_enabled': True})

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_overview_schedule_markup())
    update.callback_query.answer('Scheduled altenrative speed on')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_schedoff_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: schedoff button')

    qb.set_preferences(**{'scheduler_enabled': False})

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_overview_schedule_markup())
    update.callback_query.answer('Scheduled altenrative speed off')


updater.add_handler(CommandHandler(['overview', 'ov'], on_overview_command), bot_command=BotCommand("overview", "overview of what we're downloading and uploading"))
updater.add_handler(CommandHandler(['quick'], on_overview_command))
updater.add_handler(MessageHandler(Filters.regex(r'^[aA\.]$'), on_overview_refresh))
updater.add_handler(CallbackQueryHandler(on_refresh_button_overview, pattern=r'^(?:quick|overview):refresh:(\w+)$'))
updater.add_handler(CallbackQueryHandler(on_free_space_button_overview, pattern=r'^overview:freespace'))
updater.add_handler(CallbackQueryHandler(on_transfer_info_button_overview, pattern=r'^overview:transferinfo'))
updater.add_handler(CallbackQueryHandler(on_manage_alt_speed_button_overview, pattern=r'^overview:altspeed$'))
updater.add_handler(CallbackQueryHandler(on_manage_schedule_button_overview, pattern=r'^overview:schedule$'))
updater.add_handler(CallbackQueryHandler(on_alton_button_overview, pattern=r'^(?:quick|overview):alton$'))
updater.add_handler(CallbackQueryHandler(on_altoff_button_overview, pattern=r'^(?:quick|overview):altoff$'))
updater.add_handler(CallbackQueryHandler(on_schedon_button_overview, pattern=r'^(?:quick|overview):schedon'))
updater.add_handler(CallbackQueryHandler(on_schedoff_button_overview, pattern=r'^(?:quick|overview):schedoff'))

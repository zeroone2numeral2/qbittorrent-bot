import datetime
import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters
# noinspection PyPackageRequirements
from telegram import ParseMode, MAX_MESSAGE_LENGTH, Bot, Update, BotCommand

from bot.qbtinstance import qb
from bot.updater import updater
from utils import u
from utils import kb
from utils import Permissions

logger = logging.getLogger(__name__)

QUICK_INFO_TEXT = """➤ <b>Other:</b>
{other_torrents}

➤ <b>Active, uploading ({active_up_count}):</b>
{active_up}

➤ <b>Active, downloading ({active_down_count}):</b>
{active_down}

{current_speed}

{schedule}
<b>Last refresh:</b> {last_refresh}"""

TORRENT_STRING_COMPACT = """• <code>{short_name}</code> ({progress_pretty}% of {size_pretty}, {state_pretty}, \
<b>{generic_speed_pretty}/s</b>) [<a href="{info_deeplink}">info</a>]"""


def get_quick_info_text(sort_active_by_dl_speed=True):
    if sort_active_by_dl_speed:
        active_torrents_sort = 'dlspeed'
    else:
        active_torrents_sort = 'progress'

    active_torrents = qb.torrents(filter='active', sort=active_torrents_sort, reverse=False, get_properties=False)
    completed_torrents = qb.torrents(filter='completed', get_properties=False)

    total_completed_count = 0

    active_torrents_down_strings_list = ['no active downloading torrents']
    active_torrents_up_strings_list = ['no active uploading torrents']
    other_torrents_string = 'none'

    active_down_count = 0
    active_up_count = 0
    completed_count = len(completed_torrents)

    if active_torrents:
        # lists without stalled torrents and torrents for which we are fetching the metadata
        active_torrents_down_filtered = list()
        active_torrents_up_filtered = list()

        active_torrents_without_traffic_count = 0
        active_torrents_fetching_metadata_count = 0

        for active_torrent in active_torrents:
            if active_torrent.state in ('metaDL',):
                # torrents for which we are still fetching metadata
                active_torrents_fetching_metadata_count += 1
            elif active_torrent.state in ('stalledDL',):
                # for some reasons, sometime in the active list we find also torrents in this state
                active_torrents_without_traffic_count += 1
            elif active_torrent.state in ('forcedDL', 'forcedUP') and active_torrent.generic_speed <= 0:
                # count torrents that are not generating traffic and that have been force-started
                active_torrents_without_traffic_count += 1
            elif active_torrent.state in ('uploading',):
                # active completed torrents we are uploading (or stalled torrents we are uploading)
                active_torrents_up_filtered.append(active_torrent)
            else:
                # all the rest
                active_torrents_down_filtered.append(active_torrent)

        active_down_count = len(active_torrents_down_filtered)
        active_up_count = len(active_torrents_up_filtered)

        if active_torrents_down_filtered:
            active_torrents_down_strings_list = [TORRENT_STRING_COMPACT.format(**t.dict()) for t in active_torrents_down_filtered]
        if active_torrents_up_filtered:
            active_torrents_up_strings_list = [TORRENT_STRING_COMPACT.format(**t.dict()) for t in active_torrents_up_filtered]

        # the list contains the strings to concatenate as the last row of the active downloading torrents list
        other_torrents_list = list()
        if completed_count:
            text = '<b>{}</b> completed'.format(completed_count)
            other_torrents_list.append(text)
        if active_torrents_without_traffic_count > 0:
            text = '<b>{}</b> stalled'.format(active_torrents_without_traffic_count)
            other_torrents_list.append(text)
        if active_torrents_fetching_metadata_count > 0:
            text = '<b>{}</b> fetching metadata'.format(active_torrents_fetching_metadata_count)
            other_torrents_list.append(text)

        if other_torrents_list:
            other_torrents_string = '• ' + ', '.join(other_torrents_list)

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
    speed_limit_global = qb.get_global_speed_limit()
    speed_limit_global_set = any(speed_limit_global)
    if alt_speed_info['status'] == 'on':
        current_speed_string = '▲ <b>{current_up}/s</b> ({alt_up_limit}/s)\n▼ <b>{current_down}/s</b> ({alt_dl_limit}/s)\nalt speed is on'.format(
            current_up=current_speed[1],
            current_down=current_speed[0],
            **alt_speed_info
        )
    else:
        # add global limits in parenthesis only if they are set
        current_speed_string = '▲ <b>{current_up}/s</b>{up_limit}\n▼ <b>{current_down}/s</b>{dl_limit}{global_speed_limit_are_set}'.format(
            current_up=current_speed[1],
            current_down=current_speed[0],
            up_limit=f" ({speed_limit_global[1]}/s)" if speed_limit_global[1] else "",
            dl_limit=f" ({speed_limit_global[0]}/s)" if speed_limit_global[0] else "",
            global_speed_limit_are_set="\nsome global speed limits are set" if speed_limit_global_set else ""
        )

    text = QUICK_INFO_TEXT.format(
        other_torrents=other_torrents_string,
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
    sent_message = update.message.reply_html(text, reply_markup=kb.get_quick_menu_markup())

    context.user_data['last_overview_message_id'] = sent_message.message_id


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_overview_refresh(update: Update, context: CallbackContext):
    logger.info('/overview refresh from %s', update.message.from_user.first_name)

    message_id = context.user_data.get('last_overview_message_id', None)
    if not message_id:
        return

    context.bot.delete_message(update.effective_chat.id, update.message.message_id)

    text = get_quick_info_text()
    context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=message_id,
        text=text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.get_quick_menu_markup()
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

    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_quick_menu_markup())
    update.callback_query.answer('Refreshed')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_alton_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: alton button')

    if not bool(qb.get_alternative_speed_status()):
        qb.toggle_alternative_speed()

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_quick_menu_markup())
    update.callback_query.answer('Alternative speed enabled')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_altoff_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: altoff button')

    if bool(qb.get_alternative_speed_status()):
        qb.toggle_alternative_speed()

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_quick_menu_markup())
    update.callback_query.answer('Alternative speed disabled')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_schedon_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: schedon button')

    qb.set_preferences(**{'scheduler_enabled': True})

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_quick_menu_markup())
    update.callback_query.answer('Scheduled altenrative speed on')


@u.check_permissions(required_permission=Permissions.EDIT)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_schedoff_button_overview(update: Update, context: CallbackContext):
    logger.info('overview: schedoff button')

    qb.set_preferences(**{'scheduler_enabled': False})

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.get_quick_menu_markup())
    update.callback_query.answer('Scheduled altenrative speed off')


updater.add_handler(CommandHandler(['overview', 'ov'], on_overview_command), bot_command=BotCommand("overview", "overview of what we're downloading and uploading"))
updater.add_handler(CommandHandler(['quick'], on_overview_command))
updater.add_handler(MessageHandler(Filters.regex(r'^[aA]$'), on_overview_refresh))
updater.add_handler(CallbackQueryHandler(on_refresh_button_overview, pattern=r'^(?:quick|overview):refresh:(\w+)$'))
updater.add_handler(CallbackQueryHandler(on_alton_button_overview, pattern=r'^(?:quick|overview):alton$'))
updater.add_handler(CallbackQueryHandler(on_altoff_button_overview, pattern=r'^(?:quick|overview):altoff$'))
updater.add_handler(CallbackQueryHandler(on_schedon_button_overview, pattern=r'^(?:quick|overview):schedon'))
updater.add_handler(CallbackQueryHandler(on_schedoff_button_overview, pattern=r'^(?:quick|overview):schedoff'))

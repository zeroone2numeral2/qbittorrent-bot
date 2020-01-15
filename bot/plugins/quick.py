import logging

# noinspection PyPackageRequirements
from telegram.ext import CommandHandler, CallbackQueryHandler
# noinspection PyPackageRequirements
from telegram import ParseMode

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
{current_speed}"""

TORRENT_STRING_COMPACT = """• <code>{short_name}</code> ({progress}% of {size}, {state}, <b>{dlspeed}/s</b>) \
[<a href="{info_deeplink}">info</a>]"""


def get_quick_info_text():
    active_trnts = qb.torrents(filter='active', sort='dlspeed', reverse=False)
    completed_trnts = qb.torrents(filter='completed')

    if active_trnts:
        active_torrents_strings_list = [TORRENT_STRING_COMPACT.format(**t.dict()) for t in active_trnts]
    else:
        active_torrents_strings_list = ['no active torrent']

    if completed_trnts:
        completed_torrents_strings_list = ['{}'.format(t.short_name) for t in completed_trnts]
    else:
        completed_torrents_strings_list = ['no completed torrent']

    schedule_info = qb.get_schedule()
    if not schedule_info:
        schedule_string = '<b>Schedule</b>: off'
    else:
        schedule_string = '<b>Schedule</b>: on, from {from_hour} to {to_hour} ({days})'.format(**schedule_info)

    alt_speed_info = qb.get_alt_speed()
    alt_speed_string = '<b>Alt speed is {}</b> (down: {alt_dl_limit} kb/s, up: {alt_up_limit} kb/s)'.format(
        'on' if alt_speed_info['status'] else 'off',
        alt_dl_limit=alt_speed_info['alt_dl_limit'] if alt_speed_info['alt_dl_limit'] else 'none',
        alt_up_limit=alt_speed_info['alt_up_limit'] if alt_speed_info['alt_up_limit'] else 'none',
    )

    current_speed = qb.get_speed()
    current_speed_string = '<b>Current speed</b>: down: {0}/s, up: {1}/s'.format(*current_speed)

    text = QUICK_INFO_TEXT.format(
        completed='\n'.join(completed_torrents_strings_list),
        active='\n'.join(active_torrents_strings_list),
        schedule=schedule_string,
        alt_speed=alt_speed_string,
        current_speed=current_speed_string
    )

    return text


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_quick_info_command(_, update):
    logger.info('/quick command from %s', update.message.from_user.first_name)

    text = get_quick_info_text()
    update.message.reply_html(text, reply_markup=kb.QUICK_MENU_BUTTON)


@u.failwithmessage
@u.ignore_not_modified_exception
def on_refresh_button_quick(bot, update):
    logger.info('quick info: refresh button')

    text = get_quick_info_text()

    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Refreshed')


@u.failwithmessage
@u.ignore_not_modified_exception
def on_alton_button_quick(_, update):
    logger.info('quick info: alton button')

    if not bool(qb.get_alternative_speed_status()):
        qb.toggle_alternative_speed()

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Alternative speed enabled')


@u.failwithmessage
@u.ignore_not_modified_exception
def on_altoff_button_quick(_, update):
    logger.info('quick info: altoff button')

    if bool(qb.get_alternative_speed_status()):
        qb.toggle_alternative_speed()

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Alternative speed disabled')


@u.failwithmessage
@u.ignore_not_modified_exception
def on_schedon_button_quick(_, update):
    logger.info('quick info: schedon button')

    qb.set_preferences(**{'scheduler_enabled': True})

    text = get_quick_info_text()
    update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=kb.QUICK_MENU_BUTTON)
    update.callback_query.answer('Scheduled altenrative speed on')


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

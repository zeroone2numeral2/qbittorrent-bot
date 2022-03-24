import logging

# noinspection PyPackageRequirements
from telegram import Update, BotCommand, ParseMode
from telegram.ext import CommandHandler, CallbackContext, CallbackQueryHandler

from bot.updater import updater
from bot.qbtinstance import qb
from utils import Permissions
from utils import u
from utils import kb

logger = logging.getLogger(__name__)


TEXT = """<b>Current speed</b>
▲ {current_upload_speed}/s
▼ {current_download_speed}/s

<b>Global speed limits</b>
▲ {global_up_limit}
▼ {global_down_limit}

<b>Alternative speed limits</b>
• alt speed: {alt_speed_status}
▲ {alt_speed_down}
▼ {alt_speed_up}

<b>Data uploaded/downloaded during this session</b>
▲ {session_total_upload}
▼ {session_total_download}
• this session's share rateo: {session_share_rateo}

<b>Torrents queueing</b>
• max active: {queueing_max_active_downloads} down, {queueing_max_active_uploads} up, \
{queueing_max_active_torrents} total
• count slow torrents in these limits? {queueing_count_slow_torrents}
• slow torrent down threshold: {queueing_slow_torrent_down_threshold} kb/s
• slow torrent up threshold: {queueing_slow_torrent_up_threshold} kb/s

<b>Share rateo</b>
• share torrents until max rateo is reached? {max_ratio_enabled} (max rateo: {max_ratio})
• share torrents until max seeding time is reached? {max_seeding_time_enabled} (max seeding time: {max_seeding_time} minutes, \
then {max_ratio_act} them)"""


def get_speed_text():
    fdict = {}

    transfer_info = qb.global_transfer_info
    fdict['current_download_speed'] = u.get_human_readable(transfer_info['dl_info_speed'])
    fdict['current_upload_speed'] = u.get_human_readable(transfer_info['up_info_speed'])

    fdict['session_total_upload'] = u.get_human_readable(transfer_info['up_info_data'])
    fdict['session_total_download'] = u.get_human_readable(transfer_info['dl_info_data'])
    if transfer_info['dl_info_data'] > 0:
        fdict['session_share_rateo'] = round(transfer_info['up_info_data']/transfer_info['dl_info_data'], 2)
    else:
        fdict['session_share_rateo'] = 0

    preferences = qb.preferences()

    fdict['global_down_limit'] = u.get_human_readable(preferences['dl_limit']) if preferences['dl_limit'] else 'none'
    fdict['global_up_limit'] = u.get_human_readable(preferences['up_limit']) if preferences['up_limit'] else 'none'

    fdict['alt_speed_status'] = 'on' if qb.get_alternative_speed_status() else 'off'
    fdict['alt_speed_down'] = u.get_human_readable(preferences['alt_dl_limit'], 0) if preferences[
                                                                                          'alt_dl_limit'] > -1 else 'none'
    fdict['alt_speed_up'] = u.get_human_readable(preferences['alt_up_limit'], 0) if preferences[
                                                                                        'alt_up_limit'] > -1 else 'none'

    fdict['queueing_max_active_downloads'] = preferences['max_active_downloads']
    fdict['queueing_max_active_uploads'] = preferences['max_active_uploads']
    fdict['queueing_max_active_torrents'] = preferences['max_active_torrents']
    fdict['queueing_count_slow_torrents'] = 'no' if preferences['dont_count_slow_torrents'] else 'yes'
    fdict['queueing_slow_torrent_down_threshold'] = preferences['slow_torrent_dl_rate_threshold']
    fdict['queueing_slow_torrent_up_threshold'] = preferences['slow_torrent_ul_rate_threshold']
    fdict['queueing_slow_torrent_inactive_timer'] = preferences['slow_torrent_inactive_timer']

    fdict['max_ratio_enabled'] = "yes" if preferences['max_ratio_enabled'] else "no"
    fdict['max_ratio'] = preferences['max_ratio']
    fdict['max_seeding_time_enabled'] = "yes" if preferences['max_seeding_time_enabled'] else "no"
    fdict['max_seeding_time'] = preferences['max_seeding_time']
    fdict['max_ratio_act'] = "pause" if preferences['max_ratio_act'] == 0 else "remove"  # 0 = pause them, 1 = remove them

    return TEXT.format(**fdict)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_speed_command(update: Update, context: CallbackContext):
    logger.info('/transferinfo from %s', update.effective_user.first_name)

    text = get_speed_text()

    update.message.reply_html(text, reply_markup=kb.REFRESH_TRANSFER_INFO)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
@u.ignore_not_modified_exception
def on_refresh_button_speed(update: Update, context: CallbackContext):
    logger.info('transfer info: refresh button')

    text = get_speed_text()

    update.callback_query.edit_message_text(
        text,
        parse_mode=ParseMode.HTML,
        reply_markup=kb.REFRESH_TRANSFER_INFO
    )
    update.callback_query.answer('Refreshed')


updater.add_handler(CommandHandler(['transferinfo', 'ti', 'speed'], on_speed_command), bot_command=BotCommand("transferinfo", "overview about the current speed, queueing and rateo settings"))
updater.add_handler(CallbackQueryHandler(on_refresh_button_speed, pattern=r'^refreshtransferinfo$'))

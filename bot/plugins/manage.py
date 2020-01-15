import logging

# noinspection PyPackageRequirements
from telegram.ext import CallbackQueryHandler, RegexHandler
# noinspection PyPackageRequirements
from telegram import ParseMode, MAX_MESSAGE_LENGTH
# noinspection PyPackageRequirements
from telegram.error import BadRequest

from bot import qb
from bot import updater
from utils import u
from utils import kb
from utils import Permissions

logger = logging.getLogger(__name__)


@u.check_permissions(required_permission=Permissions.READ)
@u.failwithmessage
def on_info_deeplink(_, update, groups=[]):
    logger.info('info deeplink from %s', update.message.from_user.first_name)

    torrent_hash = groups[0]
    logger.info('torrent hash: %s', torrent_hash)

    torrent = qb.torrent(torrent_hash)

    update.message.reply_html(torrent.string(), reply_markup=torrent.short_markup())


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

    strings_list = [
        '<b>{status}:</b> {url} <b>({num_peers})</b>'.format(**{k: u.html_escape(str(v)) for k, v in tracker.items()})
        for tracker in trackers]
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
            lines_list.append(
                '<b>{}</b>: {} trackers, {} peers'.format(status, status_counts['count'], status_counts['num_peers']))

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
        'Are you sure you want to delete {}, <b>with all the connected files included</b>?'.format(
            u.html_escape(torrent.name)),
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


updater.add_handler(RegexHandler(r'^\/start info(.*)$', on_info_deeplink, pass_groups=True))
updater.add_handler(CallbackQueryHandler(manage_torrent_cb, pattern=r'^manage:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(see_trackers_cb, pattern=r'^trackers:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(refresh_torrent_cb, pattern=r'^refresh:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(pause_torrent_cb, pattern=r'^pause:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(resume_torrent_cb, pattern=r'^resume:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(force_resume_torrent_cb, pattern=r'^forceresume:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(force_start_torrent_cb, pattern=r'^forcestart:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(unforce_start_torrent_cb, pattern=r'^unforcestart:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(priority_up_cb, pattern=r'^priorityup:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(max_priority_cb, pattern=r'^maxpriority:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(recheck_cb, pattern=r'^recheck:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(ask_confirm_delete_with_files_cb, pattern=r'^deletewithfiles:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(confirm_delete_with_files_cb, pattern=r'^confirmdeletewithfiles:(.*)$', pass_groups=True))
updater.add_handler(CallbackQueryHandler(reduce_buttons, pattern=r'^reduce:(.*)$', pass_groups=True))

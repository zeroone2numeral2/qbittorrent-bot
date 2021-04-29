import logging
from functools import wraps
from html import escape as html_escape

from telegram import Bot, ParseMode, Update, MAX_MESSAGE_LENGTH
from telegram.ext import CallbackContext
from telegram.error import BadRequest, TelegramError, TimedOut
import psutil

from .permissions_storage import permissions
from config import config

FULL = '●'
EMPTY = '○'

logger = logging.getLogger(__name__)


def check_permissions(required_permission='admin'):
    def real_decorator(func):
        @wraps(func)
        def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
            user_id = update.effective_user.id
            
            if user_id in config.telegram.admins:
                # always give the green light for admins
                return func(update, context, *args, **kwargs)

            if required_permission in ('a', 'admin') or permissions['admins_only']:
                # if admins_only: no one can use the bot but the admins
                logger.info('unauthorized use by %d (%s)', user_id, update.effective_user.first_name)
                
                text = "You can't use this function"
                if update.callback_query:
                    update.callback_query.answer(text)
                elif update.message:
                    update.message.reply_text(text)
                
                return
            
            # check if the config allows one of the operations for non-admin users
            if required_permission in ('r', 'read') and permissions['free_read']:
                return func(update, context, *args, **kwargs)
            # "edit/write" permission require "read" permission to be enabled
            elif required_permission in ('w', 'write') and (permissions['free_read'] and permissions['free_write']):
                return func(update, context, *args, **kwargs)
            elif required_permission in ('e', 'edit') and (permissions['free_read'] and permissions['free_edit']):
                return func(update, context, *args, **kwargs)
            
            # all the permissions are disabled: unauthorized access
            logger.info('unauthorized command usage (%s) by %d (%s)', required_permission, user_id, update.effective_user.first_name)
            text = '"{}" permission disabled for non-admin users'.format(required_permission)
            if update.callback_query:
                update.callback_query.answer(text)
            elif update.message:
                update.message.reply_text(text)
            
            return

        return wrapped
    return real_decorator


def failwithmessage(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            return func(update, context, *args, **kwargs)
        except Exception as e:
            error_str = str(e)
            logger.info('error while running handler callback: %s', error_str, exc_info=True)
            text = 'An error occurred while processing the {}: <code>{}</code>'.format(
                'callback query' if update.callback_query else 'message',
                html_escape(error_str)
            )

            if update.callback_query and error_str.lower().startswith('query is too old'):
                update.callback_query.answer(error_str)
            else:
                update.effective_message.reply_html(text)

    return wrapped


def ignore_not_modified_exception(func):
    @wraps(func)
    def wrapped(update: Update, context: CallbackContext, *args, **kwargs):
        try:
            return func(update, context, *args, **kwargs)
        except (BadRequest, TelegramError) as err:
            logger.info('"message is not modified" error ignored')
            if 'not modified' not in str(err).lower():
                raise err
            else:
                update.callback_query.answer('Nothing to refresh')

    return wrapped


def failwithmessage_job(func):
    @wraps(func)
    def wrapped(context: CallbackContext, *args, **kwargs):
        try:
            return func(context, *args, **kwargs)
        except Exception as e:
            logger.info('error while running job: %s', str(e), exc_info=True)
            text = 'An error occurred while running a job: <code>{}</code>'.format(html_escape(str(e)))
            context.bot.send_message(config.telegram.admins[0], text, parse_mode=ParseMode.HTML)

    return wrapped


def get_human_readable(size, precision=2):
    suffixes = ['b', 'kb', 'mb', 'gb', 'tb']
    suffix_index = 0
    while size > 1024 and suffix_index < 4:
        suffix_index += 1  # increment the index of the suffix
        size = size / 1024.0

    return '%.*f %s' % (precision, size, suffixes[suffix_index])


def build_progress_bar(decimal_percentage, steps=10):
    completed_steps = round(steps * decimal_percentage)
    missing_steps = steps - completed_steps
    return '{}{}'.format(FULL * completed_steps, EMPTY * missing_steps)


def custom_timeout(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if 'timeout' not in kwargs and config.telegram.get('timeout', None):
            kwargs['timeout'] = config.telegram.timeout

        return func(*args, **kwargs)

    return wrapped


def split_text(strings_list):
    avg_len = sum(map(len, strings_list)) / len(strings_list)
    elements_per_msg = int(MAX_MESSAGE_LENGTH / avg_len)

    for i in range(0, len(strings_list), elements_per_msg):
        yield strings_list[i:i + elements_per_msg]


def free_space(dir_path, human_readable=True) -> [str, int]:
    usage = psutil.disk_usage(dir_path)

    free_space_bytes = usage.free

    if human_readable:
        return get_human_readable(free_space_bytes)
    else:
        return free_space_bytes


def send_admin(bot, text):
    """debug function"""

    return bot.send_message(config.telegram.admins, text)

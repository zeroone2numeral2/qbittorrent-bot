import logging
import os
import importlib
import re
from pathlib import Path

# noinspection PyPackageRequirements
from telegram.ext import Updater, ConversationHandler
# noinspection PyPackageRequirements
from telegram import BotCommand

logger = logging.getLogger(__name__)


class CustomUpdater(Updater):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot_commands = []

    @staticmethod
    def _load_manifest(manifest_path):
        if not manifest_path:
            return

        try:
            with open(manifest_path, 'r') as f:
                manifest_str = f.read()
        except FileNotFoundError:
            logger.debug('manifest <%s> not found', os.path.normpath(manifest_path))
            return

        if not manifest_str.strip():
            return

        manifest_str = manifest_str.replace('\r\n', '\n')
        manifest_lines = manifest_str.split('\n')

        modules_list = list()
        for line in manifest_lines:
            line = re.sub(r'(?:\s+)?#.*(?:\n|$)', '', line)  # remove comments from the line
            if line.strip():  # ignore empty lines
                items = line.split()  # split on spaces. We will consider only the first word
                modules_list.append(items[0])  # tuple: (module_to_import, [callbacks_list])

        return modules_list

    @classmethod
    def import_handlers(cls, directory):
        """A text file named "manifest" can be placed in the dir we are importing the handlers from.
        It can contain the list of the files to import, the bot will import only these
        modules as ordered in the manifest file.
        Inline comments are allowed, they must start by #"""

        paths_to_import = list()

        manifest_modules = cls._load_manifest(os.path.join(directory, 'manifest'))
        if manifest_modules:
            # build the base import path of the plugins/jobs directory
            target_dir_path = os.path.splitext(directory)[0]
            target_dir_import_path_list = list()
            while target_dir_path:
                target_dir_path, tail = os.path.split(target_dir_path)
                target_dir_import_path_list.insert(0, tail)
            base_import_path = '.'.join(target_dir_import_path_list)

            for module in manifest_modules:
                import_path = base_import_path + module

                logger.debug('importing module [%s]', import_path)

                paths_to_import.append(import_path)
        else:
            for path in sorted(Path(directory).rglob('*.py')):
                file_path = os.path.splitext(str(path))[0]

                import_path = []

                while file_path:
                    file_path, tail = os.path.split(file_path)
                    import_path.insert(0, tail)

                import_path = '.'.join(import_path)

                paths_to_import.append(import_path)

        for import_path in paths_to_import:
            logger.debug('importing module [%s]', import_path)
            importlib.import_module(import_path)

    def set_bot_commands(self, show_first: [list, None] = None):
        if show_first:
            show_first = [c.lower() for c in show_first]

            new_list = []

            for command_to_show_first in show_first:
                command: BotCommand
                for command in self.bot_commands:
                    if command.command.lower() == command_to_show_first:
                        new_list.append(command)

            new_list.extend(self.bot_commands)  # we don't care about the duplicates
            self.bot_commands = new_list

        self.bot.set_my_commands(self.bot_commands)

    def run(self, *args, **kwargs):
        logger.info('running as @%s', self.bot.username)

        self.start_polling(*args, **kwargs)
        self.idle()

    def add_handler(self, *args, bot_command=None, **kwargs):
        if isinstance(args[0], ConversationHandler):
            # ConverstaionHandler.name or the name of the first entry_point function
            logger.info('adding conversation handler <%s>', args[0].name or args[0].entry_points[0].callback.__name__)
        else:
            logger.info('adding handler <%s>', args[0].callback.__name__)

        self.dispatcher.add_handler(*args, **kwargs)

        if bot_command:
            if isinstance(bot_command, (list, tuple)):
                self.bot_commands.extend(bot_command)
            else:
                self.bot_commands.append(bot_command)

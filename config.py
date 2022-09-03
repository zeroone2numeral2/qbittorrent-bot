import os
import sys

import toml
from os import path


class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def load_config_safe(filepath: str):
    if path.exists(filepath):
        return toml.load(filepath, AttrDict)
    else:
        print(f"The file {filepath} is not found, we are trying to find values in environment variables")
        return {}


config = load_config_safe('config.toml')


def exit_with_message(message: str):
    print(f"config: {message}")
    print(f"see 'config.example.toml' for more details on how to fill the required values in 'config.toml'")
    sys.exit(0)


example_config = toml.load('config.example.toml')

for config_section, example_config_section_dict in example_config.items():
    if config_section not in config:
        value_from_env = os.getenv(config_section)
        if value_from_env is None:
            exit_with_message(f"missing section [{config_section}]")
        else:
            config[config_section] = value_from_env

    config_section_dict = config[config_section]
    for example_config_key, example_config_val in example_config_section_dict.items():
        if example_config_key not in config_section_dict:
            exit_with_message(f"missing key [{config_section}.{example_config_key}]")

        config_val = config_section_dict[example_config_key]
        if type(config_val) is not type(example_config_val):
            exit_with_message( f"type of field [{config_section}.{example_config_key}] should be of type '{type(example_config_val).__name__}'")

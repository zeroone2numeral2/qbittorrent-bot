import os
import json


class Storage:
    def __init__(self, file_path, default_dict: dict, autosave=False):
        self._file_path = os.path.normpath(file_path)
        self._data = dict()
        self._autosave = autosave
        self._default_dict = default_dict or {}

        try:
            with open(self._file_path, 'r') as f:
                self._data = json.load(f)
        except FileNotFoundError:
            self._data = default_dict
            self.dump()

    def dump(self):
        with open(self._file_path, 'w+') as f:
            json.dump(self._data, f, indent=4)

    def __getitem__(self, item):
        return self._data[item]

    def __setitem__(self, key, value):
        self._data[key] = value
        if self._autosave:
            self.dump()

    def reset_defaults(self):
        """Reset the default dict passed during the initialization fo the class

        :return: None
        """
        os.remove(self._file_path)
        self._data = self._default_dict
        self.dump()

    def get(self, key, default):
        """Get the value of a key from the class internal dict

        :param key: key to get
        :param default: default value to return
        :return: the key value
        """
        return self._data.get(key, default)

    def set(self, key, value, create_if_missing=False, save=False):
        """Set the value of an existing key, or create it if it doesn't exist when
        create_if_missing is True

        :param key: key to change/create
        :param value: value to set
        :param create_if_missing: create the key if missing
        :param save: dump the class data object to its file
        :return: the key value
        """
        if not create_if_missing:
            _ = self._data[key]  # check if the key exists first. If it doesn't, an exception will be raised

        self._data[key] = value

        if save or self._autosave:
            self.dump()

        return self._data[key]

    def unset(self, key, save=False):
        """Pop a class data value. An exception is raised if the key doesn't exist

        :param key: key to pop
        :param save: dump the class data object to its file
        :return: the popped value
        """
        value = self._data.pop(key)

        if save or self._autosave:
            self.dump()

        return value

    def __repr__(self):
        max_key_len = len(max(self._data.keys(), key=len))
        max_val_len = len(max([str(i) for i in self._data.values()], key=len))

        line_str = '{:<%d} > {:<%d} | {}' % (max_key_len, max_val_len)
        string = '\n'.join([line_str.format(k, str(v), type(v).__name__) for k, v in self._data.items()])

        return string

import json

from utils.storage import Storage


class Permissions(Storage):
    READ = 'read'
    WRITE = 'write'
    EDIT = 'edit'
    ADMIN = 'admin'

    def __init__(self, *args, **kwargs):
        with open('default_permissions.json', 'r') as f:
            default_dict = json.load(f)

        super(Permissions, self).__init__(*args, **kwargs, default_dict=default_dict)

        # migrate old json config keys from "free_permission" to "permission"
        updated_values = {}
        keys_to_pop = []
        for k, v in self._data.items():
            if not k.startswith("free_"):
                continue

            new_key = k.replace("free_", "")
            updated_values[new_key] = v
            keys_to_pop.append(k)

        self._data.update(updated_values)

        for k in keys_to_pop:
            self._data.pop(k, None)

        self.dump()


permissions = Permissions('permissions.json', autosave=True)

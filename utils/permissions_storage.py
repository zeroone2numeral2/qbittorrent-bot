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


permissions = Permissions('permissions.json', autosave=True)

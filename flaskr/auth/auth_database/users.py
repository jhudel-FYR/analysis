
from flaskr.framework.abstract.abstract_model import AbstractModel

ACCESS = {
    'guest': 0,
    'user': 1,
    'admin': 3
}


class User(AbstractModel):
    def __init__(self, email='', username='', password='', permission=0, organization='FYR'):
        super().__init__()
        self['_id'] = None
        self['email'] = email
        self['username'] = username
        self['password'] = password
        self['permission'] = permission
        self['organization'] = organization

    def get_password(self):
        return self['password']

    def get_email(self):
        return self['email']

    def get_username(self):
        return self['username']

    def get_permission(self):
        return self['permission']

    def get_organization(self):
        return self['organization']

    def is_admin(self):
        if self['permission'] == 3:
            return True
        return False

    def is_guest(self):
        if self['permission'] == 0:
            return True
        return False

    def is_allowed(self, access_level):
        return self['permission'] >= access_level

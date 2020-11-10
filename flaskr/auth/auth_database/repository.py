
from werkzeug.security import generate_password_hash

from flaskr.auth.auth_database.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'user'
    factory = Factory()

    def get_by_email(self, email: str):
        data = self.get_connection().find_one({'email': email})
        if data is None:
            return None

        model = self.factory.create(data)
        return model

    def get_by_username(self, username: str):
        data = self.get_connection().find_one({'username': username})
        if data is None:
            return None

        model = self.factory.create(data)
        return model

    def filter_by_username(self, username: str):
        data = self.get_connection().find({'username': username})
        if data is None:
            return None

        return data

    def get_by_token(self, token: None):
        data = self.get_connection().find_one({'token': token})
        if data is None:
            return None

        model = self.factory.create(data)
        return model

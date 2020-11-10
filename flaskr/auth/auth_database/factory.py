from flaskr.auth.auth_database.users import User
from flaskr.framework.abstract.abstract_factory import AbstractFactory


class Factory(AbstractFactory):
    def create(self, data=None) -> User:
        model = User()
        if data is not None:
            model.set_data(data)

        return model

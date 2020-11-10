from flaskr.database_static.primer_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'primer'
    factory = Factory()

    def get_by_name(self, name):
        data = self.get_connection().find_one({'name': name})

        if data is None:
            return None

        return self.factory.create(data)

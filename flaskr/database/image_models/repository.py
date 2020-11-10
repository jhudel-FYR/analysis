from flaskr.database.image_models.factory import Factory
from flaskr.framework.abstract.abstract_repository import AbstractRepository


class Repository(AbstractRepository):
    name = 'image'
    factory = Factory()

    def get_by_name(self, name):
        data = self.get_connection().find_one({'dataset_name': name})

        if data is None:
            return None

        return data

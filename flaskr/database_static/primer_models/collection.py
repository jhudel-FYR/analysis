
from flaskr.database_static.primer_models.factory import Factory as PrimerFactory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'primer'
    buffer = []

    def __init__(self):
        super().__init__(PrimerFactory())

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data)
        return model


from flaskr.database.base_assay_model.factory import Factory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'base_assay'
    buffer = []

    def __init__(self):
        super().__init__(Factory())

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data)
        return model





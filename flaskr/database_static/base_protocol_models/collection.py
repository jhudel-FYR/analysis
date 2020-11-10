
from flaskr.database_static.base_protocol_models.factory import Factory as BaseProtocolFactory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'base_protocol'
    buffer = []

    def __init__(self):
        super().__init__(BaseProtocolFactory())

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data)
        return model

    def get_components(self):
        for item in self:
            yield {'component_id': item['component_id'],
                   'concentration': item['concentration']}



import json

from flaskr.clinical_data.sample_models.factory import Factory as Factory
from flaskr.framework.abstract.abstract_collection import AbstractCollection


class Collection(AbstractCollection):
    name = 'sample'
    buffer = []

    def __init__(self):
        super().__init__(Factory())

    def __next__(self):
        if self.cursor is None:
            self.cursor = self.find()
        data = self.cursor.next()
        model = self.factory.create(data)
        return model

    def metadata_to_json(self):
        result = []
        for model in self:
            data = model.get_data()
            for dataKey, dataValue in data.items():
                metadata = {}
                metadata[dataKey] = dataValue
            result.append(model.get_data())
        return json.dumps(result)
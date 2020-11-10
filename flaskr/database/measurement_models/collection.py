import pandas as pd
import json

from flaskr.database.measurement_models.factory import Factory as MeasurementFactory
from flaskr.framework.abstract.abstract_collection import AbstractCollection
from bson import ObjectId


class Collection(AbstractCollection):
    name = 'measurement'
    buffer = []

    def __init__(self):
        super().__init__(MeasurementFactory())

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
                if dataKey != 'RFUs':
                    metadata[dataKey] = dataValue
                    if type(dataValue) is ObjectId:
                        # convert object ids to strings
                        data[dataKey] = str(dataValue)
            result.append(model.get_data())
        return json.dumps(result)
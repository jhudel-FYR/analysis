import json
from datetime import datetime
from bson import ObjectId


class AbstractModel:
    data = {}

    def __init__(self):
        self.data = {}
        self.data['_id'] = None

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, item):
        self.data[key] = item

    def __str__(self):
        result = ''
        for key, value in self.data.items():
            result += '%s: %s \n' % (key, str(value))

        return result

    def set_data(self, data):
        for key, value in data.items():
            self[key] = value

    def get_data(self):
        return self.data

    def get_id(self):
        return self.data['_id']

    def to_json(self):
        data = self.get_data()
        for dataKey, dataValue in data.items():
            if type(dataValue) in [ObjectId, datetime]:
                data[dataKey] = str(dataValue)
        return json.dumps(data)
